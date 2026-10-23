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
DEFAULT_RETRY_DETECT = RETRY_DETECT   # --detect-entrypoint names another repository's detect workflow
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
PROBE_SKIPPED = "SKIPPED"   # the probe ran nothing it could judge: skipped, xfail/xpass, or 0 tests


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
                tally = " ".join(done.stdout.splitlines()[-3:])
                if re.search(r"\d+ (?:skipped|xfailed|xpassed)\b", tally) and not failed:
                    self.cache[key] = PROBE_SKIPPED
                elif done.returncode == 0:
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
        if "::" not in rest:                    # a module-level function: unittest cannot run it
            return PROBE_SKIPPED
        dotted = test_file[:-3].replace("/", ".") + "." + rest.replace("::", ".")
        done = subprocess.run([self.python, "-m", "unittest", dotted], cwd=self.tree(commit),
                              capture_output=True, text=True)
        if re.search(r"^Ran 0 tests", done.stderr, re.M) or re.search(
                r"(?:skipped|expected failures|unexpected successes)=\d+", done.stderr):
            return PROBE_SKIPPED
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
           open_prs: list[Mapping[str, Any]], python: str = sys.executable,
           verification_rows: list[dict] | None = None, verification: Mapping[str, Any] | None = None,
           runner: str = PYTEST, bisect_start: str | None = None) -> dict:
    root = Path(root)
    head = rev(root, head)
    if git_ok(root, "cat-file", "-e", f"{head}:{baseline_path}"):
        baseline = json.loads(git(root, "show", f"{head}:{baseline_path}"))
        baseline_blob, baseline_read_from = git(root, "rev-parse", f"{head}:{baseline_path}").strip(), "HEAD_TREE"
    elif (root / baseline_path).is_file():
        # a baseline introduced by the change under review, judged against an older head (e.g. the main head a
        # new repository's first baseline is receipted at): read from the checkout, its blob recorded
        baseline = json.loads((root / baseline_path).read_text(encoding="utf-8"))
        baseline_blob = git(root, "hash-object", str(root / baseline_path)).strip()
        baseline_read_from = "CHECKOUT"
    else:
        raise SystemExit(f"baseline {baseline_path} is neither in {head} nor in the checkout")
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
    if start is None and bisect_start:
        # no commit on this line wrote the baseline: bisect from the supplied start (a commit where the
        # failing tests are absent or pass, e.g. the repository's first commit); absent counts as not failing
        start = rev(root, bisect_start)
    drift = []
    prober = Prober(root, python, runner)
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
        "baseline": {"path": baseline_path, "blob": baseline_blob, "read_from": baseline_read_from,
                     "written_at_commit": baseline_commit(root, head, baseline_path), "bisect_start": start,
                     "pre_existing_until": baseline.get("pre_existing_until")},
        "runner": runner,
        "ratchet": report, "drift": drift, "review_sha256": review[SEAL],
        "repair_task_id": task["task_id"] if task else None,
        "writer": writer_info, "ledger_append": ledger_append(goal), "authority_effect": "NONE",
    }
    vrows = list(verification_rows or [])
    body["verification"] = {**(verification or {}), "required_verification_skipped": len(vrows), "rows": vrows}
    if vrows:
        body.update({"disposition": "FAIL_CLOSED", **{k: vrows[0][k] for k in SIX}})
    elif drift:
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
        "finish_point": ("at one main head every listed test passes, the ratchet comparison against the baseline "
                         "reports new=0 (newly_failing empty), and this module's detect receipt at that head is ALLOW"),
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
                   retry_pr: str = RETRY_PR, verification_rows: list[dict] | None = None,
                   verification: Mapping[str, Any] | None = None,
                   baseline_receipt: Mapping[str, Any] | None = None) -> dict:
    root = Path(root)
    base, head = rev(root, base), rev(root, head)
    baseline = json.loads((root / baseline_path).read_text(encoding="utf-8")) \
        if (root / baseline_path).is_file() else json.loads(git(root, "show", f"{head}:{baseline_path}"))
    report = compare(observed, baseline)
    diff = set(changed_paths(root, base, head))
    rows = list(verification_rows or [])
    for line in unparsed or []:
        rows.append(rvs_row("COLLECTION_ERROR", None,
                            "the runner reported a failure that names no test (an import error, a setUpClass or module "
                            "fixture), so the tests behind it did not run; fix it in this change", retry_pr, goal,
                            "the next push to this pull request", outcome_line=line))
    if suite_status not in (None, 0) and not observed and not unparsed:
        rows.append(rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None,
                            f"the suite exited {suite_status} and reported no failing test, so it is not shown that "
                            "the tests ran; nothing can be judged pre-existing on no evidence", retry_pr, goal,
                            "re-run the job", suite_status=suite_status))
    prober = Prober(root, python, runner)
    try:
        for test_id in report["newly_failing"]:
            test_file = test_id.split("::", 1)[0]
            if "::" not in test_id:                 # a module-level ERROR: the module did not collect
                if not any(r.get("test") == test_id and r.get("kind") == "COLLECTION_ERROR" for r in rows):
                    rows.append(rvs_row("COLLECTION_ERROR", test_id, "the module did not collect, so none of its "
                                        "tests ran; fix the import or collection error", retry_pr, goal,
                                        "the next push to this pull request"))
                continue
            at_base = prober.status(base, test_id)
            touched = test_file in diff
            row: dict[str, Any] = {"test": test_id, "status_at_base": at_base, "test_file_in_change_diff": touched}
            if at_base == FAIL and not touched:
                row.update({"disposition": "PRE_EXISTING_BASELINE_FAILURE", "blocking": False, **item(
                    "PRE_EXISTING_BASELINE_FAILURE", "MAIN_FAILING_SET_IS_WITHIN_BASELINE",
                    "repaired under the drift repair task emitted by detect on main; this change neither touches "
                    "nor introduces it", RETRY_DETECT, goal,
                    "the push to main that completes the repair task; this change proceeds now")})
                if baseline.get("pre_existing_until"):
                    row["pre_existing_until"] = baseline["pre_existing_until"]
                if baseline_receipt is not None:
                    row["baseline_receipt"] = receipt_link(baseline_receipt, test_id)
            elif at_base == FAIL:
                row.update({"disposition": "FAIL_CLOSED", "blocking": True, **item(
                    "BASELINE_FAILURE_TOUCHED_BY_CHANGE", "CHANGE_DOES_NOT_TOUCH_A_FAILING_TEST_WITHOUT_FIXING_IT",
                    f"this change edits {test_file} and the test still fails: fix it in this change or leave it to "
                    "the drift repair task", retry_pr, goal, "the next push to this pull request")})
            elif at_base == PROBE_SKIPPED:
                row.update(rvs_row("BASE_PROBE_SKIPPED", test_id, "the test was skipped (or ran no test) on the "
                                   "base, so it was never observed failing there; it is not pre-existing", retry_pr,
                                   goal, "the next push to this pull request", status_at_base=at_base,
                                   test_file_in_change_diff=touched))
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
    if baseline_receipt is not None:
        verification = {**(verification or {}), "baseline_receipt": {
            k: baseline_receipt.get(k) for k in ("path", SEAL, "head", "seal_verifies")}}
    body: dict[str, Any] = {"schema": PR_SCHEMA, "repository": repository, "base": base, "head": head,
                            "lowest_supported_mode": "E0", "hb_epoch": epoch, "derived_from_clock": False,
                            "runner": runner, "ratchet": report, "tests": rows, "authority_effect": "NONE",
                            "verification": {**(verification or {}),
                                             "required_verification_skipped": sum(1 for r in rows
                                                                                  if r.get("failure_code") == RVS)}}
    if blocking:
        first = blocking[0]
        body.update({"disposition": "FAIL_CLOSED", **{k: first[k] for k in SIX}})
    elif rows:
        body.update({"disposition": "PRE_EXISTING_BASELINE_FAILURE", **{k: rows[0][k] for k in SIX},
                     "degraded_not_stopped": True})
    else:
        body["disposition"] = "ALLOW"
    return seal(body, SEAL)


