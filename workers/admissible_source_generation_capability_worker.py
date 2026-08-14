#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "admissible-source-generation-capability.json"
TASK_ID = "SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001"
CAPABILITY = "admissible_source_generation_capability"
CREDENTIAL_AUTHORITY = "TV/TVC"
OWNER_MANIFEST_SCHEMA = "stegverse.owner-implementation-work-manifest/v0.1"
RESULT_SCHEMA = "stegverse.local-source-generation-result/v0.1"
SOURCE_PACKET_SCHEMA = "stegverse.owner-source-generation-packet/v0.1"
INVOCATION_SCHEMA = "stegverse.worker-invocation/v0.1"
LOCAL_MODEL_CAPABILITY_ID = "stegverse:capability:sovereign-local-model:v1"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def canonical_hash(value: object) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def safe_repo_path(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return False
    normalized = posixpath.normpath(value)
    if normalized in {".", ".."} or normalized.startswith("../"):
        return False
    if normalized != value or any(ch in value for ch in "*?[]"):
        return False
    return True


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(_nonempty_string(item) for item in value)


def validate_generation_result(
    config: dict[str, Any],
    manifest: dict[str, Any],
    result: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    if manifest.get("schema") != OWNER_MANIFEST_SCHEMA:
        return None, "OWNER_WORK_SCHEMA_INVALID"
    if manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
        return None, "OWNER_WORK_NOT_ADMITTED"
    if result.get("schema") != RESULT_SCHEMA:
        return None, "GENERATION_RESULT_SCHEMA_INVALID"

    delta_id = manifest.get("delta_id")
    owner_repository = manifest.get("owner_repository")
    if result.get("delta_id") != delta_id or result.get("owner_repository") != owner_repository:
        return None, "OWNER_OR_DELTA_MISMATCH"

    expected_capability_id = config.get("capability_id")
    if result.get("generator_capability_id") != expected_capability_id:
        return None, "GENERATOR_CAPABILITY_ID_MISMATCH"
    if result.get("generator_capability_version") != config.get("capability_version"):
        return None, "GENERATOR_CAPABILITY_VERSION_MISMATCH"
    if config.get("require_activated_capability") is True and result.get("generator_phase") != "ACTIVATED":
        return None, "GENERATOR_CAPABILITY_NOT_ACTIVATED"
    if config.get("require_activation_proof") is True and not _nonempty_string(result.get("generator_activation_proof_ref")):
        return None, "GENERATOR_ACTIVATION_PROOF_MISSING"
    if config.get("require_integration_evidence") is True and not _string_list(result.get("generator_integration_evidence_refs")):
        return None, "GENERATOR_INTEGRATION_EVIDENCE_MISSING"
    if not _nonempty_string(result.get("generator_authority_ref")):
        return None, "GENERATOR_AUTHORITY_REF_MISSING"
    if not _nonempty_string(result.get("generator_profile_ref")):
        return None, "GENERATOR_PROFILE_REF_MISSING"

    if result.get("local_model_capability_id") != LOCAL_MODEL_CAPABILITY_ID:
        return None, "LOCAL_MODEL_CAPABILITY_ID_MISMATCH"
    if result.get("local_model_phase") != "ACTIVATED":
        return None, "LOCAL_MODEL_NOT_ACTIVATED"
    if not _nonempty_string(result.get("local_model_activation_proof_ref")):
        return None, "LOCAL_MODEL_ACTIVATION_PROOF_MISSING"
    if config.get("require_runtime_proof") is True and not _nonempty_string(result.get("model_runtime_proof_ref")):
        return None, "MODEL_RUNTIME_PROOF_MISSING"

    lifetime_class = result.get("lifetime_class")
    if lifetime_class not in set(config.get("allowed_lifetime_classes") or []):
        return None, "LIFETIME_CLASS_NOT_ADMITTED"
    if result.get("persistent_execution_used") is not False:
        return None, "PERSISTENT_EXECUTION_NOT_ADMITTED"
    if config.get("require_teardown_or_reconstruction_evidence") is True and not _nonempty_string(result.get("teardown_or_reconstruction_evidence_ref")):
        return None, "TEARDOWN_OR_RECONSTRUCTION_EVIDENCE_MISSING"

    if result.get("credential_authority") != CREDENTIAL_AUTHORITY:
        return None, "CREDENTIAL_AUTHORITY_INVALID"
    if result.get("github_token_runtime_authority") is not False:
        return None, "GITHUB_TOKEN_RUNTIME_AUTHORITY_FORBIDDEN"
    if result.get("non_tv_tvc_secret_or_token_used") is not False:
        return None, "NON_TV_TVC_SECRET_OR_TOKEN_USED"
    if result.get("consumer_credential_present") is not False:
        return None, "CONSUMER_CREDENTIAL_PRESENT"

    base_ref = result.get("base_ref")
    expected_base_sha = result.get("expected_base_sha")
    if not _nonempty_string(base_ref) or not isinstance(expected_base_sha, str) or len(expected_base_sha) != 40:
        return None, "BASE_IDENTITY_INVALID"

    proposed = manifest.get("proposed_paths")
    if not isinstance(proposed, list) or not proposed:
        return None, "OWNER_SCOPE_MISSING"
    proposed_set = {item for item in proposed if isinstance(item, str)}
    if len(proposed_set) != len(proposed):
        return None, "OWNER_SCOPE_INVALID"

    files = result.get("files")
    if not isinstance(files, list) or not files:
        return None, "SOURCE_FILES_MISSING"
    if len(files) > int(config["maximum_file_count"]):
        return None, "SOURCE_FILE_COUNT_EXCEEDS_LIMIT"

    normalized_files: list[dict[str, Any]] = []
    total_bytes = 0
    for row in files:
        if not isinstance(row, dict):
            return None, "SOURCE_FILE_ROW_INVALID"
        path = row.get("path")
        content = row.get("content_utf8")
        expected_source_sha = row.get("expected_source_sha256")
        replacement_sha = row.get("replacement_sha256")
        if not safe_repo_path(path):
            return None, "UNSAFE_MUTATION_PATH"
        if path not in proposed_set:
            return None, f"PATH_NOT_ADMITTED:{path}"
        if not isinstance(content, str):
            return None, f"CONTENT_NOT_TEXT:{path}"
        if expected_source_sha is not None and (not isinstance(expected_source_sha, str) or len(expected_source_sha) != 64):
            return None, f"EXPECTED_SOURCE_SHA_INVALID:{path}"
        calculated = sha256_text(content)
        if replacement_sha != calculated:
            return None, f"REPLACEMENT_SHA_MISMATCH:{path}"
        total_bytes += len(content.encode("utf-8"))
        normalized_files.append({
            "path": path,
            "content_utf8": content,
            "expected_source_sha256": expected_source_sha,
            "replacement_sha256": calculated,
        })
    if total_bytes > int(config["maximum_total_bytes"]):
        return None, "SOURCE_TOTAL_BYTES_EXCEEDS_LIMIT"

    owner_handoffs = [item for item in proposed if isinstance(item, str) and item.endswith("_MIRROR_HANDOFF.md")]
    if not owner_handoffs:
        return None, "OWNER_HANDOFF_NOT_ADMITTED"
    if normalized_files[0]["path"] not in set(owner_handoffs):
        return None, "HANDOFF_NOT_FIRST_GENERATED_FILE"

    new_branch = result.get("new_branch")
    commit_message = result.get("commit_message")
    execution_identity = result.get("execution_identity")
    if not _nonempty_string(new_branch) or not _nonempty_string(commit_message) or not _nonempty_string(execution_identity):
        return None, "EXECUTION_OR_COMMIT_IDENTITY_MISSING"

    prepared = {
        "delta_id": delta_id,
        "owner_repository": owner_repository,
        "base_ref": base_ref,
        "expected_base_sha": expected_base_sha,
        "new_branch": new_branch,
        "commit_message": commit_message,
        "files": normalized_files,
        "total_bytes": total_bytes,
        "generator_capability_id": result["generator_capability_id"],
        "generator_capability_version": result["generator_capability_version"],
        "generator_existence_hash": result.get("generator_existence_hash"),
        "generator_phase": result["generator_phase"],
        "generator_activation_proof_ref": result["generator_activation_proof_ref"],
        "generator_integration_evidence_refs": list(result["generator_integration_evidence_refs"]),
        "generator_authority_ref": result["generator_authority_ref"],
        "generator_profile_ref": result["generator_profile_ref"],
        "local_model_capability_id": result["local_model_capability_id"],
        "local_model_phase": result["local_model_phase"],
        "local_model_activation_proof_ref": result["local_model_activation_proof_ref"],
        "model_runtime_proof_ref": result["model_runtime_proof_ref"],
        "execution_identity": execution_identity,
        "lifetime_class": lifetime_class,
        "teardown_or_reconstruction_evidence_ref": result["teardown_or_reconstruction_evidence_ref"],
        "generation_result_sha256": canonical_hash(result),
        "owner_work_sha256": canonical_hash(manifest),
    }
    if not isinstance(prepared["generator_existence_hash"], str) or len(prepared["generator_existence_hash"]) != 64:
        return None, "GENERATOR_EXISTENCE_HASH_INVALID"
    return prepared, None


def build_source_packet(config: dict[str, Any], prepared: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": SOURCE_PACKET_SCHEMA,
        "source_generation_authorized": True,
        "delta_id": prepared["delta_id"],
        "owner_repository": prepared["owner_repository"],
        "base_ref": prepared["base_ref"],
        "expected_base_sha": prepared["expected_base_sha"],
        "new_branch": prepared["new_branch"],
        "commit_message": prepared["commit_message"],
        "files": prepared["files"],
        "generator_capability_id": prepared["generator_capability_id"],
        "generator_capability_version": prepared["generator_capability_version"],
        "generator_existence_hash": prepared["generator_existence_hash"],
        "generator_phase": prepared["generator_phase"],
        "generator_activation_proof_ref": prepared["generator_activation_proof_ref"],
        "generator_integration_evidence_refs": prepared["generator_integration_evidence_refs"],
        "generator_authority_ref": prepared["generator_authority_ref"],
        "generator_profile_ref": prepared["generator_profile_ref"],
        "local_model_capability_id": prepared["local_model_capability_id"],
        "local_model_phase": prepared["local_model_phase"],
        "local_model_activation_proof_ref": prepared["local_model_activation_proof_ref"],
        "model_runtime_proof_ref": prepared["model_runtime_proof_ref"],
        "execution_identity": prepared["execution_identity"],
        "lifetime_class": prepared["lifetime_class"],
        "persistent_execution_used": False,
        "teardown_or_reconstruction_evidence_ref": prepared["teardown_or_reconstruction_evidence_ref"],
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": False,
        "consumer_credential_present": False,
        "non_tv_tvc_secret_or_token_used": False,
        "generation_result_sha256": prepared["generation_result_sha256"],
        "owner_work_sha256": prepared["owner_work_sha256"],
        "authority_effect": "NONE_SOURCE_PACKET_ONLY_DOWNSTREAM_TVC_AND_OWNER_ADMISSION_REQUIRED"
    }


def evaluate(config: dict[str, Any]) -> dict[str, Any]:
    owner_dir = ROOT / str(config["owner_work_directory"])
    result_dir = ROOT / str(config["generation_result_directory"])
    emitted: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    if not owner_dir.is_dir():
        return {
            "state": "BLOCKED",
            "reason": "OWNER_WORK_DIRECTORY_MISSING",
            "packets": [],
            "blocked": [],
            "authority_effect": "NONE_FAIL_CLOSED"
        }

    for manifest_path in sorted(owner_dir.glob("*.json")):
        manifest = load(manifest_path)
        if manifest.get("schema") != OWNER_MANIFEST_SCHEMA or manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
            continue
        delta_id = manifest.get("delta_id")
        result_path = result_dir / f"{delta_id}.json"
        if not result_path.is_file():
            blocked.append({
                "delta_id": delta_id,
                "reason": "LOCAL_SOURCE_GENERATION_RESULT_MISSING",
                "release_condition": f"{result_path.relative_to(ROOT).as_posix()} exists with ACTIVATED capability + local-model activation proof"
            })
            continue
        prepared, error = validate_generation_result(config, manifest, load(result_path))
        if error:
            blocked.append({"delta_id": delta_id, "reason": error})
            continue
        emitted.append(build_source_packet(config, prepared))

    if not emitted:
        return {
            "state": "BLOCKED",
            "reason": "NO_ADMISSIBLE_SOURCE_GENERATION_RESULT",
            "packets": [],
            "blocked": blocked,
            "credential_authority": CREDENTIAL_AUTHORITY,
            "consumer_credential_present": False,
            "non_tv_tvc_secret_or_token_used": False,
            "authority_effect": "NONE_FAIL_CLOSED"
        }

    return {
        "state": "COMPLETED",
        "reason": "EXACT_OWNER_SOURCE_PACKETS_READY",
        "packets": emitted,
        "blocked": blocked,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "consumer_credential_present": False,
        "non_tv_tvc_secret_or_token_used": False,
        "authority_effect": "NONE_SOURCE_PACKET_PROJECTION_ONLY"
    }


def persist(config: dict[str, Any], result: dict[str, Any]) -> None:
    packet_dir = ROOT / str(config["source_packet_directory"])
    for packet in result.get("packets", []):
        target = packet_dir / f"{packet['delta_id']}.json"
        if target.exists():
            existing = load(target)
            if canonical_hash(existing) != canonical_hash(packet):
                raise ValueError(f"existing source packet differs for {packet['delta_id']}")
            continue
        atomic_write(target, packet)


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != INVOCATION_SCHEMA:
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID:
        return 4
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not _nonempty_string(claim_id) or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 6
    allowed = set(execution.get("allowed_paths") or [])
    if "receipts/admissible-source-generation-capability/**" not in allowed:
        return 7
    if "receipts/formalism-owner-mutation-executor/source-packages/**" not in allowed:
        return 8

    config = load(CONFIG_PATH)
    if config.get("schema") != "stegverse.admissible-source-generation-capability/v0.1":
        return 9
    if config.get("credential_authority") != CREDENTIAL_AUTHORITY:
        return 10
    if config.get("github_token_required") is not False or config.get("consumer_secret_or_token_authority") is not False:
        return 11

    result = evaluate(config)
    if result["state"] == "COMPLETED":
        persist(config, result)

    receipt = {
        "schema": "stegverse.admissible-source-generation-capability-receipt/v0.1",
        "goal_id": config["goal_id"],
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "worker_id": task.get("worker_id"),
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "state": result["state"],
        "reason": result["reason"],
        "packet_count": len(result.get("packets", [])),
        "blocked": result.get("blocked", []),
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": False,
        "consumer_credential_present": False,
        "non_tv_tvc_secret_or_token_used": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": result.get("authority_effect", "NONE")
    }
    receipt_dir = ROOT / str(config["receipt_directory"])
    atomic_write(receipt_dir / f"{TASK_ID}.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if result["state"] == "COMPLETED" else 20


if __name__ == "__main__":
    raise SystemExit(main())
