#!/usr/bin/env python3
"""Consume one bounded resident execution request after local source refresh.

The request is intent, not authority. This consumer never grants a claim, fence,
credential, heartbeat authority, or execution permission. It may only invoke the
already-installed dedicated Ecosystem Chat parent executor path, whose own
authorization and fresh-fence checks remain authoritative.

The canonical request lives in the multi-request resident registry so unrelated
resident tasks cannot overwrite it. A request id + content hash is consumed at
most once on a resident runtime. A failed or blocked attempt therefore cannot
loop merely because another source path changes. A new attempt requires a new
canonical request id/content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/ecosystem-chat-parent-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/resident-execution-request-consumption.latest.json")
TARGET_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
TARGET_MODE = "DEDICATED_ECOSYSTEM_CHAT_PARENT"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
MINIMUM_FENCE_EXCLUSIVE = 24


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"resident execution request {key} mismatch")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise RuntimeError("resident execution request_id missing")
    if request.get("fresh_fence_minimum_exclusive") != MINIMUM_FENCE_EXCLUSIVE:
        raise RuntimeError("resident execution request fresh-fence floor mismatch")
    if request.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("resident execution request may not grant heartbeat authority")
    if request.get("github_token_required") is not False:
        raise RuntimeError("resident execution request may not require GitHub token")
    if request.get("second_machine_required") is not False:
        raise RuntimeError("resident execution request may not require a second user machine")
    if request.get("network_source_fetch_allowed") is not False:
        raise RuntimeError("resident execution request may not authorize network source fetch")


def previously_consumed(runtime_root: Path, request: dict[str, Any], request_hash: str) -> bool:
    path = runtime_root / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    return (
        receipt.get("request_id") == request.get("request_id")
        and receipt.get("request_sha256") == request_hash
        and receipt.get("runtime_execution_attempted") is True
    )


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if previously_consumed(runtime, request, request_hash):
        return {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "ALREADY_CONSUMED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"resident execution entrypoint missing: {entrypoint}")

    command = [
        sys.executable,
        str(entrypoint),
        "--source-root",
        str(source),
        "--runtime-root",
        str(runtime),
        "--ecosystem-chat-parent",
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=dict(os.environ),
    )
    result: dict[str, Any] | None = None
    for line in reversed([line.strip() for line in completed.stdout.splitlines() if line.strip()]):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            result = candidate
            break

    projection = {"attempted": False, "state": "NOT_ELIGIBLE", "reason": "PARENT_NOT_TERMINAL_PASS"}
    llm_root_raw = os.environ.get("STEGVERSE_LLM_ADAPTER_ROOT", "").strip()
    terminal_pass = bool(
        isinstance(result, dict)
        and result.get("state") == "PASS"
        and result.get("same_execution") is True
        and result.get("persistent_conversational_runtime_ready") is True
    )
    if terminal_pass and llm_root_raw:
        llm_root = Path(llm_root_raw).expanduser().resolve()
        projector = llm_root / "scripts/project_independent_parent_activation.py"
        output = llm_root / "receipts/ecosystem-chat-sovereign-activation.verified.json"
        if projector.is_file():
            projected = runner(
                [sys.executable, str(projector), "--control-root", str(runtime), "--output", str(output)],
                cwd=llm_root,
                capture_output=True,
                text=True,
                check=False,
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
                },
            )
            projection = {
                "attempted": True,
                "state": "VERIFIED" if projected.returncode == 0 and output.is_file() else "FAIL_CLOSED",
                "returncode": projected.returncode,
                "output": str(output),
                "authority_effect": "NONE",
            }
        else:
            projection = {"attempted": False, "state": "NOT_AVAILABLE", "reason": "LLM_ADAPTER_PROJECTOR_NOT_MATERIALIZED"}
    elif terminal_pass:
        projection = {"attempted": False, "state": "NOT_AVAILABLE", "reason": "LLM_ADAPTER_ROOT_NOT_MATERIALIZED"}

    receipt = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "ATTEMPT_RECORDED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "post_parent_activation_projection": projection,
        "runtime_execution_attempted": True,
        "request_granted_authority": False,
        "fresh_fence_minimum_exclusive": MINIMUM_FENCE_EXCLUSIVE,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    receipt_path = runtime / CONSUMPTION_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume one bounded resident execution request.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    if receipt["state"] in {"NO_REQUEST", "ALREADY_CONSUMED"}:
        return 0
    return 0 if receipt.get("runtime_execution_attempted") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
