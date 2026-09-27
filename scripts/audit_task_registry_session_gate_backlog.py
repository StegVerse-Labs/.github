#!/usr/bin/env python3
"""Read-only, batch diagnosis of the existing component-010 Task Registry seam.

Never calls AI_SESSION_GATE, mints a COSV, writes an event, grants an execution
claim, or treats GitHub source state as authenticated resident evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data/canonical-task-registry.json"
DEFAULT_SHARDS = ROOT / "data/canonical-task-records"
GATE_REFERENCE = re.compile(r"AI_SESSION_GATE|RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010|POST_REGISTRATION_AUTHENTIC.*CHECKIN", re.I)
ACTIVE_STATES = {"ACTIVE", "CHECKED_OUT", "CLAIMED_INTEGRATION", "HANDOFF_READY_RUNTIME_PROOF_PENDING", "BLOCKED_RUNTIME_ACTIVATION"}


def audit(registry_path: Path, shards_path: Path) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry.get("generation"), int) or not isinstance(registry.get("tasks"), list):
        raise ValueError("invalid canonical Registry generation or tasks")
    rows: dict[str, dict] = {}
    for task in registry["tasks"]:
        tid = task.get("task_id")
        if not isinstance(tid, str) or not tid or tid in rows:
            raise ValueError("missing or duplicated canonical task identity")
        rows[tid] = task

    omitted_checked_out = []
    mismatched_identity = []
    unreadable = []
    for path in sorted(shards_path.glob("*.json")):
        try:
            shard = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            unreadable.append({"path": str(path.name), "error": type(exc).__name__})
            continue
        tid = shard.get("task_id")
        if tid != path.stem:
            mismatched_identity.append({"path": path.name, "declared_task_id": tid})
            continue
        canonical = rows.get(tid)
        if canonical:
            for field in ("correlation_id", "root_correlation_id", "parent_task_id"):
                a, b = canonical.get(field), shard.get(field)
                if a is not None and b is not None and a != b:
                    mismatched_identity.append({"path": path.name, "task_id": tid, "field": field})
            continue
        if (shard.get("checkout_state") == "CHECKED_OUT"
                and shard.get("coordination_state") in ACTIVE_STATES):
            omitted_checked_out.append({
                "task_id": tid,
                "shard": path.name,
                "shard_coordination_state": shard.get("coordination_state"),
                "shard_checkout_state": shard.get("checkout_state"),
                "owner_issue": shard.get("issue_ref") or shard.get("canonical_issue"),
                "authority_effect": "NONE",
            })

    waiting = []
    for tid, row in sorted(rows.items()):
        blockers = row.get("blockers") or []
        dependencies = row.get("dependencies") or []
        references = json.dumps({"blockers": blockers, "dependencies": dependencies})
        if not GATE_REFERENCE.search(references):
            continue
        waiting.append({
            "task_id": tid,
            "coordination_state": row.get("coordination_state"),
            "checkout_state": row.get("checkout_state"),
            "existing_cosv": row.get("cosv_task_vector"),
            "gate_blockers": [v for v in blockers if isinstance(v, str) and GATE_REFERENCE.search(v)],
            "source_only_gate_requirement": "NONE",
            "source_only_next_step": "RECONCILE_EXACT_CURRENT_REGISTRY_GENERATION_AND_EXISTING_OWNER_THEN_CONTINUE_NONAUTHORITATIVE_SOURCE_VALIDATION",
            "governed_next_step": "REQUIRE_AUTHENTIC_EXISTING_AI_SESSION_GATE_IF_AI_SESSION_AND_EXISTING_WORKERCOORDINATOR_INTR_MASTER_RECORDS_AS_APPLICABLE",
            "authentic_disposition_observed": False,
            "cosv_derivation_authorized_by_this_audit": False,
        })
    return {
        "schema": "stegverse.component010-gate-backlog-audit/v1",
        "registry_generation": registry["generation"],
        "registry_task_count": len(rows),
        "source": "CANONICAL_GITHUB_SOURCE_AUDIT_ONLY",
        "owner": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "component_id": "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010",
        "gate_blocked_registry_tasks": waiting,
        "omitted_checked_out_owner_shards": omitted_checked_out,
        "mismatched_identity_shards": mismatched_identity,
        "unreadable_shards": unreadable,
        "projection_complete_for_checked_out_shards": not (omitted_checked_out or mismatched_identity or unreadable),
        "shared_remediation": {
            "source_only": "NO_AI_SESSION_GATE_REQUIRED_FOR_NONAUTHORITATIVE_SOURCE_WORK_SUBJECT_TO_CURRENT_GENERATION_AND_EXISTING_OWNER",
            "authentic_resident": "EXISTING_COMPONENT010_AUTHORIZED_CALLER_AND_HASH_LINKED_EVENT_READBACK_REQUIRED",
            "no_fabricated_events_or_runtime_claims": True,
            "no_new_device_or_runtime": True,
        },
        "authority_effect": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--shards", type=Path, default=DEFAULT_SHARDS)
    parser.add_argument("--strict-projection", action="store_true",
                        help="Exit nonzero if checked-out owners are omitted or identity mismatches exist.")
    args = parser.parse_args()
    result = audit(args.registry, args.shards)
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(bool(args.strict_projection and not result["projection_complete_for_checked_out_shards"]))


if __name__ == "__main__":
    raise SystemExit(main())
