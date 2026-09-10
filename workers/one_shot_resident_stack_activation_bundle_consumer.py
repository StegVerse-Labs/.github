#!/usr/bin/env python3
"""Consume one-shot resident-stack activation using an already-local portable control bundle.

When no local bundle locator is present, this wrapper delegates unchanged to the
existing one-shot consumer. When a locator is present, it invokes the already-
canonical StegDeploy portable control-plane intake directly so a stale resident
does not first repackage its own stale control-plane tree.
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

REQUEST_REL = Path("control/resident-execution-request.d/one-shot-resident-stack-activation-001.json")
RECEIPT_REL = Path("receipts/sovereign-host/one-shot-resident-stack-activation-request-consumption.latest.json")
LEGACY_CONSUMER_REL = Path("scripts/consume_one_shot_resident_stack_activation_request.py")
TASK_ID = "SHWP-ONE-SHOT-RESIDENT-STACK-ACTIVATION-001"
BUNDLE_ENV = "STEGVERSE_ORG_CONTROL_BUNDLE"
LLM_ENV = "STEGVERSE_LLM_ADAPTER_ROOT"
HEALTH_ENV = "STEGVERSE_STEGDEPLOY_HEALTH_URL"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _stable(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([item.strip() for item in stdout.splitlines() if item.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _repo_roots(env: Mapping[str, str]) -> dict[str, str]:
    raw = str(env.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except Exception:
        return {}
    return {str(k): str(v) for k, v in value.items() if isinstance(k, str) and isinstance(v, str) and v.strip()} if isinstance(value, dict) else {}


def _llm_root(env: Mapping[str, str]) -> Path:
    raw = str(env.get(LLM_ENV) or "").strip()
    if not raw:
        raw = _repo_roots(env).get("StegVerse-org/LLM-adapter", "")
    if not raw:
        raise RuntimeError("local LLM-adapter root required for portable control-bundle intake")
    root = Path(raw).expanduser().resolve()
    if not (root / "scripts/stegdeploy_bootstrap.py").is_file():
        raise RuntimeError("local StegDeploy bootstrap missing")
    return root


def _clean_env(values: Mapping[str, str]) -> dict[str, str]:
    if any(_truthy(values.get(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environment may not consume resident control bundle")
    out = dict(values)
    for name in FORBIDDEN_ENV:
        out.pop(name, None)
    out["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    out["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    return out


def _validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if request.get(key) != expected_value:
            raise RuntimeError(f"one-shot bundle request {key} mismatch")


def _delegate(source: Path, runtime: Path, *, runner, env: Mapping[str, str]) -> dict[str, Any]:
    legacy = runtime / LEGACY_CONSUMER_REL
    if not legacy.is_file():
        raise RuntimeError("legacy one-shot consumer not materialized")
    completed = runner(
        [sys.executable, str(legacy), "--source-root", str(source), "--runtime-root", str(runtime)],
        cwd=runtime, capture_output=True, text=True, check=False, timeout=7200, env=dict(env),
    )
    return _last_json(completed.stdout) or {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "NO_MACHINE_RESULT",
        "runtime_execution_attempted": True,
        "execution_returncode": completed.returncode,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    bundle_raw = str(values.get(BUNDLE_ENV) or "").strip()
    if not bundle_raw:
        return _delegate(source, runtime, runner=runner, env=values)

    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.resident-execution-request-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    request = _load(request_path)
    _validate_request(request)
    request_sha = _stable(request)
    receipt_path = runtime / RECEIPT_REL
    if receipt_path.is_file():
        prior = _load(receipt_path)
        if prior.get("request_sha256") == request_sha and prior.get("activation_complete") is True:
            return prior

    bundle = Path(bundle_raw).expanduser().resolve()
    if not bundle.is_file():
        raise RuntimeError("resident control bundle locator does not resolve to a local file")
    llm = _llm_root(values)
    bootstrap = llm / "scripts/stegdeploy_bootstrap.py"
    health_url = str(values.get(HEALTH_ENV) or "http://127.0.0.1:8000/health").strip()
    child = _clean_env(values)
    child[BUNDLE_ENV] = str(bundle)
    completed = runner(
        [sys.executable, str(bootstrap), "deploy", "--health-url", health_url],
        cwd=llm, capture_output=True, text=True, check=False, timeout=5400, env=child,
    )
    deployment_path = llm / ".stegdeploy/deployment-receipt.json"
    deployment = _load(deployment_path) if deployment_path.is_file() else (_last_json(completed.stdout) or {})
    resident = deployment.get("resident_control_plane_bootstrap") if isinstance(deployment, dict) else None
    resident = resident if isinstance(resident, dict) else {}
    result = resident.get("result") if isinstance(resident.get("result"), dict) else {}
    prime = result.get("post_install_worker_prime") if isinstance(result.get("post_install_worker_prime"), dict) else {}
    dispatch = result.get("post_bootstrap_resident_request_dispatch") if isinstance(result.get("post_bootstrap_resident_request_dispatch"), dict) else {}
    complete = bool(
        completed.returncode == 0
        and resident.get("attempted") is True
        and prime.get("task_capable_cycle_observed") is True
        and dispatch.get("attempted") is True
    )
    receipt = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "COMPLETED" if complete else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_sha,
        "task_id": TASK_ID,
        "runtime_execution_attempted": True,
        "execution_returncode": completed.returncode,
        "activation_complete": complete,
        "retry_allowed": not complete,
        "portable_control_bundle_consumed": True,
        "control_bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "control_bundle_locator_retained": False,
        "stegdeploy_receipt_observed": bool(deployment),
        "resident_bootstrap_attempted": resident.get("attempted") is True,
        "resident_task_capable_cycle_observed": prime.get("task_capable_cycle_observed") is True,
        "resident_request_dispatch_attempted": dispatch.get("attempted") is True,
        "network_source_fetch_performed": False,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_PORTABLE_BUNDLE_INTAKE_ONLY",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        result = {"schema": "stegverse.resident-execution-request-consumption/v1", "state": "BLOCKED", "reason": str(exc), "runtime_execution_attempted": False, "authority_effect": "NONE"}
        print(json.dumps(result, sort_keys=True)); return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"NO_REQUEST", "COMPLETED", "ALREADY_CONSUMED", "ATTEMPT_RECORDED", "SOURCE_ROOTS_PENDING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
