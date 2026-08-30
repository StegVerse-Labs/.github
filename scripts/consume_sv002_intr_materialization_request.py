#!/usr/bin/env python3
"""Consume SV002 public-observation Universal InTr materialization requests.

A materialization request is queue intent only. It does not grant task authority.
The consumer binds the request to its admitted sovereign ingress receipt, attempts
non-secret route materialization from already-local roots, then invokes the
already-admitted independent task-control executor. Receiver readiness is a
downstream observation, never a prerequisite for accepting the request.
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
REQUEST_DIR_REL = Path("sv002-intr-materialization")
INGRESS_RECEIPT_DIR_REL = Path("receipts/sovereign-network/sv002-intr-materialization-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/sv002-intr-materialization")
LATEST_REL = Path("receipts/sovereign-host/sv002-intr-materialization-consumption.latest.json")
TARGET_TASK = "SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
ROUTE_MATERIALIZER = "scripts/materialize_sv002_observation_route_config.py"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "SV002:PublicObservation"}
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#493"
Runner = Callable[..., subprocess.CompletedProcess[Any]]

HOSTED_ENV = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME",
    "LOCALAPPDATA", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_STEGOS_ROOT", "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
    "STEGVERSE_SV002_OBSERVE_PORT",
}


class SV002InTrMaterializationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _sha256_uri(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise SV002InTrMaterializationError(f"{label}_invalid")
    if any(ch not in "0123456789abcdef" for ch in value[7:]):
        raise SV002InTrMaterializationError(f"{label}_invalid")
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
            raise SV002InTrMaterializationError(f"materialization_{key}_mismatch")
    materialization_id = request.get("materialization_id")
    if (
        not isinstance(materialization_id, str)
        or not materialization_id.startswith("INTR-MAT-")
        or len(materialization_id) != len("INTR-MAT-") + 24
        or any(ch not in "0123456789abcdef" for ch in materialization_id[len("INTR-MAT-"):])
    ):
        raise SV002InTrMaterializationError("materialization_id_invalid")
    for field in ("operation_id", "packet_id", "payload_ref"):
        if not isinstance(request.get(field), str) or not request[field].strip():
            raise SV002InTrMaterializationError(f"materialization_{field}_required")
    _sha256_uri(request.get("transport_intent_hash"), "transport_intent_hash")
    _sha256_uri(request.get("payload_hash"), "payload_hash")
    _sha256_uri(request.get("request_hash"), "request_hash")
    if request.get("boundary_path") != ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]:
        raise SV002InTrMaterializationError("materialization_boundary_path_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    if claimed != digest_uri(body):
        raise SV002InTrMaterializationError("materialization_request_hash_mismatch")


def scrubbed_env(env: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    child = {key: values[key] for key in NONSECRET_ENV if values.get(key)}
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        child.pop(key, None)
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


def _ingress_receipt(runtime: Path, request: dict[str, Any]) -> dict[str, Any]:
    path = runtime / INGRESS_RECEIPT_DIR_REL / f"{request['materialization_id']}.json"
    if not path.is_file():
        raise SV002InTrMaterializationError(f"ingress_receipt_missing:{path}")
    receipt = _load(path)
    if (
        receipt.get("schema") != "stegverse.sv002-intr-materialization-ingress/v1"
        or receipt.get("state") != "INGRESS_ADMITTED"
    ):
        raise SV002InTrMaterializationError("ingress_receipt_not_admitted")
    for key in (
        "materialization_id", "request_hash", "transport_intent_hash",
        "payload_hash", "operation_id", "packet_id",
    ):
        if receipt.get(key) != request.get(key):
            raise SV002InTrMaterializationError(f"ingress_receipt_binding_mismatch:{key}")
    if (
        receipt.get("credential_authority") != "TV/TVC"
        or receipt.get("github_token_runtime_authority") != "NONE"
        or receipt.get("claim_or_fence_minted") is not False
        or receipt.get("g18_required") is not False
    ):
        raise SV002InTrMaterializationError("ingress_receipt_authority_boundary_invalid")
    return receipt


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _prior_success(runtime: Path, request: dict[str, Any]) -> bool:
    path = _receipt_path(runtime, request["materialization_id"])
    if not path.is_file():
        return False
    try:
        receipt = _load(path)
    except Exception:
        return False
    return bool(
        receipt.get("request_hash") == request.get("request_hash")
        and receipt.get("state") == "MATERIALIZATION_READY_OBSERVED"
        and receipt.get("runtime_execution_attempted") is True
        and receipt.get("receiver_ready_observed") is True
    )


def _attempt(
    *,
    source: Path,
    runtime: Path,
    request: dict[str, Any],
    runner: Runner,
    env: dict[str, str] | None,
) -> dict[str, Any]:
    validate_request(request)
    if _prior_success(runtime, request):
        return {
            "schema": "stegverse.sv002-intr-materialization-consumption/v1",
            "state": "ALREADY_CONSUMED_SUCCESS",
            "materialization_id": request["materialization_id"],
            "request_hash": request["request_hash"],
            "runtime_execution_attempted": False,
            "receiver_ready_observed": True,
            "g18_required": False,
            "request_grants_authority": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }

    ingress = _ingress_receipt(runtime, request)
    safe = scrubbed_env(env)
    materializer = runtime / ROUTE_MATERIALIZER
    if not materializer.is_file():
        raise SV002InTrMaterializationError(f"route_materializer_missing:{materializer}")

    materialized = runner(
        [sys.executable, str(materializer)],
        cwd=runtime,
        env=safe,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    route_result = parse_last_json(materialized.stdout)
    if not isinstance(route_result, dict):
        raise SV002InTrMaterializationError("route_materializer_returned_no_machine_result")

    receiver_ready = False
    round_trip = False
    execution_result: dict[str, Any] | None = None
    returncode: int | None = None

    if route_result.get("state") != "PREDICATE_PENDING":
        entrypoint = runtime / TARGET_ENTRYPOINT
        if not entrypoint.is_file():
            raise SV002InTrMaterializationError(f"targeted_executor_missing:{entrypoint}")
        command = [
            sys.executable, str(entrypoint), "--source-root", str(source),
            "--runtime-root", str(runtime), "--task-id", TARGET_TASK,
        ]
        completed = runner(
            command, cwd=runtime, env=safe, check=False,
            capture_output=True, text=True, timeout=180,
        )
        returncode = completed.returncode
        execution_result = parse_last_json(completed.stdout)
        transition = (
            execution_result.get("transition_id")
            if isinstance(execution_result, dict)
            else None
        )
        nested = (
            execution_result.get("execution_result")
            if isinstance(execution_result, dict)
            and isinstance(execution_result.get("execution_result"), dict)
            else {}
        )
        nested_transition = nested.get("transition_id")
        receiver_ready = transition == "SV002_PUBLIC_OBSERVATION_RECEIVER_READY" or nested_transition == "SV002_PUBLIC_OBSERVATION_RECEIVER_READY"
        round_trip = transition == "SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED" or nested_transition == "SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED"
        receiver_ready = receiver_ready or round_trip

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    state = "MATERIALIZATION_READY_OBSERVED" if receiver_ready else "MATERIALIZATION_NONTERMINAL"
    receipt = {
        "schema": "stegverse.sv002-intr-materialization-consumption/v1",
        "state": state,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "payload_hash": request["payload_hash"],
        "destination": request["destination"],
        "downstream_owner_ref": request["downstream_owner_ref"],
        "ingress_receipt_ref": str(runtime / INGRESS_RECEIPT_DIR_REL / f"{request['materialization_id']}.json"),
        "route_materialization": route_result,
        "target_task_id": TARGET_TASK,
        "targeted_executor": TARGET_ENTRYPOINT,
        "targeted_executor_returncode": returncode,
        "execution_result": execution_result,
        "runtime_execution_attempted": execution_result is not None,
        "receiver_ready_observed": receiver_ready,
        "round_trip_observed": round_trip,
        "blocked_attempt_remains_nonterminal": not receiver_ready,
        "successful_materialization_is_not_blindly_retried": True,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "g18_required": False,
        "g18_claim_or_fence_consumed": False,
        "request_grants_authority": False,
        "claim_or_fence_minted_by_consumer": False,
        "heartbeat_grants_execution_authority": False,
        "second_user_device_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_REQUEST_ONLY",
        "consumed_at": now,
    }
    path = _receipt_path(runtime, request["materialization_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def consume_all(
    source_root: Path,
    runtime_root: Path,
    *,
    runner: Runner = subprocess.run,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_dir = runtime / REQUEST_DIR_REL
    request_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for path in sorted(request_dir.glob("*.json")):
        try:
            request = _load(path)
            if request.get("destination") != DESTINATION:
                continue
            result = _attempt(
                source=source, runtime=runtime, request=request,
                runner=runner, env=env,
            )
        except Exception as exc:
            result = {
                "schema": "stegverse.sv002-intr-materialization-consumption/v1",
                "state": "REQUEST_REJECTED",
                "request_ref": str(path),
                "reason": str(exc),
                "runtime_execution_attempted": False,
                "receiver_ready_observed": False,
                "g18_required": False,
                "request_grants_authority": False,
                "authority_effect": "NONE_REQUEST_ONLY",
            }
        results.append(result)

    ready = [r for r in results if r.get("receiver_ready_observed") is True]
    attempted = [r for r in results if r.get("runtime_execution_attempted") is True]
    batch = {
        "schema": "stegverse.sv002-intr-materialization-consumption-batch/v1",
        "state": "NO_SV002_MATERIALIZATION_REQUEST" if not results else ("READY_OBSERVED" if ready else "NONTERMINAL"),
        "request_count": len(results),
        "runtime_execution_attempt_count": len(attempted),
        "receiver_ready_count": len(ready),
        "results": results,
        "target_task_id": TARGET_TASK,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "g18_completion_required": False,
        "g18_claim_or_fence_consumed": False,
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
