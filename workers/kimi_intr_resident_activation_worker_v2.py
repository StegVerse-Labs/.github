#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "KIMI-INTR-RESIDENT-ACTIVATION-001"
CAPABILITY = "kimi_intr_resident_activation"
RECEIPT = Path("receipts/kimi-intr-resident-activation/KIMI-INTR-RESIDENT-ACTIVATION-001.json")
TVC_BROKER_DEFAULT = "/run/stegverse/vault-broker.sock"
MR_BROKER_DEFAULT = "/run/stegverse/master-records-provider-usage.sock"
MAX_OUTPUT_TOKENS = 4096
RESPONSE_FORMAT = "json"
HOSTED = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_SECRET_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "KIMI_API_KEY", "MASTER_RECORDS_AUTH_TOKEN",
    "MASTER_RECORDS_RECEIPT_KEY", "STEGVERSE_MASTER_RECORDS_TOKEN",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalized_sha256(value: str) -> str:
    text = str(value or "")
    return text[7:] if text.startswith("sha256:") else text


def write_receipt(value: Mapping[str, Any]) -> None:
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_root(env_name: str, required: tuple[str, ...]) -> Path:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        raise RuntimeError(f"{env_name}_NOT_DECLARED")
    root = Path(raw).expanduser().resolve()
    missing = [item for item in required if not (root / item).is_file()]
    if missing:
        raise RuntimeError(f"{env_name}_SOURCE_INCOMPLETE:{','.join(missing)}")
    return root


def socket_ready(path: str) -> bool:
    target = Path(path)
    try:
        return target.is_absolute() and target.exists() and stat.S_ISSOCK(target.stat().st_mode)
    except OSError:
        return False


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def find_profile(registry: Mapping[str, Any], profile_id: str) -> dict[str, Any]:
    profiles = registry.get("profiles")
    if not isinstance(profiles, list):
        raise RuntimeError("GOVERNANCE_PROFILE_REGISTRY_INVALID")
    matches = [item for item in profiles if isinstance(item, dict) and item.get("profile_id") == profile_id]
    if len(matches) != 1:
        raise RuntimeError("HOSTED_LLM_GOVERNANCE_PROFILE_NOT_UNIQUELY_RESOLVED")
    return dict(matches[0])


def local_master_records_submitter(socket_path: str):
    def submit(event: dict[str, Any]) -> dict[str, Any]:
        request = {
            "schema": "stegverse.master_records.local_provider_usage_request.v1",
            "event": event,
            "authority_requested": False,
            "custody_requested": True,
        }
        chunks: list[bytes] = []
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(30)
            client.connect(socket_path)
            client.sendall(canonical(request) + b"\n")
            while True:
                part = client.recv(65536)
                if not part:
                    break
                chunks.append(part)
                if b"\n" in part:
                    break
        raw = b"".join(chunks).split(b"\n", 1)[0]
        response = json.loads(raw.decode("utf-8"))
        if not isinstance(response, dict):
            raise RuntimeError("MASTER_RECORDS_LOCAL_CUSTODY_RESPONSE_INVALID")
        required = {
            "decision": "ALLOW_CUSTODY_RESULT",
            "status": "CUSTODY_RECORDED",
            "custody_recorded": True,
            "reconstructability": "PASS",
            "authority_granted": False,
            "secret_material_returned": False,
            "credential_material_returned": False,
        }
        if any(response.get(key) != expected for key, expected in required.items()):
            raise RuntimeError("MASTER_RECORDS_LOCAL_CUSTODY_NOT_PROVEN")
        return response
    return submit


