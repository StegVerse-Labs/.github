#!/usr/bin/env python3
"""Invocation-owned event-ephemeral Universal InTr bootstrap for canonical SHWP.

Reuses the existing shared Universal InTr listener implementation for exactly one
manifest request. It creates no new listener implementation, scheduler, task,
credential, claim/fence authority, or device dependency. TV/TVC relay
authorization remains mandatory and is supplied only from the existing runtime
binding.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
AUTH_ENV = "STEGVERSE_TVC_RELAY_AUTHORIZATION_ID"
INGRESS_ENV = "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"
SDK_ROOT_ENV = "STEGVERSE_SDK_SOURCE_ROOT"
ORGANIZATION_RECORD_OBSERVED_FIELD = "organization_master_records_organization_record_observed"
#: Master Records boundary migration: results written before the rename carry
#: this legacy flag. Readers accept it as a fallback.
LEGACY_ORGANIZATION_RECORD_OBSERVED_FIELD = "organization_master_records_closure_observed"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")


def organization_record_observed(result: Mapping[str, Any]) -> Any:
    """Read the organization-record-observed flag under the current or legacy name."""
    if ORGANIZATION_RECORD_OBSERVED_FIELD in result:
        return result[ORGANIZATION_RECORD_OBSERVED_FIELD]
    return result.get(LEGACY_ORGANIZATION_RECORD_OBSERVED_FIELD)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("HOSTED_ENVIRONMENT_NOT_AUTHORIZED_FOR_SHWP:" + ",".join(sorted(hosted)))
    env = dict(values)
    for name in FORBIDDEN_ENV:
        env.pop(name, None)
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    return env


def _nonallow(predicate: str, *, listener_started: bool = False) -> dict[str, Any]:
    return {
        "schema": "stegverse.shwp-manifest-intr-event-bootstrap/v1",
        "state": "FAIL_CLOSED",
        "disposition": "FAIL_CLOSED",
        "evaluation_boundary": "SHWP_EVENT_EPHEMERAL_INTR_BOOTSTRAP",
        "failed_predicate": predicate,
        "required_evidence_or_repair": "Repair the named existing-owner attachment predicate and retry the same manifested transition.",
        "retry_entrypoint": "scripts/run_shwp_manifest_intr_event_bootstrap.py",
        "owning_existing_goal": TASK_ID,
        "shared_listener_started": listener_started,
        "listener_loopback_only": True,
        "listener_max_requests": 1,
        "second_listener_implementation_created": False,
        "second_machine_required": False,
        "device_inventory_queried": False,
        "runtime_execution_attempted": False,
        "consequence_committed": False,
        "authority_effect": "NONE_EVENT_TRIGGER_ONLY",
    }


def run_cycle(
    source_root: Path,
    runtime_root: Path,
    *,
    runner: Callable[..., Any] = subprocess.run,
    env: Mapping[str, str] | None = None,
    server_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    try:
        safe = clean_env(env)
    except RuntimeError as exc:
        return _nonallow(str(exc))

    authorization_id = str(safe.get(AUTH_ENV) or "").strip()
    if not authorization_id:
        return _nonallow("TV_TVC_RELAY_AUTHORIZATION_REQUIRED")

    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    importlib.invalidate_caches()
    if server_factory is None:
        shared = importlib.import_module("workers.universal_intr_profiled_ingress")
        server_factory = shared.Server
        ingress_path = shared.INGRESS_PATH
    else:
        ingress_path = "/intr/materialization"

    server = server_factory(("127.0.0.1", 0), runtime, 1)
    host, port = server.server_address
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    child_env = dict(safe)
    child_env[INGRESS_ENV] = f"http://{host}:{port}{ingress_path}"
    child_env[AUTH_ENV] = authorization_id
    consumer = source / "scripts/consume_shwp_manifest_invocation.py"
    if not consumer.is_file():
        server.server_close()
        return _nonallow("SHWP_MANIFEST_INVOCATION_ENTRYPOINT_NOT_MATERIALIZED", listener_started=True)
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
    except Exception as exc:
        return _nonallow("SHWP_MANIFEST_INVOCATION_PROCESS_FAILED:" + type(exc).__name__, listener_started=True)
    finally:
        server.server_close()

    result = last_json(str(getattr(completed, "stdout", "") or ""))
    if not isinstance(result, dict):
        return _nonallow("SHWP_MANIFEST_INVOCATION_RESULT_NOT_OBSERVED", listener_started=True)

    state = str(result.get("state") or "")
    disposition = str(result.get("disposition") or "")
    return {
        "schema": "stegverse.shwp-manifest-intr-event-bootstrap/v1",
        "state": state,
        "disposition": disposition,
        "evaluation_boundary": result.get("evaluation_boundary") or "SDK_SHWP_EVENT_EPHEMERAL_MANIFEST_INVOCATION",
        "failed_predicate": result.get("failed_predicate"),
        "owning_existing_goal": TASK_ID,
        "shared_listener_implementation": "workers.universal_intr_profiled_ingress.Server",
        "shared_listener_started": True,
        "listener_loopback_only": str(host) in {"127.0.0.1", "::1", "localhost"},
        "listener_ephemeral_port": int(port),
        "listener_max_requests": 1,
        "second_listener_implementation_created": False,
        "tvc_relay_authorization_present": True,
        "tvc_relay_authorization_value_retained": False,
        "runtime_execution_attempted": result.get("runtime_execution_attempted") is True,
        "organization_master_records_organization_record_observed": organization_record_observed(result) is True,
        "next_transition": result.get("next_transition"),
        "second_machine_required": False,
        "device_inventory_queried": False,
        "consequence_committed": False,
        "consumer_returncode": int(getattr(completed, "returncode", 1)),
        "consumer_result": result,
        "authority_effect": "NONE_EVENT_TRIGGER_AND_OBSERVATION_ONLY",
    }


__all__ = ["run_cycle", "clean_env", "last_json", "TASK_ID"]
