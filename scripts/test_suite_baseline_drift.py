#!/usr/bin/env python3
"""Test-suite baseline drift: detect it on main, bisect it, review it, scope its repair, and let
unrelated pull requests proceed.

The ratchet (scripts/check_test_suite_ratchet.py) compares the failing set of a head with
data/test-suite-baseline.json. When main itself fails a test the baseline does not hold, every
pull request inherits that red ratchet and work stops. This module is the coordinated answer.
It runs at E0: no LLM, stdlib only, no clock, no network.

- `detect` (push to main): the failing set at the head, minus the baseline, is the drift. For each
  drifted test, the first failing commit is found by bisecting main's first-parent history from the
  commit that last wrote the baseline, then (for a merge) the merged branch's own history. The
  output is a sealed receipt payload naming each test and its first failing commit, a dependency
  and implication review, and one scoped repair task with a finish point.
- `pr` (pull request): a test failing on the head but not in the baseline is
  PRE_EXISTING_BASELINE_FAILURE when it also fails on the base and the change's own diff does not
  touch it. That disposition is receipted and does not block; the change proceeds one rung down
  the ladder. A failure the change introduces, or a pre-existing one it touches, is FAIL_CLOSED.
  `pr --unittest-output` adjudicates a job that runs a named unittest module list (for example
  .github/workflows/cross-task-coordination-validation.yml) the same way: each FAIL/ERROR line is
  mapped to the ratchet's node id and probed at the base with unittest, the job's own runner. An
  outcome line that names no test (an import error, setUpClass) is FAIL_CLOSED, never dropped.

Every non-ALLOW record carries failure_code, failed_predicate, required_evidence_or_repair,
retry_entrypoint, owning_existing_goal and next_attempt.

Reuse, not reimplementation: the failing set and the comparison are the ratchet's own
(run_suite, load_baseline, compare); the seal is the admission evaluator's TVC rule
(scripts/evaluate_admission_job_observation.py seal/digest, result field `receipt_sha256`); the
epoch and the per-commit main-change receipt come from StegVerse-org/.github's main-change receipt
writer (resident-runtime/main_change_receipt.py) when it is supplied at its pin (--writer,
--writer-sha256). The epoch is otherwise supplied (--hb-epoch); it is never read from a clock.

Ledger: this module never appends or dispatches. The receipt carries `ledger_append`, which names
the appender it is addressed to, or a six-field FAIL_CLOSED when no manifest-directed appender
accepts it. Non-authorizing: it validates source and reports.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_test_suite_ratchet import BASELINE, compare, load_baseline, run_suite  # noqa: E402
from evaluate_admission_job_observation import digest, seal  # noqa: E402

DRIFT_SCHEMA = "stegverse.test-suite-baseline-drift/v1"
PR_SCHEMA = "stegverse.test-suite-pr-disposition/v1"
TASK_SCHEMA = "stegverse.test-suite-baseline-repair-task/v1"
REVIEW_SCHEMA = "stegverse.test-suite-baseline-drift-review/v1"
SEAL = "receipt_sha256"
DEFAULT_GOAL = "StegVerse-org/.github#166 ENTERPRISE-HOST-PROVIDER-ERADICATION-001"
LEDGER_GOAL = "StegVerse-org/.github#162 (organization ledger) / StegVerse-org/.github#166"
RETRY_DETECT = ".github/workflows/test-suite-ratchet.yml (push to main) -> scripts/test_suite_baseline_drift.py detect"
RETRY_PR = ".github/workflows/test-suite-ratchet.yml (pull_request) -> scripts/test_suite_baseline_drift.py pr"
UNITTEST, PYTEST = "unittest", "pytest"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
OUTCOME = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)")
UNITTEST_OUTCOME = re.compile(r"^(FAIL|ERROR): (\S+) \(([^)\s]+)\)")
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SUPPLIED_EPOCH = re.compile(r"^[0-9]+$")
PR_SUBJECT = (re.compile(r"^Merge pull request #(\d+)\b"), re.compile(r"\(#(\d+)\)\s*$"))
GOAL_REF = re.compile(r"(?:[A-Za-z0-9-]+/[A-Za-z0-9._-]+)?#\d+|\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{3}\b")
# Ledger appenders this payload could be addressed to, as they stand on the base this was written
# against. Neither accepts it today; the record says so in six fields instead of guessing.
APPENDER_CANDIDATES = (
    ".github/workflows/organization-ledger-merge-transfer.yml (live; ORGANIZATION_MAIN_MERGE_TRANSFER only)",
    ".github/workflows/organization-ledger-transition-reusable.yml (DRAFT; committed .stegverse/transition-requests/, no push caller)",
    "StegVerse-Labs/.github#3255 organization-ledger-transition-writer.yml (open draft; workflow_dispatch writer)",
)

PASS, FAIL, ABSENT, UNOBSERVED = "PASS", "FAIL", "ABSENT", "UNOBSERVED"


# -- records ------------------------------------------------------------------------------------------------

def item(code: str, predicate: str, repair: str, retry: str, goal: str, nxt: str, **detail: Any) -> dict:
    return {"failure_code": code, "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": retry, "owning_existing_goal": goal, "next_attempt": nxt, **detail}


def has_six(record: Mapping[str, Any]) -> bool:
    return all(isinstance(record.get(k), str) and record.get(k) for k in SIX)


# -- git ----------------------------------------------------------------------------------------------------

def git(root: Path | str, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def git_ok(root: Path | str, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True).returncode == 0


def rev(root: Path | str, ref: str) -> str:
    return git(root, "rev-parse", "--verify", ref + "^{commit}").strip()


def first_parent_line(root: Path | str, start: str, end: str) -> list[str]:
    """start, then each first-parent commit after it up to end (oldest first)."""
    line = git(root, "rev-list", "--first-parent", "--reverse", f"{start}..{end}").split()
    return [rev(root, start), *line]


def baseline_commit(root: Path | str, head: str, baseline: str = str(BASELINE)) -> str | None:
    out = git(root, "log", "--first-parent", "-1", "--format=%H", head, "--", baseline).strip()
    return out or None


def subject(root: Path | str, commit: str) -> str:
    return git(root, "log", "-1", "--format=%s", commit).strip()


def pull_request_of(root: Path | str, commit: str) -> int | None:
    s = subject(root, commit)
    for pattern in PR_SUBJECT:
        m = pattern.search(s)
        if m:
            return int(m.group(1))
    return None


def changed_paths(root: Path | str, older: str, newer: str) -> list[str]:
    return sorted(p for p in git(root, "diff", "--name-only", older, newer).splitlines() if p)


def parents(root: Path | str, commit: str) -> list[str]:
    return git(root, "rev-list", "--parents", "-n", "1", commit).split()[1:]


# -- probing one test at one commit -------------------------------------------------------------------------

class Prober:
    """Runs single tests at commits, each commit in its own detached worktree; results are cached."""

    def __init__(self, root: Path | str, python: str = sys.executable, runner: str = PYTEST) -> None:
        self.root, self.python, self.runner = Path(root), python, runner
        self.base = Path(tempfile.mkdtemp(prefix="baseline-drift-"))
        self.trees: dict[str, Path] = {}
        self.cache: dict[tuple[str, str], str] = {}

    def tree(self, commit: str) -> Path:
        if commit not in self.trees:
            path = self.base / commit[:12]
            git(self.root, "worktree", "add", "--detach", "--quiet", str(path), commit)
            self.trees[commit] = path
        return self.trees[commit]

    def status(self, commit: str, test_id: str) -> str:
        key = (commit, test_id)
        if key not in self.cache:
            test_file = test_id.split("::", 1)[0]
            if not git_ok(self.root, "cat-file", "-e", f"{commit}:{test_file}"):
                self.cache[key] = ABSENT
            elif self.runner == UNITTEST:
                self.cache[key] = self._unittest_status(commit, test_id)
            else:
                done = subprocess.run([self.python, "-m", "pytest", test_id, "-q", "--tb=no", "-p", "no:cacheprovider"],
                                      cwd=self.tree(commit), capture_output=True, text=True)
                failed = any(OUTCOME.match(l) for l in done.stdout.splitlines())
                if done.returncode == 0:
                    self.cache[key] = PASS
                elif done.returncode == 1 and failed:
                    self.cache[key] = FAIL
                elif done.returncode in (4, 5):   # node not found / nothing collected: the test is not there
                    self.cache[key] = ABSENT
                else:
                    self.cache[key] = UNOBSERVED
        return self.cache[key]

    def _unittest_status(self, commit: str, test_id: str) -> str:
        test_file, _, rest = test_id.partition("::")
        name = rest.split("::")[-1]
        source = git(self.root, "show", f"{commit}:{test_file}")
        if not re.search(rf"^\s*(?:async\s+)?def {re.escape(name)}\(", source, re.M):
            return ABSENT
        dotted = test_file[:-3].replace("/", ".") + "." + rest.replace("::", ".")
        done = subprocess.run([self.python, "-m", "unittest", dotted], cwd=self.tree(commit),
                              capture_output=True, text=True)
        if done.returncode == 0:
            return PASS
        if re.search(r"^FAILED \(", done.stderr, re.M) and re.search(r"^(?:FAIL|ERROR): ", done.stderr, re.M):
            return FAIL
        return UNOBSERVED

    def close(self) -> None:
        for path in self.trees.values():
            subprocess.run(["git", "-C", str(self.root), "worktree", "remove", "--force", str(path)],
                           capture_output=True)
        shutil.rmtree(self.base, ignore_errors=True)
        subprocess.run(["git", "-C", str(self.root), "worktree", "prune"], capture_output=True)


def first_failing(line: list[str], status: Callable[[str], str]) -> tuple[int | None, list[dict]]:
    """Index in `line` of the first commit where the test fails, by bisection, assuming the last fails.

    Returns (None, probes) when the first commit already fails (the failure predates the range).
    An UNOBSERVED probe is never treated as pass or fail: bisection stops and reports it.
    """
    probes: list[dict] = []

    def probe(i: int) -> str:
        s = status(line[i])
        probes.append({"commit": line[i], "status": s})
        return s

    if probe(0) == FAIL:
        return None, probes
    lo, hi = 0, len(line) - 1          # line[lo] does not fail; line[hi] fails
    while hi - lo > 1:
        mid = (lo + hi) // 2
        s = probe(mid)
        if s == UNOBSERVED:
            raise LookupError(line[mid])
        if s == FAIL:
            hi = mid
        else:
            lo = mid
    return hi, probes


# -- epoch and the main-change receipt writer ---------------------------------------------------------------

def load_writer(path: str | None, expected_sha256: str | None) -> tuple[Any, dict | None]:
    if not path:
        return None, None
    p = Path(path)
    if not p.is_file():
        return None, {"present": False, "path": path}
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    info = {"present": True, "path": path, "sha256": actual, "expected_sha256": expected_sha256,
            "at_pin": expected_sha256 is not None and actual == expected_sha256}
    if not info["at_pin"]:
        return None, info
    spec = importlib.util.spec_from_file_location("main_change_receipt_pinned", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PINNED_SHA256 = actual
    return module, info


def resolve_epoch(root: Path, supplied: str | None, writer: Any, goal: str) -> tuple[str | None, str, list[dict]]:
    if supplied:
        if SUPPLIED_EPOCH.match(supplied) and int(supplied) >= 32:
            return supplied, "SUPPLIED_ARGUMENT", []
        return None, "SUPPLIED_ARGUMENT_INVALID", [item(
            "HB_EPOCH_INVALID", "EPOCH_IS_SUPPLIED_NEVER_READ_FROM_A_CLOCK",
            "supply hb_epoch as ASCII digits with value >= 32", RETRY_DETECT, goal, "re-run with a valid --hb-epoch")]
    if writer is not None:
        epoch, head = writer.ledger_epoch(root)
        if epoch:
            return epoch, f"ORGANIZATION_LEDGER_HEAD {head}", []
    return None, "UNOBSERVED", [item(
        "HB_EPOCH_SOURCE_UNOBSERVED", "EPOCH_IS_SUPPLIED_NEVER_READ_FROM_A_CLOCK",
        "fetch refs/stegverse/organization-ledger read-only and supply the pinned main-change receipt writer "
        "(--writer/--writer-sha256), or pass --hb-epoch from the carrier", RETRY_DETECT, goal,
        "the next run with a readable organization ledger head")]


def main_change_receipt(root: Path, writer: Any, commit: str, repository: str) -> dict:
    """The main-change receipt for `commit`: read from the receipt ref when ledgered, else observed with the
    pinned writer (not appended), else stated as unavailable."""
    ref = "refs/stegverse/main-change-receipts"
    path = f"receipts/{commit}.json"
    if git_ok(root, "cat-file", "-e", f"{ref}:{path}"):
        return {"source": "LEDGERED", "ref": f"{ref}:{path}", "receipt": json.loads(git(root, "show", f"{ref}:{path}"))}
    if writer is not None:
        first = (parents(root, commit) or [None])[0]
        if first:
            receipts = writer.observe(root, repository=repository, before=first, after=commit,
                                      writer={"ref": "pinned", "sha256": getattr(writer, "PINNED_SHA256", None) or "UNOBSERVED"})
            if receipts:
                return {"source": "OBSERVED_NOT_LEDGERED", "ref": f"{ref}:{path}", "receipt": receipts[-1]}
    return {"source": "UNAVAILABLE", "ref": f"{ref}:{path}", "receipt": None}


def ledger_append(goal: str) -> dict:
    return {"disposition": "FAIL_CLOSED", **item(
        "DRIFT_RECEIPT_APPENDER_NOT_AVAILABLE", "MANIFEST_DIRECTED_APPENDER_ACCEPTS_THE_DRIFT_RECEIPT",
        "a manifest-directed organization-ledger appender that accepts this payload (operation "
        "TEST_SUITE_BASELINE_DRIFT); until one exists the payload is retained as the run artifact and nothing "
        "is appended or dispatched", RETRY_DETECT, LEDGER_GOAL,
        "the first run after a manifest-directed appender for this operation is on main",
        candidates=list(APPENDER_CANDIDATES), issue_class="B"), "operation": "TEST_SUITE_BASELINE_DRIFT",
        "appended": False, "dispatched": False, "addressed_goal": goal}


# -- review -------------------------------------------------------------------------------------------------

def workflows_running(root: Path, commit: str, test_id: str) -> list[str]:
    test_file = test_id.split("::", 1)[0]
    module = test_file[:-3].replace("/", ".") if test_file.endswith(".py") else test_file
    names = []
    for path in git(root, "ls-tree", "--name-only", commit, ".github/workflows/").split():
        text = git(root, "show", f"{commit}:{path}")
        if test_file in text or module in text:
            names.append(path)
    return sorted(names)


def goal_refs(root: Path, older: str, newer: str) -> list[str]:
    text = git(root, "log", "--format=%B", f"{older}..{newer}")
    return sorted(set(GOAL_REF.findall(text)))


def review_one(root: Path, head: str, entry: Mapping[str, Any], open_prs: list[Mapping[str, Any]]) -> dict:
    test_id = entry["test"]
    test_file = test_id.split("::", 1)[0]
    first = entry.get("first_failing_commit")
    intro = entry.get("introducing_commit") or first
    paths, refs, pr = [], [], None
    if first:
        before = (parents(root, first) or [first])[0]
        paths = changed_paths(root, before, first)
        refs = goal_refs(root, before, first)
        pr = pull_request_of(root, first)
    direct = [w for w in workflows_running(root, head, test_id) if not w.endswith("test-suite-ratchet.yml")]
    touching = sorted({int(p["number"]) for p in open_prs
                       if test_file in (p.get("files") or []) or set(paths) & set(p.get("files") or [])})
    return {
        "test": test_id,
        "first_failing_commit": first,
        "introducing_commit": intro,
        "introducing_pull_request": pr,
        "introducing_subject": subject(root, intro) if intro else None,
        "classification": entry["classification"],
        "test_file_changed_by_introducing_change": test_file in paths,
        "introducing_changed_paths": paths,
        "implicated_goal_refs": refs,
        "blocks": {
            "ratchet_on_every_pull_request": "NO_WITH_THIS_CAPABILITY (PRE_EXISTING_BASELINE_FAILURE, receipted)",
            "workflows_running_the_test_directly": direct,
            "open_pull_requests_touching_test_or_introducing_paths": touching,
        },
    }


# -- detect (main) ------------------------------------------------------------------------------------------

def detect(root: Path, head: str, *, baseline_path: str, observed: set[str] | None, epoch_arg: str | None,
           writer_path: str | None, writer_sha256: str | None, repository: str, goal: str,
           open_prs: list[Mapping[str, Any]], python: str = sys.executable) -> dict:
    root = Path(root)
    head = rev(root, head)
    baseline = json.loads(git(root, "show", f"{head}:{baseline_path}"))
    if observed is None:
        observed = run_suite_at(root, head, python)
    report = compare(observed, baseline)
    writer, writer_info = load_writer(writer_path, writer_sha256)
    epoch, epoch_source, items = resolve_epoch(root, epoch_arg, writer, goal)
    if writer_info is not None and not writer_info.get("at_pin"):
        items.append(item("MAIN_CHANGE_RECEIPT_WRITER_NOT_AT_PIN", "WRITER_SHA256_EQUALS_THE_PIN",
                          "supply StegVerse-org/.github resident-runtime/main_change_receipt.py at the pinned commit",
                          RETRY_DETECT, goal, "the next run with the writer at its pin", writer=writer_info))
    start = baseline_commit(root, head, baseline_path)
    drift = []
    prober = Prober(root, python)
    try:
        line = first_parent_line(root, start, head) if start else [head]
        for test_id in report["newly_failing"]:
            entry: dict[str, Any] = {"test": test_id, "bisect_range": {"good_candidate": line[0], "bad": head,
                                                                       "first_parent_commits": len(line)}}
            try:
                index, probes = first_failing(line, lambda c: prober.status(c, test_id))
            except LookupError as exc:
                entry.update({"classification": "UNOBSERVED_DURING_BISECT", "first_failing_commit": None,
                              "unobserved_at": str(exc)})
                drift.append(entry)
                continue
            entry["probes"] = probes
            if index is None:
                entry.update({"classification": "PRE_EXISTING_NOT_RECORDED_IN_BASELINE", "first_failing_commit": None,
                              "fails_at_baseline_commit": line[0]})
            else:
                first = line[index]
                entry.update({"classification": "INTRODUCED_ON_MAIN_AFTER_BASELINE", "first_failing_commit": first,
                              "last_passing_commit": line[index - 1],
                              "status_before": prober.status(line[index - 1], test_id)})
                ps = parents(root, first)
                if len(ps) == 2:
                    branch = first_parent_line(root, git(root, "merge-base", ps[0], ps[1]).strip(), ps[1])
                    if prober.status(ps[1], test_id) == FAIL:
                        try:
                            j, bprobes = first_failing(branch, lambda c: prober.status(c, test_id))
                        except LookupError:
                            j, bprobes = None, []
                        entry["branch_probes"] = bprobes
                        entry["introducing_commit"] = branch[j] if j is not None else first
                    else:
                        entry["introducing_commit"] = first
                        entry["introduced_by_merge_interaction"] = True
                else:
                    entry["introducing_commit"] = first
                entry["main_change_receipt"] = main_change_receipt(root, writer, first, repository)
            drift.append(entry)
    finally:
        prober.close()
    review = {"schema": REVIEW_SCHEMA, "head": head, "repository": repository,
              "failures": [review_one(root, head, e, open_prs) for e in drift]}
    review = seal(review, SEAL)
    task = repair_task(head, drift, review, goal, repository) if drift else None
    body: dict[str, Any] = {
        "schema": DRIFT_SCHEMA, "repository": repository, "head": head, "lowest_supported_mode": "E0",
        "hb_epoch": epoch, "hb_epoch_source": epoch_source, "derived_from_clock": False,
        "baseline": {"path": baseline_path, "blob": git(root, "rev-parse", f"{head}:{baseline_path}").strip(),
                     "written_at_commit": start},
        "ratchet": report, "drift": drift, "review_sha256": review[SEAL],
        "repair_task_id": task["task_id"] if task else None,
        "writer": writer_info, "ledger_append": ledger_append(goal), "authority_effect": "NONE",
    }
    if drift:
        body.update({"disposition": "FAIL_CLOSED", **item(
            "TEST_SUITE_RATCHET_BASELINE_DRIFT_ON_MAIN", "MAIN_FAILING_SET_IS_WITHIN_BASELINE",
            f"complete repair task {task['task_id']}: {task['finish_point']}", RETRY_DETECT, goal,
            "the next push to main; pull requests that do not touch these tests proceed with "
            "PRE_EXISTING_BASELINE_FAILURE")})
    else:
        body["disposition"] = "ALLOW"
    body["items"] = items
    return {"receipt": seal(body, SEAL), "review": review, "repair_task": task}


def repair_task(head: str, drift: list[dict], review: Mapping[str, Any], goal: str, repository: str) -> dict:
    tests = sorted(e["test"] for e in drift)
    ident = digest({"repository": repository, "tests": tests})[7:19].upper()
    paths = sorted({e["test"].split("::", 1)[0] for e in drift}
                   | {p for f in review["failures"] for p in f["introducing_changed_paths"]
                      if not p.startswith("tests/")})
    return seal({
        "schema": TASK_SCHEMA, "task_id": f"TEST-SUITE-BASELINE-DRIFT-REPAIR-{ident}", "repository": repository,
        "owning_existing_goal": goal, "observed_at_head": head, "lowest_supported_mode": "E0",
        "scope": {"tests": tests, "candidate_paths": paths,
                  "first_failing_commits": {e["test"]: e.get("first_failing_commit") for e in drift}},
        "finish_point": ("at one main head every listed test passes, check_test_suite_ratchet.py reports new=0, "
                         "and this module's detect receipt at that head is ALLOW"),
        "out_of_scope": "baseline edits that add these tests (that records the drift, it does not repair it)",
        "retry_entrypoint": RETRY_DETECT, "authority_effect": "NONE",
    }, SEAL)


def run_suite_at(root: Path, commit: str, python: str) -> set[str]:
    """The failing set at `commit`, by the ratchet's own runner, in a worktree when commit is not checked out."""
    if git_ok(root, "diff", "--quiet", commit) and rev(root, "HEAD") == commit:
        return run_suite("tests")
    prober = Prober(root, python)
    try:
        tree = prober.tree(commit)
        done = subprocess.run([python, "-m", "pytest", "tests", "-q", "--tb=no", "-p", "no:cacheprovider"],
                              cwd=tree, capture_output=True, text=True)
        return {m.group(1) for l in done.stdout.splitlines() if (m := OUTCOME.match(l))}
    finally:
        prober.close()


