from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


UPSTREAM_POLICY_ID = "AE-CONTINUATION-CONFORMANCE-001"
UPSTREAM_COMMIT = "78d00ca0e977af3e666c2acec431b111aea0deef"
TERMINAL_REGISTRY_STATES = {"COMPLETED", "SUPERSEDED", "TERMINATED"}
FORBIDDEN_AUTHORITY = {
    "HEARTBEAT_WORKER_EXECUTOR_AUTHORITY",
    "HEARTBEAT_TRANSPORT_AUTHORITY",
    "HEARTBEAT_CUSTODY_AUTHORITY",
    "MASTER_RECORDS_EXECUTION_AUTHORITY",
    "GITHUB_TOKEN_RUNTIME_AUTHORITY",
    "NON_TV_TVC_CREDENTIAL_AUTHORITY",
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def verify(registry: dict[str, Any], projection: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    if source.get("policy_id") != UPSTREAM_POLICY_ID or source.get("source_commit") != UPSTREAM_COMMIT:
        findings.append({"code": "upstream_policy_pin_invalid", "detail": "StegCore AE conformance source pin is not canonical"})
    if source.get("credential_authority") != "TV/TVC":
        findings.append({"code": "credential_authority_invalid", "detail": "credential authority must be TV/TVC"})
    if source.get("github_token_runtime_authority") is not False:
        findings.append({"code": "github_token_runtime_authority_forbidden", "detail": "GitHub token runtime authority must be false"})
    if source.get("heartbeat_role") != "CARRIER_SYNCHRONIZATION_ONLY":
        findings.append({"code": "heartbeat_role_invalid", "detail": "heartbeat must remain carrier/synchronization only"})
    if source.get("worker_control_plane_separate") is not True:
        findings.append({"code": "worker_control_plane_not_separate", "detail": "worker control plane must remain separate from heartbeat"})
    if source.get("master_records_custody_separate") is not True:
        findings.append({"code": "master_records_custody_not_separate", "detail": "Master Records custody must remain separate"})

    registry_by_id = {t.get("task_id"): t for t in registry.get("tasks", []) if t.get("task_id")}
    projected_by_id = {t.get("task_id"): t for t in projection.get("tasks", []) if t.get("task_id")}

    for task_id, task in projected_by_id.items():
        reg = registry_by_id.get(task_id)
        if reg is None:
            findings.append({"code": "registry_task_missing", "task_id": task_id, "detail": "projected task is absent from canonical worker registry"})
            continue
        if task.get("goal_id") != reg.get("goal_id"):
            findings.append({"code": "goal_id_mismatch", "task_id": task_id, "detail": "projection goal_id differs from registry"})
        if task.get("handoff_ref") != reg.get("handoff_ref"):
            findings.append({"code": "handoff_ref_mismatch", "task_id": task_id, "detail": "projection handoff_ref differs from registry"})

        impact = task.get("ae_impact")
        if impact == "CAPABILITY":
            if not task.get("capability_id"):
                findings.append({"code": "capability_id_missing", "task_id": task_id, "detail": "capability-impacting task requires capability_id"})
            if not task.get("existence_phase"):
                findings.append({"code": "existence_phase_missing", "task_id": task_id, "detail": "capability-impacting task requires existence phase"})
            if task.get("existence_phase") == "ACTIVATED":
                if not task.get("integration_evidence_refs"):
                    findings.append({"code": "activation_integration_evidence_missing", "task_id": task_id, "detail": "ACTIVATED requires integration evidence"})
                if not task.get("activation_proof_ref"):
                    findings.append({"code": "activation_proof_missing", "task_id": task_id, "detail": "ACTIVATED requires activation proof"})
        elif impact == "NONE":
            if not task.get("ae_rationale"):
                findings.append({"code": "ae_none_rationale_missing", "task_id": task_id, "detail": "ae_impact NONE requires rationale"})
        else:
            findings.append({"code": "ae_impact_missing", "task_id": task_id, "detail": "task requires explicit CAPABILITY or NONE AE classification"})

        forbidden = sorted(set(task.get("authority_claims", [])) & FORBIDDEN_AUTHORITY)
        if forbidden:
            findings.append({"code": "forbidden_authority_claim", "task_id": task_id, "detail": ", ".join(forbidden)})

        temporal = task.get("temporal_class")
        reg_state = reg.get("state")
        if temporal == "RECENTLY_COMPLETED" and reg_state not in TERMINAL_REGISTRY_STATES:
            findings.append({"code": "completed_registry_state_invalid", "task_id": task_id, "detail": "recently completed projection is not terminal in registry"})
        if temporal == "CURRENT" and reg_state in TERMINAL_REGISTRY_STATES:
            findings.append({"code": "current_registry_state_terminal", "task_id": task_id, "detail": "current projection conflicts with terminal registry state"})
        if temporal == "FUTURE" and task.get("existence_phase") == "ACTIVATED":
            findings.append({"code": "future_activation_forbidden", "task_id": task_id, "detail": "future task cannot pre-claim ACTIVATED"})
        if temporal == "CURRENT" and task.get("blockers") and not task.get("continuation_owner"):
            findings.append({"code": "blocked_current_without_continuation_owner", "task_id": task_id, "detail": "blocked current task requires continuation owner"})

    return {
        "artifact_type": "stegverse.ae_continuation_adoption_validation",
        "schema_version": "1.0",
        "policy_id": UPSTREAM_POLICY_ID,
        "source_commit": UPSTREAM_COMMIT,
        "registry_generation": registry.get("generation"),
        "registry_hash": canonical_hash(registry),
        "projection_hash": canonical_hash(projection),
        "valid": not findings,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Worker Task Registry/HANDOFF projection verification against canonical StegCore AE continuation policy")
    parser.add_argument("--registry", type=Path, default=Path("control/worker-registry.json"))
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path("control/ae-continuation-conformance-source.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    projection = json.loads(args.projection.read_text(encoding="utf-8"))
    source = json.loads(args.source.read_text(encoding="utf-8"))
    result = verify(registry, projection, source)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
