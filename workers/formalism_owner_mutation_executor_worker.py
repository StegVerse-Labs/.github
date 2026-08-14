#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "formalism-owner-mutation-executor.json"
TASK_ID = "SHWP-FORMALISM-OWNER-MUTATION-EXECUTOR-001"
CAPABILITY = "formalism_owner_mutation_executor"
CREDENTIAL_AUTHORITY = "TV/TVC"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
OWNER_MANIFEST_SCHEMA = "stegverse.owner-implementation-work-manifest/v0.1"
SOURCE_PACKET_SCHEMA = "stegverse.owner-source-generation-packet/v0.1"
INSPECTION_RECEIPT_SCHEMA = "stegverse.tvc-github-repository-inspection-receipt/v0.1"
WARRANT_SCHEMA = "stegverse.tvc-github-repository-operation-warrant/v0.1"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def now_iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_repo_path(value: str) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return False
    normalized = posixpath.normpath(value)
    if normalized in {".", ".."} or normalized.startswith("../"):
        return False
    return normalized == value and not any(ch in value for ch in "*?[]")


def bound_state_root() -> Path | None:
    raw = os.environ.get(BOUND_STATE_ENV, "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError("bound state root must be absolute")
    return path.resolve()


def find_inspection_receipt(state_root: Path | None, *, repository: str, base_ref: str, expected_base_sha: str) -> dict[str, Any] | None:
    if state_root is None:
        return None
    inbox = state_root / "inbox"
    if not inbox.is_dir():
        return None
    matches: list[dict[str, Any]] = []
    for path in sorted(inbox.glob("*.json")):
        try:
            receipt = load(path)
        except Exception:
            continue
        if receipt.get("schema") != INSPECTION_RECEIPT_SCHEMA:
            continue
        if receipt.get("repository") != repository or receipt.get("base_ref") != base_ref or receipt.get("base_sha") != expected_base_sha:
            continue
        if receipt.get("credential_authority") != CREDENTIAL_AUTHORITY:
            continue
        if receipt.get("credential_value_exposed") is not False or receipt.get("non_tv_tvc_secret_or_token_used") is not False:
            continue
        matches.append(receipt)
    if len(matches) != 1:
        return None
    return matches[0]


def validate_source_packet(config: dict[str, Any], manifest: dict[str, Any], packet: dict[str, Any], state_root: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    if manifest.get("schema") != OWNER_MANIFEST_SCHEMA or manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
        return None, "OWNER_WORK_NOT_ADMITTED"
    if packet.get("schema") != SOURCE_PACKET_SCHEMA:
        return None, "SOURCE_PACKET_SCHEMA_INVALID"
    if packet.get("source_generation_authorized") is not True:
        return None, "SOURCE_GENERATION_NOT_AUTHORIZED"
    if not isinstance(packet.get("generator_authority_ref"), str) or not packet["generator_authority_ref"].strip():
        return None, "GENERATOR_AUTHORITY_REF_MISSING"
    if not isinstance(packet.get("generator_profile_ref"), str) or not packet["generator_profile_ref"].strip():
        return None, "GENERATOR_PROFILE_REF_MISSING"

    delta_id = manifest.get("delta_id")
    repository = manifest.get("owner_repository")
    if packet.get("delta_id") != delta_id or packet.get("owner_repository") != repository:
        return None, "OWNER_OR_DELTA_MISMATCH"
    proposed = manifest.get("proposed_paths")
    if not isinstance(proposed, list) or not proposed:
        return None, "OWNER_SCOPE_MISSING"
    proposed_set = set(item for item in proposed if isinstance(item, str))

    base_ref = packet.get("base_ref")
    expected_base_sha = packet.get("expected_base_sha")
    if not isinstance(base_ref, str) or not base_ref or not isinstance(expected_base_sha, str) or len(expected_base_sha) != 40:
        return None, "BASE_IDENTITY_INVALID"

    files = packet.get("files")
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
        })
    if total_bytes > int(config["maximum_total_bytes"]):
        return None, "SOURCE_TOTAL_BYTES_EXCEEDS_LIMIT"

    if config.get("require_handoff_first") is True:
        handoff_paths = sorted(path for path in proposed_set if path.endswith("_MIRROR_HANDOFF.md"))
        if not handoff_paths:
            return None, "ADMITTED_OWNER_HANDOFF_PATH_MISSING"
        first_path = normalized_files[0]["path"]
        if first_path not in handoff_paths:
            return None, "HANDOFF_NOT_FIRST_MUTATION"

    inspection = find_inspection_receipt(state_root, repository=repository, base_ref=base_ref, expected_base_sha=expected_base_sha)
    if config.get("require_exact_inspection_receipt") is True and inspection is None:
        return None, "EXACT_TVC_INSPECTION_RECEIPT_MISSING"

    branch_name = packet.get("new_branch")
    commit_message = packet.get("commit_message")
    if not isinstance(branch_name, str) or not branch_name.strip() or not isinstance(commit_message, str) or not commit_message.strip():
        return None, "BRANCH_OR_COMMIT_MESSAGE_MISSING"

    return {
        "delta_id": delta_id,
        "repository": repository,
        "base_ref": base_ref,
        "expected_base_sha": expected_base_sha,
        "new_branch": branch_name,
        "commit_message": commit_message,
        "files": normalized_files,
        "total_bytes": total_bytes,
        "generator_authority_ref": packet["generator_authority_ref"],
        "generator_profile_ref": packet["generator_profile_ref"],
        "source_packet_sha256": canonical_hash(packet),
        "owner_work_sha256": canonical_hash(manifest),
        "inspection_receipt_sha256": canonical_hash(inspection) if inspection is not None else None,
    }, None