# -- pr -----------------------------------------------------------------------------------------------------

def pr_disposition(root: Path, base: str, head: str, *, baseline_path: str, observed: set[str], goal: str,
                   repository: str, epoch: str | None, python: str = sys.executable, runner: str = PYTEST,
                   unparsed: list[str] | None = None, suite_status: int | None = None,
                   retry_pr: str = RETRY_PR) -> dict:
    root = Path(root)
    base, head = rev(root, base), rev(root, head)
    baseline = json.loads((root / baseline_path).read_text(encoding="utf-8")) \
        if (root / baseline_path).is_file() else json.loads(git(root, "show", f"{head}:{baseline_path}"))
    report = compare(observed, baseline)
    diff = set(changed_paths(root, base, head))
    rows = []
    for line in unparsed or []:
        rows.append({"test": None, "outcome_line": line, "disposition": "FAIL_CLOSED", "blocking": True, **item(
            "TEST_OUTCOME_NAMES_NO_TEST", "EVERY_FAILING_OUTCOME_NAMES_A_TEST",
            "the runner reported a failure that names no test (an import error, a setUpClass or module fixture); "
            "it cannot be matched to the baseline, so fix it in this change", retry_pr, goal,
            "the next push to this pull request")})
    if suite_status not in (None, 0) and not observed and not unparsed:
        rows.append({"test": None, "suite_status": suite_status, "disposition": "FAIL_CLOSED", "blocking": True,
                     **item("SUITE_FAILED_WITHOUT_TEST_OUTCOME", "A_FAILED_SUITE_NAMES_ITS_FAILING_TESTS",
                            f"the suite exited {suite_status} and reported no failing test; nothing can be judged "
                            "pre-existing on no evidence", retry_pr, goal, "re-run the job")})
    prober = Prober(root, python, runner)
    try:
        for test_id in report["newly_failing"]:
            test_file = test_id.split("::", 1)[0]
            at_base = prober.status(base, test_id)
            touched = test_file in diff
            row: dict[str, Any] = {"test": test_id, "status_at_base": at_base, "test_file_in_change_diff": touched}
            if at_base == FAIL and not touched:
                row.update({"disposition": "PRE_EXISTING_BASELINE_FAILURE", "blocking": False, **item(
                    "PRE_EXISTING_BASELINE_FAILURE", "MAIN_FAILING_SET_IS_WITHIN_BASELINE",
                    "repaired under the drift repair task emitted by detect on main; this change neither touches "
                    "nor introduces it", RETRY_DETECT, goal,
                    "the push to main that completes the repair task; this change proceeds now")})
            elif at_base == FAIL:
                row.update({"disposition": "FAIL_CLOSED", "blocking": True, **item(
                    "BASELINE_FAILURE_TOUCHED_BY_CHANGE", "CHANGE_DOES_NOT_TOUCH_A_FAILING_TEST_WITHOUT_FIXING_IT",
                    f"this change edits {test_file} and the test still fails: fix it in this change or leave it to "
                    "the drift repair task", retry_pr, goal, "the next push to this pull request")})
            elif at_base in (PASS, ABSENT):
                row.update({"disposition": "FAIL_CLOSED", "blocking": True, **item(
                    "TEST_FAILURE_INTRODUCED_BY_CHANGE", "NO_NEW_TEST_FAILURE",
                    "fix the failing test in this change; it passes (or does not exist) on the base", retry_pr, goal,
                    "the next push to this pull request")})
            else:
                row.update({"disposition": "FAIL_CLOSED", "blocking": True, **item(
                    "BASE_STATUS_UNOBSERVED", "BASE_STATUS_IS_OBSERVED",
                    "the test could not be run on the base commit; the change is not judged pre-existing on no "
                    "evidence", retry_pr, goal, "re-run the job")})
            rows.append(row)
    finally:
        prober.close()
    blocking = [r for r in rows if r["blocking"]]
    body: dict[str, Any] = {"schema": PR_SCHEMA, "repository": repository, "base": base, "head": head,
                            "lowest_supported_mode": "E0", "hb_epoch": epoch, "derived_from_clock": False,
                            "runner": runner, "ratchet": report, "tests": rows, "authority_effect": "NONE"}
    if blocking:
        first = blocking[0]
        body.update({"disposition": "FAIL_CLOSED", **{k: first[k] for k in SIX}})
    elif rows:
        body.update({"disposition": "PRE_EXISTING_BASELINE_FAILURE", **{k: rows[0][k] for k in SIX},
                     "degraded_not_stopped": True})
    else:
        body["disposition"] = "ALLOW"
    return seal(body, SEAL)


