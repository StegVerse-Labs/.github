#!/usr/bin/env python3
"""Project when a goal has reached a no-work terminal condition.

COMPLETED is the registry's authoritative statement that the task's declared
success predicates were satisfied by the bounded executor. Convergence adds the
stronger fabric-wide conditions required to stop successor generation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
OUTPUT = ROOT / "control" / "goal-convergence.json"
UNRESOLVED = {"HANDOFF_READY", "ACTIVATION_PENDING", "CLAIMED", "ACTIVE", "BLOCKED", "HUMAN_AUTHORITY_REQUIRED", "EXPIRING", "HANDOFF_WRITING", "FAILED_RETRYABLE", "QUARANTINED"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(registry: dict, root: Path = ROOT) -> dict:
    tasks = {item["task_id"]: item for item in registry.get("tasks", [])}
    handoffs = {task_id: load(root / task["handoff_ref"]) for task_id, task in tasks.items() if (root / task["handoff_ref"]).exists()}
    children: dict[str, list[str]] = {}
    for task_id, handoff in handoffs.items():
        parent = (handoff.get("task") or {}).get("parent_task_id")
        if parent:
            children.setdefault(parent, []).append(task_id)

    def descendants(task_id: str) -> list[str]:
        out: list[str] = []
        stack = list(children.get(task_id, []))
        while stack:
            current = stack.pop()
            if current in out:
                continue
            out.append(current)
            stack.extend(children.get(current, []))
        return out

    goals = []
    for task_id, task in sorted(tasks.items()):
        handoff = handoffs.get(task_id)
        if handoff is None:
            continue
        if (handoff.get("task") or {}).get("parent_task_id") is not None:
            continue
        desc = descendants(task_id)
        family = [task_id, *desc]
        success = task.get("state") == "COMPLETED"
        unresolved_desc = [item for item in desc if tasks.get(item, {}).get("state") in UNRESOLVED]
        active_claims = [item for item in family if tasks.get(item, {}).get("claim_id") or tasks.get(item, {}).get("worker_id")]
        custody_missing = []
        for item in family:
            h = handoffs.get(item) or {}
            t = tasks.get(item) or {}
            if (h.get("continuity") or {}).get("master_records_required"):
                # Terminal completed tasks are accepted when their completion evidence is
                # durable; otherwise explicit Master Records evidence is required.
                custody = t.get("state") == "COMPLETED" or any("master-records" in str(ref).lower() for ref in t.get("evidence_refs", []))
                if not custody:
                    custody_missing.append(item)
        authorized_remaining = []
        for item in family:
            t = tasks.get(item) or {}
            h = handoffs.get(item) or {}
            activation = h.get("activation") or {}
            if t.get("state") not in {"COMPLETED", "FAILED_TERMINAL"} and activation.get("executor_binding") in {"AUTHORIZED", "BOUND"} and activation.get("authorization_ref"):
                authorized_remaining.append(item)

        checks = {
            "success_predicates_satisfied": success,
            "no_unresolved_descendants": not unresolved_desc,
            "no_active_claims": not active_claims,
            "custody_reconstruction_complete": not custody_missing,
            "no_authorized_remaining_action": not authorized_remaining,
        }
        reasons = []
        if not success: reasons.append("ROOT_SUCCESS_PREDICATES_NOT_SATISFIED")
        if unresolved_desc: reasons.append("UNRESOLVED_DESCENDANTS")
        if active_claims: reasons.append("ACTIVE_CLAIMS_REMAIN")
        if custody_missing: reasons.append("CUSTODY_OR_RECONSTRUCTION_INCOMPLETE")
        if authorized_remaining: reasons.append("AUTHORIZED_REMAINING_ACTION")
        goals.append({
            "goal_id": task.get("goal_id") or (handoff.get("goal") or {}).get("goal_id"),
            "root_task_id": task_id,
            "state": task.get("state"),
            **checks,
            "converged": all(checks.values()),
            "reason_codes": reasons,
        })
    return {"schema": "stegverse.goal-convergence/v0.1", "source_registry_generation": registry.get("generation", 0), "goals": goals}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = evaluate(load(REGISTRY))
    if args.write:
        OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.check and OUTPUT.exists() and load(OUTPUT) != value:
        print(json.dumps(value, indent=2, sort_keys=True))
        print("ERROR: committed goal-convergence projection differs from current state")
        return 1
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
