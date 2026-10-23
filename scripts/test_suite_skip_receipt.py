#!/usr/bin/env python3
"""Report every test the full suite skipped on this exact head, as a receipt.

Admission readiness needs the full suite run on the exact head with zero
skipped. A skipped test proves nothing, and a skip that no one lists is a test
that silently stopped protecting anything. This reads the JUnit XML that
pytest itself wrote for the run (pytest's built-in --junitxml; no plugin, no
new dependency) and writes a machine-readable receipt naming each skipped test,
its reason and the count.

It never changes which tests run. It does not skip, deselect, convert or
retry anything: it only reads what the run already recorded.

Fail closed: any skip on the head is FAIL_CLOSED with failure_code
TEST_SUITE_SKIPPED_ON_HEAD and the six fields, and each skip is listed with the
six-field item its owner recorded in --skip-items (or, when none is recorded,
an item saying so). A missing or unreadable run is FAIL_CLOSED, never ALLOW.

With --base-junit (the same suite run on the base commit), a failure on the
head that the base already had is receipted as pre-existing and does not
block; a failure the base did not have is FAIL_CLOSED with
TEST_SUITE_NEW_FAILURE_ON_HEAD. Without --base-junit, failures are counted and
listed but not judged here: in a repository with a failure ratchet, the
ratchet judges them, separately from skips.

Deterministic: reads only the files it is given. No clock, no network, no
environment reads. Standard library only. Non-authorizing: it confers no
admission and mints no authority; a receipt is evidence for a reviewer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

SCHEMA = "stegverse.test-suite-skip-receipt/v1"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
NEXT_ATTEMPT = ("the next push to this pull request head reruns this job on "
                "the new head; nothing is dispatched")


def test_id(case: ET.Element) -> str:
    """A stable id: pytest's classname (dotted module[.Class]) and name."""
    classname = case.get("classname") or ""
    name = case.get("name") or ""
    return f"{classname}::{name}" if classname else name


def read_run(path: Path) -> dict:
    """Outcomes per test id, read from pytest's JUnit XML."""
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    if not suites:
        raise ValueError("no <testsuite> element")
    run = {"passed": [], "failed": [], "errors": [], "skipped": [], "xfailed": []}
    for suite in suites:
        for case in suite.iter("testcase"):
            tid = test_id(case)
            skipped = case.find("skipped")
            if case.find("failure") is not None:
                run["failed"].append(tid)
            elif case.find("error") is not None:
                run["errors"].append(tid)
            elif skipped is not None:
                kind = skipped.get("type") or ""
                row = {"test": tid,
                       "reason": skipped.get("message") or "",
                       "location": (skipped.text or "").strip().split(": ", 1)[0]}
                (run["xfailed"] if kind == "pytest.xfail" else run["skipped"]).append(row)
            else:
                run["passed"].append(tid)
    return run


def owner_item(row: dict, items: list[dict], retry: str) -> dict:
    """The six-field item recorded for this skip, by test-id prefix."""
    for item in items:
        if row["test"].startswith(item["test_prefix"]):
            return {k: item[k] for k in SIX} | {"classification": item.get("classification", "")}
    return {
        "failure_code": "TEST_SUITE_SKIP_UNCLASSIFIED",
        "failed_predicate": "EVERY_SKIP_HAS_A_RECORDED_OWNER",
        "required_evidence_or_repair": (
            "provide what the skip reason names in CI, or record a six-field "
            "item for it in the skip-items file under its owning Goal"),
        "retry_entrypoint": retry,
        "owning_existing_goal": "UNRECORDED",
        "next_attempt": NEXT_ATTEMPT,
        "classification": "UNCLASSIFIED",
    }


def refusal(code: str, predicate: str, repair: str, retry: str, goal: str) -> dict:
    return dict(zip(SIX, (code, predicate, repair, retry, goal, NEXT_ATTEMPT)))


