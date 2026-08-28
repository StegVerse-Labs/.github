#!/usr/bin/env python3
"""Consume one bounded SV-DN-1 resident execution request after local source refresh."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/sv-dn1-first-round-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/sv-dn1-resident-execution-request-consumption.latest.json")
TARGET_TASK = "SV-DN1-SOVEREIGN-EXECUTION-CHAIN-001"
TARGET_MODE = "SV_DN1_FIRST_ROUND_CHAIN"
TARGET_ENTRYPOINT = "scripts/run_sv_dn1_first_round_chain.py"
MINIMUM_FENCE_EXCLUSIVE = 22

HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
GITHUB_AUTH_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
)
FORBIDDEN_PROVIDER_ENV = (
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AZURE_CLIENT_SECRET", "OAUTH_TOKEN",
)
NONSECRET_FORWARD = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_SV_DN1_SOURCE_ROOT", "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT", "STEGVERSE_SV_DN1_INTR_STATE_ROOT",
    "STEGVERSE_SDK_SOURCE_ROOT", "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
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
            raise RuntimeError(f"SV-DN-1 resident execution request {key} mismatch")
    if request.get("fresh_fence_minimum_exclusive") != MINIMUM_FENCE_EXCLUSIVE:
        raise RuntimeError("SV-DN-1 resident request fresh-fence floor mismatch")
    if request.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("SV-DN-1 resident request may not grant heartbeat authority")
    if request.get("github_token_required") is not False:
        raise RuntimeError("SV-DN-1 resident request may not require GitHub token")
    if request.get("second_machine_required") is not False:
        raise RuntimeError("SV-DN-1 resident request may not require a second machine")
    if request.get("network_source_fetch_allowed") is not False:
        raise RuntimeError("request itself may not grant network acquisition authority")
    if request.get("request_granted_authority") is not False:
        raise RuntimeError("resident request cannot grant execution authority")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise RuntimeError("resident request id missing")


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume SV-DN-1 sovereign request: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_FORWARD if values.get(name)}
    for name in GITHUB_AUTH_ENV + FORBIDDEN_PROVIDER_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def previously_consumed(runtime: Path, request: Mapping[str, Any], request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    result = receipt.get("execution_result")
    return (
        receipt.get("request_id") == request.get("request_id")
        and receipt.get("request_sha256") == request_hash
        and receipt.get("runtime_execution_attempted") is True
        and isinstance(result, dict)
        and result.get("state") == "COMPLETE"
        and result.get("transition_id") == "SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE"
    )


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    temp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.sv-dn1.resident-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if previously_consumed(runtime, request, request_hash):
        return {
            "schema": "stegverse.sv-dn1.resident-request-consumption/v1",
            "state": "ALREADY_CONSUMED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"SV-DN-1 sovereign chain entrypoint missing: {entrypoint}")

    command = [
        sys.executable,
        str(entrypoint),
        "--source-root",
        str(source),
        "--runtime-root",
        str(runtime),
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=clean_exec_env(env),
        timeout=900,
    )

    result = None
    for line in reversed([line.strip() for line in completed.stdout.splitlines() if line.strip()]):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            result = candidate
            break

    receipt = {
        "schema": "stegverse.sv-dn1.resident-request-consumption/v1",
        "state": "ATTEMPT_RECORDED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "request_granted_authority": False,
        "fresh_fence_minimum_exclusive": MINIMUM_FENCE_EXCLUSIVE,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "network_authority_granted_by_request": False,
        "repository_writeback_authority": False,
        "publication_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume one bounded SV-DN-1 sovereign first-round request.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    if receipt["state"] in {"NO_REQUEST", "ALREADY_CONSUMED"}:
        return 0
    return 0 if receipt.get("execution_result_observed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