def build_warrant(config: dict[str, Any], prepared: dict[str, Any], now: datetime) -> dict[str, Any]:
    payload = {
        "delta_id": prepared["delta_id"],
        "repository": prepared["repository"],
        "base_ref": prepared["base_ref"],
        "expected_base_sha": prepared["expected_base_sha"],
        "new_branch": prepared["new_branch"],
        "source_packet_sha256": prepared["source_packet_sha256"],
        "owner_work_sha256": prepared["owner_work_sha256"],
    }
    operation_id = f"owner-mutation-{canonical_hash(payload)[:20]}"
    expires = now + timedelta(seconds=int(config["request_ttl_seconds"]))
    return {
        "schema": WARRANT_SCHEMA,
        "operation_id": operation_id,
        "operation_class": "APPLY_BOUNDED_FILE_SET",
        "repository": prepared["repository"],
        "base_ref": prepared["base_ref"],
        "expected_base_sha": prepared["expected_base_sha"],
        "credential_authority": CREDENTIAL_AUTHORITY,
        "single_use": True,
        "secret_values_present": False,
        "consumer_credential_present": False,
        "issued_at": now_iso(now),
        "expires_at": now_iso(expires),
        "nonce": canonical_hash(payload)[:24],
        "authorization_ref": f"tvc://formalism-owner-mutation/{operation_id}",
        "new_branch": prepared["new_branch"],
        "maximum_file_count": int(config["maximum_file_count"]),
        "maximum_total_bytes": int(config["maximum_total_bytes"]),
        "commit_message": prepared["commit_message"],
        "files": prepared["files"],
        "authority_effect": "NONE_REQUEST_ONLY_TVC_AUTHORIZATION_REQUIRED",
        "source_generation_authority_ref": prepared["generator_authority_ref"],
        "source_generation_profile_ref": prepared["generator_profile_ref"],
        "source_packet_sha256": prepared["source_packet_sha256"],
        "owner_work_sha256": prepared["owner_work_sha256"],
        "inspection_receipt_sha256": prepared["inspection_receipt_sha256"],
    }


def evaluate(config: dict[str, Any], now: datetime, *, state_root: Path | None = None) -> dict[str, Any]:
    manifest_dir = ROOT / str(config["owner_work_directory"])
    packet_dir = ROOT / str(config["source_package_directory"])
    broker = config.get("tvc_broker") if isinstance(config.get("tvc_broker"), dict) else {}
    warrants: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    if not manifest_dir.is_dir():
        return {"state":"BLOCKED","reason":"OWNER_WORK_DIRECTORY_MISSING","warrants":[],"blocked":[],"authority_effect":"NONE"}

    for manifest_path in sorted(manifest_dir.glob("*.json")):
        manifest = load(manifest_path)
        if manifest.get("schema") != OWNER_MANIFEST_SCHEMA or manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
            continue
        delta_id = manifest.get("delta_id")
        packet_path = packet_dir / f"{delta_id}.json"
        if not packet_path.is_file():
            blocked.append({"delta_id":delta_id,"reason":"SOURCE_GENERATION_PACKET_MISSING","release_condition":f"{packet_path.relative_to(ROOT).as_posix()} exists with explicit source-generation authority"})
            continue
        packet = load(packet_path)
        prepared, error = validate_source_packet(config, manifest, packet, state_root)
        if error:
            blocked.append({"delta_id":delta_id,"reason":error})
            continue
        warrants.append(build_warrant(config, prepared, now))

    if not warrants:
        return {"state":"BLOCKED","reason":"NO_ADMISSIBLE_OWNER_MUTATION_WARRANTS","warrants":[],"blocked":blocked,"authority_effect":"NONE_FAIL_CLOSED"}

    live_projection_allowed = not bool(broker.get("canonical_required_for_live_projection")) or broker.get("standing") == "CANONICAL_VALIDATED"
    return {
        "state":"COMPLETED" if live_projection_allowed else "BLOCKED",
        "reason":"OWNER_MUTATION_WARRANTS_READY" if live_projection_allowed else "TVC_BROKER_NOT_CANONICAL_VALIDATED",
        "warrants":warrants,
        "blocked":blocked,
        "live_projection_allowed":live_projection_allowed,
        "credential_authority":CREDENTIAL_AUTHORITY,
        "consumer_credential_present":False,
        "non_tv_tvc_secret_or_token_used":False,
        "authority_effect":"NONE_NONSECRET_TVC_WARRANT_PREPARATION_ONLY"
    }


