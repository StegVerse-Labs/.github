#!/usr/bin/env python3
"""Consume the non-authorizing KV AI memory resident execution request.

The consumer never reads private packet/prompt bytes itself. When the packet and
provider-request input exist but the admission is absent, it may invoke the
resident-local shared-InTr submitter as a separate process. Only an authentic
returned ingress receipt may create the admission file; otherwise the consumer
remains in a wait state. Once all inputs exist it delegates to the existing
WorkerCoordinator path.
"""
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
REQUEST_REL = Path("control/resident-execution-request.d/kv-ai-memory-resident-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/kv-ai-memory-resident-request-consumption.latest.json")
TARGET_TASK = "SV-KV-AI-PERSISTENCE-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
BOUND_STATE_REL = Path(".stegverse/state/kv-ai-memory-resident")
PACKET_INPUT = Path("inputs/context-packet.json")
ADMISSION_INPUT = Path("inputs/memory-packet-admission.json")
PROVIDER_INPUT = Path("inputs/provider-request-input.json")
REQUIRED_INPUTS = (PACKET_INPUT, ADMISSION_INPUT, PROVIDER_INPUT)
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
NONSECRET_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT", "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL")
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "ACTIONS_RUNTIME_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "ZAI_API_KEY", "KIMI_API_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
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
        "private_content_in_request": False,
        "bound_state_root": "~/.stegverse/state/kv-ai-memory-resident",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise RuntimeError(f"KV AI memory resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"]:
        raise RuntimeError("KV AI memory resident request_id missing")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume sovereign KV AI memory request: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def bound_state_root(env: Mapping[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    home = str(values.get("HOME") or "").strip()
    if not home:
        raise RuntimeError("HOME required to resolve fenced KV AI memory bound state")
    return Path(home).expanduser().resolve() / BOUND_STATE_REL


def input_readiness(env: Mapping[str, str] | None = None) -> tuple[bool, list[str]]:
    root = bound_state_root(env)
    missing = [path.as_posix() for path in REQUIRED_INPUTS if not (root / path).is_file()]
    return not missing, missing


def admission_inputs_ready(env: Mapping[str, str] | None = None) -> bool:
    root = bound_state_root(env)
    return (root / PACKET_INPUT).is_file() and (root / PROVIDER_INPUT).is_file() and not (root / ADMISSION_INPUT).is_file()


def previously_consumed(runtime: Path, request: dict[str, Any], request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_object(path)
    except Exception:
        return False
    return receipt.get("request_id") == request.get("request_id") and receipt.get("request_sha256") == request_hash and receipt.get("runtime_execution_attempted") is True


def last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def attempt_memory_packet_admission(source: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    ingress_url = str(values.get("STEGVERSE_UNIVERSAL_INTR_INGRESS_URL") or "").strip()
    if not ingress_url:
        return {
            "state": "INGRESS_NOT_READY",
            "admission_attempted": False,
            "private_input_bytes_read_by_consumer": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    preparer = source / "scripts/prepare_kv_ai_memory_intr_runtime_source.py"
    router = source / "workers/universal_intr_profiled_ingress.py"
    submitter = source / "scripts/submit_kv_ai_memory_packet_local.py"
    for path in (preparer, router, submitter):
        if not path.is_file():
            raise RuntimeError(f"KV AI memory admission source missing: {path}")
    sanitized = clean_env(values)
    prepared = runner([sys.executable, str(preparer), "--source-root", str(source)], cwd=source, capture_output=True, text=True, check=False, env=sanitized, timeout=120)
    if prepared.returncode != 0:
        return {
            "state": "ROUTE_PREPARATION_FAILED",
            "admission_attempted": False,
            "route_preparation_returncode": prepared.returncode,
            "private_input_bytes_read_by_consumer": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    preparation = last_json(prepared.stdout)
    if not isinstance(preparation, dict) or preparation.get("state") not in {"ROUTE_INSTALLED_LOCAL_SOURCE", "ROUTE_ALREADY_INSTALLED"}:
        return {
            "state": "ROUTE_PREPARATION_RESULT_INVALID",
            "admission_attempted": False,
            "route_preparation_returncode": prepared.returncode,
            "private_input_bytes_read_by_consumer": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    stage = bound_state_root(values)
    submitted = runner([sys.executable, str(submitter), "--stage-root", str(stage)], cwd=source, capture_output=True, text=True, check=False, env=sanitized, timeout=30)
    result = last_json(submitted.stdout)
    return {
        "state": result.get("state") if isinstance(result, dict) else "SUBMISSION_RESULT_UNREADABLE",
        "admission_attempted": True,
        "route_preparation_state": preparation.get("state"),
        "submission_returncode": submitted.returncode,
        "admission_written": bool(isinstance(result, dict) and result.get("admission_written") is True),
        "receipt_hash": result.get("receipt_hash") if isinstance(result, dict) else None,
        "private_input_bytes_read_by_consumer": False,
        "authority_effect": "NONE_ADMISSION_ATTEMPT_ONLY",
    }


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.kv-ai-memory.resident-request-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    request = load_object(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if previously_consumed(runtime, request, request_hash):
        return {"schema": "stegverse.kv-ai-memory.resident-request-consumption/v1", "state": "ALREADY_CONSUMED", "request_id": request["request_id"], "request_sha256": request_hash, "runtime_execution_attempted": False, "authority_effect": "NONE"}

    admission_attempt = None
    if admission_inputs_ready(env):
        admission_attempt = attempt_memory_packet_admission(source, runner=runner, env=env)

    ready, missing = input_readiness(env)
    if not ready:
        return {
            "schema": "stegverse.kv-ai-memory.resident-request-consumption/v1",
            "state": "BOUND_STATE_INPUT_NOT_READY",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "missing_input_refs": missing,
            "admission_attempt": admission_attempt,
            "private_input_bytes_read": False,
            "runtime_execution_attempted": False,
            "request_granted_authority": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError("KV AI memory resident entrypoint missing")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(env), timeout=1800)
    result = last_json(completed.stdout)
    valid = bool(
        isinstance(result, dict)
        and result.get("task_id") == TARGET_TASK
        and result.get("runtime_execution_attempted") is True
        and result.get("network_fetch_performed") is False
        and result.get("github_token_runtime_authority") == "NONE"
        and result.get("credential_authority") == "TV/TVC"
        and result.get("authority_effect") == "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"
    )
    receipt = {
        "schema": "stegverse.kv-ai-memory.resident-request-consumption/v1",
        "state": "ATTEMPT_RECORDED" if valid else "FAIL_CLOSED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "bridge_contract_valid": valid,
        "runtime_execution_attempted": True,
        "admission_attempt": admission_attempt,
        "private_input_bytes_read_by_consumer": False,
        "request_granted_authority": False,
        "activation_claimed": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    receipt_path = runtime / CONSUMPTION_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST", "ALREADY_CONSUMED", "BOUND_STATE_INPUT_NOT_READY", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
