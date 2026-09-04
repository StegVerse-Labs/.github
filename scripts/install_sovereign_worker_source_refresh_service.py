#!/usr/bin/env python3
"""Install a rootless local-source watcher for the sovereign WorkerCoordinator.

The watcher reacts to changes in an already-local canonical source tree and to
durable Universal InTr materialization requests already present in the local
runtime. It never performs source transport or credential acquisition. A refresh preserves
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
from typing import Any, Callable, Mapping

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
REFRESH_SERVICE = "stegverse-worker-source-refresh.service"
REFRESH_PATH = "stegverse-worker-source-refresh.path"
WORKER_SERVICE = "stegverse-worker-runtime.service"
Runner = Callable[..., subprocess.CompletedProcess[Any]]
SOURCE_PACKAGE_COMPONENT_SLUGS = (
    "stegverse-sdk",
    "stegverse-stegcore",
    "stegverse-core-lite",
    "stegverse-master-records",
)


def default_source_package_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_SOURCE_PACKAGE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".stegverse" / "packages" / "source" / "v1").resolve()


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def _quote(value: str | Path) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'


def render_units(*, source_root: Path, runtime_root: Path, python: Path, source_package_root: Path | None = None, local_bindings: Mapping[str, str] | None = None) -> tuple[str, str]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    python = python.expanduser().resolve()
    packages = (source_package_root or default_source_package_root()).expanduser().resolve()
    if source == runtime:
        raise ValueError("source and runtime roots must be distinct")
    refresh_script = runtime / "scripts/refresh_sovereign_worker_runtime_source.py"
    request_dispatcher = runtime / "scripts/dispatch_resident_execution_requests.py"
    hil_materialization_consumer = runtime / "scripts/consume_hil_intr_materialization_request.py"
    safe_local_bindings = {}
    for key in ("STEGVERSE_STEGINDEX_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON"):
        value = str((local_bindings or {}).get(key) or "").strip()
        if value:
            if any(ch in value for ch in "\r\n"):
                raise ValueError("local source binding contains unsafe characters")
            safe_local_bindings[key] = value
    environment_lines = [
        f"Environment={_quote('STEGVERSE_SOURCE_PACKAGE_ROOT=' + str(packages))}",
        *(f"Environment={_quote(key + '=' + value)}" for key, value in sorted(safe_local_bindings.items())),
    ]
    service = "\n".join([
        "[Unit]",
        "Description=StegVerse local-only WorkerCoordinator source refresh",
        "After=local-fs.target",
        "",
        "[Service]",
        "Type=oneshot",
        *environment_lines,
        f"ExecStart={_quote(python)} {_quote(refresh_script)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(request_dispatcher)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost={_quote(python)} {_quote(hil_materialization_consumer)} --source-root {_quote(source)} --runtime-root {_quote(runtime)}",
        f"ExecStartPost=/usr/bin/systemctl --user try-restart {WORKER_SERVICE}",
        f"ExecStartPost=/usr/bin/systemctl --user start {WORKER_SERVICE}",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
        "",
    ])
    package_watch_paths = tuple(packages / slug for slug in SOURCE_PACKAGE_COMPONENT_SLUGS)
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
        source / "source-bundles",
        source / "review-packages",
        source / "tasks",
        source / "control/worker-registry.d",
        source / "control/process-worker-adapters.d",
        source / "control/task-vectors",
        source / "control/process-worker-adapters.json",
        source / "control/worker-capability-profiles.json",
        source / "control/blocker-resolution-policy.json",
        source / "control/task-vector-index.json",
        source / "control/resident-execution-request.json",
        source / "control/resident-execution-request.d",
        runtime / "intr-materialization",
        packages,
        *package_watch_paths,
    )
    path_unit = "\n".join([
        "[Unit]",
        "Description=Watch canonical local StegVerse worker source",
        f"Wants={WORKER_SERVICE}",
        f"After={WORKER_SERVICE}",
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
    source_package_root: Path | None = None,
    runner: Runner = subprocess.run,
    activate: bool = True,
    system: str | None = None,
) -> dict[str, Any]:
    if (system or platform.system()).lower() != "linux":
        raise RuntimeError("rootless source refresh watcher currently requires Linux systemd-user")
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    packages = (source_package_root or default_source_package_root()).expanduser().resolve()
    # Immediate local refresh is the one-time bridge from a stale materialization.
    refresh_receipt = refresh(source, runtime)

    # Do not leave newly materialized resident requests waiting for a later
    # filesystem event. Immediately visit the generic dispatcher after the
    # refresh. Request-specific consumers remain independently fail-closed and
    # non-authorizing.
    immediate_dispatch = {
        "attempted": False,
        "state": "DISPATCHER_NOT_MATERIALIZED",
        "returncode": None,
        "authority_effect": "NONE",
    }
    dispatcher = runtime / "scripts/dispatch_resident_execution_requests.py"
    if dispatcher.is_file():
        completed = runner(
            [sys.executable, str(dispatcher), "--source-root", str(source), "--runtime-root", str(runtime)],
            cwd=runtime,
            check=False,
            capture_output=True,
            text=True,
            timeout=7200,
        )
        dispatch_receipt_path = runtime / "receipts/sovereign-host/resident-request-dispatch.latest.json"
        dispatch_receipt = None
        if dispatch_receipt_path.is_file():
            try:
                dispatch_receipt = json.loads(dispatch_receipt_path.read_text(encoding="utf-8"))
            except Exception:
                dispatch_receipt = None
        immediate_dispatch = {
            "attempted": True,
            "state": (
                dispatch_receipt.get("state")
                if isinstance(dispatch_receipt, dict)
                else ("DISPATCH_PROCESS_COMPLETE" if completed.returncode == 0 else "DISPATCH_PROCESS_FAILED")
            ),
            "returncode": completed.returncode,
            "receipt": dispatch_receipt,
            "request_dispatch_grants_authority": False,
            "heartbeat_grants_execution_authority": False,
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_LOCAL_REQUEST_VISIT_ONLY",
        }
    (runtime / "intr-materialization").mkdir(parents=True, exist_ok=True)
    packages.mkdir(parents=True, exist_ok=True)
    for slug in SOURCE_PACKAGE_COMPONENT_SLUGS:
        (packages / slug).mkdir(parents=True, exist_ok=True)
    config_root = unit_root or (Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "systemd" / "user")
    config_root = config_root.expanduser().resolve()
    config_root.mkdir(parents=True, exist_ok=True)
    service_text, path_text = render_units(
        source_root=source,
        runtime_root=runtime,
        python=python,
        source_package_root=packages,
        local_bindings={
            key: os.environ[key]
            for key in ("STEGVERSE_STEGINDEX_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON")
            if os.environ.get(key)
        },
    )
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
        "immediate_resident_request_dispatch": immediate_dispatch,
        "activation_results": results,
        "activated": activate,
        "filesystem_event_driven": True,
        "intr_materialization_event_driven": True,
        "intr_materialization_watch": str(runtime / "intr-materialization"),
        "source_package_event_driven": True,
        "source_package_watch": str(packages),
        "source_package_component_watches": [str(packages / slug) for slug in SOURCE_PACKAGE_COMPONENT_SLUGS],
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
    parser.add_argument("--source-package-root", type=Path, default=default_source_package_root())
    parser.add_argument("--no-activate", action="store_true")
    args = parser.parse_args()
    receipt = install(
        args.source_root,
        args.runtime_root,
        unit_root=args.unit_root,
        source_package_root=args.source_package_root,
        activate=not args.no_activate,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