def persist_warrant(config: dict[str, Any], state_root: Path | None, warrant: dict[str, Any]) -> None:
    request_dir = ROOT / str(config["request_directory"])
    operation_id = warrant["operation_id"]
    target = request_dir / f"{operation_id}.json"
    if not target.exists():
        atomic_write(target, warrant)
    if state_root is not None:
        outbox = state_root / "outbox" / f"{operation_id}.json"
        inbox = state_root / "inbox" / f"{operation_id}.json"
        processed = state_root / "processed" / f"{operation_id}.json"
        if not outbox.exists() and not inbox.exists() and not processed.exists():
            atomic_write(outbox, warrant)


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID:
        return 4
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 6
    allowed = set(execution.get("allowed_paths") or [])
    if "receipts/formalism-owner-mutation-executor/**" not in allowed or "requests/tvc-repository-operations/**" not in allowed:
        return 7

    config = load(CONFIG_PATH)
    if config.get("schema") != "stegverse.formalism-owner-mutation-executor/v0.1":
        return 8
    if config.get("credential_authority") != CREDENTIAL_AUTHORITY or config.get("github_token_required") is not False or config.get("consumer_secret_or_token_authority") is not False:
        return 9

    now = datetime.now(timezone.utc)
    state_root = bound_state_root()
    result = evaluate(config, now, state_root=state_root)
    if result["state"] == "COMPLETED":
        for warrant in result["warrants"]:
            persist_warrant(config, state_root, warrant)

    receipt = {
        "schema":"stegverse.formalism-owner-mutation-executor-receipt/v0.1",
        "goal_id":config["goal_id"],
        "task_id":TASK_ID,
        "heartbeat_epoch":epoch,
        "claim_id":claim_id,
        "worker_id":task.get("worker_id"),
        "worker_instance_id":task.get("worker_instance_id"),
        "fencing_token":fence,
        "generated_at":now_iso(now),
        "state":result["state"],
        "transition_id":f"FORMALISM_OWNER_MUTATION_{result['state']}",
        "result":result,
        "credential_authority":CREDENTIAL_AUTHORITY,
        "github_token_required":False,
        "consumer_credential_present":False,
        "non_tv_tvc_secret_or_token_used":False,
        "direct_owner_mutation_performed":False,
        "heartbeat_grants_execution_authority":False,
        "authority_effect":"NONE_NONSECRET_TVC_WARRANT_PREPARATION_ONLY"
    }
    receipt_root = ROOT / str(config["receipt_directory"])
    atomic_write(receipt_root / f"{TASK_ID}.json", receipt)

    blocker = None
    if result["state"] != "COMPLETED":
        blocker = {
            "dependency_class":"INTERNAL_CAPABILITY",
            "problem_statement":result["reason"],
            "solution_required":True,
            "may_remain_blocked":True,
            "next_solution_action":"RECHECK_OWNER_WORK_SOURCE_PACKET_TVC_INSPECTION_AND_BROKER_STANDING",
            "machine_observable_release_condition":"Admitted owner work, explicit source-generation packet, exact TVC inspection receipt, and CANONICAL_VALIDATED TVC broker standing are simultaneously present"
        }
    response = {
        "schema":"stegverse.worker-response/v0.1",
        "state":result["state"],
        "transition_id":receipt["transition_id"],
        "transition_sequence":1,
        "expected_next_transition":None if result["state"] == "COMPLETED" else "FORMALISM_OWNER_MUTATION_RECHECK",
        "expected_next_earliest_epoch":None if result["state"] == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch":None if result["state"] == "COMPLETED" else epoch + 1,
        "checkpoint_ref":f"receipts/formalism-owner-mutation-executor/{TASK_ID}.json",
        "evidence_refs":["control/formalism-owner-mutation-executor.json", f"receipts/formalism-owner-mutation-executor/{TASK_ID}.json"],
        "blocker":blocker,
        "cost_observation":{"hb_transition_count":1,"compute_units":1,"external_cost_usd":0,"task_class":"formalism_owner_mutation_executor"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
