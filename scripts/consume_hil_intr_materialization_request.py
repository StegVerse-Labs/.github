#!/usr/bin/env python3
"""Consume HIL-destined Universal InTr materialization requests.

An admitted materialization request is non-authorizing. The consumer first binds
it to the authentic HIL InTr ingress receipt, materializes an event-ephemeral
sovereign runtime through the existing StegOS ESRL adapter, and only then invokes
the already-admitted HIL targeted executor. WorkerCoordinator remains the sole
claim/fence authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_RECEIPT_DIR_REL = Path("receipts/sovereign-network/hil-intr-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/hil-intr-materialization")
LATEST_REL = Path("receipts/sovereign-host/hil-intr-materialization-consumption.latest.json")
TARGET_TASK = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "HIL:Ingress"}
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#246"
Runner = Callable[..., subprocess.CompletedProcess[Any]]
RuntimeMaterializer = Callable[..., dict[str, Any]]

HOSTED_ENV = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
CREDENTIAL_ENV = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "STEGVERSE_GITHUB_TOKEN",
    "TVC_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)


class HILInTrMaterializationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _sha256_uri(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise HILInTrMaterializationError(f"{label}_invalid")
    if any(ch not in "0123456789abcdef" for ch in value[7:]):
        raise HILInTrMaterializationError(f"{label}_invalid")
    return value


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "destination": DESTINATION,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise HILInTrMaterializationError(f"materialization_{key}_mismatch")
    materialization_id = request.get("materialization_id")
    if not isinstance(materialization_id, str) or not materialization_id.startswith("INTR-MAT-") or len(materialization_id) != len("INTR-MAT-") + 24:
        raise HILInTrMaterializationError("materialization_id_invalid")
    if any(ch not in "0123456789abcdef" for ch in materialization_id[len("INTR-MAT-"):]):
        raise HILInTrMaterializationError("materialization_id_invalid")
    for field in ("operation_id", "packet_id", "payload_ref"):
        if not isinstance(request.get(field), str) or not request[field].strip():
            raise HILInTrMaterializationError(f"materialization_{field}_required")
    _sha256_uri(request.get("transport_intent_hash"), "transport_intent_hash")
    _sha256_uri(request.get("payload_hash"), "payload_hash")
    _sha256_uri(request.get("request_hash"), "request_hash")
    if request.get("boundary_path") != ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]:
        raise HILInTrMaterializationError("materialization_boundary_path_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    if claimed != digest_uri(body):
        raise HILInTrMaterializationError("materialization_request_hash_mismatch")


def scrubbed_env(env: dict[str, str] | None = None) -> dict[str, str]:
    child = dict(os.environ if env is None else env)
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HILInTrMaterializationError(f"object_required:{path}")
    return value


def _receipt_path(runtime: Path, materialization_id: str) -> Path:
    return runtime / RECEIPT_DIR_REL / f"{materialization_id}.json"


def _ingress_receipt(runtime: Path, request: dict[str, Any]) -> dict[str, Any]:
    path = runtime / INGRESS_RECEIPT_DIR_REL / f"{request['materialization_id']}.json"
    if not path.is_file():
        raise HILInTrMaterializationError(f"ingress_receipt_missing:{path}")
    receipt = _load(path)
    if receipt.get("schema") != "stegverse.hil-intr-materialization-ingress/v1" or receipt.get("state") != "INGRESS_ADMITTED":
        raise HILInTrMaterializationError("ingress_receipt_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        if receipt.get(key) != request.get(key):
            raise HILInTrMaterializationError(f"ingress_receipt_binding_mismatch:{key}")
    if receipt.get("credential_authority") != "TV/TVC" or receipt.get("claim_or_fence_minted") is not False:
        raise HILInTrMaterializationError("ingress_receipt_authority_boundary_invalid")
    return receipt


def _default_runtime_materializer(*, source: Path, intake_runtime: Path, request: dict[str, Any], ingress_receipt: dict[str, Any], env: dict[str, str] | None) -> dict[str, Any]:
    from workers.hil_esrl_runtime_bridge import materialize_hil_runtime
    return materialize_hil_runtime(control_root=source, intake_runtime_root=intake_runtime, request=request, ingress_receipt=ingress_receipt, env=scrubbed_env(env))


def _prior_success(runtime: Path, request: dict[str, Any]) -> bool:
    path = _receipt_path(runtime, request["materialization_id"])
    if not path.is_file():
        return False
    try:
        receipt = _load(path)
    except Exception:
        return False
    return receipt.get("request_hash") == request.get("request_hash") and receipt.get("runtime_execution_attempted") is True and receipt.get("targeted_executor_returncode") == 0 and receipt.get("state") == "MATERIALIZATION_EXECUTION_ATTEMPTED"


def _attempt(*, source: Path, runtime: Path, request: dict[str, Any], runner: Runner, env: dict[str, str] | None, runtime_materializer: RuntimeMaterializer) -> dict[str, Any]:
    validate_request(request)
    if _prior_success(runtime, request):
        return {"schema": "stegverse.hil-intr-materialization-consumption/v1", "state": "ALREADY_CONSUMED_SUCCESS", "materialization_id": request["materialization_id"], "request_hash": request["request_hash"], "runtime_execution_attempted": False, "request_grants_authority": False, "authority_effect": "NONE_REQUEST_ONLY"}

    ingress = _ingress_receipt(runtime, request)
    materialized = runtime_materializer(source=source, intake_runtime=runtime, request=request, ingress_receipt=ingress, env=env)
    execution_runtime = Path(str(materialized.get("runtime_root", ""))).resolve()
    evidence = materialized.get("evidence")
    if not execution_runtime.is_dir() or not isinstance(evidence, dict):
        raise HILInTrMaterializationError("esrl_runtime_materialization_invalid")
    if evidence.get("state") != "LEASE_OPEN" or evidence.get("lease_state") != "LEASE_OPEN":
        raise HILInTrMaterializationError("esrl_lease_not_open")
    if evidence.get("runtime_instantiated") is not True or evidence.get("local_identity_verified") is not True:
        raise HILInTrMaterializationError("esrl_runtime_not_verified")
    if evidence.get("same_device_execution_required") is not True or evidence.get("requires_other_machine") is not False:
        raise HILInTrMaterializationError("esrl_same_device_invariant_not_proven")
    if evidence.get("hil_public_https_rendezvous_observed") is not False or evidence.get("public_gateway_readiness_verified") is not False:
        raise HILInTrMaterializationError("esrl_public_gateway_must_not_be_activation_prerequisite")

    entrypoint = execution_runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise HILInTrMaterializationError(f"targeted_executor_missing:{entrypoint}")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(execution_runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=execution_runtime, env=scrubbed_env(env), check=False, capture_output=True, text=True, timeout=180)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema": "stegverse.hil-intr-materialization-consumption/v1",
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "materialization_id": request["materialization_id"], "request_hash": request["request_hash"], "transport_intent_hash": request["transport_intent_hash"],
        "operation_id": request["operation_id"], "packet_id": request["packet_id"], "payload_hash": request["payload_hash"], "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"], "source_ingress_receipt_id": evidence.get("source_receipt_id"),
        "esrl_lease_id": evidence.get("lease_id"), "esrl_lease_state": evidence.get("lease_state"), "esrl_runtime_root": str(execution_runtime),
        "esrl_runtime_instantiated": True, "esrl_local_identity_verified": True,
        "hil_public_https_rendezvous_observed": evidence.get("hil_public_https_rendezvous_observed") is True,
        "public_gateway_readiness_verified": evidence.get("public_gateway_readiness_verified") is True,
        "public_gateway_origin": evidence.get("public_gateway_origin"),
        "public_observation_is_downstream_optional": evidence.get("public_observation_is_downstream_optional") is True,
        "same_device_execution_required": evidence.get("same_device_execution_required") is True,
        "requires_other_machine": evidence.get("requires_other_machine") is True,
        "target_task_id": TARGET_TASK, "targeted_executor": TARGET_ENTRYPOINT, "targeted_executor_returncode": completed.returncode,
        "runtime_execution_attempted": True, "successful_attempt_is_not_blindly_retried": True, "blocked_attempt_remains_nonterminal": completed.returncode != 0,
        "request_grants_authority": False, "claim_or_fence_minted_by_consumer": False, "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE", "credential_authority": "TV/TVC", "authority_effect": "NONE_REQUEST_ONLY", "consumed_at": now,
    }
    path = _receipt_path(runtime, request["materialization_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def consume_all(source_root: Path, runtime_root: Path, *, runner: Runner = subprocess.run, env: dict[str, str] | None = None, runtime_materializer: RuntimeMaterializer | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_dir = runtime / REQUEST_DIR_REL
    request_dir.mkdir(parents=True, exist_ok=True)
    materializer = _default_runtime_materializer if runtime_materializer is None else runtime_materializer
    results: list[dict[str, Any]] = []
    for path in sorted(request_dir.glob("*.json")):
        try:
            request = _load(path)
            if request.get("destination") != DESTINATION:
                continue
            result = _attempt(source=source, runtime=runtime, request=request, runner=runner, env=env, runtime_materializer=materializer)
        except Exception as exc:
            result = {"schema": "stegverse.hil-intr-materialization-consumption/v1", "state": "REQUEST_REJECTED", "request_ref": str(path), "reason": str(exc), "runtime_execution_attempted": False, "request_grants_authority": False, "authority_effect": "NONE_REQUEST_ONLY"}
        results.append(result)
    attempted = [r for r in results if r.get("runtime_execution_attempted") is True]
    blocked = [r for r in attempted if r.get("targeted_executor_returncode") != 0]
    batch = {
        "schema": "stegverse.hil-intr-materialization-consumption-batch/v1",
        "state": "NO_HIL_MATERIALIZATION_REQUEST" if not results else ("BLOCKED" if blocked else "PROCESSED"),
        "request_count": len(results), "runtime_execution_attempt_count": len(attempted), "blocked_attempt_count": len(blocked), "results": results,
        "target_task_id": TARGET_TASK, "event_triggered": True, "always_on_receiver_required": False, "g18_completion_required": False, "g18_claim_or_fence_consumed": False,
        "request_dispatch_grants_authority": False, "heartbeat_grants_execution_authority": False, "github_token_runtime_authority": "NONE", "credential_authority": "TV/TVC", "authority_effect": "NONE_DISPATCH_ONLY",
    }
    latest = runtime / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume HIL Universal InTr materialization requests.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume_all(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
