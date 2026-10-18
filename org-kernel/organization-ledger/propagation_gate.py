#!/usr/bin/env python3
"""The run's last step: pass only when every appended request has a recorded ALLOW propagation.

Lane B review (StegVerse-org/.github#162), G1/G2. The step used to read only the
`propagation.json` files that existed and to fail only on `"FAIL_CLOSED"`. So an
absent record, an empty or missing `results/`, and a DENY, PENDING or malformed
record all passed. This gate fails closed on each of them:

- `results/` missing, or holding no request directory: absence, FAIL_CLOSED.
- A directory that appended (it has `ingress.json` or `closure.json` that is
  not `ALREADY_RECORDED`) must hold `propagation.json`.
- That record passes only when `schema` is the propagation result schema,
  `disposition` is exactly `ALLOW` and the recorded `propagation.exit` is 0.
  Any other disposition, an unreadable record, a nonzero exit or a missing
  `propagation.exit` (G3: both call sites always write it) fails.
- No request directory (N3). The run legitimately had nothing to propagate only
  when the receive step recorded `results/NO_REQUESTS.json`: no request was
  received (none was listed, or every listed request was deferred for want of a
  mesh), so nothing was appended. That is ALLOW with `applicability:
  NO_REQUEST_RECEIVED`. Without that marker an empty `results/` is FAIL_CLOSED
  `PROPAGATION_NO_REQUEST_RECORDED`; a marker that is unreadable, inconsistent or
  contradicted by request directories is FAIL_CLOSED
  `PROPAGATION_NO_REQUESTS_MARKER_INVALID`.

Every failure prints a six-field FAIL_CLOSED record on stdout and exits 1. It
reads only the run's own results, writes nothing and reads no clock.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RESULT_SCHEMA = "stegverse.organization-repository-propagation/v1"
RETRY = ".github/workflows/organization-ledger-transition-reusable.yml step \"Fail on a recorded propagation refusal (six fields)\""
GOAL = "StegVerse-org/.github#163"
ABSENT = "PROPAGATION_GATE_TREATS_ABSENCE_AS_PASS"
EXIT_ABSENT = "PROPAGATION_EXIT_STATUS_ABSENT"
NO_REQUEST = "PROPAGATION_NO_REQUEST_RECORDED"
MARKER_INVALID = "PROPAGATION_NO_REQUESTS_MARKER_INVALID"
NO_REQUESTS = "NO_REQUESTS.json"
NO_REQUESTS_SCHEMA = "stegverse.organization-ledger-no-requests/v1"
PREDICATE = "EVERY_APPENDED_REQUEST_HAS_A_PROPAGATION_RECORD_AND_ONLY_A_RECOGNIZED_SUCCESS_PASSES"
APPEND_RECORDS = ("ingress.json", "closure.json")


def refusal(where: str, code: str, repair: str) -> dict:
    return {"schema": "stegverse.organization-repository-propagation-gate/v1", "disposition": "FAIL_CLOSED",
            "request": where, "failure_code": code, "failed_predicate": PREDICATE,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY, "owning_existing_goal": GOAL,
            "next_attempt": "rerun propagate_after_append.py for this request with the run's --hb-epoch, then re-run "
                            "the transition; the receipts already appended and published stand",
            "consequence_committed": False, "authority_effect": "NONE_GATE_ONLY"}


def _read(path: Path):
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return None, type(exc).__name__ + ": " + str(exc)
    return (value, None) if isinstance(value, dict) else (None, "not a JSON object")


def no_requests(results: Path) -> tuple[bool, list[dict]]:
    """(the run recorded that it received no request, findings about that marker)."""
    path = results / NO_REQUESTS
    if not path.exists():
        return False, []
    marker, error = _read(path)
    if marker is None:
        return False, [refusal(NO_REQUESTS, MARKER_INVALID, "results/" + NO_REQUESTS + " is unreadable (" + error + ")")]
    deferred = marker.get("deferred")
    listed = marker.get("requests_listed")
    if (marker.get("schema") != NO_REQUESTS_SCHEMA or marker.get("received") != 0 or not isinstance(deferred, list)
            or isinstance(listed, bool) or not isinstance(listed, int) or listed != len(deferred)):
        return False, [refusal(NO_REQUESTS, MARKER_INVALID, "results/" + NO_REQUESTS + " does not record that no "
                               "request was received (schema " + NO_REQUESTS_SCHEMA + ", received 0, requests_listed "
                               "equal to the number deferred): " + json.dumps(marker, sort_keys=True)[:300])]
    return True, []


def evaluate(results: Path) -> list[dict]:
    """Every finding as a six-field record; an empty list is the only pass."""
    if not results.is_dir():
        return [refusal(str(results), ABSENT, "the run left no results/ directory, so no propagation is recorded; "
                                              "absence is not a pass")]
    dirs = sorted(p for p in results.iterdir() if p.is_dir())
    received_none, marker_findings = no_requests(results)
    if marker_findings:
        return marker_findings
    if received_none and dirs:
        return [refusal(NO_REQUESTS, MARKER_INVALID, "results/" + NO_REQUESTS + " says no request was received, but "
                        "request directories exist: " + ", ".join(d.name for d in dirs))]
    if not dirs:
        if received_none:
            return []   # nothing was received, so nothing was appended and there is nothing to propagate
        return [refusal(str(results), NO_REQUEST, "results/ holds no request directory and the receive step recorded "
                                                  "no " + NO_REQUESTS + ", so whether any request ran is not recorded; "
                                                  "an unrecorded run is not a pass")]
    findings, appended = [], 0
    for d in dirs:
        marker = next((d / n for n in APPEND_RECORDS if (d / n).is_file()), None)
        if marker is None:
            findings.append(refusal(d.name, ABSENT, "neither ingress.json nor closure.json was recorded for " + d.name))
            continue
        record, error = _read(marker)
        if record is not None and record.get("disposition") == "ALREADY_RECORDED":
            continue   # one manifest is one transition: nothing was appended, nothing to propagate
        appended += 1
        path = d / "propagation.json"
        if not path.is_file():
            findings.append(refusal(d.name, ABSENT, "no propagation.json for " + d.name + ", which appended; the "
                                                    "propagation outcome must be recorded, and absence is not a pass"))
            continue
        result, error = _read(path)
        if result is None:
            findings.append(refusal(d.name, "PROPAGATION_RECORD_UNREADABLE", "propagation.json for " + d.name
                                    + " is unreadable (" + error + "); record it again"))
            continue
        exit_file = d / "propagation.exit"
        if not exit_file.is_file():
            findings.append(refusal(d.name, EXIT_ABSENT, "no propagation.exit for " + d.name + "; both call sites "
                                    "record the wrapper's exit status, so a missing one is absence, not exit 0"))
            continue
        try:
            exit_code = exit_file.read_text().strip()
        except OSError as exc:
            exit_code = "unreadable (" + type(exc).__name__ + ")"
        if result.get("schema") != RESULT_SCHEMA or result.get("disposition") != "ALLOW" or exit_code != "0":
            code = result.get("failure_code") if result.get("disposition") not in (None, "ALLOW") else None
            findings.append(refusal(d.name, code or "PROPAGATION_NOT_ALLOW",
                                    "propagation for " + d.name + " is not a recognized success (schema "
                                    + repr(result.get("schema")) + ", disposition " + repr(result.get("disposition"))
                                    + ", exit " + exit_code + "); only disposition ALLOW under " + RESULT_SCHEMA
                                    + " with exit 0 passes. Repair what it recorded: "
                                    + str(result.get("required_evidence_or_repair") or "no repair was recorded")))
    return findings


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(json.dumps(refusal("", ABSENT, "usage: propagation_gate.py <results dir>"), sort_keys=True))
        return 1
    results = Path(args[0])
    for d in sorted(p for p in results.glob("*/propagation.json")):
        print(d.parent.name, d.read_text(errors="replace").strip()[:2000])
    findings = evaluate(results)
    for finding in findings:
        print(json.dumps(finding, sort_keys=True))
    if not findings:
        applicability = "NO_REQUEST_RECEIVED" if no_requests(results)[0] else "EVERY_APPENDED_REQUEST_PROPAGATED"
        print(json.dumps({"disposition": "ALLOW", "gate": "PROPAGATION_GATE", "applicability": applicability,
                          "results": str(results)}, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
