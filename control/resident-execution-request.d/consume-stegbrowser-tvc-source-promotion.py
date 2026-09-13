#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

REQUEST_REL = Path("control/resident-execution-request.d/stegbrowser-tvc-source-promotion-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json")
PRIVATE_SOURCE_REL = Path("tvc-handoff/private-source-request.json")
TASK_ID = "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
MODE = "TVC_EXACT_SOURCE_PROMOTION_REQUEST"
ENTRYPOINT = "control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py"
SOURCE_REPOSITORY = "StegVerse-Labs/TVC"
TARGET_SHA = "aef6b6f5dc99d2a531718ca475d20858ae8e68a6"
MATERIALIZATION_ID = "stegbrowser-tvc-runtime-aef6b6f5"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object:{path}")
    return value


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def validate_request(value: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "source_repository": SOURCE_REPOSITORY,
        "reference_mode": "IMMUTABLE_COMMIT",
        "exact_sha": TARGET_SHA,
        "materialization_id": MATERIALIZATION_ID,
        "ttl_seconds": 900,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise RuntimeError(f"StegBrowser TVC source request {key} mismatch")
    if not isinstance(value.get("request_id"), str) or not value.get("request_id"):
        raise RuntimeError("StegBrowser TVC source request_id required")


def _private_source_request() -> dict[str, Any]:
    return {
        "caller_repository": "StegVerse-Labs/.github",
        "source_repository": SOURCE_REPOSITORY,
        "consumer_task": TASK_ID,
        "reference_mode": "IMMUTABLE_COMMIT",
        "exact_ref": "commit:" + TARGET_SHA,
        "exact_sha": TARGET_SHA,
        "materialization_id": MATERIALIZATION_ID,
        "ttl_seconds": 900,
    }


def _same_identity(value: Mapping[str, Any]) -> bool:
    return (
        value.get("caller_repository") == "StegVerse-Labs/.github"
        and value.get("source_repository") == SOURCE_REPOSITORY
        and value.get("consumer_task") == TASK_ID
        and value.get("reference_mode") == "IMMUTABLE_COMMIT"
    )


def consume(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    request = _load(request_path if request_path.is_file() else source / REQUEST_REL)
    validate_request(request)
    desired = _private_source_request()
    target = runtime / PRIVATE_SOURCE_REL
    staged = False
    restaged = False
    outcome = "STAGED"
    reason = None

    if target.is_file():
        existing = _load(target)
        if existing == desired:
            outcome = "ALREADY_STAGED"
        elif _same_identity(existing):
            _atomic(target, desired)
            restaged = True
            outcome = "RESTAGED_EXACT_SOURCE"
        else:
            outcome = "HANDOFF_READY"
            reason = "PRIVATE_SOURCE_REQUEST_SLOT_OCCUPIED_BY_OTHER_TASK"
    else:
        _atomic(target, desired)
        staged = True

    receipt = {
        "schema": "stegverse.stegbrowser-tvc-source-promotion-request-consumption/v1",
        "state": "ATTEMPT_RECORDED",
        "outcome": outcome,
        "request_id": request["request_id"],
        "request_sha256": _hash(request),
        "task_id": TASK_ID,
        "private_source_request_path": str(target),
        "private_source_request_sha256": _hash(desired),
        "source_repository": SOURCE_REPOSITORY,
        "exact_sha": TARGET_SHA,
        "materialization_id": MATERIALIZATION_ID,
        "request_staged": staged,
        "request_restaged": restaged,
        "retry_allowed": outcome == "HANDOFF_READY",
        "pending_reason": reason,
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "network_source_fetch_performed": False,
        "systemd_service_start_requested": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    _atomic(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        result = {
            "schema": "stegverse.stegbrowser-tvc-source-promotion-request-consumption/v1",
            "state": "BLOCKED",
            "reason": str(exc),
            "task_id": TASK_ID,
            "credential_material_present": False,
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") == "ATTEMPT_RECORDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
