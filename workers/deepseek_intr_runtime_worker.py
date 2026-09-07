#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-DEEPSEEK-INTR-RUNTIME-001"
CAPABILITY = "deepseek_intr_runtime_cycle"
REQUEST_REL = Path("control/resident-execution-request.d/deepseek-intr-runtime-001.json")
RECEIPT_REL = Path("receipts/deepseek-intr-runtime/SHWP-DEEPSEEK-INTR-RUNTIME-001.json")
INGRESS_REL = Path("receipts/deepseek-intr-runtime/ingress-steggate.latest.json")
EGRESS_REL = Path("receipts/deepseek-intr-runtime/egress-steggate.latest.json")
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "STEGVERSE_PROVIDER_TOKEN")
RUNTIME_PROFILE_ID = "stegverse:runtime-profile:llm-adapter-deepseek:v1"
PROTOCOL = "stegverse.intr.deepseek.transport.v1"


def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(value), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def require_local_root(env_name: str, required: tuple[str, ...]) -> Path:
    raw = str(os.environ.get(env_name) or "").strip()
    if not raw:
        raise RuntimeError(f"{env_name}_NOT_DECLARED")
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"{env_name}_NOT_MATERIALIZED")
    for rel in required:
        if not (root / rel).is_file():
            raise RuntimeError(f"{env_name}_REQUIRED_SOURCE_MISSING:{rel}")
    return root


def configure_imports() -> tuple[Path, Path, Path]:
    llm = require_local_root("STEGVERSE_LLM_ADAPTER_ROOT", (
        "llm_adapter/deepseek_tvc_runtime_executor.py",
        "llm_adapter/deepseek_tvc_broker.py",
        "llm_adapter/steggate_portable_consumer.py",
    ))
    tvc = require_local_root("STEGVERSE_TVC_ROOT", (
        "scripts/tvc_issue_deepseek_intr_lease.py",
        "tvc_provider_operation_broker.py",
        "config/provider_operation_profiles.json",
    ))
    stegcore = require_local_root("STEGVERSE_STEGCORE_SOURCE_ROOT", (
        "src/stegcore/portable_steggate.py",
        "src/stegcore/steggate.py",
    ))
    for path in (str(llm), str(tvc), str(stegcore / "src")):
        if path not in sys.path:
            sys.path.insert(0, path)
    return llm, tvc, stegcore


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
        "entrypoint": "scripts/refresh_and_execute_resident_task.py",
        "runtime_profile_id": RUNTIME_PROFILE_ID,
        "base_runtime_profile_id": "stegverse:runtime-profile:hb-intr-resident:v1",
        "protocol": PROTOCOL,
        "provider": "deepseek",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "provider_credential_material_allowed": False,
        "hosted_runtime_allowed": False,
        "master_records_custody_required_for_egress": True,
        "same_execution_required": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"resident_request_mismatch:{key}")
    if not isinstance(request.get("prompt"), str) or not request["prompt"].strip():
        raise RuntimeError("resident_request_prompt_missing")
    if not isinstance(request.get("model"), str) or not request["model"].strip():
        raise RuntimeError("resident_request_model_missing")
    if not isinstance(request.get("max_output_tokens"), int) or not 1 <= request["max_output_tokens"] <= 2048:
        raise RuntimeError("resident_request_output_bound_invalid")


def validate_claim(task: Mapping[str, Any]) -> dict[str, Any]:
    timing = task.get("heartbeat_timing") or {}
    snapshot = {
        "task_id": task.get("task_id"),
        "state": task.get("state"),
        "claim_id": task.get("claim_id"),
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": timing.get("fencing_token"),
        "executor_binding": task.get("executor_binding"),
    }
    if snapshot["task_id"] != TASK_ID:
        raise RuntimeError("worker_claim_task_mismatch")
    if snapshot["state"] != "ACTIVE":
        raise RuntimeError("worker_claim_not_active")
    if snapshot["worker_id"] != "deepseek-intr-runtime-worker":
        raise RuntimeError("worker_claim_worker_mismatch")
    if not isinstance(snapshot["claim_id"], str) or not snapshot["claim_id"]:
        raise RuntimeError("worker_claim_id_missing")
    if not isinstance(snapshot["worker_instance_id"], str) or not snapshot["worker_instance_id"]:
        raise RuntimeError("worker_instance_id_missing")
    if not isinstance(snapshot["fencing_token"], int) or snapshot["fencing_token"] <= 0:
        raise RuntimeError("worker_fence_missing")
    if snapshot["executor_binding"] != "AUTHORIZED":
        raise RuntimeError("worker_executor_not_authorized")
    return snapshot


