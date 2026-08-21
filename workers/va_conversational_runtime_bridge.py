#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any

CREDENTIAL_AUTHORITY = "TV/TVC"
FORBIDDEN_ENV = {
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
}


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _terminate(pid: int) -> None:
    if not _pid_alive(pid):
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    for _ in range(30):
        if not _pid_alive(pid):
            return
        time.sleep(0.05)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _readiness(endpoint: str) -> dict[str, Any] | None:
    try:
        request = urllib.request.Request(
            endpoint.rstrip("/") + "/api/va-claims/v1/readiness",
            headers={"accept": "application/json", "user-agent": "StegVerse-VA-Runtime-Bridge/1"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return value if isinstance(value, dict) else None


def load_state(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _child_env(adapter_root: Path, proof_path: Path, route_path: Path) -> dict[str, str]:
    source_registry = adapter_root / "va_claim_assistant" / "source-registry.site-projection.json"
    if not source_registry.is_file():
        raise RuntimeError("va_source_registry_projection_missing")
    env = {key: value for key, value in os.environ.items() if key not in FORBIDDEN_ENV}
    env["PYTHONPATH"] = str(adapter_root)
    env["STEGVERSE_CANONICAL_RUNTIME_PROOF_FILE"] = str(proof_path)
    env["STEGVERSE_TVC_ROUTE_RECEIPT_FILE"] = str(route_path)
    env["STEGVERSE_VA_SOURCE_REGISTRY_FILE"] = str(source_registry)
    env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"] = "NONE"
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = CREDENTIAL_AUTHORITY
    return env


def runtime_state_verified(state: dict[str, Any] | None, *, proof_path: Path, route_path: Path) -> bool:
    if not isinstance(state, dict):
        return False
    pid = state.get("pid")
    endpoint = state.get("endpoint")
    if not isinstance(pid, int) or not isinstance(endpoint, str) or not _pid_alive(pid):
        return False
    ready = _readiness(endpoint)
    return (
        state.get("schema") == "stegverse.va-conversational-runtime-process/v1"
        and state.get("state") == "LIVE_VERIFIED"
        and state.get("proof_path") == str(proof_path)
        and state.get("route_path") == str(route_path)
        and state.get("credential_authority") == CREDENTIAL_AUTHORITY
        and state.get("credential_requirement") == "NONE"
        and state.get("github_token_required") is False
        and state.get("public_authority_effect") is False
        and isinstance(ready, dict)
        and ready.get("state") == "READY"
        and ready.get("credential_requirement") == "NONE"
        and ready.get("github_token_required") is False
    )


def ensure_runtime_gateway(
    adapter_root: Path,
    *,
    proof_path: Path,
    route_path: Path,
    state_path: Path,
) -> dict[str, Any]:
    existing = load_state(state_path)
    if runtime_state_verified(existing, proof_path=proof_path, route_path=route_path):
        return {
            "attempted": False,
            "state": "COMPLETE",
            "reason": "REUSED_LIVE_VERIFIED_VA_RUNTIME",
            "runtime_state": existing,
            "github_token_required": False,
        }

    if isinstance(existing, dict) and isinstance(existing.get("pid"), int) and existing.get("heartbeat_owned") is True:
        _terminate(existing["pid"])

    port = _free_port()
    endpoint = f"http://127.0.0.1:{port}"
    try:
        env = _child_env(adapter_root, proof_path, route_path)
    except Exception as exc:
        return {
            "attempted": False,
            "state": "FAILED",
            "reason": f"VA_RUNTIME_INPUT_CONFIGURATION_FAILED:{exc}",
            "github_token_required": False,
        }
    command = [sys.executable, "-m", "llm_adapter.va_runtime_http_server"]
    process = subprocess.Popen(
        command,
        cwd=adapter_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        env={**env, "HOST": "127.0.0.1", "PORT": str(port)},
    )

    ready: dict[str, Any] | None = None
    for _ in range(100):
        if process.poll() is not None:
            break
        ready = _readiness(endpoint)
        if ready and ready.get("state") == "READY":
            break
        time.sleep(0.05)

    if not ready or ready.get("state") != "READY":
        _terminate(process.pid)
        return {
            "attempted": True,
            "state": "FAILED",
            "reason": "VA_RUNTIME_GATEWAY_NOT_READY",
            "pid": process.pid,
            "endpoint": endpoint,
            "github_token_required": False,
        }

    state = {
        "schema": "stegverse.va-conversational-runtime-process/v1",
        "state": "LIVE_VERIFIED",
        "heartbeat_owned": True,
        "pid": process.pid,
        "endpoint": endpoint,
        "readiness_path": "/api/va-claims/v1/readiness",
        "chat_path": "/api/va-claims/v1/chat",
        "runtime_module": "llm_adapter.va_runtime_http_server",
        "adapter_root": str(adapter_root),
        "source_registry_path": str(adapter_root / "va_claim_assistant" / "source-registry.site-projection.json"),
        "proof_path": str(proof_path),
        "route_path": str(route_path),
        "credential_authority": CREDENTIAL_AUTHORITY,
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_auth_env_forwarded": False,
        "third_party_inference_required": False,
        "public_authority_effect": False,
        "activation_effect": False,
        "private_document_upload_active": False,
        "filing_active": False,
        "release_condition": "retain while the admitted model proof and TVC route remain current; retire on stale authority, failed health, or explicit governed shutdown",
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "attempted": True,
        "state": "COMPLETE",
        "reason": "VA_RUNTIME_GATEWAY_LIVE_VERIFIED",
        "runtime_state": state,
        "readiness": ready,
        "github_token_required": False,
    }


__all__ = ["CREDENTIAL_AUTHORITY", "ensure_runtime_gateway", "load_state", "runtime_state_verified"]
