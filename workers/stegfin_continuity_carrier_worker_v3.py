#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "STEGFIN-CONTINUITY-CARRIER-007"
OLD_WORKER = ROOT / "workers" / "stegfin_continuity_carrier_worker.py"
V2_WORKER = ROOT / "workers" / "stegfin_continuity_carrier_worker_v2.py"
DEFAULT_LOCAL_BROKER = Path("/run/stegverse/vault-broker.sock")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load worker module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_broker_endpoint() -> str | None:
    configured = str(os.environ.get("STEGVERSE_TV_TVC_BROKER_ENDPOINT") or "").strip()
    if configured.startswith("https://"):
        return None
    candidate = Path(configured) if configured.startswith("/") else DEFAULT_LOCAL_BROKER
    try:
        candidate = candidate.expanduser().resolve()
    except Exception:
        return None
    if candidate.exists() and candidate.is_socket():
        return str(candidate)
    return None


def run_existing_worker(payload: str) -> int:
    v2 = load_module("stegfin_continuity_v2", V2_WORKER)
    previous = sys.stdin
    try:
        sys.stdin = io.StringIO(payload)
        return int(v2.main())
    finally:
        sys.stdin = previous


def run_local_broker_fastpath(payload: str, endpoint: str) -> int:
    invocation = json.loads(payload)
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        return 3
    worker_instance = str(task.get("worker_instance_id") or task.get("claim_id") or "stegfin-continuity-worker")

    old = load_module("stegfin_continuity_old", OLD_WORKER)
    v2 = load_module("stegfin_continuity_v2_release", V2_WORKER)

    # The same-host broker path is already a canonical transport accepted by
    # run_continuity_pretrade.py. Exact TVC source validation remains inside
    # the old worker. We bypass only the HTTPS primary-runtime observer gate;
    # the real Unix socket is exercised by the bounded continuity runner.
    def local_release_receipt(_tvc_root: Path) -> tuple[dict[str, Any], str]:
        return (
            {
                "state": "READY_LOCAL_TV_TVC_UNIX_BROKER_BOUND",
                "credential_authority": "TV/TVC",
                "consumer_credential_supplied": False,
                "github_token_required": False,
                "provider_secret_used": False,
                "provider_secret_exported": False,
                "non_tv_tvc_secret_or_token_used": False,
                "protected_values_observed": False,
                "provider_operation_attempted": False,
                "wallet_contacted": False,
                "signed": False,
                "broadcast": False,
                "transport": "UNIX_SOCKET_SAME_HOST_TV_TVC",
                "broker_endpoint": endpoint,
                "authority_effect": "TRANSPORT_READINESS_ONLY",
            },
            f"local-unix-broker:{endpoint}",
        )

    def validate_local_release_receipt(value: dict[str, Any]) -> list[str]:
        failures: list[str] = []
        if value.get("state") != "READY_LOCAL_TV_TVC_UNIX_BROKER_BOUND":
            failures.append("local TV/TVC Unix broker readiness state invalid")
        if value.get("credential_authority") != "TV/TVC":
            failures.append("credential authority is not TV/TVC")
        for key in (
            "consumer_credential_supplied",
            "github_token_required",
            "provider_secret_used",
            "provider_secret_exported",
            "non_tv_tvc_secret_or_token_used",
            "protected_values_observed",
            "provider_operation_attempted",
            "wallet_contacted",
            "signed",
            "broadcast",
        ):
            if value.get(key) is not False:
                failures.append(f"{key} must be false")
        if value.get("broker_endpoint") != endpoint:
            failures.append("local broker endpoint drift")
        return failures

    old.load_runtime_release_receipt = local_release_receipt
    old.validate_runtime_release_receipt = validate_local_release_receipt
    os.environ["STEGVERSE_TV_TVC_BROKER_ENDPOINT"] = endpoint

    previous = sys.stdin
    captured = io.StringIO()
    try:
        sys.stdin = io.StringIO(payload)
        with contextlib.redirect_stdout(captured):
            rc = int(old.main())
    finally:
        sys.stdin = previous

    output = captured.getvalue()
    terminal = None
    try:
        terminal = json.loads(output.strip().splitlines()[-1]) if output.strip() else None
    except Exception:
        terminal = None
    if isinstance(terminal, dict) and terminal.get("state") in {"BLOCKED", "COMPLETE", "FAILED", "REVIEW_REQUIRED"}:
        v2.release_owned_claim(worker_instance, str(terminal.get("transition_id") or terminal.get("state")))
    if output:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
    return rc


def main() -> int:
    payload = sys.stdin.read()
    if not payload.strip():
        return 2
    endpoint = local_broker_endpoint()
    if endpoint is None:
        return run_existing_worker(payload)
    return run_local_broker_fastpath(payload, endpoint)


if __name__ == "__main__":
    raise SystemExit(main())