def governance_facts(*, claim: Mapping[str, Any], signal_ref: str, reference_hash: str, capability_allowed: bool, continuity_receipt: str | None = None):
    from llm_adapter.steggate_portable_consumer import GovernanceFacts
    continuity = continuity_receipt is not None
    return GovernanceFacts(
        refusal_available=True,
        operator_recoverability="available",
        workload_state="supported",
        time_pressure="normal",
        isolation_state="supported",
        judgment_evidence_refs=(f"worker-claim:{claim['claim_id']}", signal_ref),
        admitted_signal_refs=(signal_ref,),
        missing_inputs=(),
        uncertainty_state="bounded",
        reference_state_hash=reference_hash,
        expected_reference_state_hash=reference_hash,
        reconstruction_available=True,
        transformation_provenance_complete=True,
        actor_authority_current=True,
        policy_current=True,
        delegation_current=True,
        evidence_current=True,
        affected_entity_conditions_represented=True,
        recoverability_profile="recoverable",
        validity_window_open=True,
        policy_ref="policy:deepseek-intr-runtime:v1",
        delegation_ref=f"worker-fence:{claim['fencing_token']}",
        execution_evidence_refs=(f"worker-instance:{claim['worker_instance_id']}",),
        capability_allowed=capability_allowed,
        continuity_required=continuity,
        previous_receipt_verified=True if continuity else None,
        previous_receipt_hash=continuity_receipt,
        approval_required=False,
        approval_valid=None,
        approval_candidate_hash=None,
        permission_present=False,
    )