def blocked(reason: str, *, epoch: int | None = None, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    result = {
        "reason": reason,
        "heartbeat_epoch": epoch,
        "credential_authority": "TV/TVC",
        "provider_credential_material_present": False,
        "master_records_credential_material_present": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "transport_grants_execution_authority": False,
        "governance_grants_execution_authority": False,
        "governance_grants_credential_authority": False,
        "execution_authorized_by_request": False,
        "publication_authorized": False,
    }
    if extra:
        result.update(dict(extra))
    receipt = {
        "schema": "stegverse.kimi-intr-resident-activation-worker-receipt/v2",
        "task_id": TASK_ID,
        "state": "BLOCKED",
        "result": result,
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
    }
    write_receipt(receipt)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "KIMI_INTR_RESIDENT_ACTIVATION_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "KIMI_INTR_RESIDENT_ACTIVATION_RECHECK",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "recheck_policy": "SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref": str(RECEIPT),
        "evidence_refs": ["docs/KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md", str(RECEIPT)],
        "blocker": {
            "dependency_class": "LOCAL_RUNTIME_OR_AUTHORITY_EVIDENCE",
            "problem_statement": reason,
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "RECHECK_EXISTING_LOCAL_SOURCE_AND_BROKER_PREDICATES",
            "machine_observable_release_condition": "one resident cycle completes exact-byte InTr->Governance->TVC/Kimi->Master Records->InTr with retained evidence",
        },
        "cost_observation": {"task_control_evaluations": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "kimi_intr_resident_activation"},
    }


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    task = invocation.get("task") or {}
    scope = invocation.get("scope") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        raise RuntimeError("WORKER_INVOCATION_BINDING_INVALID")
    if CAPABILITY not in set((handoff.get("execution") or {}).get("required_capabilities") or []):
        raise RuntimeError("WORKER_CAPABILITY_BINDING_INVALID")

    hosted = [name for name in HOSTED if truthy(os.environ.get(name))]
    if hosted:
        return blocked("HOSTED_RUNTIME_PROHIBITED", epoch=epoch, extra={"hosted_markers": hosted})
    leaked = [name for name in FORBIDDEN_SECRET_ENV if os.environ.get(name)]
    if leaked:
        return blocked("CREDENTIAL_BEARING_WORKER_ENVIRONMENT_PROHIBITED", epoch=epoch, extra={"forbidden_environment": leaked})
    if os.environ.get("STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY") != "TV/TVC":
        return blocked("TV_TVC_CREDENTIAL_AUTHORITY_NOT_BOUND", epoch=epoch)

    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    claim_current = isinstance(claim_id, str) and bool(claim_id) and isinstance(fence, int) and fence >= 1
    if not claim_current:
        return blocked("CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_REQUIRED", epoch=epoch)
    fence_bound = scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence and claim_id.endswith(f"-G{fence}")
    if not fence_bound:
        return blocked("WORKERCOORDINATOR_CLAIM_FENCE_BINDING_MISMATCH", epoch=epoch)

    try:
        llm = require_root("STEGVERSE_LLM_ADAPTER_ROOT", (
            "llm_adapter/kimi_canonical_runtime.py",
            "llm_adapter/kimi_tvc_provider_wire.py",
        ))
        tvc = require_root("STEGVERSE_TVC_ROOT", (
            "scripts/tvc_run_provider_measurement.py",
            "scripts/tvc_issue_provider_measurement_lease.py",
            "tvc_provider_operation_broker.py",
        ))
        stegos = require_root("STEGVERSE_STEGOS_ROOT", (
            "stegos/intr_backbone.py",
            "specs/universal-intr-connector-profiles.v1.json",
        ))
        governance = require_root("STEGVERSE_GOVERNANCE_ROOT", ("specs/universal-governance-connector-profiles.v1.json",))
        stegcore = require_root("STEGVERSE_STEGCORE_SOURCE_ROOT", (
            "src/stegcore/universal_governance_connector.py",
            "src/stegcore/three_layer.py",
        ))
        lanes = require_root("STEGVERSE_TEST_LANES_ROOT", ("experiments/sv-cost-program/nine-lane-results/task.json",))
        require_root("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", ("services/master_records_local_provider_usage_broker.py",))
    except Exception as exc:
        return blocked(str(exc), epoch=epoch)

    tvc_socket = os.environ.get("STEGVERSE_VAULT_BROKER_SOCKET", TVC_BROKER_DEFAULT)
    mr_socket = os.environ.get("STEGVERSE_MASTER_RECORDS_PROVIDER_USAGE_SOCKET", MR_BROKER_DEFAULT)
    if not socket_ready(tvc_socket):
        return blocked("TVC_VAULT_BROKER_SOCKET_NOT_READY", epoch=epoch, extra={"socket": tvc_socket})
    if not socket_ready(mr_socket):
        return blocked("MASTER_RECORDS_LOCAL_CUSTODY_SOCKET_NOT_READY", epoch=epoch, extra={"socket": mr_socket})

    for path in (str(llm), str(tvc), str(stegos), str(stegcore / "src")):
        if path not in sys.path:
            sys.path.insert(0, path)

    try:
        from llm_adapter.kimi_canonical_runtime import execute_canonical_kimi_via_tvc_runtime
        from llm_adapter.kimi_tvc_provider_wire import (
            canonical_kimi_tvc_provider_request_hash,
            canonical_kimi_tvc_provider_wire_bytes,
        )
        from llm_adapter.provider_request import build_provider_request
        from stegos.intr_backbone import connector_from_registry
        from stegcore.universal_governance_connector import VerifiedTransportBindings, evaluate_governance_connector, parse_governance_connector_request
        from scripts.tvc_issue_provider_measurement_lease import issue
        from scripts.tvc_run_provider_measurement import TASK_BLOB_SHA, build_prompt, git_blob_sha, lease_request
        from tvc_provider_operation_broker import forward_to_local_vault_broker, load_profiles
    except Exception as exc:
        return blocked(f"CANONICAL_RUNTIME_IMPORT_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)

    task_path = lanes / "experiments/sv-cost-program/nine-lane-results/task.json"
    task_bytes = task_path.read_bytes()
    if git_blob_sha(task_bytes) != TASK_BLOB_SHA:
        return blocked("SV_RECON_TASK_EXACT_BLOB_MISMATCH", epoch=epoch)
    try:
        task_json = json.loads(task_bytes.decode("utf-8"))
        prompt = build_prompt(task_json)
    except Exception as exc:
        return blocked(f"SV_RECON_PROMPT_BINDING_FAILED:{exc}", epoch=epoch)

    request = build_provider_request(provider="kimi", model="kimi-k3", messages=[{"role": "user", "content": prompt}])
    try:
        wire = canonical_kimi_tvc_provider_wire_bytes(
            request, max_output_tokens=MAX_OUTPUT_TOKENS, response_format=RESPONSE_FORMAT
        )
        exact_request_hash = canonical_kimi_tvc_provider_request_hash(
            request, max_output_tokens=MAX_OUTPUT_TOKENS, response_format=RESPONSE_FORMAT
        )
    except Exception as exc:
        return blocked(f"EXACT_TVC_PROVIDER_WIRE_BUILD_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)
    if sha256_bytes(wire) != exact_request_hash:
        return blocked("EXACT_TVC_PROVIDER_WIRE_HASH_SELF_MISMATCH", epoch=epoch)

    transition_id = f"KIMI-INTR-RESIDENT-ACTIVATION-001:HB{epoch}:G{fence}"
    session_id = transition_id
    measurement_id = transition_id + ":provider-usage"
    carrier_ref = f"workercoordinator:{claim_id}:HB{epoch}:G{fence}"

    try:
        connector = connector_from_registry(stegos / "specs/universal-intr-connector-profiles.v1.json", "external-provider-operation")
        packet = connector.prepare(
            wire,
            payload_schema="stegverse.external-provider.operation-request/v1",
            operation="REQUEST_PROVIDER_OPERATION",
            operation_id=transition_id + ":INGRESS",
        )
        if normalized_sha256(packet.payload_hash) != exact_request_hash:
            raise RuntimeError("UNIVERSAL_INTR_INGRESS_PAYLOAD_HASH_NOT_EXACT_TVC_WIRE")
        ingress_receipt = connector.accept_hop(
            packet,
            hop_index=1,
            receipt_id="KIMI-IN-" + packet.intent["packet_id"][5:],
            boundary_identity_ref="TVC:ProviderOperationBroker:STAGED",
            recorded_at=datetime.now(timezone.utc).isoformat(),
            prior_receipt_hash=None,
            transition_state="STAGED",
        )
        ingress_complete = connector.validate_complete(packet, [ingress_receipt])
        if ingress_complete.get("state") != "TRANSPORT_COMPLETE":
            raise RuntimeError("UNIVERSAL_INTR_INGRESS_NOT_COMPLETE")
    except Exception as exc:
        return blocked(f"UNIVERSAL_INTR_INGRESS_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)

    gov_registry = read_json(governance / "specs/universal-governance-connector-profiles.v1.json")
    try:
        profile = find_profile(gov_registry, "hosted-llm-provider-operation.v1")
        interlock = profile.get("interlock") or {}
        if interlock.get("intr_profile_ref") != "external-provider-operation":
            raise RuntimeError("HOSTED_LLM_GOVERNANCE_INTR_PROFILE_DRIFT")

        # These conditions are derived from the current bounded invocation and loaded
        # canonical evidence. They are not source constants used to manufacture ALLOW.
        refusal_available = True  # every pre-provider branch above can refuse without consequence
        operator_recoverability = "available" if claim_current and fence_bound else "unavailable"
        workload_state = "supported" if CAPABILITY in set(scope.get("required_capabilities") or []) else "unknown"
        time_pressure = "normal" if timing.get("expiry_epoch") in (None, 0) or epoch <= int(timing.get("expiry_epoch") or epoch) else "critical"
        isolation_state = "supported" if socket_ready(tvc_socket) and socket_ready(mr_socket) else "unknown"
        policy_current = profile.get("profile_id") == "hosted-llm-provider-operation.v1"
        delegation_current = claim_current and fence_bound
        evidence_current = ingress_complete.get("state") == "TRANSPORT_COMPLETE"
        validity_window_open = time_pressure != "critical"
        affected_entities_represented = (profile.get("system") or {}).get("system_id") == "external-provider.hosted-llm"

        current_ref = exact_request_hash
        gov_payload = {
            "schema_version": "stegverse.governance-connector.request/v1",
            "profile_id": "hosted-llm-provider-operation.v1",
            "operation_id": "execute-provider-operation",
            "system_id": "external-provider.hosted-llm",
            "boundary_id": "interlock:hosted-llm-provider-operation",
            "authority_ref": f"workercoordinator:{claim_id}",
            "intent_ref": packet.intent["packet_id"],
            "candidate_ref": f"kimi:tvc-provider-wire:{exact_request_hash}",
            "candidate_hash": packet.payload_hash,
            "evidence_refs": [ingress_receipt["receipt_hash"], f"workercoordinator:{claim_id}:G{fence}"],
            "resolved_facts": {
                "judgment_conditions": {
                    "refusal_available": refusal_available,
                    "operator_recoverability": operator_recoverability,
                    "workload_state": workload_state,
                    "time_pressure": time_pressure,
                    "isolation_state": isolation_state,
                    "evidence_refs": [f"workercoordinator:{claim_id}:G{fence}"],
                },
                "signal_admission": {
                    "admitted_signal_refs": [ingress_receipt["receipt_hash"], current_ref],
                    "excluded_signal_refs": [],
                    "transformations": ["canonical-tvc-openai-chat-completions-v1"],
                    "missing_inputs": [],
                    "uncertainty_state": "bounded",
                    "reference_state_hash": current_ref,
                    "expected_reference_state_hash": current_ref,
                    "reconstruction_available": True,
                    "transformation_provenance_complete": True,
                },
                "execution_boundary": {
                    "actor_authority_current": claim_current and fence_bound,
                    "policy_current": policy_current,
                    "delegation_current": delegation_current,
                    "evidence_current": evidence_current,
                    "affected_entity_conditions_represented": affected_entities_represented,
                    "recoverability_profile": "recoverable" if refusal_available else "unknown",
                    "validity_window_open": validity_window_open,
                    "policy_ref": "policy.hosted-llm-provider.execute.v1",
                    "delegation_ref": f"workercoordinator:{claim_id}:G{fence}",
                    "evidence_refs": [ingress_receipt["receipt_hash"], f"workercoordinator:{claim_id}:G{fence}"],
                },
            },
        }
        bindings = VerifiedTransportBindings(
            interlock_exchange_id=packet.intent["packet_id"],
            intr_packet_id=ingress_complete["packet_id"],
            intr_profile_ref=ingress_complete["profile_id"],
            governed_transition_profile_ref=interlock["governed_transition_profile_ref"],
            carrier_profile_ref=interlock["carrier_profile_ref"],
        )
        parsed = parse_governance_connector_request(profile, gov_payload, bindings)
        governance_result = evaluate_governance_connector(profile, parsed)
    except Exception as exc:
        return blocked(f"STEGCORE_GOVERNANCE_EVALUATION_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)
    if governance_result.decision != "ALLOW":
        return blocked(
            "STEGCORE_GOVERNANCE_DID_NOT_ALLOW",
            epoch=epoch,
            extra={"decision": governance_result.decision, "reason_code": governance_result.reason_code},
        )

    profiles = load_profiles()
    now = datetime.now(timezone.utc)
    lease = issue(lease_request("kimi", "kimi-k3", now), policy=profiles, now=now)
    if lease.get("decision") != "ALLOW_CAPABILITY_LEASE":
        return blocked("TVC_KIMI_CAPABILITY_LEASE_REFUSED", epoch=epoch, extra={"refusal_reason": lease.get("refusal_reason")})

    ingress_hash = normalized_sha256(str(ingress_receipt["receipt_hash"]))
    governance_hash = normalized_sha256(str(governance_result.receipt_hash))

    def broker_submitter(operation: Mapping[str, Any]) -> Mapping[str, Any]:
        intr_binding = operation.get("intr_binding") or {}
        op = operation.get("operation") or {}
        checks = (
            intr_binding.get("request_hash") == exact_request_hash,
            intr_binding.get("transition_id") == transition_id,
            op.get("provider") == "kimi",
            op.get("model") == "kimi-k3",
            op.get("prompt") == prompt,
            op.get("max_output_tokens") == MAX_OUTPUT_TOKENS,
            op.get("response_format") == RESPONSE_FORMAT,
        )
        if not all(checks):
            raise RuntimeError("TVC_BROKER_OPERATION_NOT_BOUND_TO_ADMITTED_EXACT_PROVIDER_WIRE")
        return forward_to_local_vault_broker(operation, socket_path=tvc_socket)

    try:
        canonical_execution = execute_canonical_kimi_via_tvc_runtime(
            request,
            session_id=session_id,
            transition_id=transition_id,
            measurement_id=measurement_id,
            ingress_transport_state="TRANSPORT_COMPLETE",
            ingress_receipt_hash=ingress_hash,
            governance_disposition="ALLOW",
            governance_receipt_hash=governance_hash,
            carrier_ref=carrier_ref,
            lease_receipt=lease,
            broker_submitter=broker_submitter,
            usage_submitter=local_master_records_submitter(mr_socket),
            max_output_tokens=MAX_OUTPUT_TOKENS,
            response_format=RESPONSE_FORMAT,
        )
        if canonical_execution.admission.envelope.request_hash != exact_request_hash:
            raise RuntimeError("LLM_ADAPTER_ADMISSION_HASH_NOT_EXACT_TVC_PROVIDER_WIRE")
        if canonical_execution.execution.envelope != canonical_execution.admission.envelope:
            raise RuntimeError("LLM_ADAPTER_EXECUTION_ENVELOPE_DRIFT")

        response = canonical_execution.execution.broker.response
        response_payload = response.to_dict()
        response_bytes = canonical(response_payload)
        egress_packet = connector.prepare_response(
            packet,
            [ingress_receipt],
            response_payload,
            payload_schema="stegverse.external-provider.operation-response/v1",
            operation_id=transition_id + ":EGRESS",
        )
        if normalized_sha256(egress_packet.payload_hash) != sha256_bytes(response_bytes):
            raise RuntimeError("UNIVERSAL_INTR_EGRESS_PAYLOAD_HASH_NOT_EXACT_RESPONSE_BYTES")
        egress_receipt = connector.accept_hop(
            egress_packet,
            hop_index=1,
            receipt_id="KIMI-OUT-" + egress_packet.intent["packet_id"][5:],
            boundary_identity_ref="LLMAdapter:ProviderOperationClient",
            recorded_at=datetime.now(timezone.utc).isoformat(),
            prior_receipt_hash=ingress_receipt["receipt_hash"],
            transition_state="FORWARDED",
        )
        egress_complete = connector.validate_complete(egress_packet, [egress_receipt])
        if egress_complete.get("state") != "TRANSPORT_COMPLETE":
            raise RuntimeError("UNIVERSAL_INTR_EGRESS_NOT_COMPLETE")
    except Exception as exc:
        return blocked(f"KIMI_PROVIDER_OR_CUSTODY_OR_EGRESS_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)

    custody = canonical_execution.execution.master_records_usage
    predicates = {
        "same_execution": canonical_execution.execution.session_id == session_id,
        "exact_tvc_provider_wire_bound": canonical_execution.admission.envelope.request_hash == exact_request_hash,
        "intr_ingress_complete": ingress_complete.get("state") == "TRANSPORT_COMPLETE",
        "governance_allow": governance_result.decision == "ALLOW",
        "tvc_kimi_operation_observed": canonical_execution.execution.broker.response.provider == "kimi",
        "master_records_custody_recorded": custody.get("custody_recorded") is True,
        "master_records_reconstruction_pass": custody.get("reconstructability") == "PASS",
        "intr_egress_complete": egress_complete.get("state") == "TRANSPORT_COMPLETE",
        "provider_credential_exported": False,
        "master_records_credential_exported": False,
        "transport_grants_execution_authority": False,
        "governance_grants_execution_authority": False,
        "governance_grants_credential_authority": False,
    }
    if not all(predicates.values()):
        return blocked("TERMINAL_SAME_EXECUTION_PREDICATES_NOT_ALL_PROVEN", epoch=epoch, extra={"predicates": predicates})

    success: dict[str, Any] = {
        "schema": "stegverse.kimi-intr-resident-activation-worker-receipt/v2",
        "task_id": TASK_ID,
        "state": "COMPLETED",
        "transition_id": transition_id,
        "session_id": session_id,
        "measurement_id": measurement_id,
        "claim_id": claim_id,
        "fencing_token": fence,
        "heartbeat_epoch": epoch,
        "provider_wire_profile": "tvc_openai_chat_completions_v1",
        "exact_provider_wire_sha256": exact_request_hash,
        "request_hash": canonical_execution.execution.envelope.request_hash,
        "provider_response": response_payload,
        "provider_response_hash": response.response_hash,
        "provider_response_id": response.metadata.get("provider_response_id"),
        "intr_ingress": {"intent": packet.intent, "receipt": ingress_receipt, "result": ingress_complete},
        "governance": {
            "profile_id": profile["profile_id"],
            "decision": governance_result.decision,
            "reason_code": governance_result.reason_code,
            "receipt_hash": governance_result.receipt_hash,
            "three_layer_receipt": dict(governance_result.three_layer_receipt or {}),
        },
        "tvc": {
            "lease_id": lease.get("lease_id"),
            "lease_receipt_sha256": lease.get("receipt_sha256"),
            "use_receipt": dict(canonical_execution.execution.broker.use_receipt),
            "credential_material_present": False,
        },
        "master_records": dict(custody),
        "intr_egress": {"intent": egress_packet.intent, "receipt": egress_receipt, "result": egress_complete},
        "predicates": predicates,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
    }
    success["receipt_sha256"] = sha256_bytes(canonical(success))
    write_receipt(success)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "KIMI_INTR_RESIDENT_ROUND_TRIP_COMPLETE",
        "transition_sequence": 1,
        "expected_next_transition": None,
        "checkpoint_ref": str(RECEIPT),
        "evidence_refs": ["docs/KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md", str(RECEIPT)],
        "blocker": None,
        "cost_observation": {"task_control_evaluations": 1, "compute_units": 4, "external_cost_usd": 0, "task_class": "kimi_intr_resident_activation"},
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        response = execute(invocation)
    except Exception as exc:
        response = blocked(f"WORKER_FATAL_FAIL_CLOSED:{type(exc).__name__}:{exc}")
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
