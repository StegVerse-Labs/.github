#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "KIMI-INTR-RESIDENT-ACTIVATION-001"
CAPABILITY = "kimi_intr_resident_activation"
RECEIPT = Path("receipts/kimi-intr-resident-activation/KIMI-INTR-RESIDENT-ACTIVATION-001.json")
TVC_BROKER_DEFAULT = "/run/stegverse/vault-broker.sock"
MR_BROKER_DEFAULT = "/run/stegverse/master-records-provider-usage.sock"
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


def sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(raw).hexdigest()


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
    p = Path(path)
    try:
        return p.is_absolute() and p.exists() and stat.S_ISSOCK(p.stat().st_mode)
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
    matches = [p for p in profiles if isinstance(p, dict) and p.get("profile_id") == profile_id]
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
        payload = canonical(request) + b"\n"
        chunks: list[bytes] = []
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(30)
            client.connect(socket_path)
            client.sendall(payload)
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
        if (
            response.get("decision") != "ALLOW_CUSTODY_RESULT"
            or response.get("status") != "CUSTODY_RECORDED"
            or response.get("custody_recorded") is not True
            or response.get("reconstructability") != "PASS"
            or response.get("authority_granted") is not False
            or response.get("secret_material_returned") is not False
            or response.get("credential_material_returned") is not False
        ):
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
    receipt = {"schema":"stegverse.kimi-intr-resident-activation-worker-receipt/v1","task_id":TASK_ID,"state":"BLOCKED","result":result,"authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"}
    write_receipt(receipt)
    return {
        "schema":"stegverse.worker-response/v0.1",
        "state":"BLOCKED",
        "transition_id":"KIMI_INTR_RESIDENT_ACTIVATION_BLOCKED",
        "transition_sequence":1,
        "expected_next_transition":"KIMI_INTR_RESIDENT_ACTIVATION_RECHECK",
        "expected_next_earliest_epoch":None,
        "expected_next_latest_epoch":None,
        "recheck_policy":"SEPARATE_TASK_CONTROL_EVALUATION",
        "checkpoint_ref":str(RECEIPT),
        "evidence_refs":["docs/KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md",str(RECEIPT)],
        "blocker":{
            "dependency_class":"LOCAL_RUNTIME_OR_AUTHORITY_EVIDENCE",
            "problem_statement":reason,
            "solution_required":True,
            "may_remain_blocked":True,
            "next_solution_action":"RECHECK_EXISTING_LOCAL_SOURCE_AND_BROKER_PREDICATES",
            "machine_observable_release_condition":"one resident cycle completes InTr->Governance->TVC/Kimi->Master Records->InTr with exact retained evidence"
        },
        "cost_observation":{"task_control_evaluations":1,"compute_units":1,"external_cost_usd":0,"task_class":"kimi_intr_resident_activation"},
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
        return blocked("HOSTED_RUNTIME_PROHIBITED", epoch=epoch, extra={"hosted_markers":hosted})
    leaked = [name for name in FORBIDDEN_SECRET_ENV if os.environ.get(name)]
    if leaked:
        return blocked("CREDENTIAL_BEARING_WORKER_ENVIRONMENT_PROHIBITED", epoch=epoch, extra={"forbidden_environment":leaked})
    if os.environ.get("STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY") != "TV/TVC":
        return blocked("TV_TVC_CREDENTIAL_AUTHORITY_NOT_BOUND", epoch=epoch)

    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int) or fence < 1:
        return blocked("CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_REQUIRED", epoch=epoch)
    if scope.get("claim_id") != claim_id or scope.get("fencing_token") != fence or not claim_id.endswith(f"-G{fence}"):
        return blocked("WORKERCOORDINATOR_CLAIM_FENCE_BINDING_MISMATCH", epoch=epoch)

    try:
        llm = require_root("STEGVERSE_LLM_ADAPTER_ROOT", ("llm_adapter/kimi_canonical_runtime.py", "llm_adapter/kimi_intr_transport.py"))
        tvc = require_root("STEGVERSE_TVC_ROOT", ("scripts/tvc_run_provider_measurement.py", "scripts/tvc_issue_provider_measurement_lease.py", "tvc_provider_operation_broker.py"))
        stegos = require_root("STEGVERSE_STEGOS_ROOT", ("stegos/intr_backbone.py", "specs/universal-intr-connector-profiles.v1.json"))
        governance = require_root("STEGVERSE_GOVERNANCE_ROOT", ("specs/universal-governance-connector-profiles.v1.json",))
        stegcore = require_root("STEGVERSE_STEGCORE_SOURCE_ROOT", ("src/stegcore/universal_governance_connector.py", "src/stegcore/three_layer.py"))
        lanes = require_root("STEGVERSE_TEST_LANES_ROOT", ("experiments/sv-cost-program/nine-lane-results/task.json",))
        require_root("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", ("services/master_records_local_provider_usage_broker.py",))
    except Exception as exc:
        return blocked(str(exc), epoch=epoch)

    tvc_socket = os.environ.get("STEGVERSE_VAULT_BROKER_SOCKET", TVC_BROKER_DEFAULT)
    mr_socket = os.environ.get("STEGVERSE_MASTER_RECORDS_PROVIDER_USAGE_SOCKET", MR_BROKER_DEFAULT)
    if not socket_ready(tvc_socket):
        return blocked("TVC_VAULT_BROKER_SOCKET_NOT_READY", epoch=epoch, extra={"socket":tvc_socket})
    if not socket_ready(mr_socket):
        return blocked("MASTER_RECORDS_LOCAL_CUSTODY_SOCKET_NOT_READY", epoch=epoch, extra={"socket":mr_socket})

    for path in (str(llm), str(tvc), str(stegos), str(stegcore / "src")):
        if path not in sys.path:
            sys.path.insert(0, path)

    try:
        from llm_adapter.kimi_canonical_runtime import execute_canonical_kimi_via_tvc_runtime
        from llm_adapter.kimi_intr_transport import kimi_wire_bytes
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
    task_json = json.loads(task_bytes.decode("utf-8"))
    try:
        prompt = build_prompt(task_json)
    except Exception as exc:
        return blocked(f"SV_RECON_PROMPT_BINDING_FAILED:{exc}", epoch=epoch)

    request = build_provider_request(provider="kimi", model="kimi-k3", messages=[{"role":"user","content":prompt}])
    wire = kimi_wire_bytes(request)
    transition_id = f"KIMI-INTR-RESIDENT-ACTIVATION-001:HB{epoch}:G{fence}"
    session_id = transition_id
    measurement_id = transition_id + ":provider-usage"
    carrier_ref = f"workercoordinator:{claim_id}:HB{epoch}:G{fence}"

    try:
        connector = connector_from_registry(stegos / "specs/universal-intr-connector-profiles.v1.json", "external-provider-operation")
        packet = connector.prepare(wire, payload_schema="stegverse.external-provider.operation-request/v1", operation="REQUEST_PROVIDER_OPERATION", operation_id=transition_id + ":INGRESS")
        ingress_receipt = connector.accept_hop(packet, hop_index=1, receipt_id="KIMI-IN-" + packet.intent["packet_id"][5:], boundary_identity_ref="TVC:ProviderOperationBroker:STAGED", recorded_at=datetime.now(timezone.utc).isoformat(), prior_receipt_hash=None, transition_state="STAGED")
        ingress_complete = connector.validate_complete(packet, [ingress_receipt])
    except Exception as exc:
        return blocked(f"UNIVERSAL_INTR_INGRESS_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)

    gov_registry = read_json(governance / "specs/universal-governance-connector-profiles.v1.json")
    try:
        profile = find_profile(gov_registry, "hosted-llm-provider-operation.v1")
        if profile.get("interlock", {}).get("intr_profile_ref") != "external-provider-operation":
            raise RuntimeError("HOSTED_LLM_GOVERNANCE_INTR_PROFILE_DRIFT")
        current_ref = packet.payload_hash
        gov_payload = {
            "schema_version":"stegverse.governance-connector.request/v1",
            "profile_id":"hosted-llm-provider-operation.v1",
            "operation_id":"execute-provider-operation",
            "system_id":"external-provider.hosted-llm",
            "boundary_id":"interlock:hosted-llm-provider-operation",
            "authority_ref":f"workercoordinator:{claim_id}",
            "intent_ref":packet.intent["packet_id"],
            "candidate_ref":f"kimi:{request.request_hash}",
            "candidate_hash":packet.payload_hash,
            "evidence_refs":[ingress_receipt["receipt_hash"], f"workercoordinator:{claim_id}:G{fence}"],
            "resolved_facts":{
                "judgment_conditions":{
                    "refusal_available":True,
                    "operator_recoverability":"available",
                    "workload_state":"supported",
                    "time_pressure":"normal",
                    "isolation_state":"supported",
                    "evidence_refs":[f"workercoordinator:{claim_id}:G{fence}"]
                },
                "signal_admission":{
                    "admitted_signal_refs":[ingress_receipt["receipt_hash"], current_ref],
                    "excluded_signal_refs":[],
                    "transformations":["canonical-kimi-wire-bytes"],
                    "missing_inputs":[],
                    "uncertainty_state":"bounded",
                    "reference_state_hash":current_ref,
                    "expected_reference_state_hash":current_ref,
                    "reconstruction_available":True,
                    "transformation_provenance_complete":True
                },
                "execution_boundary":{
                    "actor_authority_current":scope.get("claim_id")==claim_id and scope.get("fencing_token")==fence,
                    "policy_current":True,
                    "delegation_current":claim_id.endswith(f"-G{fence}"),
                    "evidence_current":ingress_complete.get("state")=="TRANSPORT_COMPLETE",
                    "affected_entity_conditions_represented":profile.get("system",{}).get("system_id")=="external-provider.hosted-llm",
                    "recoverability_profile":"recoverable",
                    "validity_window_open":True,
                    "policy_ref":"policy.hosted-llm-provider.execute.v1",
                    "delegation_ref":f"workercoordinator:{claim_id}:G{fence}",
                    "evidence_refs":[ingress_receipt["receipt_hash"], f"workercoordinator:{claim_id}:G{fence}"]
                }
            }
        }
        bindings = VerifiedTransportBindings(
            interlock_exchange_id=packet.intent["packet_id"],
            intr_packet_id=ingress_complete["packet_id"],
            intr_profile_ref=ingress_complete["profile_id"],
            governed_transition_profile_ref=profile["interlock"]["governed_transition_profile_ref"],
            carrier_profile_ref=profile["interlock"]["carrier_profile_ref"],
        )
        parsed = parse_governance_connector_request(profile, gov_payload, bindings)
        governance_result = evaluate_governance_connector(profile, parsed)
    except Exception as exc:
        return blocked(f"STEGCORE_GOVERNANCE_EVALUATION_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)
    if governance_result.decision != "ALLOW":
        return blocked("STEGCORE_GOVERNANCE_DID_NOT_ALLOW", epoch=epoch, extra={"decision":governance_result.decision,"reason_code":governance_result.reason_code})

    profiles = load_profiles()
    now = datetime.now(timezone.utc)
    lease = issue(lease_request("kimi", "kimi-k3", now), policy=profiles, now=now)
    if lease.get("decision") != "ALLOW_CAPABILITY_LEASE":
        return blocked("TVC_KIMI_CAPABILITY_LEASE_REFUSED", epoch=epoch, extra={"refusal_reason":lease.get("refusal_reason")})

    ingress_hash = str(ingress_receipt["receipt_hash"])
    if ingress_hash.startswith("sha256:"):
        ingress_hash = ingress_hash[7:]
    governance_hash = str(governance_result.receipt_hash)

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
            broker_submitter=lambda operation: forward_to_local_vault_broker(operation, socket_path=tvc_socket),
            usage_submitter=local_master_records_submitter(mr_socket),
            max_output_tokens=4096,
            response_format="json",
        )
        response = canonical_execution.execution.broker.response
        response_payload = response.to_dict()
        egress_packet = connector.prepare_response(packet, [ingress_receipt], response_payload, payload_schema="stegverse.external-provider.operation-response/v1", operation_id=transition_id + ":EGRESS")
        egress_receipt = connector.accept_hop(egress_packet, hop_index=1, receipt_id="KIMI-OUT-" + egress_packet.intent["packet_id"][5:], boundary_identity_ref="LLMAdapter:ProviderOperationClient", recorded_at=datetime.now(timezone.utc).isoformat(), prior_receipt_hash=ingress_receipt["receipt_hash"], transition_state="FORWARDED")
        egress_complete = connector.validate_complete(egress_packet, [egress_receipt])
    except Exception as exc:
        return blocked(f"KIMI_PROVIDER_OR_CUSTODY_OR_EGRESS_FAILED:{type(exc).__name__}:{exc}", epoch=epoch)

    success = {
        "schema":"stegverse.kimi-intr-resident-activation-worker-receipt/v1",
        "task_id":TASK_ID,
        "state":"COMPLETED",
        "transition_id":transition_id,
        "session_id":session_id,
        "measurement_id":measurement_id,
        "claim_id":claim_id,
        "fencing_token":fence,
        "heartbeat_epoch":epoch,
        "request_hash":canonical_execution.execution.envelope.request_hash,
        "provider_response":response_payload,
        "provider_response_hash":response.response_hash,
        "provider_response_id":response.metadata.get("provider_response_id"),
        "intr_ingress":{"intent":packet.intent,"receipt":ingress_receipt,"result":ingress_complete},
        "governance":{"profile_id":profile["profile_id"],"decision":governance_result.decision,"reason_code":governance_result.reason_code,"receipt_hash":governance_result.receipt_hash,"three_layer_receipt":dict(governance_result.three_layer_receipt or {})},
        "tvc":{"lease_id":lease.get("lease_id"),"lease_receipt_sha256":lease.get("receipt_sha256"),"use_receipt":dict(canonical_execution.execution.broker.use_receipt),"credential_material_present":False},
        "master_records":dict(canonical_execution.execution.master_records_usage),
        "intr_egress":{"intent":egress_packet.intent,"receipt":egress_receipt,"result":egress_complete},
        "predicates":{
            "same_execution":True,
            "intr_ingress_complete":True,
            "governance_allow":True,
            "tvc_kimi_operation_observed":True,
            "master_records_custody_recorded":True,
            "master_records_reconstruction_pass":True,
            "intr_egress_complete":True,
            "provider_credential_exported":False,
            "master_records_credential_exported":False,
            "transport_grants_execution_authority":False,
            "governance_grants_execution_authority":False,
            "governance_grants_credential_authority":False
        },
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "authority_effect":"EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"
    }
    success["receipt_sha256"] = sha256(success)
    write_receipt(success)
    return {
        "schema":"stegverse.worker-response/v0.1",
        "state":"COMPLETED",
        "transition_id":"KIMI_INTR_RESIDENT_ROUND_TRIP_COMPLETE",
        "transition_sequence":1,
        "expected_next_transition":None,
        "checkpoint_ref":str(RECEIPT),
        "evidence_refs":["docs/KIMI_INTR_RESIDENT_ACTIVATION_MIRROR_HANDOFF.md",str(RECEIPT)],
        "blocker":None,
        "cost_observation":{"task_control_evaluations":1,"compute_units":4,"external_cost_usd":0,"task_class":"kimi_intr_resident_activation"},
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
