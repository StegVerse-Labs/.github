#!/usr/bin/env python3
"""Fail when a pull request adds a test failure the baseline does not already hold.

Every workflow in this repository is path-filtered to an explicit file list, so
a test that no workflow names is never run by CI. At the time this was written
that was 562 of 662 test files. Tests existed, passed locally, and protected
nothing - which is how a cross-repository seam break shipped with both
repositories green.

This runs the whole suite on every pull request and compares the *set* of
failing tests against a committed baseline. A set, not a count: a change that
breaks one test while another is fixed leaves the count unchanged, and that is
exactly the regression a count would miss.

The baseline records failures that already exist on main. It is a ceiling, not
an endorsement: nothing here requires those failures to be fixed, and nothing
stops the ceiling being lowered as they are. Newly passing tests are reported so
the baseline can be tightened deliberately rather than drifting.

Non-authorizing. This validates supplied source only: it mints no receipt,
confers no admission and observes no runtime.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_gate_findings import evaluation, finding  # noqa: E402

GATE = "TEST_SUITE_RATCHET"
BASELINE = Path("data/test-suite-baseline.json")
# pytest prints one of these per failing or erroring test in -q output.
OUTCOME = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)")
REPAIR = ("repair the actual failing test in its owning source lane; "
          "do not add failures or exclusions to the ratchet baseline")
OWNING_GOAL = "H6b / StegVerse-Labs/.github#3039 test-suite ratchet"
RETRY = "python scripts/check_test_suite_ratchet.py --base-sha <exact PR base sha>"


def refusal(code: str, predicate: str, repair: str, detail: str = "") -> dict:
    """The standard six-field FAIL_CLOSED refusal; it changes nothing."""
    return {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY,
            "owning_existing_goal": OWNING_GOAL,
            "next_attempt": "re-run the integrity check on the exact PR base after repair",
            "detail": detail, "authority_effect": "NONE"}


def _refuse(message: str, code: str, predicate: str, repair: str, detail: str = "") -> int:
    print(f"{GATE}: FAIL_CLOSED {message} "
          + json.dumps(refusal(code, predicate, repair, detail), sort_keys=True))
    return 1


def run_suite(target: str) -> set[str]:
    """Return the set of failing test ids, by running the suite."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "--tb=no", "-p", "no:cacheprovider"],
        capture_output=True, text=True,
    )
    return {
        match.group(1)
        for line in completed.stdout.splitlines()
        if (match := OUTCOME.match(line))
    }


def load_baseline(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"{GATE}: FAIL_CLOSED baseline {path} is missing; restore it from main "
                         "(regeneration is prohibited)")
    return json.loads(path.read_text(encoding="utf-8"))


def excluded_tests(baseline: dict) -> set[str]:
    """Tests the gate ignores in both directions, each naming why.

    An exclusion is not a silent retry. It is recorded in the baseline with a
    reason, so what the gate is not watching stays visible to a reviewer.
    """
    if not isinstance(baseline, dict):
        raise ValueError("benchmark is not an object")
    rows = baseline.get("excluded") or []
    if not isinstance(rows, list):
        raise ValueError("excluded is not a list")
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("test"), str) or not row["test"]:
            raise ValueError(f"excluded row without a test id: {row!r}")
    return {row["test"] for row in rows}


def known_failures(baseline: dict) -> set[str]:
    """The known-failing ids, each an exact non-empty str: a string or object here is not a list of tests."""
    if not isinstance(baseline, dict):
        raise ValueError("benchmark is not an object")
    rows = baseline.get("known_failing") or []
    if type(rows) is not list or any(type(row) is not str or not row for row in rows):
        raise ValueError(f"known_failing is not a list of test ids: {rows!r}")
    return set(rows)


def baseline_integrity(current: dict, base: dict) -> dict:
    """A PR may shrink known failures/exclusions, never add or reclassify them.

    This is separate from the runtime test comparison: no PR can grant itself
    a green ratchet by editing the benchmark it is measured against.
    """
    current_known = known_failures(current)
    base_known = known_failures(base)
    current_excluded = excluded_tests(current)
    base_excluded = excluded_tests(base)
    return {
        "added_known_failures": sorted(current_known - base_known),
        "added_exclusions": sorted(current_excluded - base_excluded),
        "moved_from_known_to_excluded": sorted(current_excluded & base_known),
        "removed_known_failures": sorted(base_known - current_known),
        "removed_exclusions": sorted(base_excluded - current_excluded),
    }


