#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "formalism-tvc-repository-transport.json"
RECEIPT_ROOT = (ROOT / "receipts" / "formalism-tvc-repository-transport").resolve()
TASK_ID = "SHWP-FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001"
CAPABILITY = "formalism_tvc_repository_transport"
CREDENTIAL_AUTHORITY = "TV/TVC"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def now_iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def request_id(prefix: str, payload: dict[str, Any]) -> str:
    return f"{prefix}-{canonical_hash(payload)[:20]}"


def bound_state_root() -> Path | None:
    raw = os.environ.get(BOUND_STATE_ENV, "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError("bound state root must be an absolute sandbox path")
    return path.resolve()


def source_requests(config: dict[str, Any], receipt: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    missing = result.get("missing") if isinstance(result.get("missing"), list) else []
    requests: list[dict[str, Any]] = []
    expires = now + timedelta(seconds=int(config["request_ttl_seconds"]))
    for repository in sorted(item for item in missing if isinstance(item, str) and "/" in item):
        payload = {
            "repository": repository,
            "base_ref": "main",
            "paths": ["README.md"],
            "destination_identity": str(Path(config["materialization_root"]) / repository),
        }
        requests.append({
            "schema": "stegverse.tvc-github-repository-inspection-request/v0.1",
            "request_id": request_id("inspect-source", payload),
            "operation_class": "INSPECT_REPOSITORY_STATE",
            "repository": repository,
            "base_ref": "main",
            "paths": ["README.md"],
            "credential_authority": CREDENTIAL_AUTHORITY,
            "consumer_credential_present": False,
            "secret_values_present": False,
            "issued_at": now_iso(now),
            "expires_at": now_iso(expires),
            "source_receipt_ref": config["source_discovery_receipt"],
            "next_operation_on_receipt": "MATERIALIZE_SOURCE_ARCHIVE",
            "destination_identity": payload["destination_identity"],
            "maximum_total_bytes": int(config["max_materialization_bytes"]),
            "authority_effect": "NONE_REQUEST_ONLY",
        })
    return requests


def owner_requests(config: dict[str, Any], owner_dir: Path, now: datetime) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    if not owner_dir.is_dir():
        return requests
    expires = now + timedelta(seconds=int(config["request_ttl_seconds"]))
    for path in sorted(owner_dir.glob("*.json")):
        manifest = load(path)
        if manifest.get("schema") != "stegverse.owner-implementation-work-manifest/v0.1":
            continue
        if manifest.get("claim_state") != "READY_FOR_SEPARATE_OWNER_ADMISSION":
            continue
        repository = manifest.get("owner_repository")
        proposed_paths = manifest.get("proposed_paths")
        if not isinstance(repository, str) or "/" not in repository or not isinstance(proposed_paths, list) or not proposed_paths:
            continue
        payload = {
            "repository": repository,
            "base_ref": "main",
            "paths": sorted(item for item in proposed_paths if isinstance(item, str)),
            "delta_id": manifest.get("delta_id"),
        }
        requests.append({
            "schema": "stegverse.tvc-github-repository-inspection-request/v0.1",
            "request_id": request_id("inspect-owner", payload),
            "operation_class": "INSPECT_REPOSITORY_STATE",
            "repository": repository,
            "base_ref": "main",
            "paths": payload["paths"],
            "credential_authority": CREDENTIAL_AUTHORITY,
            "consumer_credential_present": False,
            "secret_values_present": False,
            "issued_at": now_iso(now),
            "expires_at": now_iso(expires),
            "source_owner_work_ref": path.relative_to(ROOT).as_posix(),
            "delta_id": manifest.get("delta_id"),
            "next_operation_on_receipt": "OWNER_MUTATION_PREPARE",
            "authority_effect": "NONE_REQUEST_ONLY",
        })
    return requests


def inbox_receipts(state_root: Path | None) -> list[dict[str, Any]]:
    if state_root is None:
        return []
    inbox = state_root / "inbox"
    if not inbox.is_dir():
        return []
    receipts: list[dict[str, Any]] = []
    for path in sorted(inbox.glob("*.json")):
        try:
            value = load(path)
        except Exception:
            continue
        if value.get("credential_authority") != CREDENTIAL_AUTHORITY:
            continue
        if value.get("credential_value_exposed") is not False:
            continue
        if value.get("non_tv_tvc_secret_or_token_used") is not False:
            continue
        receipts.append(value)
    return receipts


def evaluate(config: dict[str, Any], now: datetime, *, state_root: Path | None = None) -> dict[str, Any]:
    broker = config.get("tvc_broker") if isinstance(config.get("tvc_broker"), dict) else {}
    observed_receipts = inbox_receipts(state_root)
    if broker.get("canonical_required") is True and broker.get("standing") != "CANONICAL_VALIDATED":
        return {
            "state": "BLOCKED",
            "reason": "TVC_BROKER_NOT_CANONICAL_VALIDATED",
            "requests": [],
            "observed_tvc_receipts": observed_receipts,
            "broker": broker,
            "credential_authority": CREDENTIAL_AUTHORITY,
            "consumer_credential_present": False,
            "github_token_required": False,
            "bound_state_available": state_root is not None,
            "authority_effect": "NONE_TRANSPORT_NOT_ADMITTED",
        }

    source_path = ROOT / str(config["source_discovery_receipt"])
    source_receipt = load(source_path) if source_path.is_file() else {"result": {"missing": []}}
    owner_dir = ROOT / str(config["owner_work_directory"])
    requests = source_requests(config, source_receipt, now) + owner_requests(config, owner_dir, now)
    return {
        "state": "COMPLETED" if requests else "BLOCKED",
        "reason": "TRANSPORT_REQUESTS_READY" if requests else "NO_ACTIONABLE_TRANSPORT_INPUTS",
        "requests": requests,
        "request_count": len(requests),
        "observed_tvc_receipts": observed_receipts,
        "observed_tvc_receipt_count": len(observed_receipts),
        "credential_authority": CREDENTIAL_AUTHORITY,
        "consumer_credential_present": False,
        "github_token_required": False,
        "bound_state_available": state_root is not None,
        "authority_effect": "NONE_NONSECRET_REQUEST_EMISSION_ONLY",
    }


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
    if "requests/tvc-repository-operations/**" not in allowed or "receipts/formalism-tvc-repository-transport/**" not in allowed:
        return 7

    config = load(CONFIG_PATH)
    if config.get("schema") != "stegverse.formalism-tvc-repository-transport/v0.1":
        return 8
    if config.get("credential_authority") != CREDENTIAL_AUTHORITY or config.get("github_token_required") is not False or config.get("consumer_secret_or_token_authority") is not False:
        return 9

    state_root = bound_state_root()
    now = datetime.now(timezone.utc)
    result = evaluate(config, now, state_root=state_root)
    request_dir = (ROOT / str(config["request_directory"])).resolve()
    if result["state"] == "COMPLETED":
        for request in result["requests"]:
            atomic_write(request_dir / f"{request['request_id']}.json", request)
            if state_root is not None:
                atomic_write(state_root / "outbox" / f"{request['request_id']}.json", request)

    receipt = {
        "schema": "stegverse.formalism-tvc-repository-transport-receipt/v0.1",
        "goal_id": config["goal_id"],
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": fence,
        "generated_at": now_iso(now),
        "state": result["state"],
        "transition_id": f"FORMALISM_TVC_REPOSITORY_TRANSPORT_{result['state']}",
        "result": result,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "consumer_credential_present": False,
        "github_token_required": False,
        "bound_state_used": state_root is not None,
        "bound_state_authoritative_path_observed": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_NONSECRET_REQUEST_EMISSION_ONLY",
    }
    atomic_write(RECEIPT_ROOT / f"{TASK_ID}.json", receipt)

    blocker = None
    if result["state"] != "COMPLETED":
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": result["reason"],
            "solution_required": True,
            "may_remain_blocked": True,
            "next_solution_action": "RECHECK_TVC_BROKER_STANDING_FORMALISM_INPUTS_AND_LOCAL_SPOOL",
            "machine_observable_release_condition": "TVC broker standing is CANONICAL_VALIDATED, bounded local spool is available, and an actionable missing-source or owner-work input is present"
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": result["state"],
        "transition_id": receipt["transition_id"],
        "transition_sequence": 1,
        "expected_next_transition": None if result["state"] == "COMPLETED" else "FORMALISM_TVC_REPOSITORY_TRANSPORT_RECHECK",
        "expected_next_earliest_epoch": None if result["state"] == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if result["state"] == "COMPLETED" else epoch + 1,
        "checkpoint_ref": f"receipts/formalism-tvc-repository-transport/{TASK_ID}.json",
        "evidence_refs": ["FORMALISM_TVC_REPOSITORY_TRANSPORT_CONSUMERS_MIRROR_HANDOFF.md", "FORMALISM_TVC_LOCAL_SPOOL_MIRROR_HANDOFF.md", "control/formalism-tvc-repository-transport.json"],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "formalism_tvc_repository_transport"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