def build(junit: Path, head: str, retry: str, goal: str, items: list[dict],
          base_junit: Path | None = None, base: str | None = None) -> dict:
    receipt = {"schema": SCHEMA, "head_sha": head, "authority_effect": "NONE",
               "skips_are_never_converted_or_deselected": True}
    try:
        run = read_run(junit)
    except (OSError, ET.ParseError, ValueError) as exc:
        receipt |= {"disposition": "FAIL_CLOSED", "refusals": [refusal(
            "TEST_SUITE_NOT_OBSERVED_ON_HEAD", "FULL_SUITE_RAN_ON_EXACT_HEAD",
            f"a readable JUnit XML of the full suite on this head ({exc.__class__.__name__})",
            retry, goal)]}
        return receipt
    receipt["counts"] = {k: len(v) for k, v in run.items()}
    receipt["counts"]["tests"] = sum(receipt["counts"].values())
    receipt["skipped"] = [row | {"item": owner_item(row, items, retry)}
                          for row in sorted(run["skipped"], key=lambda r: r["test"])]
    receipt["xfailed"] = sorted(run["xfailed"], key=lambda r: r["test"])
    failing = sorted(set(run["failed"]) | set(run["errors"]))
    receipt["failing_on_head"] = failing
    refusals = []
    if run["skipped"]:
        refusals.append(refusal(
            "TEST_SUITE_SKIPPED_ON_HEAD", "FULL_SUITE_ON_EXACT_HEAD_ZERO_SKIPPED",
            (f"{len(run['skipped'])} skipped; a run on this exact head with "
             "skipped=0: provide in CI what each listed skip names (a pinned "
             "checkout of an existing StegVerse repository, no new third-party "
             "dependency), or resolve each listed item under its owning Goal. "
             "Never skip, deselect or convert a test"),
            retry, goal))
    if receipt["counts"]["tests"] == 0:
        refusals.append(refusal(
            "TEST_SUITE_NOT_OBSERVED_ON_HEAD", "FULL_SUITE_RAN_ON_EXACT_HEAD",
            "the run recorded no tests; run the full suite on this head", retry, goal))
    if base_junit is not None:
        receipt["base_sha"] = base
        try:
            base_run = read_run(base_junit)
        except (OSError, ET.ParseError, ValueError) as exc:
            refusals.append(refusal(
                "TEST_SUITE_NOT_OBSERVED_ON_BASE", "FULL_SUITE_RAN_ON_BASE",
                f"a readable JUnit XML of the full suite on the base ({exc.__class__.__name__})",
                retry, goal))
        else:
            known = set(base_run["failed"]) | set(base_run["errors"])
            receipt["pre_existing_on_base_not_blocking"] = [t for t in failing if t in known]
            new = [t for t in failing if t not in known]
            receipt["new_failures_on_head"] = new
            if new:
                refusals.append(refusal(
                    "TEST_SUITE_NEW_FAILURE_ON_HEAD", "NO_TEST_FAILS_ON_HEAD_THAT_PASSED_ON_BASE",
                    f"{len(new)} test(s) fail on this head and not on the base; fix them",
                    retry, goal))
    receipt["refusals"] = refusals
    receipt["disposition"] = "FAIL_CLOSED" if refusals else "ALLOW"
    return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--junit", required=True, type=Path)
    p.add_argument("--head", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--retry-entrypoint", required=True)
    p.add_argument("--owning-goal", required=True)
    p.add_argument("--skip-items", type=Path)
    p.add_argument("--base-junit", type=Path)
    p.add_argument("--base")
    a = p.parse_args(argv)
    items = []
    if a.skip_items is not None:
        items = json.loads(a.skip_items.read_text(encoding="utf-8"))["items"]
    receipt = build(a.junit, a.head, a.retry_entrypoint, a.owning_goal, items,
                    a.base_junit, a.base)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    counts = receipt.get("counts", {})
    print(f"TEST_SUITE_SKIP_RECEIPT head={a.head} disposition={receipt['disposition']} "
          f"skipped={counts.get('skipped', 'UNKNOWN')} tests={counts.get('tests', 'UNKNOWN')} "
          f"failing={len(receipt.get('failing_on_head', []))}")
    for row in receipt.get("skipped", []):
        print(f"SKIPPED {row['test']} :: {row['reason']} :: owner={row['item']['owning_existing_goal']}")
    for r in receipt["refusals"]:
        print("FAIL_CLOSED " + " ".join(f"{k}={r[k]!r}" for k in SIX))
    return 0 if receipt["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