# -- cli ----------------------------------------------------------------------------------------------------

def unittest_node(name: str, dotted: str) -> str | None:
    """`FAIL: name (tests.mod.Class.name)` (or the pre-3.11 `(tests.mod.Class)`) -> tests/mod.py::Class::name."""
    parts = dotted.split(".")
    if parts and parts[-1] == name:
        parts = parts[:-1]
    if len(parts) < 2 or not IDENT.match(name) or not name.startswith("test") or parts[0] == "unittest" \
            or not all(IDENT.match(p) for p in parts):
        return None
    return "/".join(parts[:-1]) + ".py::" + parts[-1] + "::" + name


def observed_unittest(path: str) -> tuple[set[str], list[str]]:
    found, unparsed = set(), []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = UNITTEST_OUTCOME.match(line)
        if m:
            node = unittest_node(m.group(2), m.group(3))
            if node:
                found.add(node)
            else:
                unparsed.append(line.strip())
    return found, sorted(set(unparsed))


def _observed(path: str | None) -> set[str] | None:
    if not path:
        return None
    text = Path(path).read_text(encoding="utf-8")
    return {m.group(1) for l in text.splitlines() if (m := OUTCOME.match(l))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".")
    common.add_argument("--head", default="HEAD")
    common.add_argument("--baseline", default=str(BASELINE))
    common.add_argument("--repository", default="StegVerse-Labs/.github")
    common.add_argument("--owning-goal", default=DEFAULT_GOAL)
    common.add_argument("--pytest-output", help="pytest -q output already produced for --head (else it is run)")
    common.add_argument("--hb-epoch")
    common.add_argument("--out-dir", required=True)
    common.add_argument("--writer", help="StegVerse-org/.github resident-runtime/main_change_receipt.py")
    common.add_argument("--writer-sha256", help="the writer's pinned sha256; any other bytes are not loaded")
    d = sub.add_parser("detect", parents=[common])
    d.add_argument("--open-prs", help="JSON list of {number, files} for the implication review")
    p = sub.add_parser("pr", parents=[common])
    p.add_argument("--base", required=True)
    p.add_argument("--unittest-output", help="`python -m unittest -v` output already produced for --head; its "
                   "FAIL/ERROR lines are the observed set and the base is probed with unittest")
    p.add_argument("--suite-status", type=int, help="exit status of the run that produced the output")
    p.add_argument("--retry-entrypoint", default=RETRY_PR, help="the workflow a blocked change re-runs")
    args = parser.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(args.root).resolve()
    if args.command == "detect":
        open_prs = json.loads(Path(args.open_prs).read_text()) if args.open_prs else []
        result = detect(root, args.head, baseline_path=args.baseline, observed=_observed(args.pytest_output),
                        epoch_arg=args.hb_epoch, writer_path=args.writer, writer_sha256=args.writer_sha256,
                        repository=args.repository, goal=args.owning_goal, open_prs=open_prs)
        for name, record in result.items():
            if record is not None:
                (out / f"{name.replace('_', '-')}.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        receipt = result["receipt"]
        print(json.dumps({k: receipt.get(k) for k in ("disposition", *SIX, "repair_task_id", SEAL)
                          if receipt.get(k) is not None}, sort_keys=True))
        for e in receipt["drift"]:
            print(f"DRIFT {e['test']} first_failing_commit={e.get('first_failing_commit')} {e['classification']}")
        return 0 if receipt["disposition"] == "ALLOW" else 1
    unparsed: list[str] = []
    runner = PYTEST
    if args.unittest_output:
        observed, unparsed = observed_unittest(args.unittest_output)
        runner = UNITTEST
    else:
        observed = _observed(args.pytest_output)
        if observed is None:
            observed = run_suite("tests")
    writer, _info = load_writer(args.writer, args.writer_sha256)
    epoch, _source, _items = resolve_epoch(root, args.hb_epoch, writer, args.owning_goal)
    record = pr_disposition(root, args.base, args.head, baseline_path=args.baseline, observed=observed,
                            goal=args.owning_goal, repository=args.repository, epoch=epoch, runner=runner,
                            unparsed=unparsed, suite_status=args.suite_status, retry_pr=args.retry_entrypoint)
    (out / "pr-disposition.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: record.get(k) for k in ("disposition", *SIX, SEAL) if record.get(k) is not None},
                     sort_keys=True))
    for row in record["tests"]:
        print(f"{row['disposition']} {row['test'] or row.get('outcome_line') or row.get('failure_code')} "
              f"blocking={row['blocking']}")
    return 1 if record["disposition"] == "FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
