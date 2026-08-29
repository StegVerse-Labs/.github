#!/usr/bin/env python3
"""Install a rootless local-source watcher for the sovereign WorkerCoordinator.

The watcher reacts only to changes in an already-local canonical source tree. It
never performs source transport or credential acquisition. A refresh preserves
mutable runtime state and restarts only the worker control-plane process; the
independent heartbeat carrier is not restarted or used as execution authority.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
REFRESH_SERVICE = "stegverse-worker-source-refresh.service"
REFRESH_PATH = "stegverse-worker-source-refresh.path"
WORKER_SERVICE = "stegverse-worker-runtime.service"
Runner = Callable[..., subprocess.CompletedProcess[Any]]


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def _quote(value: str | Path) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'


def render_units(*, source_root: Path, runtime_root: Path, python: Path) -> tuple[str, str]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    python = python.expanduser().resolve()
    if source == runtime:
        raise ValueError("source and runtime roots must be distinct")
    refresh_script = runtime / "scripts/refresh_sovereign_worker_runtime_source.py"
    request_consumer = runtime / "scripts/consume_resident_execution_request.py"
    g18_request_consumer = runtime / "scripts/consume_g18_resident_execution_request.py"
    hil_request_consumer = runtime / "scripts/consume_hil_resident_execution_request.py"
    ara_graph_request_consumer = runtime / "scripts/consume_ara_graph_resident_execution_request.py"
    sv_dn1_request_consumer = runtime / "scripts/consume_sv_dn1_resident_execution_request.py"
    tvc_broker_validation_consumer = runtime / "scripts/consume_tvc_broker_validation_request.py"
    service = "\n".join([
        "[Unit]",
        "Description=StegVerse local-only WorkerCoordinator source refresh",
        "After=local-fs.target",
        "",
        "[Service]",
        "Type=oneshot",
        f"ExecStart={_quote(python)} {_quote(refresh_script)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(request_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(g18_request_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(hil_request_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(ara_graph_request_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(sv_dn1_request_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(tvc_broker_validation_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost=/usr/bin/systemctl --user try-restart {WORKER_SERVICE}",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "",
    ])
    watched_paths = (
        source / "heartbeat_runtime",
        source / "workers",
        source / "handoffs",
        source / "authorizations",
        source / "schemas",
        source / "cost-basis",
        source / "management",
        source / "state_language",
        source / "scripts",
        source / "control/worker-registry.d",
        source / "control/process-worker-adapters.d",
        source / "control/task-vectors",
        source / "control/process-worker-adapters.json",
        source / "control/worker-capability-profiles.json",
        source / "control/blocker-resolution-policy.json",
        source / "control/task-vector-index.json",
        source / "control/resident-execution-request.json",
        source / "control/resident-execution-request.d",
    )
    path_unit = "\n".join([
        "[Unit]",
        "Description=Watch canonical local StegVerse worker source",
        "",
        "[Path]",
        *(f"PathChanged={path}" for path in watched_paths),
        f"Unit={REFRESH_SERVICE}",
        "",
        "[Install]",
        "WantedBy=default.target",
        "",
    ])
    combined = service + "\n" + path_unit
    # Split these markers so raw-source guards do not mistake the guard itself
    # for an executable transport/credential path. The reconstructed values are
    # still the exact strings forbidden in generated unit text.
    forbidden = (
        "GITHUB" + "_TOKEN",
        "GH" + "_TOKEN",
        "x-" + "access-token",
        "git " + "clone",
        "git " + "fetch",
        "git " + "pull",
        "Load" + "Credential=",
    )
    if any(value in combined for value in forbidden):
        raise ValueError("refresh watcher contains forbidden transport/credential authority")
    return service, path_unit


def install(
    source_root: Path,
    runtime_root: Path,
    *,
    unit_root: Path | None = None,
    python: Path = Path(sys.executable),
    runner: Runner = subprocess.run,
    activate: bool = True,
    system: str | None = None,
) -> dict[str, Any]:
    if (system or platform.system()).lower() != "linux":
        raise RuntimeError("rootless source refresh watcher currently requires Linux systemd-user")
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    # Immediate local refresh is the one-time bridge from a stale materialization.
    refresh_receipt = refresh(source, runtime)
    config_root = unit_root or (Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "systemd" / "user")
    config_root = config_root.expanduser().resolve()
    config_root.mkdir(parents=True, exist_ok=True)
    service_text, path_text = render_units(source_root=source, runtime_root=runtime, python=python)
    service_path = config_root / REFRESH_SERVICE
    path_path = config_root / REFRESH_PATH
    service_path.write_text(service_text, encoding="utf-8")
    path_path.write_text(path_text, encoding="utf-8")

    commands: list[list[str]] = []
    results: list[dict[str, Any]] = []
    if activate:
        if shutil.which("systemctl") is None:
            raise RuntimeError("systemctl unavailable")
        commands = [
            ["systemctl", "--user", "daemon-reload"],
            ["systemctl", "--user", "enable", "--now", REFRESH_PATH],
            ["systemctl", "--user", "try-restart", WORKER_SERVICE],
        ]
        for command in commands:
            completed = runner(command, check=False, capture_output=True, text=True)
            results.append({"command": command, "returncode": completed.returncode})
        if any(row["returncode"] != 0 for row in results):
            raise RuntimeError("failed to activate local WorkerCoordinator source refresh watcher")

    receipt = {
        "schema": "stegverse.sovereign-worker-source-refresh-installation/v1",
        "source_root": str(source),
        "runtime_root": str(runtime),
        "refresh_service": str(service_path),
        "refresh_path_unit": str(path_path),
        "worker_service": WORKER_SERVICE,
        "immediate_refresh": refresh_receipt,
        "activation_results": results,
        "activated": activate,
        "filesystem_event_driven": True,
        "second_heartbeat_created": False,
        "third_party_scheduler_required": False,
        "network_fetch_performed": False,
        "credential_read_or_acquired": False,
        "github_token_required": False,
        "credential_authority": "TV/TVC",
        "heartbeat_grants_execution_authority": False,
        "carrier_restarted_by_refresh": False,
        "authority_effect": "NONE_LOCAL_SOURCE_REFRESH_INSTALLATION",
    }
    receipt_path = runtime / "receipts/sovereign-host/worker-source-refresh-installation.latest.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the rootless local-source refresh watcher for WorkerCoordinator.")
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runtime-root", type=Path, default=default_runtime_root())
    parser.add_argument("--unit-root", type=Path)
    parser.add_argument("--no-activate", action="store_true")
    args = parser.parse_args()
    receipt = install(
        args.source_root,
        args.runtime_root,
        unit_root=args.unit_root,
        activate=not args.no_activate,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
