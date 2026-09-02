#!/usr/bin/env python3
"""Event-ephemeral SV002 public-observation materialization consumer.

The ingress event is non-authorizing. This consumer validates the exact queued
Universal InTr request and its write-once ingress receipt, materializes a fresh
sovereign event-ephemeral runtime, and then invokes only the already-admitted
SV002 observation task through WorkerCoordinator claim/fence authority.
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
DOWNSTREAM_OWNER = "StegVerse-Labs/.github#493"
Runner = Callable[..., subprocess.CompletedProcess[Any]]
RuntimeMaterializer = Callable[..., dict[str, Any]]
LeaseResumer = Callable[..., dict[str, Any]]

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
    for field in ("transport_intent_hash", "payload_hash", "request_hash"):
        value = request.get(field)
        if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71 or any(ch not in "0123456789abcdef" for ch in value[7:]):
            raise SV002InTrMaterializationError(f"{field}_invalid")
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


def _default_lease_resumer(*, source: Path, execution_runtime: Path, snapshot_path: Path, expected_snapshot_digest: str, env: Mapping[str, str] | None) -> dict[str, Any]:
    from workers.sv002_public_profile_lease_resumer import resume_public_lease
    return resume_public_lease(
        control_root=source,
        execution_runtime=execution_runtime,
        snapshot_path=snapshot_path,
        expected_snapshot_digest=expected_snapshot_digest,
        env=env,
    )


def consume_one(source_root: Path, runtime_root: Path, materialization_id: str, *, runner: Runner = subprocess.run, env: Mapping[str, str] | None = None, runtime_materializer: RuntimeMaterializer | None = None, lease_resumer: LeaseResumer | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request = _load(runtime / REQUEST_DIR_REL / f"{materialization_id}.json")
    validate_request(request)
    ingress = _ingress_receipt(runtime, request)
    safe = scrubbed_env(env)
    materializer = _default_materializer if runtime_materializer is None else runtime_materializer
    materialized = materializer(source=source, intake_runtime=runtime, request=request, ingress_receipt=ingress, env=safe)
    execution_runtime = Path(str(materialized.get("runtime_root", ""))).resolve()
    evidence = materialized.get("evidence")
    if not execution_runtime.is_dir() or not isinstance(evidence, dict):
        raise SV002InTrMaterializationError("sv002_esrl_runtime_materialization_invalid")
    if evidence.get("state") != "PUBLIC_VERIFYING" or evidence.get("lease_state") != "PUBLIC_VERIFYING" or evidence.get("runtime_instantiated") is not True or evidence.get("local_identity_verified") is not True:
        raise SV002InTrMaterializationError("sv002_esrl_runtime_not_public_verifying")
    snapshot_ref = evidence.get("canonical_runtime_lease_snapshot_ref")
    snapshot_digest = evidence.get("canonical_runtime_lease_snapshot_sha256")
    if not isinstance(snapshot_ref, str) or not snapshot_ref or not isinstance(snapshot_digest, str):
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_required")
    snapshot_path = Path(snapshot_ref).expanduser().resolve()
    try:
        snapshot_path.relative_to(execution_runtime)
    except ValueError as exc:
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_outside_runtime") from exc
    if not snapshot_path.is_file():
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_missing")
    snapshot = _load(snapshot_path)
    if digest_uri(snapshot) != snapshot_digest:
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_digest_mismatch")
    if snapshot.get("schema") != "stegverse.esrl.lease-machine-snapshot/v1" or snapshot.get("state") != "PUBLIC_VERIFYING":
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_state_invalid")
    history = snapshot.get("history")
    if not isinstance(history, list) or history != ["ABSENT", "REQUESTED", "ADMITTED", "PROVISIONING", "LOCAL_READY", "PUBLIC_VERIFYING"]:
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_history_invalid")
    if snapshot.get("credential_authority") != "TV/TVC" or snapshot.get("authority_effect") != "NONE":
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_snapshot_authority_invalid")
    if evidence.get("g18_completion_required") is not False or evidence.get("observer_direct_relation_to_stegverse_002") is not False:
        raise SV002InTrMaterializationError("sv002_esrl_semantic_boundary_invalid")

    selected_resumer = _default_lease_resumer if lease_resumer is None else lease_resumer
    resumed = selected_resumer(
        source=source,
        execution_runtime=execution_runtime,
        snapshot_path=snapshot_path,
        expected_snapshot_digest=snapshot_digest,
        env=safe,
    )
    if resumed.get("state") != "LEASE_OPEN":
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_open_required")
    open_snapshot = resumed.get("lease_snapshot")
    open_digest = resumed.get("lease_snapshot_sha256")
    public_observation = resumed.get("public_profile_observation")
    if not isinstance(open_snapshot, dict) or not isinstance(open_digest, str) or not isinstance(public_observation, dict):
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_open_evidence_invalid")
    if open_snapshot.get("schema") != "stegverse.esrl.lease-machine-snapshot/v1" or open_snapshot.get("state") != "LEASE_OPEN":
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_open_snapshot_invalid")
    if open_snapshot.get("history") != ["ABSENT", "REQUESTED", "ADMITTED", "PROVISIONING", "LOCAL_READY", "PUBLIC_VERIFYING", "LEASE_OPEN"]:
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_open_history_invalid")
    if digest_uri(open_snapshot) != open_digest:
        raise SV002InTrMaterializationError("sv002_canonical_runtime_lease_open_digest_invalid")
    if public_observation.get("observation_origin") != "INDEPENDENT_PUBLIC_HTTPS":
        raise SV002InTrMaterializationError("sv002_public_profile_observation_origin_invalid")
    if public_observation.get("public_profile_url") != "https://stegverse.org/intr/profile":
        raise SV002InTrMaterializationError("sv002_public_profile_url_invalid")
    if public_observation.get("required_profile") != "SV002:PublicObservation":
        raise SV002InTrMaterializationError("sv002_public_profile_capability_invalid")
    if any(public_observation.get(field) is not False for field in (
        "receiver_ready_claimed", "round_trip_claimed", "master_records_custody_claimed",
        "sv002_principal_execution_claimed", "public_profile_grants_execution_authority",
        "public_profile_grants_transition_authority",
    )):
        raise SV002InTrMaterializationError("sv002_public_profile_evidence_overclaim")

    entrypoint = execution_runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise SV002InTrMaterializationError(f"sv002_targeted_executor_missing:{entrypoint}")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(execution_runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=execution_runtime, env=safe, check=False, capture_output=True, text=True, timeout=180)
    receipt = {
        "schema": "stegverse.sv002-intr-materialization-consumption/v1",
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "target_task_id": TARGET_TASK,
        "targeted_executor_returncode": completed.returncode,
        "runtime_execution_attempted": True,
        "canonical_runtime_lease_state": "LEASE_OPEN",
        "canonical_runtime_lease_snapshot_ref": str(snapshot_path),
        "canonical_runtime_lease_snapshot_sha256": open_digest,
        "canonical_runtime_lease_resume_required": False,
        "canonical_runtime_lease_public_verification_observed": True,
        "public_profile_url": public_observation["public_profile_url"],
        "public_profile_schema": public_observation["public_profile_schema"],
        "public_profile_sha256": public_observation["public_profile_sha256"],
        "public_profile_observation_origin": public_observation["observation_origin"],
        "public_profile_required_profile": public_observation["required_profile"],
        "public_profile_grants_execution_authority": False,
        "public_profile_grants_transition_authority": False,
        "receiver_ready_is_precondition": False,
        "g18_completion_required": False,
        "observer_direct_relation_to_stegverse_002": False,
        "request_grants_authority": False,
        "claim_or_fence_minted_by_consumer": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_REQUEST_ONLY",
        "consumed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    path = runtime / RECEIPT_DIR_REL / f"{materialization_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest = runtime / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume one admitted SV002 materialization request.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    print(json.dumps(consume_one(args.source_root, args.runtime_root, args.materialization_id), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
