#!/usr/bin/env python3
"""Reuse the already-local TVC primary-runtime binding and diagnostic observer.

This wrapper exists only so the generic reusable-task trigger can execute a local
`scripts/*.py` entrypoint while TVC remains the owner of runtime binding,
activation, provider-operation, and credential semantics. It performs no source
fetch, exports no protected value, and emits no standardized reusable completion
result; the generic trigger therefore stops at evidence reconciliation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def emit(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    emit(completed)
    return completed


def main() -> int:
    raw = os.getenv("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    if not raw:
        print(json.dumps({"state":"BOUNDARY_RECORDED","reason":"TVC_LOCAL_SOURCE_ROOT_MAP_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    roots = json.loads(raw)
    if not isinstance(roots, dict):
        raise SystemExit("STEGVERSE_REPO_ROOTS_JSON must be an object")
    tvc_raw = roots.get("StegVerse-Labs/TVC")
    if not isinstance(tvc_raw, str) or not tvc_raw:
        print(json.dumps({"state":"BOUNDARY_RECORDED","reason":"TVC_LOCAL_SOURCE_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    tvc_root = Path(tvc_raw).expanduser().resolve()
    observer = tvc_root / "scripts" / "observe_tvc_runtime_boundary.py"
    installer = tvc_root / "scripts" / "install_tvc_primary_runtime_service.py"
    if not observer.is_file() or not installer.is_file():
        print(json.dumps({"state":"BOUNDARY_RECORDED","reason":"TVC_DECLARED_RUNNER_DEPENDENCY_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3

    activation_delivery = run(
        [sys.executable, str(installer), "--repo-root", str(tvc_root), "--activate"],
        cwd=tvc_root,
    )
    if activation_delivery.returncode != 0:
        return activation_delivery.returncode

    params_raw = os.getenv("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "{}").strip() or "{}"
    params = json.loads(params_raw)
    command = [sys.executable, str(observer)]
    provider_route = params.get("provider_operation_route") if isinstance(params, dict) else None
    if isinstance(provider_route, str) and provider_route:
        command.extend(["--provider-route", provider_route])
    observed = run(command, cwd=tvc_root)
    return observed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
