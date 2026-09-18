#!/usr/bin/env python3
"""Consume one admitted SV002 self-characterization materialization.

Admission is non-authorizing. This consumer validates the exact Goal/COSV/request
binding, opens one existing ESRL EVENT_EPHEMERAL lease, and invokes the already
registered Goal through the existing targeted WorkerCoordinator executor.
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
TASK_ID = "STEGVERSE-002-EXPERIMENT-RERUN-001"
COSV = "50000000107000"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_RECEIPT_DIR_REL = Path("receipts/sovereign-network/sv002-self-characterization-intr-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/sv002-self-characterization-intr-materialization")
LATEST_REL = Path("receipts/sovereign-host/sv002-self-characterization-intr-materialization-consumption.latest.json")
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
INGRESS_SCHEMA = "stegverse.sv002-self-characterization-intr-materialization-ingress/v1"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "SV002:SelfCharacterization"}
DOWNSTREAM_OWNER = "StegVerse-002/.github"
Runner = Callable[..., subprocess.CompletedProcess[Any]]
RuntimeMaterializer = Callable[..., dict[str, Any]]

HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN",
)


class SV002SelfCharacterizationMaterializationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SV002SelfCharacterizationMaterializationError(f"object_required:{path}")
    return value


def scrubbed_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    if any(str(values.get(k, "")).strip().lower() not in {"", "0", "false", "no"} for k in HOSTED_ENV):
        raise SV002SelfCharacterizationMaterializationError("hosted_environment_forbidden")
    child = dict(values)
    for key in HOSTED_ENV + CREDENTIAL_ENV:
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def validate_sv002_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SV002SelfCharacterizationMaterializationError("sv002_request_object_required")
    expected = {
        "schema_version": "stegverse.external_organization.interlock_request.v1",
        "request_class": "EXTERNAL_ORGANIZATION_INTERACTION",
        "operation": "REQUEST_SELF_CHARACTERIZATION",
        "transport": "InTr",
        "authority_transfer": False,
        "sdk_mints_intr_receipt": False,
        "sdk_claims_delivery": False,
        "authority_effect_resolution": "DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise SV002SelfCharacterizationMaterializationError(f"sv002_request_{key}_mismatch")
    manifest = ((value.get("payload") or {}).get("manifest"))
    bindings = value.get("bindings")
    if not isinstance(manifest, dict) or not isinstance(bindings, dict):
        raise SV002SelfCharacterizationMaterializationError("sv002_manifest_or_bindings_missing")
    expected_bindings = {
        "experiment_id": "STEGVERSE-002-SELF-CHARACTERIZATION-001",
        "source_organization_id": "StegVerse-SDK-Evaluator",
        "target_entity_id": "StegVerse-002",
        "manifest_id": "SDK-SV002-FIRST-SELF-CHARACTERIZATION-001",
    }
    for key, wanted in expected_bindings.items():
        if bindings.get(key) != wanted:
            raise SV002SelfCharacterizationMaterializationError(f"sv002_binding_{key}_mismatch")
    if manifest.get("manifest_sha256") != bindings.get("manifest_sha256"):
        raise SV002SelfCharacterizationMaterializationError("sv002_manifest_sha_binding_mismatch")
    body = dict(manifest)
    claimed = body.pop("manifest_sha256", None)
    actual = hashlib.sha256(canonical_bytes(body)).hexdigest()
    if claimed != actual:
        raise SV002SelfCharacterizationMaterializationError("sv002_manifest_sha256_mismatch")
    if manifest.get("operation") != "REQUEST_SELF_CHARACTERIZATION":
        raise SV002SelfCharacterizationMaterializationError("sv002_manifest_operation_mismatch")
    if manifest.get("objective") != "Determine what constitutes the entity identified as StegVerse-002 and produce a representation sufficient for another system to evaluate and reconstruct your conclusion.":
        raise SV002SelfCharacterizationMaterializationError("sv002_manifest_objective_mismatch")
    policy = manifest.get("knowledge_policy")
    if not isinstance(policy, dict) or set(policy) != {
        "prescribe_self_ontology", "prescribe_formalism", "prescribe_transition_elements",
        "prescribe_external_followup", "prescribe_admissible_existence_connection",
    } or any(v is not False for v in policy.values()):
        raise SV002SelfCharacterizationMaterializationError("sv002_knowledge_policy_mismatch")
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
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_count": 1,
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise SV002SelfCharacterizationMaterializationError(f"materialization_{key}_mismatch")
    mid = request.get("materialization_id")
    if not isinstance(mid, str) or not mid.startswith("INTR-MAT-") or len(mid) != 33:
        raise SV002SelfCharacterizationMaterializationError("materialization_id_invalid")
    body = dict(request)
    claimed = body.pop("request_hash", None)
    if claimed != digest_uri(body):
        raise SV002SelfCharacterizationMaterializationError("materialization_request_hash_mismatch")
    exact = validate_sv002_request(request.get("sv002_request"))
    if digest_uri(exact) != request.get("payload_hash"):
        raise SV002SelfCharacterizationMaterializationError("sv002_exact_request_payload_hash_mismatch")


def ingress_receipt(runtime: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    path = runtime / INGRESS_RECEIPT_DIR_REL / f"{request['materialization_id']}.json"
    if not path.is_file():
        raise SV002SelfCharacterizationMaterializationError("ingress_receipt_missing")
    receipt = load(path)
    expected = {
        "schema": INGRESS_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_count": 1,
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_execution_attempted": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }
    for key, wanted in expected.items():
        if receipt.get(key) != wanted:
            raise SV002SelfCharacterizationMaterializationError(f"ingress_{key}_mismatch")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        if receipt.get(key) != request.get(key):
            raise SV002SelfCharacterizationMaterializationError(f"ingress_request_binding_mismatch:{key}")
    return receipt


def default_materializer(*, source: Path, intake_runtime: Path, request: Mapping[str, Any], ingress: Mapping[str, Any], env: Mapping[str, str] | None) -> dict[str, Any]:
    from workers.sv002_self_characterization_esrl_runtime_bridge import materialize_sv002_self_characterization_runtime
    return materialize_sv002_self_characterization_runtime(
        control_root=source,
        intake_runtime_root=intake_runtime,
        request=request,
        ingress_receipt=ingress,
        env=env,
    )


def consume_one(
    source_root: Path,
    runtime_root: Path,
    materialization_id: str,
    *,
    runner: Runner = subprocess.run,
    env: Mapping[str, str] | None = None,
    runtime_materializer: RuntimeMaterializer | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    intake = runtime_root.expanduser().resolve()
    request_path = intake / REQUEST_DIR_REL / f"{materialization_id}.json"
    if not request_path.is_file():
        raise SV002SelfCharacterizationMaterializationError("materialization_request_missing")
    request = load(request_path)
    validate_request(request)
    if request.get("materialization_id") != materialization_id:
        raise SV002SelfCharacterizationMaterializationError("materialization_id_path_binding_mismatch")
    ingress = ingress_receipt(intake, request)

    materializer = default_materializer if runtime_materializer is None else runtime_materializer
    materialized = materializer(source=source, intake_runtime=intake, request=request, ingress=ingress, env=env)
    execution_runtime = Path(str(materialized.get("runtime_root") or "")).resolve()
    evidence = materialized.get("evidence")
    if not execution_runtime.is_dir() or not isinstance(evidence, dict):
        raise SV002SelfCharacterizationMaterializationError("event_ephemeral_runtime_invalid")
    if evidence.get("state") != "LEASE_OPEN" or evidence.get("runtime_class") != "EVENT_EPHEMERAL":
        raise SV002SelfCharacterizationMaterializationError("event_ephemeral_lease_not_open")
    if evidence.get("runtime_instantiated") is not True or evidence.get("local_identity_verified") is not True:
        raise SV002SelfCharacterizationMaterializationError("event_ephemeral_identity_not_verified")
    if evidence.get("same_device_execution_required") is not True or evidence.get("requires_other_machine") is not False:
        raise SV002SelfCharacterizationMaterializationError("same_device_invariant_failed")

    entrypoint = execution_runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise SV002SelfCharacterizationMaterializationError("targeted_executor_missing")
    safe = scrubbed_env(env)
    safe["STEGVERSE_SV002_RERUN_INTAKE_RUNTIME_ROOT"] = str(intake)
    safe["STEGVERSE_SV002_RERUN_MATERIALIZATION_ID"] = materialization_id
    safe["STEGVERSE_SV002_RERUN_ESRL_LEASE_ID"] = str(evidence.get("lease_id") or "")
    command = [
        sys.executable, str(entrypoint),
        "--source-root", str(source),
        "--runtime-root", str(execution_runtime),
        "--task-id", TASK_ID,
        "--cosv-task-vector", COSV,
    ]
    completed = runner(command, cwd=execution_runtime, env=safe, check=False, capture_output=True, text=True, timeout=2400)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema": "stegverse.sv002-self-characterization-intr-materialization-consumption/v1",
        "state": "MATERIALIZATION_EXECUTION_ATTEMPTED" if completed.returncode == 0 else "MATERIALIZATION_EXECUTION_BLOCKED",
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_count": 1,
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "node_id": ingress.get("node_id"),
        "interlock_id": ingress.get("interlock_id"),
        "outbox_entry_hash": ingress.get("outbox_entry_hash"),
        "request_bound_observed": bool(ingress.get("node_id") and ingress.get("interlock_id") and ingress.get("outbox_entry_hash")),
        "intr_materialization_admitted": True,
        "esrl_lease_id": evidence.get("lease_id"),
        "esrl_runtime_id": evidence.get("runtime_id"),
        "invocation_scoped_lease_established": True,
        "event_ephemeral_runtime_materialized": True,
        "execution_time_runtime_identity_bound": True,
        "target_task_id": TASK_ID,
        "targeted_executor_returncode": completed.returncode,
        "runtime_execution_attempted": True,
        "claim_or_fence_minted_by_consumer": False,
        "request_grants_execution_authority": False,
        "second_user_operated_device_used": False,
        "standing_runtime_created": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_EVENT_CONSUMPTION_ONLY",
        "consumed_at": now,
    }
    out = intake / RECEIPT_DIR_REL / f"{materialization_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if out.exists() and out.read_text(encoding="utf-8") != rendered:
        raise SV002SelfCharacterizationMaterializationError("consumption_receipt_write_once_collision")
    if not out.exists():
        out.write_text(rendered, encoding="utf-8")
    latest = intake / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(rendered, encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--materialization-id", required=True)
    args = parser.parse_args()
    result = consume_one(args.source_root, args.runtime_root, args.materialization_id)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["targeted_executor_returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
