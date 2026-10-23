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
REPAIR = ("fix the newly failing test, or - when the failure is genuinely "
          "pre-existing and newly surfaced - add it to the baseline in the same "
          "change, where a reviewer sees it")


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
        raise SystemExit(f"{GATE}: baseline {path} is missing; generate it with --write-baseline")
    return json.loads(path.read_text(encoding="utf-8"))


def excluded_tests(baseline: dict) -> set[str]:
    """Tests the gate ignores in both directions, each naming why.

    An exclusion is not a silent retry. It is recorded in the baseline with a
    reason, so what the gate is not watching stays visible to a reviewer.
    """
    return {row["test"] for row in (baseline.get("excluded") or [])}


def compare(observed: set[str], baseline: dict) -> dict:
    """Classify the run against the baseline.

    An excluded test can neither fail the gate nor be reported as fixed.
    """
    known = set(baseline.get("known_failing") or [])
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
    parser.add_argument("--target", default="tests")
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--write-baseline", action="store_true",
                        help="record the current failing set as the baseline")
    parser.add_argument("--findings", action="store_true",
                        help="emit Healer-intake findings instead of prose")
    args = parser.parse_args()
    path = Path(args.baseline)

    observed = run_suite(args.target)

    if args.write_baseline:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "stegverse.test-suite-baseline/v1",
            "target": args.target,
            "known_failing": sorted(x for x in observed
                                    if x not in {r["test"] for r in (existing.get("excluded") or [])}),
            # Preserved across regeneration: an exclusion and its reason survive.
            "excluded": existing.get("excluded") or [],
            "baseline_is_a_ceiling_not_an_endorsement": True,
            "authority_effect": "NONE",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{GATE}: wrote baseline of {len(observed)} failing tests to {path}")
        return 0

    report = compare(observed, load_baseline(path))

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