def evaluate_interlock(*, phase: str, request_hash: str, model: str, claim: Mapping[str, Any], capability_allowed: bool, continuity_receipt: str | None = None):
    from llm_adapter.steggate_portable_consumer import UserLLMIntent, create_user_llm_governed_package
    from stegcore.portable_steggate import evaluate_governed_package

    intent = UserLLMIntent(
        user_id="stegverse-resident-worker",
        llm_id="deepseek-intr-runtime",
        provider="deepseek",
        model=model,
        prompt_hash=request_hash,
        route=f"deepseek_intr_{phase}",
        action="invoke_llm" if phase == "ingress" else "admit_llm_response",
    )
    package = create_user_llm_governed_package(
        package_id=f"deepseek-intr-{phase}-{request_hash[:24]}",
        intent=intent,
        governance=governance_facts(
            claim=claim,
            signal_ref=f"deepseek:{phase}:{request_hash}",
            reference_hash=request_hash,
            capability_allowed=capability_allowed,
            continuity_receipt=continuity_receipt,
        ),
        declared_execution_context={
            "runtime_profile_id": RUNTIME_PROFILE_ID,
            "worker_claim_id": claim["claim_id"],
            "worker_fencing_token": claim["fencing_token"],
            "phase": phase,
        },
    )
    receipt = evaluate_governed_package(package)
    value = asdict(receipt)
    disposition = (value.get("evaluation") or {}).get("disposition")
    return value, disposition


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if not isinstance(invocation, dict) or invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if task.get("task_id") != TASK_ID:
        return 4
    if CAPABILITY not in set((handoff.get("execution") or {}).get("required_capabilities") or []):
        return 5

    hosted = [key for key in HOSTED if truthy(os.environ.get(key))]
    secret_env = [key for key in FORBIDDEN if os.environ.get(key)]
    receipt: dict[str, Any] = {
        "schema": "stegverse.deepseek-intr-runtime-worker-receipt/v1",
        "task_id": TASK_ID,
        "state": "BLOCKED",
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "same_execution": False,
    }
    result: dict[str, Any] = {}
    transition = "DEEPSEEK_INTR_RUNTIME_BLOCKED"

    try:
        if hosted:
            raise RuntimeError("HOSTED_RUNTIME_PROHIBITED")
        if secret_env:
            raise RuntimeError("PROVIDER_CREDENTIAL_ENVIRONMENT_PROHIBITED")
        request = load_json(ROOT / REQUEST_REL)
        validate_request(request)
        claim = validate_claim(task)
        llm_root, tvc_root, _ = configure_imports()

        from llm_adapter.deepseek_intr_transport import build_deepseek_intr_envelope
        from llm_adapter.deepseek_tvc_runtime_executor import (
            admit_deepseek_tvc_runtime_egress,
            execute_governed_deepseek_via_tvc_runtime,
        )
        from llm_adapter.provider_request import build_provider_request
        from scripts.tvc_issue_deepseek_intr_lease import build_request as build_lease_request, issue as issue_lease
        from tvc_provider_operation_broker import forward_to_local_vault_broker

        provider_request = build_provider_request(
            provider="deepseek",
            model=request["model"],
            messages=[{"role": "user", "content": request["prompt"]}],
            purpose=request.get("purpose") or "bounded_connectivity_proof",
            temperature=0.0,
            metadata={"resident_task_id": TASK_ID, "credential_material_present": False},
        )
        provider_request_hash = provider_request.request_hash
        ingress_receipt, ingress_disposition = evaluate_interlock(
            phase="ingress",
            request_hash=provider_request_hash,
            model=request["model"],
            claim=claim,
            capability_allowed=True,
        )
        write_json(ROOT / INGRESS_REL, ingress_receipt)
        if ingress_disposition != "ALLOW":
            result = {"reason": "INGRESS_STEGGATE_NOT_ALLOWED", "disposition": ingress_disposition, "ingress_receipt_hash": ingress_receipt.get("receipt_hash")}
            raise RuntimeError("INGRESS_STEGGATE_NOT_ALLOWED")
        ingress_receipt_hash = str(ingress_receipt["receipt_hash"])
        transition_id = f"deepseek-intr:{claim['claim_id']}:{provider_request_hash[:16]}"
        carrier_ref = f"worker:{claim['worker_instance_id']}:fence:{claim['fencing_token']}"
        envelope = build_deepseek_intr_envelope(
            provider_request,
            transition_id=transition_id,
            ingress_disposition="ALLOW",
            ingress_receipt_hash=ingress_receipt_hash,
            carrier_ref=carrier_ref,
        )
        lease_request = build_lease_request(
            model=request["model"],
            transition_id=transition_id,
            request_hash=envelope.request_hash,
            ingress_receipt_hash=ingress_receipt_hash,
            carrier_ref=carrier_ref,
        )
        lease_receipt = issue_lease(lease_request)
        if lease_receipt.get("decision") != "ALLOW_CAPABILITY_LEASE":
            result = {"reason": "TVC_DEEPSEEK_LEASE_REFUSED", "refusal_reason": lease_receipt.get("refusal_reason")}
            raise RuntimeError("TVC_DEEPSEEK_LEASE_REFUSED")

        socket_path = str(os.environ.get("STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET") or "/run/stegverse/vault-broker.sock")
        broker_submitter = lambda value: forward_to_local_vault_broker(value, socket_path=socket_path)
        execution = execute_governed_deepseek_via_tvc_runtime(
            provider_request,
            session_id=f"deepseek-resident:{claim['claim_id']}",
            transition_id=transition_id,
            measurement_id=f"deepseek-measurement:{provider_request_hash[:24]}",
            ingress_disposition="ALLOW",
            ingress_receipt_hash=ingress_receipt_hash,
            carrier_ref=carrier_ref,
            lease_receipt=lease_receipt,
            broker_submitter=broker_submitter,
            max_output_tokens=request["max_output_tokens"],
            response_format=request["response_format"],
        )
        custody_recorded = execution.master_records_usage.get("custody_recorded") is True
        reconstruction = execution.master_records_usage.get("reconstructability")
        custody_pass = custody_recorded and reconstruction in {"PASS", "PENDING", None}
        egress_receipt, egress_disposition = evaluate_interlock(
            phase="egress",
            request_hash=execution.response_hash,
            model=request["model"],
            claim=claim,
            capability_allowed=custody_pass,
            continuity_receipt=ingress_receipt_hash,
        )
        write_json(ROOT / EGRESS_REL, egress_receipt)
        if not custody_recorded:
            result = {
                "reason": "MASTER_RECORDS_CUSTODY_NOT_RECORDED",
                "master_records_status": execution.master_records_usage.get("status"),
                "response_hash": execution.response_hash,
                "tvc_use_receipt_hash": execution.egress_handoff.get("tvc_use_receipt_hash"),
                "egress_disposition": egress_disposition,
            }
            raise RuntimeError("MASTER_RECORDS_CUSTODY_NOT_RECORDED")
        if egress_disposition != "ALLOW":
            result = {
                "reason": "EGRESS_STEGGATE_NOT_ALLOWED",
                "disposition": egress_disposition,
                "response_hash": execution.response_hash,
                "master_records_status": execution.master_records_usage.get("status"),
            }
            raise RuntimeError("EGRESS_STEGGATE_NOT_ALLOWED")
        admission = admit_deepseek_tvc_runtime_egress(
            execution,
            egress_disposition="ALLOW",
            egress_receipt_hash=str(egress_receipt["receipt_hash"]),
            admitted_response_hash=execution.response_hash,
        )
        receipt["state"] = "COMPLETED"
        receipt["same_execution"] = True
        transition = "DEEPSEEK_INTR_SAME_EXECUTION_COMPLETE"
        result = {
            "reason": "DEEPSEEK_INTR_SAME_EXECUTION_COMPLETE",
            "claim": claim,
            "provider_request_hash": provider_request_hash,
            "wire_request_hash": envelope.request_hash,
            "transition_id": transition_id,
            "transport_id": envelope.transport_id,
            "ingress_receipt_hash": ingress_receipt_hash,
            "tvc_lease_receipt_hash": stable_hash(lease_receipt),
            "tvc_use_receipt_hash": execution.egress_handoff.get("tvc_use_receipt_hash"),
            "response_hash": execution.response_hash,
            "provider_usage_event_sha256": execution.provider_usage_event.get("event_sha256"),
            "master_records_status": execution.master_records_usage.get("status"),
            "master_records_custody_recorded": execution.master_records_usage.get("custody_recorded") is True,
            "master_records_reconstructability": execution.master_records_usage.get("reconstructability"),
            "egress_receipt_hash": admission.egress_receipt_hash,
            "egress_state": admission.state,
            "runtime_profile_id": RUNTIME_PROFILE_ID,
            "provider_output_authority": "NONE",
            "credential_material_present": False,
        }
    except Exception as exc:
        if not result:
            reason = str(exc)
            if not reason or len(reason) > 160:
                reason = type(exc).__name__
            result = {"reason": reason, "error_type": type(exc).__name__}

    receipt["result"] = result
    write_json(ROOT / RECEIPT_REL, receipt)
    blocker = None if receipt["state"] == "COMPLETED" else {
        "dependency_class": "RUNTIME_PREDICATE",
        "problem_statement": result.get("reason", "DEEPSEEK_INTR_RUNTIME_BLOCKED"),
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": "REEXECUTE_SAME_RESIDENT_TASK_AFTER_REPAIRING_RECORDED_FIRST_FAILED_PREDICATE",
        "machine_observable_release_condition": "one WorkerCoordinator execution emits a same-execution DeepSeek ingress/TVC/provider/Master-Records/egress receipt chain"
    }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": receipt["state"],
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if receipt["state"] == "COMPLETED" else "DEEPSEEK_INTR_RUNTIME_RECHECK",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "recheck_policy": None if receipt["state"] == "COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref": RECEIPT_REL.as_posix(),
        "evidence_refs": [
            "handoffs/SHWP-DEEPSEEK-INTR-RUNTIME-001.json",
            RECEIPT_REL.as_posix(),
            INGRESS_REL.as_posix(),
            EGRESS_REL.as_posix(),
        ],
        "blocker": blocker,
        "cost_observation": {"task_control_evaluations": 1, "compute_units": 1, "external_cost_usd": None, "task_class": "deepseek_intr_runtime_cycle"},
    }
    json.dump(response, sys.stdout, sort_keys=True); sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
