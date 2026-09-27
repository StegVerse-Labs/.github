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
        # An earlier attempted invocation is not evidence of completion. Read the
        # original retained local diagnostic; do not rerun unchanged source or
        # invent a successor claim, manifest, receipt, or downstream disposition.
        previous = load_json(runtime / CONSUMPTION_REL)
        previous_allow = previous.get("disposition") == "ALLOW"
        return {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "ALREADY_CONSUMED" if previous_allow else "ALREADY_CONSUMED_NON_ALLOW",
            "disposition": "ALLOW" if previous_allow else "FAIL_CLOSED",
            "disposition_scope": "CONSUMER_REPLAY_PROTECTION_ONLY",
            "consequence_committed": False,
            "failed_predicate": None if previous_allow else (
                previous.get("failed_predicate") or "EARLIER_ATTEMPT_OUTCOME_NOT_VERIFIED"
            ),
            "retry_entrypoint": None if previous_allow else "EXISTING_MANIFEST_BOUND_OWNER_CORRECTION",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "previous_execution_receipt_path": str(runtime / CONSUMPTION_REL),
            "authentic_intr_disposition_observed_by_consumer": False,
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

    # The portable bridge returns an outer resident-refresh envelope. The actual
    # parent returns COMPLETED/HANDOFF_READY one level deeper; only its
    # independently reconstructed activation receipt has state PASS. An attempt
    # or a subprocess return code cannot be promoted to completed execution.
    bridge_ok = bool(
        completed.returncode == 0
        and isinstance(result, dict)
        and result.get("schema") == "stegverse.resident-refresh-targeted-execution/v3"
        and result.get("task_id") == TARGET_TASK
        and result.get("mode") == TARGET_MODE
        and result.get("execution_returncode") == 0
        and result.get("execution_result_observed") is True
    )
    parent_result = result.get("execution_result") if bridge_ok else None
    parent_ok = isinstance(parent_result, dict) and (
        parent_result.get("schema") == "stegverse.independent-ecosystem-chat-parent-execution/v1"
        and parent_result.get("task_id") == TARGET_TASK
        and parent_result.get("state") == "COMPLETED"
        and isinstance(parent_result.get("attempt_fencing_token"), int)
        and parent_result["attempt_fencing_token"] > MINIMUM_FENCE_EXCLUSIVE
    )
    activation = parent_result.get("terminal_activation_receipt") if parent_ok else None
    terminal_pass = bool(
        parent_ok and isinstance(activation, dict)
        and activation.get("schema") == "stegverse.ecosystem-chat-independent-parent-activation/v1"
        and activation.get("task_id") == TARGET_TASK
        and activation.get("state") == "PASS"
        and activation.get("fencing_token") == parent_result["attempt_fencing_token"]
        and all(activation.get(key) is True for key in (
            "sovereign_runtime_execution_surface_observed",
            "ephemeral_e1_e2_execution_observed",
            "measured_usage_persisted",
            "provider_usage_reconstruction_pass",
            "transition_reconstruction_pass",
            "same_execution",
            "persistent_conversational_runtime_ready",
        ))
        and activation.get("credential_authority") == "TV/TVC"
        and activation.get("github_token_required") is False
    )
    projection = {"attempted": False, "state": "NOT_ELIGIBLE",
                  "reason": "PARENT_NOT_TERMINAL_PASS"}
    llm_root_raw = os.environ.get("STEGVERSE_LLM_ADAPTER_ROOT", "").strip()
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

    # This is a consumer-boundary outcome only. A source check, child JSON
    # envelope or successful process exit cannot impersonate native InTr ALLOW.
    if not bridge_ok:
        failure_code = "PORTABLE_BRIDGE_RESULT_NOT_VERIFIED"
    elif not terminal_pass:
        failure_code = "PARENT_TERMINAL_RECONSTRUCTION_NOT_VERIFIED"
    elif projection.get("state") != "VERIFIED":
        failure_code = "ACTIVATION_EVIDENCE_PROJECTION_NOT_VERIFIED"
    else:
        failure_code = None
    disposition = "ALLOW" if failure_code is None else "FAIL_CLOSED"

    receipt = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "ATTEMPT_RECORDED",
        "disposition": disposition,
        "disposition_scope": "CONSUMER_RETURN_AND_ACTIVATION_PROJECTION_ONLY",
        "consequence_committed": failure_code is None,
        "failed_predicate": failure_code,
        "retry_entrypoint": None if failure_code is None else "EXISTING_MANIFEST_BOUND_OWNER_CORRECTION",
        "next_attempt": None if failure_code is None else "REPAIR_FIRST_PROVEN_FAILED_STAGE_WITH_NEW_ADMITTED_MANIFEST",
        "upstream_parent_terminal_claim_observed": terminal_pass,
        "upstream_parent_receipt_sha256_verified_by_consumer": False,
        "authentic_intr_disposition_observed_by_consumer": False,
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
    return 0 if receipt.get("disposition") == "ALLOW" or receipt["state"] in {"NO_REQUEST", "ALREADY_CONSUMED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