def check_baseline_against_base(base_sha: str, path: Path) -> int:
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha):
        return _refuse("invalid exact base commit SHA", "BASE_SHA_INVALID",
                       "EXACT_40_HEX_PR_BASE_SHA", "pass github.event.pull_request.base.sha")
    # The base benchmark is always the repository's own path at the exact base; `path` is the head's copy,
    # read as data, so the base's checker can run from a base worktree against the PR's benchmark.
    result = subprocess.run(["git", "show", f"{base_sha}:{BASELINE.as_posix()}"],
                            capture_output=True, text=True)
    if result.returncode:
        return _refuse("cannot read benchmark from exact PR base", "BASE_BENCHMARK_UNREADABLE",
                       "BASE_BENCHMARK_READABLE_AT_EXACT_SHA",
                       "fetch full history so the exact PR base commit is present")
    try:
        base = json.loads(result.stdout)
        current = load_baseline(path)
        delta = baseline_integrity(current, base)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        return _refuse(f"invalid benchmark: {exc}", "BENCHMARK_INVALID",
                       "BENCHMARK_IS_AN_OBJECT_WITH_TEST_ID_EXCLUSION_ROWS",
                       "every excluded row must be an object naming its test", str(exc))
    if any(delta[k] for k in ("added_known_failures", "added_exclusions",
                              "moved_from_known_to_excluded")):
        print(f"{GATE}: FAIL_CLOSED BASELINE_EXPANSION_OR_EXCLUSION_FORBIDDEN "
              + json.dumps(delta, sort_keys=True))
        return 1
    print(f"{GATE}: BASELINE_INTEGRITY_PASS (existing failures are NOT passes) "
          + json.dumps(delta, sort_keys=True))
    return 0


def compare(observed: set[str], baseline: dict) -> dict:
    """Classify the run against the baseline.

    An excluded test can neither fail the gate nor be reported as fixed.
    """
    known = known_failures(baseline)
    excluded = excluded_tests(baseline)
    return {
        "observed_failing_count": len(observed),
        "baseline_failing_count": len(known),
        "newly_failing": sorted(observed - known - excluded),
        "newly_passing": sorted(known - observed - excluded),
        "excluded": sorted(excluded),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-sha", help="validate baseline monotonicity against exact PR base")
    parser.add_argument("--target", default="tests")
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--write-baseline", action="store_true",
                        help="deprecated and prohibited: cannot regenerate the failure baseline")
    parser.add_argument("--findings", action="store_true",
                        help="emit Healer-intake findings instead of prose")
    args = parser.parse_args()
    path = Path(args.baseline)

    if args.base_sha:
        if args.write_baseline or args.findings:
            print(f"{GATE}: FAIL_CLOSED --base-sha cannot mutate or mask evidence")
            return 1
        return check_baseline_against_base(args.base_sha, path)

    if args.write_baseline:
        print(f"{GATE}: FAIL_CLOSED automatic baseline regeneration is prohibited; "
              "repair the actual tests and separately review any baseline reduction")
        return 1

    # The benchmark is validated before the suite runs: a malformed one is a six-field refusal,
    # never a traceback and never a comparison against a misread ceiling.
    try:
        baseline = load_baseline(path)
        known_failures(baseline)
        excluded_tests(baseline)
    except (ValueError, OSError, TypeError) as exc:
        return _refuse(f"invalid benchmark: {exc}", "BENCHMARK_INVALID",
                       "BENCHMARK_IS_AN_OBJECT_WITH_TEST_ID_EXCLUSION_ROWS",
                       "known_failing is a list of test ids and every excluded row an object naming its test",
                       str(exc))

    observed = run_suite(args.target)
    report = compare(observed, baseline)

    if args.findings:
        rows = [
            finding(gate=GATE, task_id=test_id, predicate_id="NO_NEW_TEST_FAILURE",
                    detail=f"{test_id} fails on this head and is not in the baseline",
                    evidence=[str(path)], repair=REPAIR,
                    retry_entrypoint=f"{Path(__file__).name} --findings")
            for test_id in report["newly_failing"]
        ]
        print(json.dumps(evaluation(GATE, rows), indent=2, sort_keys=True))
        return 1 if rows else 0

    for test_id in report["newly_failing"]:
        print(f"{GATE}: NEW_FAILURE {test_id}")
    for test_id in report["newly_passing"]:
        print(f"{GATE}: NEWLY_PASSING {test_id} - tighten the baseline")
    print("TEST_SUITE_RATCHET_STATUS=REGRESSION_COMPARISON_ONLY_NOT_FULL_SUITE_PASS")
    print(
        f"{GATE}_AUDIT observed={report['observed_failing_count']} "
        f"baseline={report['baseline_failing_count']} "
        f"new={len(report['newly_failing'])} "
        f"newly_passing={len(report['newly_passing'])} "
        f"excluded={len(report['excluded'])}"
    )
    return 1 if report["newly_failing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
