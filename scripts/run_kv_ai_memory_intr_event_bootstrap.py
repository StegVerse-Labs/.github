#!/usr/bin/env python3
"""Run one KV AI memory admission cycle on the existing shared Universal InTr listener.

This is an event-triggered resident-local bridge. It starts no new listener
implementation: it instantiates workers.universal_intr_profiled_ingress.Server on
loopback with an ephemeral port for exactly one request, supplies that bound URL
only to the existing KV AI memory resident consumer, then closes the server.

Private packet/prompt bytes remain in fenced bound state and are read only by the
existing submitter/worker subprocesses. This bootstrap grants no InTr decision,
claim/fence, credential, provider, KV-write, or activation authority.
"""
from __future__ import annotations

import argparse
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
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "ACTIONS_RUNTIME_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY", "ZAI_API_KEY", "KIMI_API_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC")
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT",
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
    required = (PACKET_INPUT, PROVIDER_INPUT)
    missing = [rel.as_posix() for rel in required if not (root / rel).is_file()]
    return not missing, missing


def prepare_source(source: Path, *, runner=subprocess.run, env: Mapping[str, str]) -> dict[str, Any]:
    preparer = source / "scripts/prepare_kv_ai_memory_intr_runtime_source.py"
    if not preparer.is_file():
        raise RuntimeError("KV AI memory runtime-source preparer missing")
    completed = runner(
        [sys.executable, str(preparer), "--source-root", str(source)],
        cwd=source,
        capture_output=True,
        text=True,
        check=False,
        env=dict(env),
        timeout=120,
    )
    result = last_json(completed.stdout)
    if completed.returncode != 0 or not isinstance(result, dict) or result.get("state") not in {"ROUTE_INSTALLED_LOCAL_SOURCE", "ROUTE_ALREADY_INSTALLED"}:
        raise RuntimeError("KV AI memory shared InTr route preparation failed")
    return result


def run_cycle(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    safe = clean_env(env)
    ready, missing = staged_input_state(safe)
    if not ready:
        return {
            "schema": "stegverse.kv-ai-memory.intr-event-bootstrap/v1",
            "state": "BOUND_STATE_INPUT_NOT_READY",
            "missing_input_refs": missing,
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

    runtime.mkdir(parents=True, exist_ok=True)
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
            cwd=runtime,
            capture_output=True,
            text=True,
            check=False,
            env=child_env,
            timeout=1800,
        )
        thread.join(timeout=30)
    finally:
        server.server_close()

    result = last_json(completed.stdout)
    admission_path = bound_state_root(safe) / ADMISSION_INPUT
    admission_observed = admission_path.is_file()
    return {
        "schema": "stegverse.kv-ai-memory.intr-event-bootstrap/v1",
        "state": "EVENT_CYCLE_COMPLETED" if completed.returncode == 0 else "EVENT_CYCLE_FAIL_CLOSED",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one resident-local KV AI memory cycle on the existing shared Universal InTr listener.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = run_cycle(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"BOUND_STATE_INPUT_NOT_READY", "EVENT_CYCLE_COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
