#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PREFIX = "data/canonical-task-records/"
REVIEW_ORDER = [
    "STEG-BROWSER-RETAINED-RESIDENT-NODE",
    "STEGOS-CURRENT-DEVICE-NODE",
    "STEG-BROWSER-EPHEMERAL-LEASE",
    "SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER",
    "ADMITTED-EPHEMERAL-STEGOS-NODE",
    "REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT",
]
DISPOSITIONS = {"SELECTED", "SUITABLE", "PENDING_EVIDENCE", "UNSUITABLE", "NOT_APPLICABLE"}
LIMITATIONS = {"NONE", "EVIDENCE_REACHABILITY", "ARCHITECTURAL", "AUTHORITY", "PLATFORM", "NOT_APPLICABLE"}


def fail(message: str) -> None:
    raise ValueError(message)


def runtime_capable(record: dict) -> bool:
    return isinstance(record.get("runtime_requirements"), dict)


def validate_resolution(record: dict) -> None:
    if not runtime_capable(record):
        return
    task_id = str(record.get("task_id") or "<unknown>")
    resolution = record.get("execution_substrate_resolution")
    if not isinstance(resolution, dict):
        fail(f"{task_id}: runtime-capable task registration requires execution_substrate_resolution")
    if resolution.get("schema") != "stegverse.execution-substrate-resolution/v1":
        fail(f"{task_id}: execution_substrate_resolution schema mismatch")
    if resolution.get("review_order") != REVIEW_ORDER:
        fail(f"{task_id}: substrate review_order must match canonical single-device-first order")
    if resolution.get("authority_effect") != "NONE":
        fail(f"{task_id}: substrate resolution authority_effect must be NONE")
    if resolution.get("second_user_operated_device_allowed") is not False:
        fail(f"{task_id}: second_user_operated_device_allowed must be false")

    reviews = resolution.get("reviews")
    if not isinstance(reviews, list) or len(reviews) != len(REVIEW_ORDER):
        fail(f"{task_id}: reviews must contain exactly one entry per canonical substrate")
    seen = []
    for row in reviews:
        if not isinstance(row, dict):
            fail(f"{task_id}: every substrate review must be an object")
        sid = row.get("substrate_id")
        seen.append(sid)
        disposition = row.get("disposition")
        limitation = row.get("limitation_class")
        if disposition not in DISPOSITIONS:
            fail(f"{task_id}: invalid disposition for {sid}")
        if limitation not in LIMITATIONS:
            fail(f"{task_id}: invalid limitation_class for {sid}")
        evidence_refs = row.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not all(isinstance(x, str) and x.strip() for x in evidence_refs):
            fail(f"{task_id}: evidence_refs for {sid} must be a string array")
        if limitation == "EVIDENCE_REACHABILITY" and disposition == "UNSUITABLE":
            fail(f"{task_id}: evidence/reachability gap may not be promoted to UNSUITABLE for {sid}")
        if disposition == "UNSUITABLE" and not evidence_refs:
            fail(f"{task_id}: UNSUITABLE substrate {sid} requires evidence_refs")
    if seen != REVIEW_ORDER:
        fail(f"{task_id}: substrate reviews must preserve canonical review order")

    selected = resolution.get("selected_substrate_id")
    if selected is not None and selected not in REVIEW_ORDER:
        fail(f"{task_id}: selected_substrate_id is not canonical")
    selected_rows = [r for r in reviews if r.get("disposition") == "SELECTED"]
    if selected is None and selected_rows:
        fail(f"{task_id}: SELECTED review requires selected_substrate_id")
    if selected is not None:
        if len(selected_rows) != 1 or selected_rows[0].get("substrate_id") != selected:
            fail(f"{task_id}: selected_substrate_id must match exactly one SELECTED review")

    external_required = resolution.get("external_device_required")
    if not isinstance(external_required, bool):
        fail(f"{task_id}: external_device_required must be boolean")
    if external_required:
        prior = reviews[:-1]
        for row in prior:
            if row.get("disposition") not in {"UNSUITABLE", "NOT_APPLICABLE"}:
                fail(f"{task_id}: external device cannot be required before all single-device substrates are exhausted")
            if row.get("limitation_class") == "EVIDENCE_REACHABILITY":
                fail(f"{task_id}: external device cannot be required from an evidence/reachability gap")
        last = reviews[-1]
        if last.get("disposition") != "SELECTED" or selected != REVIEW_ORDER[-1]:
            fail(f"{task_id}: external_device_required requires last-resort external substrate selection")


def added_task_records(base_ref: str) -> list[Path]:
    proc = subprocess.run(
        ["git", "diff", "--diff-filter=A", "--name-only", base_ref, "HEAD", "--", RECORD_PREFIX],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith(RECORD_PREFIX) and line.endswith(".json"):
            out.append(ROOT / line)
    return out


def validate_path(path: Path) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    validate_resolution(record)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref")
    parser.add_argument("--record", action="append", default=[])
    args = parser.parse_args()

    paths = [Path(p).resolve() for p in args.record]
    if args.base_ref:
        paths.extend(added_task_records(args.base_ref))
    if not paths:
        print("TASK_REGISTRATION_SUBSTRATE_RESOLUTION_NO_NEW_RECORDS")
        return

    failures = []
    for path in sorted(set(paths)):
        try:
            validate_path(path)
        except Exception as exc:
            failures.append(f"{path}: {exc}")
    if failures:
        for row in failures:
            print(f"ERROR: {row}", file=sys.stderr)
        raise SystemExit(1)
    print(f"TASK_REGISTRATION_SUBSTRATE_RESOLUTION_PASS count={len(set(paths))}")


if __name__ == "__main__":
    main()
