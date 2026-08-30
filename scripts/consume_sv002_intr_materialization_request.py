#!/usr/bin/env python3
"""Consume node-triggered Universal InTr materialization for SV002 observation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_RECEIPT_DIR_REL = Path("receipts/sovereign-network/sv002-intr-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/sv002-intr-materialization")
LATEST_REL = Path("receipts/sovereign-host/sv002-intr-materialization-consumption.latest.json")
TARGET_TASK = "SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "SV002:PublicObservation"}
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#462"
Runner = Callable[..., subprocess.CompletedProcess[Any]]
RuntimeMaterializer = Callable[..., dict[str, Any]]

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN",
)

class SV002InTrMaterializationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _sha256_uri(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise SV002InTrMaterializationError(f"{label}_invalid")
    if any(ch not in "0123456789abcdef" for ch in value[7:]):
        raise SV002InTrMaterializationError(f"{label}_invalid")
    return value


def validate_request(request: Mapping[str, Any]) -> None:
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
            raise SV002InTrMaterializationError(f"sv002_materialization_{key}_mismatch")
    materialization_id = request.get("materialization_id")
    if not isinstance(materialization_id, str) or not materialization_id.startswith("INTR-MAT-") or len(materialization_id) != 33:
        raise SV002InTrMaterializationError("sv002_materialization_id_invalid")
    if any(ch not in "0123456789abcdef" for ch in materialization_id[9:]):
        raise SV002InTrMaterializationError("sv002_materialization_id_invalid")
    for field in ("operation_id", "packet_id", "payload_ref"):
        if not isinstance(request.get(field), str) or not str(request[field]).strip():
            raise SV002InTrMaterializationError(f"sv002_materialization_{field}_required")
    _sha256_uri(request.get("transport_intent_hash"), "transport_intent_hash")
    _sha256_uri(request.get("payload_hash"), "payload_hash")
    _sha256_uri(request.get("request_hash"), "request_hash")
    if request.get("boundary_path") != ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]:
        raise SV002InTrMaterializationError("sv002_materialization_boundary_path_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    if claimed != digest_uri(body):
        raise SV002InTrMaterializationError("sv002_materialization_request_hash_mismatch")


def scrubbed_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    if any(str(values.get(name, "")).strip().lower() not in {"", "0", "false", "no"} for name in HOSTED_ENV):
        raise SV002InTrMaterializationError("hosted_environment_cannot_execute_sv002_materialization")
    for name in CREDENTIAL_ENV:
        if str(values.get(name, "")).strip():
            raise SV002InTrMaterializationError(f"credential_environment_forbidden:{name}")
    keep = {
        "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
        "STEGVERSE_STEGOS_ROOT", "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
        "STEGVERSE_SELF_CHAR_STATE_ROOT", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG", "STEGVERSE_SV002_OBSERVE_PORT",
        "STEGVERSE_SOVEREIGN_NODE", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    }
    child = {key: values[key] for key in keep if values.get(key)}
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SV002InTrMaterializationError(f"object_required:{path}")
    return value


def _receipt_path(runtime: Path, materialization_id: str) -> Path:
    return runtime / RECEIPT_DIR_REL / f"{materialization_id}.json"


def _ingress_receipt(runtime: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    path = runtime / INGRESS_RECEIPT_DIR_REL / f"{request['materialization_id']}.json"
    if not path.is_file():
        raise SV002InTrMaterializationError(f"sv002_ingress_receipt_missing:{path}")
    receipt = _load(path)
    if receipt.get("schema") != "stegverse.sv002-intr-materialization-ingress/v1" or receipt.get("state") != "INGRESS_ADMITTED":
        raise SV002InTrMaterializationError("sv002_ingress_receipt_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        if receipt.get(key) != request.get(key):
            raise SV002InTrMaterializationError(f"sv002_ingress_receipt_binding_mismatch:{key}")
    if receipt.get("credential_authority") != "TV/TVC" or receipt.get("claim_or_fence_minted") is not False:
        raise SV002InTrMaterializationError("sv002_ingress_authority_boundary_invalid")
    return receipt


def _default_materializer(*, source: Path, intake_runtime: Path, request: Mapping[str, Any], ingress_receipt: Mapping[str, Any], env: Mapping[str, str] | None) -> dict[str, Any]:
    from workers.sv002_observation_esrl_runtime_bridge import materialize_sv002_observation_runtime
    return materialize_sv002_observation_runtime(control_root=source, intake_runtime_root=intake_runtime, request=request, ingress_receipt=ingress_receipt, env=env)


def _prior_success(runtime: Path, request: Mapping[str, Any]) -> bool:
    path = _receipt_path(runtime, str(request["materialization_id"]))
    if not path.is_file():
        return False
    try:
        receipt = _load(path)
    except Exception:
        return False
    return (
        receipt.get("request_hash") == request.get("request_hash")
        and receipt.get("runtime_execution_attempted") is True
        and receipt.get("targeted_executor_returncode") == 0
        and receipt.get("state") == "MATERIALIZATION_EXECUTION_ATTEMPTED"
    )


def _attempt(*, source: Path, runtime: Path, request: dict[str, Any], runner: Runner, env: Mapping[str, str] | None, runtime_materializer: RuntimeMaterializer) -> dict[str, Any]:
    validate_request(request)
    if _prior_success(runtime, request):
        return {
            "schema": "stegverse.sv002-intr-materialization-consumption/v1",
            "state": "ALREADY_CONSUMED_SUCCESS",
            "materialization_id": request["materialization_id"],
            "request_hash": request["request_hash"],
            "runtime_execution_attempted": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }
    ingress = _ingress_receipt(runtime, request)
    safe = scrubbed_env(env)
    materialized = runtime_materializer(source=source, intake_runtime=runtime, request=request, ingress_receipt=ingress, env=safe)
    execution_runtime = Path(str(materialized.get("runtime_root", ""))).resolve()
    evidence = materialized.get("evidence")
    if not execution_runtime.is_dir() or not isinstance(evidence, dict):
        raise SV002InTrMaterializationError("sv002_esrl_runtime_materialization_invalid")
    if evidence.get("state") != "LOCAL_READY" or evidence.get("runtime_instantiated") is not True or evidence.get("local_identity_verified") is not True:
        raise SV002InTrMaterializationError("sv002_esrl_runtime_not_local_ready")
    if evidence.get("g18_completion_required") is not False or evidence.get("observer_direct_relation_to_stegverse_002") is not False:
        raise SV002InTrMaterializationError("sv002_esrl_semantic_boundary_invalid")
    entrypoint = execution_runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise SV002InTrMaterializationError(f"sv002_targeted_executor_missing:{entrypoint}")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(execution_runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=execution_runtime, env=safe, check=False, capture_output=True, text=True, timeout=180)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema": "stegverse.sv002-intr-materialization-consumption/v1",
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "payload_hash": request["payload_hash"],
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
        "source_ingress_receipt_id": evidence.get("source_receipt_id"),
        "esrl_lease_id": evidence.get("lease_id"),
        "esrl_lease_state": evidence.get("lease_state"),
        "esrl_runtime_root": str(execution_runtime),
        "esrl_runtime_instantiated": True,
        "esrl_local_identity_verified": True,
        "target_task_id": TARGET_TASK,
        "targeted_executor": TARGET_ENTRYPOINT,
        "targeted_executor_returncode": completed.returncode,
        "runtime_execution_attempted": True,
        "receiver_ready_is_precondition": False,
        "g18_completion_required": False,
        "observer_direct_relation_to_stegverse_002": False,
        "request_grants_authority": False,
        "claim_or_fence_minted_by_consumer": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_REQUEST_ONLY",
        "consumed_at": now,
    }
    path = _receipt_path(runtime, str(request["materialization_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def consume_all(source_root: Path, runtime_root: Path, *, runner: Runner = subprocess.run, env: Mapping[str, str] | None = None, runtime_materializer: RuntimeMaterializer | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_dir = runtime / REQUEST_DIR_REL
    request_dir.mkdir(parents=True, exist_ok=True)
    materializer = _default_materializer if runtime_materializer is None else runtime_materializer
    results: list[dict[str, Any]] = []
    for path in sorted(request_dir.glob("*.json")):
        try:
            request = _load(path)
            if request.get("destination") != DESTINATION or request.get("downstream_owner_ref") != DOWNSTREAM_OWNER:
                continue
            result = _attempt(source=source, runtime=runtime, request=request, runner=runner, env=env, runtime_materializer=materializer)
        except Exception as exc:
            result = {
                "schema": "stegverse.sv002-intr-materialization-consumption/v1",
                "state": "REQUEST_REJECTED",
                "request_ref": str(path),
                "reason": str(exc),
                "runtime_execution_attempted": False,
                "authority_effect": "NONE_REQUEST_ONLY",
            }
        results.append(result)
    attempted = [row for row in results if row.get("runtime_execution_attempted") is True]
    blocked = [row for row in attempted if row.get("targeted_executor_returncode") != 0]
    batch = {
        "schema": "stegverse.sv002-intr-materialization-consumption-batch/v1",
        "state": "NO_SV002_MATERIALIZATION_REQUEST" if not results else ("BLOCKED" if blocked else "PROCESSED"),
        "request_count": len(results),
        "runtime_execution_attempt_count": len(attempted),
        "blocked_attempt_count": len(blocked),
        "results": results,
        "target_task_id": TARGET_TASK,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "receiver_ready_is_precondition": False,
        "g18_completion_required": False,
        "second_user_device_required": False,
        "request_dispatch_grants_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_DISPATCH_ONLY",
    }
    latest = runtime / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume SV002 Universal InTr materialization requests.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume_all(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