def load_baseline_receipt(path: str) -> dict:
    """A detect receipt (this module's own output) naming each pre-existing failure and its first failing commit;
    its seal is checked, never assumed."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"path": path, SEAL: record.get(SEAL), "head": record.get("head"),
            "seal_verifies": seal({k: v for k, v in record.items() if k != SEAL}, SEAL).get(SEAL) == record.get(SEAL),
            "drift": {e["test"]: e for e in record.get("drift") or []}}


def receipt_link(receipt: Mapping[str, Any], test_id: str) -> dict:
    entry = receipt["drift"].get(test_id) if receipt.get("seal_verifies") else None
    if entry is None:
        return {"receipted": False, "receipt_sha256": receipt.get(SEAL), "seal_verifies": receipt.get("seal_verifies"),
                "detail": "failing on the base but not named by a seal-verifying baseline receipt: the next detect "
                          "run on main receipts it"}
    return {"receipted": True, "receipt_sha256": receipt[SEAL], "receipt_head": receipt.get("head"),
            "classification": entry.get("classification"), "first_failing_commit": entry.get("first_failing_commit"),
            "introducing_commit": entry.get("introducing_commit")}


def load_selection(path: str) -> dict:
    """scripts/test_set_selection.py's sealed selection: which sets this change selected and why, what ran, and the
    six-field items for selected sets whose inputs are unavailable. Its seal is checked, never assumed."""
    from test_set_selection import seal_verifies as selection_seal_verifies
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    return {**record, "path": path, "seal_verifies": selection_seal_verifies(record)}


def in_selection(node: str, selection: Mapping[str, Any] | None) -> bool:
    """A test node is in scope when a runnable selected set runs it and no deselection removes it."""
    if selection is None:
        return True

    def under(n: str, t: str) -> bool:
        return n == t or n.startswith(t + "::") or n.startswith(t + "[") or n.startswith(t + ".")
    run = selection.get("run", {})
    return any(under(node, t) for t in run.get("tests", [])) and \
        not any(under(node, d) for d in run.get("deselect", []))


def selection_rows(selection: Mapping[str, Any], retry: str, goal: str, root: Path | None = None,
                   base: str | None = None) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    nxt = "the next run of this job at the exact head"
    if not selection.get("seal_verifies"):
        rows.append(rvs_row("SELECTION_UNVERIFIED", selection.get("path"), "the test-set selection's seal does not "
                            "verify, so it is not shown which sets this change requires; re-run the selection",
                            retry, goal, nxt))
    if root is not None:
        # the sealed record must be for the exact head (and base) this adjudication runs on, never a reused one
        from test_set_selection import resolve
        here = resolve(root, "HEAD")
        if selection.get("head_sha") != here or here is None:
            rows.append(rvs_row("SELECTION_HEAD_MISMATCH", selection.get("path"), f"the selection was computed for "
                                f"head {selection.get('head_sha')!r}, not this head {here!r}; select on this head",
                                retry, goal, nxt, selection_head_sha=selection.get("head_sha"), head_sha=here))
        if base is not None:
            want = resolve(root, base)
            if selection.get("base_sha") != want or want is None:
                rows.append(rvs_row("SELECTION_BASE_MISMATCH", selection.get("path"), f"the selection was computed "
                                    f"against base {selection.get('base_sha')!r}, not this base {want!r}; select "
                                    "against this base", retry, goal, nxt, selection_base_sha=selection.get("base_sha"),
                                    base_sha=want))
    for u in list(selection.get("rows") or []) + list(selection.get("input_unavailable") or []):
        rows.append({"test": f"set:{u.get('set')}" if u.get("set") else u.get("failure_code"),
                     "kind": "INPUT_UNAVAILABLE" if u.get("set") else u.get("failure_code"),
                     "disposition": "FAIL_CLOSED", "blocking": True,
                     **{k: u[k] for k in SIX}, **{k: u[k] for k in ("set", "input") if k in u}})
    info = {"path": selection.get("path"), SEAL: selection.get(SEAL), "seal_verifies": selection.get("seal_verifies"),
            "head_sha": selection.get("head_sha"), "base_sha": selection.get("base_sha"),
            "pr_head_sha": selection.get("pr_head_sha"),
            "mode": selection.get("mode"), "all_reasons": selection.get("all_reasons"),
            "sets_total": selection.get("sets_total"), "selected_count": selection.get("selected_count"),
            "not_selected_count": selection.get("not_selected_count"),
            "selected": [{"id": x["id"], "runnable": x["runnable"], "reasons": x["reasons"]}
                         for x in selection.get("selected", [])]}
    return rows, info


# -- required verification: nothing skipped, nothing unrun, nothing missing ------------------------------------
#
# Rigel's standing rule (relayed by Coordination, Oct 23): merge readiness needs the full suite run on the
# exact head with 0 skipped. Drift handling only ever marks a receipted pre-existing FAILURE non-blocking; a
# test that was skipped, xfailed/xpassed, not collected, not run, or present at the base but missing at the
# head, and a required job a path filter leaves unrun on a change in its scope, are each FAIL_CLOSED
# REQUIRED_VERIFICATION_SKIPPED (six fields) and are never PRE_EXISTING_BASELINE_FAILURE.

RVS = "REQUIRED_VERIFICATION_SKIPPED"
SKIPPED, NOT_RUN = "SKIPPED", "NOT_RUN"
PREDICATES = {
    "SELECTION_UNVERIFIED": "TEST_SET_SELECTION_SEAL_VERIFIES",
    "SELECTION_HEAD_MISMATCH": "TEST_SET_SELECTION_IS_BOUND_TO_THIS_EXACT_HEAD",
    "SELECTION_BASE_MISMATCH": "TEST_SET_SELECTION_IS_BOUND_TO_THIS_EXACT_BASE",
    "SKIPPED": "REQUIRED_TEST_IS_NOT_SKIPPED",
    "XFAIL": "REQUIRED_TEST_IS_NOT_SKIPPED",
    "XPASS": "REQUIRED_TEST_IS_NOT_SKIPPED",
    "EXPECTED_FAILURE": "REQUIRED_TEST_IS_NOT_SKIPPED",
    "UNEXPECTED_SUCCESS": "REQUIRED_TEST_IS_NOT_SKIPPED",
    "COLLECTION_ERROR": "REQUIRED_MODULE_IS_COLLECTED_AND_RUN",
    "MODULE_NOT_RUN": "REQUIRED_MODULE_IS_COLLECTED_AND_RUN",
    "TEST_NOT_RUN": "EVERY_REQUIRED_TEST_RUNS_AT_THE_EXACT_HEAD",
    "REQUIRED_TEST_NOT_RUN_IN_REQUIRED_JOB": "EVERY_REQUIRED_TEST_RUNS_AT_THE_EXACT_HEAD",
    "TEST_MISSING_AT_HEAD": "TEST_PRESENT_AT_BASE_RUNS_AT_HEAD",
    "BASE_PROBE_SKIPPED": "BASE_STATUS_IS_OBSERVED_BY_RUNNING_THE_TEST",
    "SUITE_ACCOUNTING_UNOBSERVED": "EVERY_TEST_OUTCOME_IS_ACCOUNTED",
    "REQUIRED_JOB_PATH_FILTERED_OUT": "REQUIRED_JOB_RUNS_ON_A_CHANGE_IN_ITS_SCOPE",
    "REQUIRED_JOB_MISSING": "EVERY_REQUIRED_JOB_AT_THE_BASE_EXISTS_AT_THE_HEAD",
}
JUNIT_SUMMARY = re.compile(r"(\d+) (passed|failed|skipped|xfailed|xpassed|errors?|deselected|warnings?)\b")
XPASS_LINE = re.compile(r"^XPASS (\S+)")
COLLECT_ERROR_LINE = re.compile(r"^ERROR (\S+\.py)(?:\s|$)")
UNITTEST_RESULT = re.compile(r"^(\S+) \(([^)\s]+)\)(?:\n.*?)? \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$")
UNITTEST_HEAD = re.compile(r"^(\S+) \(([^)\s]+)\)(?: \.\.\. (.*))?$")
UNITTEST_TAIL = re.compile(r" \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$")
UNITTEST_WORD = re.compile(r"^(ok|FAIL|ERROR|skipped '.*'|expected failure|unexpected success)$")
# a test's own output printed without a trailing newline glues the outcome word onto its last line (`}ok`)
UNITTEST_GLUED = re.compile(r"(?:^|[^\w'\"])(ok|FAIL|ERROR|expected failure|unexpected success)$")
# the failure summary (`FAIL: name (id)` / `ERROR: name (id) (params)`) is authoritative for failing outcomes
UNITTEST_SUMMARY = re.compile(r"^(FAIL|ERROR): (\S+) \(([^)\s]+)\)")
UNITTEST_SUBTEST = re.compile(r"^\s+(\S+) \(([^)\s]+)\) \(.*\) \.\.\. (ok|FAIL|ERROR|skipped.*)$")
UNITTEST_COUNTS = re.compile(r"^(?:OK|FAILED) \((.*)\)$|^OK$")
UNITTEST_RAN = re.compile(r"^Ran (\d+) tests? in ")
REFERENCED_PATH = re.compile(r"(?<![\w./-])((?:tests|scripts|resident-runtime|workers)/[\w./-]+\.py)\b")
REFERENCED_MODULE = re.compile(r"(?<![\w.])(tests(?:\.\w+)+)\b")


def rvs_row(kind: str, subject: str | None, repair: str, retry: str, goal: str, nxt: str, **detail: Any) -> dict:
    return {"test": subject, "kind": kind, "disposition": "FAIL_CLOSED", "blocking": True,
            **item(RVS, PREDICATES[kind], repair, retry, goal, nxt), **detail}


def _module_path(root: Path, dotted_parts: list[str]) -> tuple[str, list[str]] | None:
    """Longest prefix of dotted parts that is a .py file under root -> (path, remaining parts)."""
    for k in range(len(dotted_parts), 0, -1):
        rel = "/".join(dotted_parts[:k]) + ".py"
        if (root / rel).is_file():
            return rel, dotted_parts[k:]
    return None


def junit_cases(root: Path, junit_path: str) -> list[dict]:
    """pytest --junitxml testcases as {node, outcome, kind, message}; outcome PASS/FAIL/SKIPPED/NOT_RUN."""
    import xml.etree.ElementTree as ET
    cases = []
    for tc in ET.parse(junit_path).getroot().iter("testcase"):
        classname, name = tc.get("classname") or "", tc.get("name") or ""
        children = {c.tag: c for c in tc}
        message = next((c.get("message") or "" for c in tc if c.tag in ("skipped", "error", "failure")), "")
        if "error" in children and "collection failure" in message.lower() or (not classname and "error" in children):
            path = name.replace(".", "/") + ".py" if not name.endswith(".py") else name
            cases.append({"node": path, "outcome": NOT_RUN, "kind": "COLLECTION_ERROR", "message": message})
            continue
        if not classname:                      # a module-level skip: name is the dotted module
            node = name if name.endswith(".py") else name.replace(".", "/") + ".py"
        else:
            split = _module_path(root, classname.split("."))
            node = (split[0] + "::" + "::".join([*split[1], name])) if split else f"{classname}::{name}"
        if "skipped" in children:
            kind = "XFAIL" if (children["skipped"].get("type") or "").endswith("xfail") else "SKIPPED"
            cases.append({"node": node, "outcome": SKIPPED, "kind": kind, "message": message})
        elif "failure" in children or "error" in children:
            cases.append({"node": node, "outcome": FAIL, "kind": None, "message": message})
        else:
            cases.append({"node": node, "outcome": PASS, "kind": None, "message": ""})
    return cases


def pytest_verification(root: Path, text: str, junit_path: str | None, retry: str, goal: str) -> tuple[list[dict], dict, set[str]]:
    """Rows for every skipped / xfailed / xpassed / uncollected test of one pytest run, its counts, and the set
    of node ids the run reported (any outcome)."""
    counts: dict[str, int] = {}
    for line in text.splitlines()[::-1]:
        found = JUNIT_SUMMARY.findall(line)
        if found and (" in " in line or "passed" in line or "failed" in line):
            counts = {k if not k.startswith("error") else "errors": int(n) for n, k in found}
            break
    rows: list[dict] = []
    nodes: set[str] = set()
    nxt = "the next run of this job at the exact head"
    if not junit_path or not Path(junit_path).is_file():
        rows.append(rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None,
                            "run pytest with --junitxml so every test's outcome is accounted; skipped, xfailed and "
                            "uncollected tests cannot be told from passing ones without it", retry, goal, nxt))
        return rows, counts, nodes
    for case in junit_cases(root, junit_path):
        nodes.add(case["node"])
        if case["outcome"] in (SKIPPED, NOT_RUN):
            rows.append(rvs_row(case["kind"], case["node"],
                                f"run this test at the exact head; it was {case['kind'].lower().replace('_', ' ')} "
                                f"({case['message'][:200]}). A skipped run is unproven, not passed, and is never "
                                "a pre-existing baseline failure", retry, goal, nxt))
    for line in text.splitlines():
        m = XPASS_LINE.match(line)
        if m:
            rows.append(rvs_row("XPASS", m.group(1), "an xfail-marked test passed: remove the marker so it runs as "
                                "a required test", retry, goal, nxt))
        m = COLLECT_ERROR_LINE.match(line)
        if m and not any(r["test"] == m.group(1) and r["kind"] == "COLLECTION_ERROR" for r in rows):
            rows.append(rvs_row("COLLECTION_ERROR", m.group(1), "the module did not collect, so none of its tests "
                                "ran; fix the import or collection error", retry, goal, nxt))
    for key, kind in (("skipped", "SKIPPED"), ("xfailed", "XFAIL"), ("xpassed", "XPASS")):
        if counts.get(key, 0) > sum(1 for r in rows if r["kind"] == kind):
            rows.append(rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None, f"pytest reported {counts[key]} {key} but the "
                                "junit record names fewer; every one must be named and run", retry, goal, nxt))
    return rows, counts, nodes


def unittest_results(text: str) -> tuple[dict[str, str], dict[str, int], int | None]:
    """`python -m unittest -v` output -> ({dotted id: outcome word}, summary counts, Ran N)."""
    results: dict[str, str] = {}
    pending: str | None = None
    counts: dict[str, int] = {}
    ran = None
    def dotted(name: str, ident: str) -> str:
        return ident if ident.endswith("." + name) else ident + "." + name

    for line in text.splitlines():
        summary = UNITTEST_SUMMARY.match(line)
        if summary:
            results[dotted(summary.group(2), summary.group(3))] = summary.group(1)
            pending = None
            continue
        # a subTest outcome (`  name (id) (params) ... ERROR`) is that test's outcome; a failing one wins
        sub = UNITTEST_SUBTEST.match(line)
        if sub:
            test_id = dotted(sub.group(1), sub.group(2))
            if results.get(test_id) not in ("FAIL", "ERROR"):
                results[test_id] = sub.group(3)
            continue
        m = UNITTEST_HEAD.match(line)
        if m and m.group(3) is not None and UNITTEST_TAIL.search(line):
            results[dotted(m.group(1), m.group(2))] = UNITTEST_TAIL.search(line).group(1)
            pending = None
            continue
        if m:
            # `name (id)` (a docstring line follows), `name (id) ... ` (subTests follow) or `name (id) ... <the
            # test's own output>`: the outcome is on a later line
            pending = dotted(m.group(1), m.group(2))
            continue
        t = UNITTEST_TAIL.search(line) or UNITTEST_WORD.match(line) or (UNITTEST_GLUED.search(line) if pending else None)
        if t and pending:
            if results.get(pending) not in ("FAIL", "ERROR"):
                results[pending] = t.group(1)
            pending = None
            continue
        r = UNITTEST_RAN.match(line)
        if r:
            ran = int(r.group(1))
        c = UNITTEST_COUNTS.match(line)
        if c:
            counts = {k.strip(): int(v) for k, v in (p.split("=") for p in (c.group(1) or "").split(",") if "=" in p)}
    return results, counts, ran


LIST_TESTS = r"""
import ast, json, sys, unittest
out = {}
for mod in sys.argv[1:]:
    entry = {"unittest": [], "import_error": None, "pytest_only": []}
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(mod)
    except Exception as exc:
        entry["import_error"] = repr(exc)[:300]
        out[mod] = entry
        continue
    def walk(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                yield from walk(t)
            else:
                yield t
    for t in walk(suite):
        if type(t).__name__ in ("_FailedTest", "ModuleImportFailure"):
            entry["import_error"] = t.id()
        else:
            entry["unittest"].append(t.id())
    try:
        tree = ast.parse(open(mod.replace(".", "/") + ".py", encoding="utf-8").read())
        entry["pytest_only"] = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                                and n.name.startswith("test")]
    except OSError:
        pass
    out[mod] = entry
