#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
USER_ACTION_SHARING = {"SHAREABLE", "EXCLUSIVE"}
USER_ACTION_REQUIRED_FIELDS = (
    "surface_id",
    "url_route",
    "device_browser_context_class",
    "runtime_surface",
    "action_type",
    "owner_task_id",
    "sharing",
)


def fail(message: str) -> None:
    raise ValueError(message)


def runtime_capable(record: dict) -> bool:
    return isinstance(record.get("runtime_requirements"), dict)


def validate_user_action_surfaces(record: dict) -> None:
    rows = record.get("user_action_surfaces")
    if rows is None:
        return
    task_id = str(record.get("task_id") or "<unknown>")
    if not isinstance(rows, list):
        fail(f"{task_id}: user_action_surfaces must be an array")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            fail(f"{task_id}: every user action surface must be an object")
        extras = set(row) - (set(USER_ACTION_REQUIRED_FIELDS) | {"request_id"})
        if extras:
            fail(f"{task_id}: unsupported user action surface fields: {sorted(extras)}")
        for key in USER_ACTION_REQUIRED_FIELDS:
            value = row.get(key)
            if not isinstance(value, str) or not value.strip():
                fail(f"{task_id}: user action surface {key} must be a non-empty string")
        if row["owner_task_id"] != task_id:
            fail(f"{task_id}: user action surface owner_task_id must equal task_id")
        if row["sharing"] not in USER_ACTION_SHARING:
            fail(f"{task_id}: user action surface sharing must be SHAREABLE or EXCLUSIVE")
        request_id = row.get("request_id")
        if request_id is not None and (not isinstance(request_id, str) or not request_id.strip()):
            fail(f"{task_id}: user action surface request_id must be null or non-empty string")
        identity = (
            row["url_route"],
            row["device_browser_context_class"],
            row["runtime_surface"],
            row["action_type"],
            row["surface_id"],
        )
        if identity in seen:
            fail(f"{task_id}: duplicate user action surface identity")
        seen.add(identity)


def validate_resolution(record: dict) -> None:
    validate_user_action_surfaces(record)
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
        for row in reviews[:-1]:
            if row.get("disposition") not in {"UNSUITABLE", "NOT_APPLICABLE"}:
                fail(f"{task_id}: external device cannot be required before all single-device substrates are exhausted")
            if row.get("limitation_class") == "EVIDENCE_REACHABILITY":
                fail(f"{task_id}: external device cannot be required from an evidence/reachability gap")
        last = reviews[-1]
        if last.get("disposition") != "SELECTED" or selected != REVIEW_ORDER[-1]:
            fail(f"{task_id}: external_device_required requires last-resort external substrate selection")


def changed_task_records(base_ref: str) -> list[Path]:
    """Return added or modified canonical task records for PR validation.

    Existing task records can change substrate selection without being newly added,
    so validating additions only leaves an unsafe conformance gap.
    """
    proc = subprocess.run(
        ["git", "diff", "--diff-filter=AM", "--name-only", base_ref, "HEAD", "--", RECORD_PREFIX],
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


def github_pr_base_ref() -> str | None:
    event_path = str(os.environ.get("GITHUB_EVENT_PATH") or "").strip()
    if not event_path:
        return None
    path = Path(event_path)
    if not path.exists():
        return None
    event = json.loads(path.read_text(encoding="utf-8"))
    pr = event.get("pull_request")
    if not isinstance(pr, dict):
        return None

    # Validation workflows intentionally checkout refs/pull/<n>/merge. The event's
    # pull_request.base.sha can lag current main when the PR remains open while
    # unrelated canonical work advances. Prefer the synthetic merge commit's first
    # parent, which is the exact current base used to construct the tested merge.
    commit_text = subprocess.run(
        ["git", "cat-file", "-p", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    parents = [line.split()[1] for line in commit_text.splitlines() if line.startswith("parent ")]
    if len(parents) >= 2:
        current_merge_base = parents[0]
        probe = subprocess.run(["git", "cat-file", "-e", f"{current_merge_base}^{{commit}}"], cwd=ROOT)
        if probe.returncode != 0:
            subprocess.run(
                ["git", "fetch", "--depth=1", "origin", current_merge_base],
                cwd=ROOT,
                check=True,
                env={k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN"}},
            )
        return current_merge_base

    base_sha = str(((pr.get("base") or {}).get("sha") or "")).strip()
    if not base_sha:
        return None
    probe = subprocess.run(["git", "cat-file", "-e", f"{base_sha}^{{commit}}"], cwd=ROOT)
    if probe.returncode != 0:
        subprocess.run(
            ["git", "fetch", "--depth=1", "origin", base_sha],
            cwd=ROOT,
            check=True,
            env={k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN"}},
        )
    return base_sha


def validate_path(path: Path) -> None:
    record = json.loads(path.read_text(encoding="utf-8"))
    validate_resolution(record)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref")
    parser.add_argument("--record", action="append", default=[])
    args = parser.parse_args()

    paths = [Path(p).resolve() for p in args.record]
    base_ref = args.base_ref or github_pr_base_ref()
    if base_ref:
        paths.extend(changed_task_records(base_ref))
    if not paths:
        print("TASK_REGISTRATION_SUBSTRATE_RESOLUTION_NO_CHANGED_RECORDS")
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
