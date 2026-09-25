#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/sdk-tt-richard-seam-authentic-runtime-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime-targeted-request-consumption.latest.json")
IMMUTABLE_CONSUMPTION_DIR_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/targeted-consumption")
CLOSE_LATEST_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/close.latest.json")
TARGET_TASK = "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"
TARGET_VECTOR = "20010000110000"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ENDPOINT", "STEGVERSE_MASTER_RECORDS_TOKEN", "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
    "STEGVERSE_ORG_LEDGER_ROOT",
    "MASTER_RECORDS_DB", "MASTER_RECORDS_RECEIPT_KEY", "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
    "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_SDK_SOURCE_ROOT", "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_WARRANT_JSON", "TV_POLICY_BUNDLE_SHA256", "TV_WARRANT_ISSUER_PUBKEY_B64", "TV_WARRANT_MAX_TTL_SECONDS",
)
FORBIDDEN = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ZAI_API_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object:{path}")
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume Test 3 Richard-seam targeted request:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "cosv_profile": "task.v1",
        "cosv_task_vector": TARGET_VECTOR,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive": 0,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "provider_credential_material_allowed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"Test 3 Richard-seam targeted request {key} mismatch")
    if request.get("argv") != ["--task-id", TARGET_TASK, "--cosv-task-vector", TARGET_VECTOR]:
        raise RuntimeError("Test 3 Richard-seam targeted request argv mismatch")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.sdk-tt-richard-seam-targeted-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"targeted execution entrypoint missing:{entrypoint}")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK, "--cosv-task-vector", TARGET_VECTOR]
    executions: list[dict[str, Any]] = []
    completed = None
    result = None
    pointer_verified = False
    first_failed_cycle = None
    close_observed_in_attempt = False
    close_path = runtime / CLOSE_LATEST_REL
    # The latest pointer can predate this bounded invocation. A stale close
    # is diagnostic history, not a reason to skip the fresh governed close.
    try:
        previous_close = stable_hash(load_json(close_path)) if close_path.is_file() else None
    except (OSError, ValueError):
        # Unreadable historical latest is not current-run governed closure.
        previous_close = None
    for cycle_index in range(2):
        try:
            completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(env), timeout=1800)
        except Exception as exc:
            # Retain the first invocation boundary instead of letting an
            # exception bypass the immutable targeted-consumption receipt.
            # This proves only a local invocation failure, never worker
            # execution or an authenticated governed transition.
            completed = None
            result = None
            pointer_verified = False
            first_failed_cycle = {
                "cycle_index": cycle_index,
                "boundary": "TARGETED_SUBPROCESS_INVOCATION_EXCEPTION",
                "exception_type": type(exc).__name__,
                "returncode": None,
            }
            executions.append({
                "cycle_index": cycle_index,
                "returncode": None,
                "result": None,
                "pointer_binding_verified": False,
                "cycle_valid": False,
            })
            break
        result = parse_last_json(completed.stdout)
        pointer = result.get("cosv_task_pointer") if isinstance(result, dict) else None
        pointer_verified = bool(
            isinstance(pointer, dict)
            and pointer.get("task_id") == TARGET_TASK
            and pointer.get("vector") == TARGET_VECTOR
            and pointer.get("binding_verified") is True
            and pointer.get("authority_effect") == "NONE"
        )
        result_valid = bool(
            isinstance(result, dict)
            and result.get("mode") == TARGET_MODE
            and result.get("task_id") == TARGET_TASK
            and result.get("runtime_execution_attempted") is True
            and result.get("network_fetch_performed") is False
            and result.get("github_token_runtime_authority") == "NONE"
            and result.get("credential_authority") == "TV/TVC"
            and result.get("authority_effect") == "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"
        )
        cycle_valid = completed.returncode == 0 and result_valid and pointer_verified
        executions.append({
            "cycle_index": cycle_index,
            "returncode": completed.returncode,
            "result": result,
            "pointer_binding_verified": pointer_verified,
            "cycle_valid": cycle_valid,
        })
        if not cycle_valid:
            first_failed_cycle = {
                "cycle_index": cycle_index,
                "boundary": (
                    "PROCESS_EXIT_NONZERO" if completed.returncode != 0
                    else "TARGETED_RESULT_OR_COSV_POINTER_INVALID"
                ),
                "returncode": completed.returncode,
            }
            # Do not conceal the first observed process/identity failure by
            # driving another invocation. This is a local attempt diagnostic,
            # NOT an authenticated org-level failed transition.
            break
        if close_path.is_file():
            try:
                close_receipt = load_json(close_path)
            except (OSError, ValueError):
                close_receipt = {}
            if (
                close_receipt.get("state") == "AUTHENTIC_TASK_CLOSED_WORKER_RETIRED_RECORDS_ONLY"
                and close_receipt.get("task_id") == TARGET_TASK
                and stable_hash(close_receipt) != previous_close
            ):
                close_observed_in_attempt = True
                # Stop condition only; actual governance and Master Records
                # closure require separate authoritative reconstruction.
                break

    valid = bool(executions and all(row["cycle_valid"] for row in executions))
    receipt = {
        "schema": "stegverse.sdk-tt-richard-seam-targeted-consumption/v1",
        "state": "ATTEMPT_RECORDED" if valid else "FAIL_CLOSED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "cosv_task_vector": TARGET_VECTOR,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode if completed is not None else None,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "targeted_cycle_count": len(executions),
        "targeted_cycles": executions,
        "bounded_cycle_limit": 2,
        "first_failed_cycle": first_failed_cycle,
        "fresh_close_snapshot_seen": close_observed_in_attempt,
        "pointer_binding_verified_before_execution": pointer_verified,
        "runtime_execution_attempted": True,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "provider_credential_material_allowed": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_CONSUMPTION_ONLY",
    }
    # Preserve every actual result, including earliest failure, before replacing latest.
    body_sha256 = stable_hash(receipt)
    receipt["receipt_body_sha256"] = "sha256:" + body_sha256
    immutable = runtime / IMMUTABLE_CONSUMPTION_DIR_REL / (body_sha256 + ".json")
    immutable.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if immutable.exists():
        if immutable.read_text(encoding="utf-8") != encoded:
            raise RuntimeError("immutable Richard consumption receipt collision")
    else:
        immutable.write_text(encoded, encoding="utf-8")
    destination = runtime / CONSUMPTION_REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(encoded, encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] in {"NO_REQUEST", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
