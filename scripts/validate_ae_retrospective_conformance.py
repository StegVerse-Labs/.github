#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "control" / "admissible-existence-retrospective-conformance.json"
TERMINAL = {"COMPLETED", "SUPERSEDED", "TERMINATED"}
CURRENT_STATES = {"ACTIVE", "BLOCKED", "HANDOFF_READY", "CLAIMED", "RETRY", "REVIEW_REQUIRED", "FAILED"}
RESULTS = {"PASS", "REVIEW_REQUIRED", "FAIL_CLOSED"}
AE_IMPACTS = {"NONE", "CAPABILITY", "SUPPORTING_OPERATION_OF"}
RELATIONSHIPS = {"develops_capability", "integrates_capability", "validates_capability", "propagates_capability"}
KNOWN_PHASES = {
    "stegverse:capability:steggate:canonical:v1": "ACTIVATED",
    "stegverse:capability:sovereign-local-model:v1": "ADMISSIBLE",
    "stegverse:capability:transaction-discovery:v1": "ADMISSIBLE",
    "stegverse:capability:stegfin-base-pretrade:v1": "ADMISSIBLE",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def effective_tasks() -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    aggregate = load(ROOT / "control" / "worker-registry.json")
    for task in aggregate.get("tasks", []):
        if isinstance(task, dict) and isinstance(task.get("task_id"), str):
            tasks[task["task_id"]] = task
    for path in sorted((ROOT / "control" / "worker-registry.d").glob("*.json")):
        doc = load(path)
        for task in doc.get("tasks", []):
            if isinstance(task, dict) and isinstance(task.get("task_id"), str):
                tasks[task["task_id"]] = task
    return tasks


def main() -> int:
    report = load(REPORT)
    errors: list[str] = []
    if report.get("schema") != "stegverse.admissible-existence-retrospective-conformance/v1":
        errors.append("report schema mismatch")
    if report.get("credential_authority") != "TV/TVC":
        errors.append("report credential_authority must be TV/TVC")
    if report.get("github_token_runtime_authority") is not False:
        errors.append("report GitHub-token runtime authority must be false")

    tasks = effective_tasks()
    entries = report.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be list")
        entries = []
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("task_id"), str):
            errors.append("every entry requires task_id")
            continue
        task_id = entry["task_id"]
        if task_id in indexed:
            errors.append(f"duplicate classification:{task_id}")
        indexed[task_id] = entry

    missing = sorted(set(tasks) - set(indexed))
    extra = sorted(set(indexed) - set(tasks))
    if missing:
        errors.append("missing classifications:" + ",".join(missing))
    if extra:
        errors.append("classifications without effective task:" + ",".join(extra))

    for task_id, task in tasks.items():
        entry = indexed.get(task_id)
        if entry is None:
            continue
        state = task.get("state")
        if entry.get("operational_state") != state:
            errors.append(f"{task_id}: operational_state mismatch {entry.get('operational_state')} != {state}")
        temporal = entry.get("temporal_class")
        if state in TERMINAL and temporal != "recently_completed":
            errors.append(f"{task_id}: terminal effective task must be recently_completed")
        if state not in TERMINAL and temporal != "current":
            errors.append(f"{task_id}: nonterminal effective task must be current")
        if entry.get("result") not in RESULTS:
            errors.append(f"{task_id}: invalid result")
        if entry.get("credential_authority") != "TV/TVC":
            errors.append(f"{task_id}: credential authority must be TV/TVC")
        if entry.get("github_token_runtime_authority") is not False:
            errors.append(f"{task_id}: GitHub-token runtime authority must be false")
        if not isinstance(entry.get("evidence_refs"), list) or not entry.get("evidence_refs"):
            errors.append(f"{task_id}: evidence_refs required")
        if not isinstance(entry.get("rationale"), str) or not entry.get("rationale"):
            errors.append(f"{task_id}: rationale required")
        if temporal == "current" and not entry.get("continuation_owner"):
            errors.append(f"{task_id}: current classification requires continuation_owner")

        impact = entry.get("ae_impact")
        if impact not in AE_IMPACTS:
            errors.append(f"{task_id}: invalid ae_impact")
            continue
        if impact == "NONE":
            if entry.get("phase") is not None or entry.get("activation_proof_ref") not in (None, ""):
                errors.append(f"{task_id}: ae_impact NONE cannot carry phase/activation proof")
        else:
            cap = entry.get("capability_id")
            if not isinstance(cap, str) or not cap:
                errors.append(f"{task_id}: capability_id required")
            if not isinstance(entry.get("capability_version"), str) or not entry.get("capability_version"):
                errors.append(f"{task_id}: capability_version required")
            if entry.get("task_relationship") not in RELATIONSHIPS:
                errors.append(f"{task_id}: valid task_relationship required")
            known = KNOWN_PHASES.get(cap)
            if known is not None and entry.get("phase") != known:
                errors.append(f"{task_id}: phase {entry.get('phase')} diverges from canonical {known}")
            if entry.get("phase") == "ACTIVATED" and not entry.get("activation_proof_ref"):
                errors.append(f"{task_id}: ACTIVATED requires independent activation proof")
            if entry.get("phase") == "ADMISSIBLE" and entry.get("activation_proof_ref"):
                errors.append(f"{task_id}: ADMISSIBLE may not carry activation proof")

    if errors:
        for error in errors:
            print("AE_RETROSPECTIVE_INVALID:" + error)
        return 1

    counts = {name: 0 for name in sorted(RESULTS)}
    for entry in entries:
        counts[entry["result"]] += 1
    print(
        "AE_RETROSPECTIVE_CONFORMANCE_PASS "
        f"effective_tasks={len(tasks)} classified={len(indexed)} "
        f"pass={counts['PASS']} review_required={counts['REVIEW_REQUIRED']} fail_closed={counts['FAIL_CLOSED']} "
        f"registry_generation={report['as_of_registry_generation']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
