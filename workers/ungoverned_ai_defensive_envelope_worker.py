#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
CAPABILITY = "ungoverned_ai_defensive_envelope_runtime_probe"
TVC_SOURCE_FLOOR = "0b82b45de7d214fbdb2f24bc4027a6aeb31a7312"
RECEIPT_REL = Path("receipts/ai-defensive-envelope/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json")
HOSTED = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","OPENAI_API_KEY","ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY","STEGVERSE_PROVIDER_TOKEN","MASTER_RECORDS_TOKEN",
    "MASTER_RECORDS_RECEIPT_KEY","STEGVERSE_VAULT_AGENT_SOCKET",
    "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET",
)

def _truthy(v: Any) -> bool:
    return str(v or "").strip().lower() not in {"","0","false","no"}

def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _claim(task: Mapping[str, Any], scope: Mapping[str, Any]) -> dict[str, Any]:
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if task.get("task_id") != TASK_ID or task.get("state") != "ACTIVE":
        raise RuntimeError("CURRENT_WORKERCOORDINATOR_TASK_NOT_ACTIVE")
    if not isinstance(claim_id, str) or not claim_id:
        raise RuntimeError("CURRENT_WORKERCOORDINATOR_CLAIM_MISSING")
    if not isinstance(fence, int) or fence < 1 or not claim_id.endswith(f"-G{fence}"):
        raise RuntimeError("CURRENT_WORKERCOORDINATOR_FENCE_INVALID")
    if scope.get("claim_id") != claim_id or scope.get("fencing_token") != fence:
        raise RuntimeError("WORKERCOORDINATOR_SCOPE_CLAIM_FENCE_MISMATCH")
    return {"claim_id": claim_id, "fencing_token": fence, "worker_id": task.get("worker_id")}

def _tvc_root() -> tuple[Path, str]:
    raw = str(os.environ.get("STEGVERSE_TVC_ROOT") or "").strip()
    if not raw:
        raise RuntimeError("TVC_SES_BOUNDARY_SOURCE_NOT_MATERIALIZED")
    root = Path(raw).expanduser().resolve()
    target = root / "tasks" / "ungoverned_ai_defensive_envelope.py"
    if not root.is_dir() or not target.is_file():
        raise RuntimeError("TVC_SES_BOUNDARY_SOURCE_NOT_MATERIALIZED")
    head = subprocess.run(
        ["git","-C",str(root),"rev-parse","HEAD"],
        capture_output=True,text=True,check=False,timeout=10,
        env={"PATH": os.environ.get("PATH","")},
    )
    anc = subprocess.run(
        ["git","-C",str(root),"merge-base","--is-ancestor",TVC_SOURCE_FLOOR,"HEAD"],
        capture_output=True,text=True,check=False,timeout=10,
        env={"PATH": os.environ.get("PATH","")},
    )
    if head.returncode != 0 or anc.returncode != 0:
        raise RuntimeError("TVC_SES_BOUNDARY_SOURCE_FLOOR_NOT_VERIFIED")
    return root, head.stdout.strip()