print(json.dumps(out))
"""


def list_unittest_tests(tree: Path, modules: list[str], python: str = sys.executable) -> dict[str, dict] | None:
    done = subprocess.run([python, "-c", LIST_TESTS, *modules], cwd=tree, capture_output=True, text=True)
    try:
        return json.loads(done.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def unittest_verification(root: Path, text: str, modules: list[str], retry: str, goal: str,
                          python: str = sys.executable, pytest_proof: str | None = None) -> tuple[list[dict], dict]:
    """Rows for every listed-module test the unittest run skipped or did not run. Module-level test functions
    unittest cannot run are NOT_RUN unless `pytest_proof` names the required job that runs them at this head
    (that job then fails closed itself if they do not run: --required-unittest-modules-from)."""
    results, counts, ran = unittest_results(text)
    nxt = "the next run of this job at the exact head"
    rows: list[dict] = []
    listing = list_unittest_tests(root, modules, python) if modules else {}
    if listing is None:
        return [rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None, "the listed modules' tests could not be enumerated "
                        "at the head, so nothing can be shown to have run", retry, goal, nxt)], {}
    words = {"expected failure": "EXPECTED_FAILURE", "unexpected success": "UNEXPECTED_SUCCESS"}
    for test_id, word in sorted(results.items()):
        kind = "SKIPPED" if word.startswith("skipped") else words.get(word)
        if kind:
            rows.append(rvs_row(kind, test_id, f"run this test at the exact head; unittest reported '{word}'. A "
                                "skipped run is unproven, not passed", retry, goal, nxt))
    delegated: list[dict] = []
    for mod, entry in listing.items():
        if entry["import_error"]:
            rows.append(rvs_row("COLLECTION_ERROR", mod, f"the module does not import ({entry['import_error']}); "
                                "none of its tests ran", retry, goal, nxt))
            continue
        for test_id in entry["unittest"]:
            if test_id not in results:
                rows.append(rvs_row("TEST_NOT_RUN", test_id, "the listed module's test did not run in this job",
                                    retry, goal, nxt))
        if not entry["unittest"] and not entry["pytest_only"]:
            rows.append(rvs_row("MODULE_NOT_RUN", mod, "the listed module defines no test this job can run", retry,
                                goal, nxt))
        for name in entry["pytest_only"]:
            node = mod.replace(".", "/") + ".py::" + name
            if pytest_proof:
                delegated.append({"test": node, "kind": "PYTEST_ONLY_FUNCTION", "verified_by": pytest_proof})
            else:
                rows.append(rvs_row("TEST_NOT_RUN", node, "a module-level test function: unittest never runs it; run "
                                    "it under pytest in a required job at this head", retry, goal, nxt))
    if ran is None:
        rows.append(rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None, "the run printed no 'Ran N tests' line", retry,
                            goal, nxt))
    for key, kind in (("skipped", "SKIPPED"), ("expected failures", "EXPECTED_FAILURE"),
                      ("unexpected successes", "UNEXPECTED_SUCCESS")):
        if counts.get(key, 0) > sum(1 for r in rows if r["kind"] == kind):
            rows.append(rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None, f"unittest reported {key}={counts[key]} but "
                                "named fewer; every one must be named and run", retry, goal, nxt))
    return rows, {"ran": ran, "counts": counts, "results": len(results), "delegated": delegated,
                  "modules": len(listing)}


def collect_pytest(tree: Path, python: str = sys.executable) -> set[str] | None:
    done = subprocess.run([python, "-m", "pytest", "tests", "--collect-only", "-q", "-p", "no:cacheprovider"],
                          cwd=tree, capture_output=True, text=True)
    if done.returncode not in (0, 1, 2, 5):
        return None
    return {l.strip() for l in done.stdout.splitlines() if "::" in l and not l.startswith(" ")}


def missing_at_head(base_nodes: set[str] | None, head_nodes: set[str], retry: str, goal: str) -> list[dict]:
    nxt = "the next push to this pull request"
    if base_nodes is None:
        return [rvs_row("SUITE_ACCOUNTING_UNOBSERVED", None, "the base's test set could not be collected, so a test "
                        "removed by this change cannot be ruled out", retry, goal, "re-run the job")]
    return [rvs_row("TEST_MISSING_AT_HEAD", node, "the test exists at the base and did not run at the head (removed, "
                    "renamed or uncollected); restore it, or land its removal as its own reviewed change with the "
                    "replacement test named", retry, goal, nxt)
            for node in sorted(base_nodes - head_nodes)]


def required_modules(workflow_text: str) -> list[str]:
    """The dotted test modules a workflow names (handed to `python -m unittest` directly or through a
    variable): every `tests.<...>.test_<name>` in its text."""
    return list(dict.fromkeys(re.findall(r"(?<![\w./-])tests(?:\.\w+)*\.test_\w+\b", workflow_text)))


def required_test_nodes(root: Path, modules: list[str]) -> list[str]:
    """pytest node ids of every test the modules define (TestCase methods and module-level functions)."""
    import ast
    nodes = []
    for mod in modules:
        path = root / (mod.replace(".", "/") + ".py")
        if not path.is_file():
            nodes.append(mod.replace(".", "/") + ".py")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rel = mod.replace(".", "/") + ".py"
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
                nodes.append(f"{rel}::{n.name}")
            elif isinstance(n, ast.ClassDef) and (n.name.startswith("Test") or any(
                    ast.unparse(b).endswith("TestCase") for b in n.bases)):
                if any(isinstance(s, ast.Assign) and any(getattr(t, "id", "") == "__test__" for t in s.targets)
                       for s in n.body):
                    continue
                for s in n.body:
                    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and s.name.startswith("test"):
                        nodes.append(f"{rel}::{n.name}::{s.name}")
    return nodes


def required_nodes_rows(required: list[str], ran: set[str], skipped: set[str], workflow: str, retry: str,
                        goal: str) -> list[dict]:
    rows = []
    for node in required:
        hits = {n for n in ran if n == node or n.startswith(node + "[")}
        if not hits or hits <= skipped:
            rows.append(rvs_row("REQUIRED_TEST_NOT_RUN_IN_REQUIRED_JOB", node,
                                f"{workflow} lists this module and delegates its pytest-only tests to this job; the "
                                "test must run here at the exact head", retry, goal,
                                "the next run of this job at the exact head", required_by=workflow))
    return rows


def _glob_regex(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + "$")


def workflow_pr_filter(text: str) -> tuple[bool, list[str] | None, list[str]]:
    """(triggers on pull_request, its `paths` list or None when unfiltered, its `paths-ignore` list)."""
    lines = text.splitlines()
    on_idx = next((i for i, l in enumerate(lines) if re.match(r"^(on|'on'|\"on\"|true):", l)), None)
    if on_idx is None:
        return False, None, []
    head = lines[on_idx]
    if "pull_request" in head:                                   # on: [push, pull_request] / on: pull_request
        return bool(re.search(r"\bpull_request\b(?!_)", head)), None, []
    block, i = [], on_idx + 1
    while i < len(lines) and (not lines[i].strip() or lines[i].startswith((" ", "\t", "#"))):
        block.append(lines[i])
        i += 1
    pr_at = next((j for j, l in enumerate(block) if re.match(r"^\s+pull_request\s*:", l)), None)
    if pr_at is None:
        return any(re.match(r"^\s+-\s*pull_request\s*$", l) for l in block), None, []
    indent = len(block[pr_at]) - len(block[pr_at].lstrip())
    sub, j = [], pr_at + 1
    while j < len(block) and (not block[j].strip() or block[j].lstrip().startswith("#")
                              or len(block[j]) - len(block[j].lstrip()) > indent):
        sub.append(block[j])
        j += 1
    lists: dict[str, list[str]] = {}
    key = None
    for l in sub:
        m = re.match(r"^\s+(paths|paths-ignore|branches|types|branches-ignore)\s*:\s*(\[.*\])?\s*$", l)
        if m:
            key = m.group(1)
            lists[key] = [p.strip().strip("'\"") for p in m.group(2)[1:-1].split(",")] if m.group(2) else []
            continue
        m = re.match(r"^\s+-\s*['\"]?([^'\"#]+?)['\"]?\s*(?:#.*)?$", l)
        if m and key:
            lists[key].append(m.group(1))
        elif l.strip() and not l.lstrip().startswith("#"):
            key = None
    return True, lists.get("paths"), lists.get("paths-ignore", [])


def workflow_jobs(text: str) -> list[str]:
    lines = text.splitlines()
    at = next((i for i, l in enumerate(lines) if re.match(r"^jobs\s*:", l)), None)
    if at is None:
        return []
    jobs = []
    for l in lines[at + 1:]:
        if l and not l.startswith((" ", "\t", "#")):
            break
        m = re.match(r"^  ([A-Za-z_][\w-]*)\s*:", l)
        if m:
            jobs.append(m.group(1))
    return jobs


def missing_job_rows(root: Path, base: str, head: str, retry: str, goal: str) -> list[dict]:
    """Every pull_request job at the base must exist at the head: a deleted workflow or a removed job is a
    required verification that no longer runs -> FAIL_CLOSED (its replacement lands as its own change)."""
    def table(commit: str) -> dict[str, list[str]]:
        out = {}
        for wf in git(root, "ls-tree", "--name-only", commit, ".github/workflows/").split():
            if wf.endswith((".yml", ".yaml")):
                text = git(root, "show", f"{commit}:{wf}")
                if workflow_pr_filter(text)[0]:
                    out[wf] = workflow_jobs(text)
        return out
    at_base, at_head = table(base), table(head)
    rows = []
    for wf, jobs in sorted(at_base.items()):
        for job in jobs:
            if job not in at_head.get(wf, []):
                rows.append(rvs_row("REQUIRED_JOB_MISSING", f"{wf}#{job}",
                                    "this pull_request job runs at the base and is absent at the head (its workflow, "
                                    "its pull_request trigger or the job was removed); restore it, or land its "
                                    "retirement as its own reviewed change naming where its checks now run", retry,
                                    goal, "the next push to this pull request"))
    return rows


def path_filter_rows(root: Path, head: str, diff: Iterable[str], retry: str, goal: str) -> tuple[list[dict], list[dict]]:
    """For each path-filtered pull_request workflow at `head`: when this change edits a file the workflow's run
    steps name (a test, script or module) and its filter does not match any changed path, the job is left
    unrun on a change in its scope -> FAIL_CLOSED. Returns (rows, the per-workflow trigger table)."""
    diff = sorted(diff)
    rows, table = [], []
    for wf in git(root, "ls-tree", "--name-only", head, ".github/workflows/").split():
        if not wf.endswith((".yml", ".yaml")):
            continue
        text = git(root, "show", f"{head}:{wf}")
        on_pr, paths, ignore = workflow_pr_filter(text)
        if not on_pr:
            continue
        referenced = set(REFERENCED_PATH.findall(text)) | {m.replace(".", "/") + ".py" for m in REFERENCED_MODULE.findall(text)}
        referenced.add(wf)
        if paths is None:
            triggered = bool(diff) and not (ignore and all(any(_glob_regex(p).match(f) for p in ignore) for f in diff))
        else:
            pats = [_glob_regex(p) for p in paths if not p.startswith("!")]
            negs = [_glob_regex(p[1:]) for p in paths if p.startswith("!")]
            triggered = any(any(r.match(f) for r in pats) and not any(n.match(f) for n in negs) for f in diff)
        in_scope = sorted(set(diff) & referenced)
        table.append({"workflow": wf, "path_filtered": paths is not None, "triggered": triggered,
                      "changed_files_it_names": in_scope})
        if in_scope and not triggered:
            rows.append(rvs_row("REQUIRED_JOB_PATH_FILTERED_OUT", wf,
                                f"this change edits {', '.join(in_scope)}, which {wf} runs, but its pull_request "
                                "path filter does not match the change, so the job never runs: add those paths to "
                                "its filter (or drop the filter)", retry, goal, "the next push to this pull request",
                                changed_files=in_scope))
    return rows, table


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
    common.add_argument("--junit-xml", help="pytest --junitxml record of the --pytest-output run: every skipped, "
                        "xfailed or uncollected test in it is FAIL_CLOSED REQUIRED_VERIFICATION_SKIPPED")
    common.add_argument("--unittest-output", help="`python -m unittest -v` output already produced for --head; its "
                        "FAIL/ERROR lines are the observed set and probes (base, bisection) use unittest")
    common.add_argument("--unittest-modules", nargs="*", default=[], help="the module list the unittest run was "
                        "given; each listed test must have run, and none may be skipped")
    common.add_argument("--selection", help="scripts/test_set_selection.py's sealed selection for this run: only "
                        "its runnable selected sets were run, so only their tests are expected; its unavailable-input "
                        "items block, routed to each input's owner; unselected sets are neither run nor reported")
    common.add_argument("--detect-entrypoint", help="the workflow that runs detect on main in this repository "
                        f"(default: {DEFAULT_RETRY_DETECT})")
    common.add_argument("--required-unittest-modules-from", action="append", default=[],
                        help="a workflow whose `python -m unittest` module list must have every test run in this "
                        "pytest run (its pytest-only functions are delegated here)")
    d = sub.add_parser("detect", parents=[common])
    d.add_argument("--open-prs", help="JSON list of {number, files} for the implication review")
    d.add_argument("--bisect-start", help="when no commit on the first-parent line wrote the baseline, bisect from "
                   "this commit (e.g. the repository's first commit)")
    p = sub.add_parser("pr", parents=[common])
    p.add_argument("--base", required=True)
    p.add_argument("--suite-status", type=int, help="exit status of the run that produced the output")
    p.add_argument("--retry-entrypoint", default=RETRY_PR, help="the workflow a blocked change re-runs")
    p.add_argument("--pytest-proof", help="the required job at this head that runs the listed modules' pytest-only "
                   "functions and fails closed if they do not run (e.g. test-suite-ratchet.yml ratchet)")
    p.add_argument("--baseline-receipt", help="this module's sealed detect receipt for the main head the "
                   "baseline was receipted at: each PRE_EXISTING_BASELINE_FAILURE row names its entry")
    p.add_argument("--path-filter-check", action="store_true", help="fail closed when a path-filtered workflow "
                   "that runs a file this change edits would not be triggered by the change")
    args = parser.parse_args(argv)
    global RETRY_DETECT
    if args.detect_entrypoint:
        RETRY_DETECT = args.detect_entrypoint
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(args.root).resolve()
    retry = RETRY_DETECT if args.command == "detect" else args.retry_entrypoint
    vrows: list[dict] = []
    vinfo: dict[str, Any] = {}
    head_nodes: set[str] = set()
    selection = load_selection(args.selection) if args.selection else None
    if selection is not None:
        srows, sinfo = selection_rows(selection, retry, args.owning_goal, root, getattr(args, "base", None))
        vrows += srows
        vinfo["selection"] = sinfo
    if not getattr(args, "unittest_output", None):
        text = Path(args.pytest_output).read_text(encoding="utf-8") if args.pytest_output else ""
        if args.pytest_output or args.junit_xml:
            prows, counts, head_nodes = pytest_verification(root, text, args.junit_xml, retry, args.owning_goal)
            vinfo.update({"runner": PYTEST, "counts": counts, "tests_reported": len(head_nodes)})
            skipped_nodes = {r["test"] for r in prows if r.get("test")}
            vrows += prows          # after the selection's rows, never in place of them
            for wf in args.required_unittest_modules_from:
                mods = required_modules((root / wf).read_text(encoding="utf-8"))
                need = [n for n in required_test_nodes(root, mods) if in_selection(n, selection)]
                vrows += required_nodes_rows(need, head_nodes, skipped_nodes, wf, retry, args.owning_goal)
                vinfo.setdefault("required_by_workflows", []).append(
                    {"workflow": wf, "modules": len(mods), "tests_required": len(need)})
    if args.command == "detect":
        open_prs = json.loads(Path(args.open_prs).read_text()) if args.open_prs else []
        runner, observed_d = PYTEST, _observed(args.pytest_output)
        if args.unittest_output:
            runner = UNITTEST
            observed_d, _unparsed = observed_unittest(args.unittest_output)
            rows_u, info_u = unittest_verification(root, Path(args.unittest_output).read_text(encoding="utf-8"),
                                                   args.unittest_modules, retry, args.owning_goal)
            for line in _unparsed:
                if not any(r["kind"] == "COLLECTION_ERROR" for r in rows_u):
                    rows_u.append(rvs_row("COLLECTION_ERROR", None, "the runner reported a failure that names no test",
                                          retry, args.owning_goal, "the next run of this job at the exact head",
                                          outcome_line=line))
            vrows += rows_u
            vinfo.update({"runner": UNITTEST, **info_u})
        result = detect(root, args.head, baseline_path=args.baseline, observed=observed_d,
                        epoch_arg=args.hb_epoch, writer_path=args.writer, writer_sha256=args.writer_sha256,
                        repository=args.repository, goal=args.owning_goal, open_prs=open_prs,
                        verification_rows=vrows, verification=vinfo, runner=runner,
                        bisect_start=args.bisect_start)
        for name, record in result.items():
            if record is not None:
                (out / f"{name.replace('_', '-')}.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        receipt = result["receipt"]
        print(json.dumps({k: receipt.get(k) for k in ("disposition", *SIX, "repair_task_id", SEAL)
                          if receipt.get(k) is not None}, sort_keys=True))
        for e in receipt["drift"]:
            print(f"DRIFT {e['test']} first_failing_commit={e.get('first_failing_commit')} {e['classification']}")
        for r in receipt["verification"]["rows"]:
            print(f"FAIL_CLOSED {RVS}/{r['kind']} {r['test']}")
        print(f"VERIFICATION counts={receipt['verification'].get('counts')} "
              f"required_verification_skipped={receipt['verification']['required_verification_skipped']}")
        return 0 if receipt["disposition"] == "ALLOW" else 1
    unparsed: list[str] = []
    runner = PYTEST
    base_sha, head_sha = rev(root, args.base), rev(root, args.head)
    if args.unittest_output:
        observed, unparsed = observed_unittest(args.unittest_output)
        runner = UNITTEST
        text = Path(args.unittest_output).read_text(encoding="utf-8")
        rows_u, info_u = unittest_verification(root, text, args.unittest_modules, retry, args.owning_goal,
                                               pytest_proof=args.pytest_proof)
        vrows += rows_u
        vinfo.update({"runner": UNITTEST, **info_u})
        if args.unittest_modules:
            prober = Prober(root)
            try:
                base_list = list_unittest_tests(prober.tree(base_sha), args.unittest_modules)
            finally:
                prober.close()
            head_list = list_unittest_tests(root, args.unittest_modules) or {}

            def ids(listing: Mapping[str, Any]) -> set[str]:
                return {t for m, e in listing.items() for t in e["unittest"]} | \
                       {m.replace(".", "/") + ".py::" + n for m, e in listing.items() for n in e["pytest_only"]}
            vrows += missing_at_head(ids(base_list) if base_list is not None else None, ids(head_list), retry,
                                     args.owning_goal)
    else:
        observed = _observed(args.pytest_output)
        if observed is None:
            observed = run_suite("tests")
        if args.junit_xml and Path(args.junit_xml).is_file():
            prober = Prober(root)
            try:
                base_nodes = collect_pytest(prober.tree(base_sha))
            finally:
                prober.close()
            if base_nodes is not None and selection is not None:
                base_nodes = {n for n in base_nodes if in_selection(n, selection)}
            vrows += missing_at_head(base_nodes, head_nodes, retry, args.owning_goal)
            vinfo["base_tests_collected"] = len(base_nodes) if base_nodes is not None else None
    if args.path_filter_check:
        prow, table = path_filter_rows(root, head_sha, changed_paths(root, base_sha, head_sha), retry,
                                       args.owning_goal)
        vrows += prow + missing_job_rows(root, base_sha, head_sha, retry, args.owning_goal)
        vinfo["workflows_triggered"] = table
    writer, _info = load_writer(args.writer, args.writer_sha256)
    epoch, _source, _items = resolve_epoch(root, args.hb_epoch, writer, args.owning_goal)
    record = pr_disposition(root, args.base, args.head, baseline_path=args.baseline, observed=observed,
                            goal=args.owning_goal, repository=args.repository, epoch=epoch, runner=runner,
                            unparsed=unparsed, suite_status=args.suite_status, retry_pr=args.retry_entrypoint,
                            verification_rows=vrows, verification=vinfo,
                            baseline_receipt=load_baseline_receipt(args.baseline_receipt) if args.baseline_receipt
                            else None)
    (out / "pr-disposition.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: record.get(k) for k in ("disposition", *SIX, SEAL) if record.get(k) is not None},
                     sort_keys=True))
    for row in record["tests"]:
        label = row.get("kind") if row.get("failure_code") == RVS else None
        print(f"{row['disposition']}{' ' + RVS + '/' + label if label else ''} "
              f"{row['test'] or row.get('outcome_line') or row.get('failure_code')} blocking={row['blocking']}")
    v = record.get("verification", {})
    print(f"VERIFICATION runner={v.get('runner')} counts={v.get('counts')} "
          f"required_verification_skipped={v.get('required_verification_skipped')}")
    return 1 if record["disposition"] == "FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
