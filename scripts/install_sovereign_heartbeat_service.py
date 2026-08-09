#!/usr/bin/env python3
"""Materialize and activate the canonical heartbeat on a StegVerse-owned node.

This installer deliberately removes deployment-platform authority from SHWP:
- the runtime is copied from an already-present canonical source tree;
- no GitHub/network fetch is performed;
- mutable state lives on the local StegVerse node;
- cadence remains owned by HeartbeatRuntime --continuous;
- process liveness is supplied by the host OS service manager only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]
COPY_DIRS = (
    "heartbeat_runtime", "control", "handoffs", "authorizations", "workers",
    "schemas", "checkpoints", "events", "receipts", "heartbeats", "cost-basis",
)
COPY_FILES = ("scripts/run_heartbeat_runtime.py",)


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    name = platform.system().lower()
    if name == "windows":
        base = Path(values.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif name == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def _copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, target, dirs_exist_ok=True)


def materialize(source_root: Path, target_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    for rel in COPY_DIRS:
        _copy_tree(source_root / rel, target_root / rel)
    for rel in COPY_FILES:
        source = source_root / rel
        if not source.is_file():
            raise RuntimeError(f"missing canonical runtime file: {rel}")
        target = target_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    required = (
        target_root / "heartbeat_runtime" / "engine_v8.py",
        target_root / "control" / "heartbeat-state.json",
        target_root / "control" / "worker-registry.json",
        target_root / "scripts" / "run_heartbeat_runtime.py",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("materialized runtime is incomplete")
    receipt = {
        "schema": "stegverse.sovereign-heartbeat-materialization/v1",
        "source_root": str(source_root),
        "runtime_root": str(target_root),
        "network_fetch_required": False,
        "third_party_scheduler_required": False,
        "third_party_deployment_required": False,
        "heartbeat_timing_authority": "HeartbeatRuntime.engine_v8",
        "execution_authority_effect": "NONE",
        "manual_action_required": False,
    }
    receipt_path = target_root / "receipts" / "sovereign-host" / "materialization.latest.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def _command(root: Path, interval_ms: float) -> list[str]:
    return [
        sys.executable, str(root / "scripts" / "run_heartbeat_runtime.py"),
        "--root", str(root), "--continuous", "--interval-ms", str(interval_ms),
    ]


def materialize_service(root: Path, *, interval_ms: float = 250.0, system: str | None = None,
                        env: dict[str, str] | None = None) -> dict[str, Any]:
    name = (system or platform.system()).lower()
    values = dict(os.environ if env is None else env)
    command = _command(root, interval_ms)
    if name == "linux":
        config = Path(values.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = config / "systemd" / "user" / "stegverse-heartbeat.service"
        content = "\n".join([
            "[Unit]", "Description=StegVerse Single Heartbeat Runtime", "After=network-online.target", "",
            "[Service]", "Type=simple", "ExecStart=" + " ".join(f'\"{p}\"' for p in command),
            "Restart=always", "RestartSec=2", f'Environment=STEGVERSE_HEARTBEAT_ROOT={root}', "",
            "[Install]", "WantedBy=default.target", "",
        ])
        activate = [["systemctl", "--user", "daemon-reload"], ["systemctl", "--user", "enable", "--now", path.name]]
        kind = "systemd-user"
    elif name == "darwin":
        path = Path.home() / "Library" / "LaunchAgents" / "org.stegverse.heartbeat.plist"
        payload = {
            "Label": "org.stegverse.heartbeat", "ProgramArguments": command,
            "RunAtLoad": True, "KeepAlive": True,
            "EnvironmentVariables": {"STEGVERSE_HEARTBEAT_ROOT": str(root)},
            "StandardOutPath": str(root / "receipts" / "sovereign-host" / "stdout.log"),
            "StandardErrorPath": str(root / "receipts" / "sovereign-host" / "stderr.log"),
        }
        content = plistlib.dumps(payload).decode("utf-8")
        uid = getattr(os, "getuid", lambda: int(values.get("UID", "0")))()
        domain = f"gui/{uid}"
        activate = [["launchctl", "bootout", domain, str(path)], ["launchctl", "bootstrap", domain, str(path)]]
        kind = "launch-agent"
    elif name == "windows":
        appdata = Path(values.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        path = appdata / "StegVerse" / "heartbeat-start.cmd"
        content = "@echo off\r\n" + subprocess.list2cmdline(command) + "\r\n"
        activate = [["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Heartbeat", "/TR", str(path)]]
        kind = "scheduled-task"
    else:
        raise RuntimeError(f"unsupported sovereign host platform: {name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {
        "schema": "stegverse.sovereign-heartbeat-service/v1",
        "platform": name,
        "registration_kind": kind,
        "registration_path": str(path),
        "activation_commands": activate,
        "runtime_root": str(root),
        "third_party_deployment_required": False,
        "third_party_scheduler_required": False,
        "manual_action_required": False,
    }


def install(source_root: Path, target_root: Path, runner: Runner = subprocess.run,
            *, interval_ms: float = 250.0, system: str | None = None,
            env: dict[str, str] | None = None) -> dict[str, Any]:
    materialization = materialize(source_root, target_root)
    service = materialize_service(target_root, interval_ms=interval_ms, system=system, env=env)
    results = []
    for command in service["activation_commands"]:
        completed = runner(command, check=False, capture_output=True, text=True)
        results.append({"command": command, "returncode": completed.returncode})
    active = bool(results) and results[-1]["returncode"] == 0
    receipt = {**materialization, **service, "activation_results": results, "active": active}
    path = target_root / "receipts" / "sovereign-host" / "activation.latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the StegVerse-owned heartbeat runtime on a sovereign node")
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--interval-ms", type=float, default=250.0)
    parser.add_argument("--materialize-only", action="store_true")
    args = parser.parse_args()
    root = (args.runtime_root or default_runtime_root()).resolve()
    if args.materialize_only:
        result = materialize(args.source_root, root)
        result["service"] = materialize_service(root, interval_ms=args.interval_ms)
    else:
        result = install(args.source_root, root, interval_ms=args.interval_ms)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("active", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