def _response(state: str, transition: str, evidence: list[str], error: str | None = None, *, boundary_receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_RUNTIME_RECHECK",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": RECEIPT_REL.as_posix() if evidence else None,
        "evidence_refs": evidence,
        "cost_observation": {
            "compute_units": 1, "token_units": 0, "storage_bytes": 8192,
            "network_bytes": 0, "operator_seconds": 0, "external_cost_usd": 0,
            "latency_ms": None, "failure_recovery_units": 0 if state == "COMPLETED" else 1,
            "services_used": [],
        },
    }
    if boundary_receipt is not None:
        canonical = json.dumps(dict(boundary_receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        out["boundary_receipt_sha256"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
        out["boundary_claim_id"] = (boundary_receipt.get("claim") or {}).get("claim_id")
        out["boundary_fencing_token"] = (boundary_receipt.get("claim") or {}).get("fencing_token")
    if error:
        out["error"] = error
    return out

def run(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("WORKER_INVOCATION_SCHEMA_MISMATCH")
    task = invocation.get("task")
    handoff = invocation.get("handoff")
    scope = invocation.get("scope")
    if not isinstance(task, dict) or not isinstance(handoff, dict) or not isinstance(scope, dict):
        raise RuntimeError("WORKER_INVOCATION_FIELDS_MISSING")
    required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if CAPABILITY not in required:
        raise RuntimeError("DEFENSIVE_ENVELOPE_CAPABILITY_NOT_ADMITTED")
    claim = _claim(task, scope)

    if any(_truthy(os.environ.get(name)) for name in HOSTED):
        raise RuntimeError("HOSTED_RUNTIME_NOT_ADMITTED")
    exposed = [name for name in FORBIDDEN_ENV if os.environ.get(name)]
    if exposed:
        raise RuntimeError("AMBIENT_PROTECTED_AUTHORITY_ENVIRONMENT_PRESENT:" + ",".join(sorted(exposed)))

    tvc, tvc_head = _tvc_root()
    sys.path.insert(0, str(tvc))
    from tasks.ungoverned_ai_defensive_envelope import run_defensive_envelope_probe

    probe = run_defensive_envelope_probe()
    admitted = probe.get("admitted_interaction") or {}
    denied = probe.get("denied_interactions") or []
    checks = {
        "component": probe.get("component_id") == "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011",
        "external_provider_not_claimed": probe.get("external_provider_observed") is False,
        "allow_consumed": admitted.get("decision") == "ALLOW" and admitted.get("consumed") is True,
        "allow_result": admitted.get("result_observed") == 42,
        "filesystem_not_exposed": admitted.get("filesystem_capability_exposed") is False,
        "network_not_exposed": admitted.get("network_capability_exposed") is False,
        "candidate_not_materialized": admitted.get("candidate_source_materialized_to_filesystem") is False,
        "temporary_state_destroyed": admitted.get("temporary_state_destroyed") is True,
        "deny_present": len(denied) >= 1,
        "deny_not_consumed": bool(denied) and all(row.get("decision") == "DENY" and row.get("consumed") is False for row in denied),
        "deny_consequence_unreachable": bool(denied) and all(row.get("consequence_reachable") is False for row in denied),
        "ambient_credentials_not_exposed": probe.get("ambient_credential_capability_exposed") is False,
        "task_registry_not_exposed": probe.get("task_registry_authority_exposed") is False,
        "tv_tvc_not_exposed": probe.get("tv_tvc_authority_exposed") is False,
        "intr_not_exposed": probe.get("interlock_intr_authority_exposed") is False,
        "master_records_not_exposed": probe.get("master_records_authority_exposed") is False,
        "publisher_not_exposed": probe.get("publisher_authority_exposed") is False,
        "host_runtime_not_exposed": probe.get("host_runtime_authority_exposed") is False,
        "sovereignty_preserved": probe.get("candidate_internal_sovereignty_preserved") is True,
        "egress_evidence_only": probe.get("governed_egress_disposition") == "EVIDENCE_ONLY_NO_CONSEQUENTIAL_EGRESS_REQUESTED",
    }
    failed = sorted(k for k,v in checks.items() if not v)
    if failed:
        raise RuntimeError("DEFENSIVE_ENVELOPE_RUNTIME_INVARIANT_MISMATCH:" + ",".join(failed))

    receipt = {
        "schema": "stegverse.ungoverned-ai-defensive-envelope-resident-boundary/v1",
        "task_id": TASK_ID,
        "component_id": "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011",
        "state": "REPRESENTATIVE_BOUNDARY_PROBE_OBSERVED",
        "claim": claim,
        "tvc_source_floor": TVC_SOURCE_FLOOR,
        "tvc_source_head": tvc_head,
        "candidate_origin": probe.get("candidate_origin"),
        "external_provider_observed": False,
        "probe": probe,
        "checks": checks,
        "governed_egress_disposition": "EVIDENCE_ONLY_NO_CONSEQUENTIAL_EGRESS_REQUESTED",
        "goal_runtime_completion_claimed": False,
        "authority_effect": "NONE_BOUNDARY_EVIDENCE_ONLY",
    }
    _write(RECEIPT_REL, receipt)
    return _response(
        "COMPLETED",
        "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_REPRESENTATIVE_BOUNDARY_OBSERVED",
        [RECEIPT_REL.as_posix()],
        boundary_receipt=receipt,
    )

def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        if not isinstance(invocation, dict):
            raise RuntimeError("WORKER_INVOCATION_NOT_OBJECT")
        result = run(invocation)
    except Exception as exc:
        result = _response(
            "HANDOFF_READY",
            "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_RUNTIME_NOT_PROVEN",
            [],
            f"{type(exc).__name__}: {exc}"[:1200],
        )
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
