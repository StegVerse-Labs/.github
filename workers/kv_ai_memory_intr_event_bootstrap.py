#!/usr/bin/env python3
"""Resident-native one-cycle KV AI memory bootstrap on the shared Universal InTr listener.

When fenced inputs are absent, this bootstrap may resolve an already-local Personal-KV
root through the existing secret-free provider-root resolver and invoke the existing
continuity-vault-kit private stager against real user-custodied input files. It never
creates default memory, provider/model settings, or an admission artifact.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
BOUND_STATE_REL = Path(".stegverse/state/kv-ai-memory-resident")
PACKET_INPUT = Path("inputs/context-packet.json")
PROVIDER_INPUT = Path("inputs/provider-request-input.json")
ADMISSION_INPUT = Path("inputs/memory-packet-admission.json")
PERSONAL_KV_INPUT_ROOT_REL = Path("_System/AI/Memory/Inputs")
CONTEXT_REQUEST_NAME = "context-request.json"
CONTEXT_ENTRIES_NAME = "context-entries.json"
PROVIDER_REQUEST_NAME = "provider-request-input.json"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "ACTIONS_RUNTIME_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "ZAI_API_KEY", "KIMI_API_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC")
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT",
    "STEGVERSE_KV_PROVIDER_BINDING_PATH", "STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT",
    "STEGVERSE_TVC_PROVIDER_MATERIALIZATION_RESULT_FILE",
    "STEGVERSE_KV_AI_CONTEXT_REQUEST_PATH", "STEGVERSE_KV_AI_CONTEXT_ENTRIES_PATH",
    "STEGVERSE_KV_AI_PROVIDER_REQUEST_INPUT_PATH",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not run sovereign KV AI memory event bootstrap: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def bound_state_root(env: Mapping[str, str]) -> Path:
    home = str(env.get("HOME") or "").strip()
    if not home:
        raise RuntimeError("HOME required to resolve KV AI memory fenced bound state")
    return Path(home).expanduser().resolve() / BOUND_STATE_REL


def last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def staged_input_state(env: Mapping[str, str]) -> tuple[bool, list[str]]:
    root = bound_state_root(env)
    missing = [rel.as_posix() for rel in (PACKET_INPUT, PROVIDER_INPUT) if not (root / rel).is_file()]
    return not missing, missing


def _resolve_personal_kv_root(source: Path, runtime: Path, *, runner, env: Mapping[str, str]) -> tuple[Path | None, dict[str, Any] | None, str | None]:
    explicit = str(env.get("STEGVERSE_KV_ROOT") or "").strip()
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if root.is_dir():
            return root, {"state": "EXISTING_LOCAL_ROOT", "kv_root": str(root)}, None
    resolver = source / "scripts/materialize_personal_kv_provider_root.py"
    if not resolver.is_file():
        return None, None, "PERSONAL_KV_ROOT_RESOLVER_MISSING"
    completed = runner(
        [sys.executable, str(resolver), "--runtime-root", str(runtime)],
        cwd=runtime, capture_output=True, text=True, check=False, env=dict(env), timeout=300,
    )
    result = last_json(completed.stdout)
    if completed.returncode != 0 or not isinstance(result, dict) or result.get("state") != "KV_ROOT_RESOLVED":
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        suffix = detail[-1] if detail else "resolution_failed"
        return None, result, "PERSONAL_KV_ROOT_NOT_RESOLVED:" + suffix[:240]
    root = Path(str(result.get("kv_root") or "")).expanduser().resolve()
    if not root.is_dir():
        return None, result, "PERSONAL_KV_ROOT_NOT_DIRECTORY"
    return root, result, None


def _candidate_input_paths(kv_root: Path, env: Mapping[str, str]) -> dict[str, Path]:
    default_root = kv_root / PERSONAL_KV_INPUT_ROOT_REL
    return {
        "context_request": Path(str(env.get("STEGVERSE_KV_AI_CONTEXT_REQUEST_PATH") or (default_root / CONTEXT_REQUEST_NAME))).expanduser().resolve(),
        "context_entries": Path(str(env.get("STEGVERSE_KV_AI_CONTEXT_ENTRIES_PATH") or (default_root / CONTEXT_ENTRIES_NAME))).expanduser().resolve(),
        "provider_request_input": Path(str(env.get("STEGVERSE_KV_AI_PROVIDER_REQUEST_INPUT_PATH") or (default_root / PROVIDER_REQUEST_NAME))).expanduser().resolve(),
    }


def stage_from_personal_kv(source: Path, runtime: Path, *, runner, env: Mapping[str, str]) -> dict[str, Any]:
    kv_root, resolution, error = _resolve_personal_kv_root(source, runtime, runner=runner, env=env)
    if error or kv_root is None:
        return {
            "state": "PERSONAL_KV_ROOT_NOT_READY",
            "reason": error,
            "kv_root_resolution": resolution,
            "private_content_exported_to_repository": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    paths = _candidate_input_paths(kv_root, env)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {
            "state": "PERSONAL_KV_AI_MEMORY_INPUTS_NOT_FOUND",
            "kv_root": str(kv_root),
            "missing_inputs": missing,
            "expected_relative_root": PERSONAL_KV_INPUT_ROOT_REL.as_posix(),
            "private_content_exported_to_repository": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    kv_source = str(env.get("STEGVERSE_KV_SOURCE_ROOT") or "").strip()
    if not kv_source:
        return {
            "state": "PERSONAL_KV_STAGER_SOURCE_NOT_READY",
            "reason": "STEGVERSE_KV_SOURCE_ROOT missing",
            "private_content_exported_to_repository": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    stager = Path(kv_source).expanduser().resolve() / "scripts/stage_kv_ai_memory_resident_inputs.py"
    if not stager.is_file():
        return {
            "state": "PERSONAL_KV_STAGER_SOURCE_NOT_READY",
            "reason": "stage_kv_ai_memory_resident_inputs.py missing",
            "private_content_exported_to_repository": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    completed = runner(
        [
            sys.executable, str(stager),
            "--context-request", str(paths["context_request"]),
            "--entries", str(paths["context_entries"]),
            "--provider-request-input", str(paths["provider_request_input"]),
            "--stage-root", str(bound_state_root(env)),
        ],
        cwd=Path(kv_source).expanduser().resolve(), capture_output=True, text=True,
        check=False, env=dict(env), timeout=300,
    )
    result = last_json(completed.stdout)
    if completed.returncode != 0 or not isinstance(result, dict) or result.get("state") != "PRIVATE_INPUTS_STAGED_AWAITING_INTR_ADMISSION":
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        suffix = detail[-1] if detail else "staging_failed"
        return {
            "state": "PERSONAL_KV_PRIVATE_STAGING_FAIL_CLOSED",
            "reason": suffix[:240],
            "private_content_exported_to_repository": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    return {
        "state": "PERSONAL_KV_PRIVATE_INPUTS_STAGED",
        "packet_id": result.get("packet_id"),
        "selected_item_count": result.get("selected_item_count"),
        "memory_packet_admission_present": result.get("memory_packet_admission_present"),
        "private_content_exported_to_repository": False,
        "authority_effect": "NONE_PRIVATE_STAGING_ONLY",
    }


def prepare_source(source: Path, *, runner=subprocess.run, env: Mapping[str, str]) -> dict[str, Any]:
    preparer = source / "scripts/prepare_kv_ai_memory_intr_runtime_source.py"
    if not preparer.is_file():
        raise RuntimeError("KV AI memory runtime-source preparer missing")
    completed = runner(
        [sys.executable, str(preparer), "--source-root", str(source)], cwd=source,
        capture_output=True, text=True, check=False, env=dict(env), timeout=120,
    )
    result = last_json(completed.stdout)
    if completed.returncode != 0 or not isinstance(result, dict) or result.get("state") not in {"ROUTE_INSTALLED_LOCAL_SOURCE", "ROUTE_ALREADY_INSTALLED"}:
        raise RuntimeError("KV AI memory shared InTr route preparation failed")
    return result


def run_cycle(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    safe = clean_env(env)
    ready, missing = staged_input_state(safe)
    staging_result = None
    if not ready:
        staging_result = stage_from_personal_kv(source, runtime, runner=runner, env=safe)
        ready, missing = staged_input_state(safe)
        if not ready:
            return {
                "schema": "stegverse.kv-ai-memory.intr-event-bootstrap/v1",
                "state": str(staging_result.get("state") if isinstance(staging_result, dict) else "BOUND_STATE_INPUT_NOT_READY"),
                "missing_input_refs": missing,
                "private_staging_result": staging_result,
                "shared_listener_started": False,
                "runtime_execution_attempted": False,
                "private_input_bytes_read_by_bootstrap": False,
                "authority_effect": "NONE_WAIT_STATE",
            }

    preparation = prepare_source(source, runner=runner, env=safe)
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    importlib.invalidate_caches()
    shared = importlib.import_module("workers.universal_intr_profiled_ingress")

    server = shared.Server(("127.0.0.1", 0), runtime, 1)
    host, port = server.server_address
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    child_env = dict(safe)
    child_env["STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"] = f"http://{host}:{port}{shared.INGRESS_PATH}"
    consumer = source / "scripts/consume_kv_ai_memory_resident_request.py"
    if not consumer.is_file():
        server.server_close()
        raise RuntimeError("KV AI memory resident consumer missing")
    try:
        completed = runner(
            [sys.executable, str(consumer), "--source-root", str(source), "--runtime-root", str(runtime)],
            cwd=runtime, capture_output=True, text=True, check=False, env=child_env, timeout=1800,
        )
        thread.join(timeout=30)
    finally:
        server.server_close()

    result = last_json(completed.stdout)
    admission_observed = (bound_state_root(safe) / ADMISSION_INPUT).is_file()
    return {
        "schema": "stegverse.kv-ai-memory.intr-event-bootstrap/v1",
        "state": "EVENT_CYCLE_COMPLETED" if completed.returncode == 0 else "EVENT_CYCLE_FAIL_CLOSED",
        "private_staging_result": staging_result,
        "route_preparation_state": preparation.get("state"),
        "shared_listener_implementation": "workers.universal_intr_profiled_ingress.Server",
        "shared_listener_started": True,
        "listener_loopback_only": str(host) in {"127.0.0.1", "::1", "localhost"},
        "listener_ephemeral_port": int(port),
        "listener_max_requests": 1,
        "second_listener_implementation_created": False,
        "consumer_returncode": completed.returncode,
        "consumer_result": result,
        "authentic_admission_artifact_observed": admission_observed,
        "private_input_bytes_read_by_bootstrap": False,
        "runtime_execution_attempted": bool(isinstance(result, dict) and result.get("runtime_execution_attempted") is True),
        "heartbeat_grants_execution_authority": False,
        "claim_or_fence_minted_by_bootstrap": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_EVENT_TRIGGER_AND_OBSERVATION_ONLY",
    }
