#!/usr/bin/env python3
"""Validate the single shared runtime-evidence owner invariant.

This is source/coordination validation only. It does not prove runtime execution.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "control" / "runtime-node-profiles.json"
TASKS = ROOT / "data" / "canonical-task-records"
GLOBAL_OWNER = "GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001"
GLOBAL_DEP = "DEP-GLOBAL-RUNTIME-EVIDENCE-CLOSURE"
RUNTIME_OWNER_TERMS = (
    "runtime-materialization remediation",
    "runtime materialization remediation",
    "runtime-evidence owner",
    "runtime evidence owner",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def dependency_ids(record: dict) -> set[str]:
    return {
        dep.get("dependency_id")
        for dep in record.get("dependencies", [])
        if isinstance(dep, dict) and dep.get("dependency_id")
    }


def belongs_to_profiled_lane(record: dict, lane_ids: set[str]) -> bool:
    return any(
        value in lane_ids
        for value in (
            record.get("task_id"),
            record.get("root_correlation_id"),
            record.get("parent_task_id"),
        )
    )


def describes_runtime_owner_like_remediation(record: dict) -> bool:
    text = " ".join(
        str(record.get(key, "")).lower()
        for key in ("goal", "remediates_defect")
    )
    components = record.get("targets", {}).get("components", [])
    text += " " + " ".join(str(item).lower() for item in components)
    return any(term in text for term in RUNTIME_OWNER_TERMS)


def validate() -> list[str]:
    errors: list[str] = []
    profiles = load_json(PROFILES)
    if profiles.get("goal_task_id") != GLOBAL_OWNER:
        errors.append("profile registry goal_task_id is not the global runtime owner")
    if profiles.get("shared_runtime_evidence_owner_task_id") != GLOBAL_OWNER:
        errors.append("profile registry shared owner is not GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001")
    if not profiles.get("profile_policy", {}).get("single_shared_runtime_evidence_owner_required"):
        errors.append("single shared runtime-evidence owner policy is not enabled")
    if not profiles.get("profile_policy", {}).get("duplicate_runtime_materialization_owner_for_profiled_lane_prohibited"):
        errors.append("duplicate runtime-materialization owner prohibition is not enabled")

    lane_profiles = profiles.get("profiles", [])
    if len(lane_profiles) != 18:
        errors.append(f"expected 18 runtime lanes, found {len(lane_profiles)}")
    lane_ids = {entry.get("task_id") for entry in lane_profiles}
    if None in lane_ids or len(lane_ids) != len(lane_profiles):
        errors.append("runtime lane task IDs are missing or duplicated")

    for entry in lane_profiles:
        if entry.get("shared_runtime_evidence_owner_task_id") != GLOBAL_OWNER:
            errors.append(f"{entry.get('task_id')}: shared runtime-evidence owner mismatch")

    for path in sorted(TASKS.glob("*.json")):
        record = load_json(path)
        declared_owner = record.get("shared_runtime_evidence_owner_task_id")
        if declared_owner and declared_owner != GLOBAL_OWNER:
            errors.append(f"{path.name}: declares noncanonical shared runtime-evidence owner {declared_owner}")
        if record.get("task_id") == GLOBAL_OWNER:
            continue
        if belongs_to_profiled_lane(record, lane_ids) and describes_runtime_owner_like_remediation(record):
            if GLOBAL_DEP not in dependency_ids(record):
                errors.append(
                    f"{path.name}: profiled-lane runtime remediation lacks {GLOBAL_DEP} binding"
                )

    stegbrowser = load_json(TASKS / "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")
    if stegbrowser.get("shared_runtime_evidence_owner_task_id") != GLOBAL_OWNER:
        errors.append("StegBrowser remediation is not explicitly bound to the global owner")
    if GLOBAL_DEP not in dependency_ids(stegbrowser):
        errors.append("StegBrowser remediation lacks the global-owner dependency")
    if stegbrowser.get("authority_model", {}).get("lane_task_may_create_runtime_evidence_owner") is not False:
        errors.append("StegBrowser lane does not prohibit creation of another runtime-evidence owner")

    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print("PASS: all 18 runtime lanes reuse GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001; duplicate runtime owner remediation is rejected")
