from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

RUNNER_RESULT_SCHEMA = "stegverse.reusable-task-runner-result/v1"
RUNNER_EXPIRY_SCHEMA = "stegverse.reusable-task-runner-expiry/v1"
RESIDUAL_SCHEMA = "stegverse.reusable-task-residual-recording/v1"
CUSTODY_REQUEST_SCHEMA = "stegverse.reusable-task-master-records-custody-request/v1"
CUSTODY_RECORD_SCHEMA = "master-records.reusable-task-lifecycle-custody/v1"
ENTROPY_SCHEMA = "stegverse.reusable-task-entropy-recovery/v1"


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_runner_result(result: dict[str, Any], *, invocation_id: str, reusable_task_id: str, manifest_hash: str, completion_predicates: list[str]) -> None:
    if result.get("schema") != RUNNER_RESULT_SCHEMA:
        raise ValueError("runner result schema mismatch")
    if result.get("invocation_id") != invocation_id or result.get("reusable_task_id") != reusable_task_id:
        raise ValueError("runner result invocation binding mismatch")
    if result.get("manifest_hash") != manifest_hash:
        raise ValueError("runner result manifest hash mismatch")
    observed = result.get("completion_predicates_satisfied")
    if not isinstance(observed, list) or sorted(observed) != sorted(completion_predicates):
        raise ValueError("runner result does not satisfy exact declared completion predicates")
    if result.get("runtime_observed") is not True or result.get("completion_evidence_observed") is not True:
        raise ValueError("runner result lacks runtime completion evidence")
    if result.get("authority_effect") != "NONE":
        raise ValueError("runner result authority effect must be NONE")


def build_runner_expiry(*, invocation_id: str, reusable_task_id: str, manifest_hash: str, runner_ref: str, returncode: int, result: dict[str, Any]) -> dict[str, Any]:
    if returncode != 0:
        raise ValueError("runner expiry receipt requires successful process return")
    return {
        "schema": RUNNER_EXPIRY_SCHEMA,
        "invocation_id": invocation_id,
        "reusable_task_id": reusable_task_id,
        "manifest_hash": manifest_hash,
        "runner_ref": runner_ref,
        "runner_returncode": returncode,
        "runner_process_return_observed": True,
        "runner_expired": True,
        "runner_result_sha256": stable_hash(result),
        "original_execution_purpose_revoked": True,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


def recording_levels(manifest: dict[str, Any]) -> list[str]:
    recording = manifest.get("recording")
    levels = recording.get("levels") if isinstance(recording, dict) else manifest.get("recording_levels")
    if not isinstance(levels, list) or not all(isinstance(x, str) and x for x in levels):
        raise ValueError("manifest recording levels must be a non-empty string list")
    return list(levels)


def build_residual_recording(*, manifest: dict[str, Any], runner_result: dict[str, Any], runner_expiry: dict[str, Any]) -> dict[str, Any]:
    levels = recording_levels(manifest)
    return {
        "schema": RESIDUAL_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": manifest["reusable_task_id"],
        "task_id": manifest.get("task_id"),
        "cosv_task_vector": manifest.get("cosv_task_vector"),
        "manifest_hash": manifest["manifest_hash"],
        "runner_result_sha256": stable_hash(runner_result),
        "runner_expiry_sha256": stable_hash(runner_expiry),
        "recording_levels_required": levels,
        "recording_levels_carried": levels,
        "runner_expired": True,
        "execution_authority": False,
        "credential_acquisition_authority": False,
        "claim_or_fence_minting_authority": False,
        "provider_operation_authority": False,
        "self_extension_authority": False,
        "master_records_custody_pending": True,
        "authority_effect": "NONE_RECORDING_ONLY",
    }


def build_custody_request(*, manifest: dict[str, Any], trigger_receipt: dict[str, Any], runner_result: dict[str, Any], runner_expiry: dict[str, Any], residual_recording: dict[str, Any]) -> dict[str, Any]:
    bundle = {
        "manifest": manifest,
        "trigger_receipt": trigger_receipt,
        "runner_result": runner_result,
        "runner_expiry": runner_expiry,
        "residual_recording": residual_recording,
    }
    return {
        "schema": CUSTODY_REQUEST_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": manifest["reusable_task_id"],
        "manifest_hash": manifest["manifest_hash"],
        "destination": "master-records/core-lite",
        "custody_requested": True,
        "reconstruction_requested": True,
        "destination_custody_accepted": False,
        "destination_acknowledgement_minted": False,
        "execution_authority_granted": False,
        "runtime_activation": False,
        "publication_authority_granted": False,
        "evidence_bundle": bundle,
        "evidence_bundle_sha256": stable_hash(bundle),
        "authority_effect": "NONE_SOURCE_REQUEST_ONLY",
    }


def verify_custody_record(record: dict[str, Any], request: dict[str, Any]) -> None:
    if record.get("schema") != CUSTODY_RECORD_SCHEMA:
        raise ValueError("Master Records custody schema mismatch")
    if record.get("invocation_id") != request.get("invocation_id") or record.get("reusable_task_id") != request.get("reusable_task_id"):
        raise ValueError("Master Records custody identity mismatch")
    if record.get("source_request_sha256") != stable_hash(request):
        raise ValueError("Master Records custody request hash mismatch")
    if record.get("evidence_bundle_sha256") != request.get("evidence_bundle_sha256"):
        raise ValueError("Master Records evidence bundle hash mismatch")
    required_true = ("destination_custody_accepted", "destination_acknowledgement_minted", "independent_validation_complete", "reconstruction_confirmed")
    if not all(record.get(key) is True for key in required_true):
        raise ValueError("Master Records custody/reconstruction predicates not satisfied")
    required_false = ("runtime_activation", "execution_authority_granted", "publication_authority_granted")
    if not all(record.get(key) is False for key in required_false):
        raise ValueError("Master Records custody record escalates authority")
    if record.get("authority_effect") != "NONE_CUSTODY_RECONSTRUCTION_ONLY":
        raise ValueError("Master Records authority effect mismatch")


def build_entropy_recovery(*, manifest: dict[str, Any], runner_expiry: dict[str, Any], residual_recording: dict[str, Any], custody_request: dict[str, Any], custody_record: dict[str, Any]) -> dict[str, Any]:
    verify_custody_record(custody_record, custody_request)
    levels_complete = residual_recording.get("recording_levels_carried") == residual_recording.get("recording_levels_required")
    if runner_expiry.get("runner_expired") is not True or not levels_complete:
        raise ValueError("entropy recovery prerequisites are incomplete")
    return {
        "schema": ENTROPY_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": manifest["reusable_task_id"],
        "manifest_hash": manifest["manifest_hash"],
        "runner_expired": True,
        "required_recording_levels_complete": True,
        "master_records_custody_accepted": True,
        "master_records_reconstruction_confirmed": True,
        "unrecorded_successor_or_correction_dependency": False,
        "residual_construct_displaced": True,
        "required_evidence_deleted": False,
        "master_records_history_deleted": False,
        "original_runner_reactivated": False,
        "custody_record_sha256": stable_hash(custody_record),
        "authority_effect": "NONE_TERMINAL_DISPLACEMENT_ONLY",
    }
