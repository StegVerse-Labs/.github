#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "control" / "admissible-existence-retrospective-conformance.json"
FRAGMENT_DIR = ROOT / "control" / "admissible-existence-retrospective-conformance.d"
OVERRIDES = ROOT / "control" / "admissible-existence-retrospective-conformance.overrides.json"
TERMINAL = {"COMPLETED", "SUPERSEDED", "TERMINATED"}
RESULTS = {"PASS", "REVIEW_REQUIRED", "FAIL_CLOSED"}
IMPACTS = {"NONE", "CAPABILITY", "SUPPORTING_OPERATION_OF"}
RELATIONSHIPS = {"develops_capability", "integrates_capability", "validates_capability", "propagates_capability"}
KNOWN_PHASES = {
    "stegverse:capability:steggate:canonical:v1": "ACTIVATED",
    "stegverse:capability:sovereign-local-model:v1": "ADMISSIBLE",
    "stegverse:capability:transaction-discovery:v1": "ADMISSIBLE",
    "stegverse:capability:stegfin-base-pretrade:v1": "ADMISSIBLE",
    "stegverse:capability:stegfin-sovereign-internal-trading:v1": "ADMISSIBLE"
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def effective_tasks() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    aggregate = load(ROOT / "control" / "worker-registry.json")
    for task in aggregate.get("tasks", []):
        if isinstance(task, dict) and isinstance(task.get("task_id"), str): found[task["task_id"]] = task
    for path in sorted((ROOT / "control" / "worker-registry.d").glob("*.json")):
        doc = load(path)
        for task in doc.get("tasks", []):
            if isinstance(task, dict) and isinstance(task.get("task_id"), str): found[task["task_id"]] = task
    return found


def effective_entries(report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    entries = list(report.get("entries")) if isinstance(report.get("entries"), list) else []
    errors: list[str] = []
    if FRAGMENT_DIR.exists():
        for path in sorted(FRAGMENT_DIR.glob("*.json")):
            try:
                doc = load(path)
            except ValueError as exc:
                errors.append(str(exc)); continue
            if doc.get("schema") != "stegverse.admissible-existence-retrospective-conformance-fragment/v1":
                errors.append(f"AE retrospective fragment schema mismatch:{path.name}")
                continue
            fragment_entries = doc.get("entries")
            if not isinstance(fragment_entries, list):
                errors.append(f"AE retrospective fragment entries invalid:{path.name}")
                continue
            entries.extend(fragment_entries)
    return entries, errors


def apply_overrides(indexed: dict[str, dict[str, Any]]) -> None:
    if not OVERRIDES.is_file(): return
    doc = load(OVERRIDES)
    if doc.get("schema") != "stegverse.admissible-existence-retrospective-conformance-overrides/v1":
        raise ValueError("AE retrospective override schema mismatch")
    for override in doc.get("overrides", []):
        if not isinstance(override, dict) or not isinstance(override.get("task_id"), str):
            raise ValueError("invalid AE retrospective override")
        task_id = override["task_id"]
        if task_id not in indexed: raise ValueError(f"AE retrospective override targets missing task:{task_id}")
        for key in ("temporal_class", "continuation_owner", "rationale"):
            if key in override: indexed[task_id][key] = override[key]


def main() -> int:
    report = load(REPORT); tasks = effective_tasks(); errors: list[str] = []
    if report.get("schema") != "stegverse.admissible-existence-retrospective-conformance/v1": errors.append("schema mismatch")
    if report.get("credential_authority") != "TV/TVC": errors.append("credential authority must be TV/TVC")
    if report.get("github_token_runtime_authority") is not False: errors.append("GitHub-token runtime authority must be false")
    entries, fragment_errors = effective_entries(report); errors.extend(fragment_errors)
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("task_id"), str): errors.append("entry without task_id"); continue
        if entry["task_id"] in indexed: errors.append(f"duplicate:{entry['task_id']}")
        indexed[entry["task_id"]] = dict(entry)
    try: apply_overrides(indexed)
    except ValueError as exc: errors.append(str(exc))
    missing = sorted(set(tasks) - set(indexed)); extra = sorted(set(indexed) - set(tasks))
    if missing: errors.append("missing:" + ",".join(missing))
    if extra: errors.append("extra:" + ",".join(extra))
    for task_id, task in tasks.items():
        entry = indexed.get(task_id)
        if not entry: continue
        state = task.get("state"); temporal = entry.get("temporal_class")
        if state in TERMINAL and temporal != "recently_completed": errors.append(f"{task_id}:terminal must be recently_completed")
        if state not in TERMINAL and temporal != "current": errors.append(f"{task_id}:nonterminal must be current")
        if entry.get("result") not in RESULTS: errors.append(f"{task_id}:invalid result")
        if entry.get("ae_impact") not in IMPACTS: errors.append(f"{task_id}:invalid ae_impact")
        if entry.get("task_relationship") not in RELATIONSHIPS: errors.append(f"{task_id}:invalid relationship")
        if not entry.get("rationale"): errors.append(f"{task_id}:rationale required")
        if temporal == "current" and not entry.get("continuation_owner"): errors.append(f"{task_id}:continuation owner required")
        if entry.get("ae_impact") == "NONE":
            if entry.get("phase") is not None or entry.get("capability_id") is not None: errors.append(f"{task_id}:NONE may not claim capability phase")
        else:
            cap = entry.get("capability_id")
            if not isinstance(cap, str) or not cap: errors.append(f"{task_id}:capability_id required")
            known = KNOWN_PHASES.get(cap)
            if known and entry.get("phase") != known: errors.append(f"{task_id}:phase differs from canonical snapshot {known}")
            if entry.get("phase") == "ACTIVATED":
                binding = task.get("admissible_existence") if isinstance(task.get("admissible_existence"), dict) else {}
                if not binding.get("activation_proof_ref") and cap != "stegverse:capability:steggate:canonical:v1": errors.append(f"{task_id}:ACTIVATED lacks independent activation proof")
        doc_binding = task.get("admissible_existence") if isinstance(task.get("admissible_existence"), dict) else None
        if doc_binding and entry.get("ae_impact") != "NONE":
            for key in ("capability_id", "phase", "task_relationship"):
                if entry.get(key) != doc_binding.get(key): errors.append(f"{task_id}:{key} disagrees with explicit registry binding")
    if errors:
        for error in errors: print("AE_RETROSPECTIVE_INVALID:" + error)
        return 1
    counts = {key: 0 for key in RESULTS}
    for entry in indexed.values(): counts[entry["result"]] += 1
    print(f"AE_RETROSPECTIVE_CONFORMANCE_PASS effective_tasks={len(tasks)} classified={len(indexed)} pass={counts['PASS']} review_required={counts['REVIEW_REQUIRED']} fail_closed={counts['FAIL_CLOSED']} registry_generation={report['source_registry_generation']}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
