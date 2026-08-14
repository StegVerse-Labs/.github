#!/usr/bin/env python3
"""Install a rootless native service for the bounded StegFin continuity executor."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import subprocess
import sys
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]
SERVICE_NAME = "stegverse-stegfin-continuity.service"
FORBIDDEN_TEXT = (
    "GITHUB_TOKEN=", "GH_TOKEN=", "GITHUB_PAT=", "API_KEY=", "PRIVATE_KEY=",
    "MNEMONIC=", "SEED=", "PASSWORD=", "BEARER=", "AUTHORIZATION=",
    "WALLET_KEY=", "PROVIDER_SECRET=",
)


def command(root: Path) -> list[str]:
    return [sys.executable, str(root / "scripts" / "run_stegfin_continuity_machine_executor.py"), "--root", str(root)]


def materialize_service(root: Path, *, system: str | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    root = root.resolve()
    if not (root / "scripts" / "run_stegfin_continuity_machine_executor.py").is_file():
        raise RuntimeError("continuity executor source is missing")
    values = dict(os.environ if env is None else env)
    name = (system or platform.system()).lower()
    cmd = command(root)
    if name == "linux":
        base = Path(values.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = base / "systemd" / "user" / SERVICE_NAME
        content = "\n".join([
            "[Unit]",
            "Description=StegVerse StegFin Bounded Continuity Executor",
            "After=local-fs.target",
            "",
            "[Service]",
            "Type=oneshot",
            "ExecStart=" + " ".join(f'\"{part}\"' for part in cmd),
            "Restart=on-failure",
            "RestartSec=60",
            "NoNewPrivileges=yes",
            "PrivateTmp=yes",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "ReadWritePaths=%h/.stegverse %h/.local/state",
            "",
            "[Install]",
            "WantedBy=default.target",
            "",
        ])
        activate = [["systemctl", "--user", "daemon-reload"], ["systemctl", "--user", "enable", "--now", SERVICE_NAME]]
        kind = "systemd-user"
    elif name == "darwin":
        path = Path.home() / "Library" / "LaunchAgents" / "org.stegverse.stegfin-continuity.plist"
        uid = getattr(os, "getuid", lambda: int(values.get("UID", "0")))()
        domain = f"gui/{uid}"
        content = plistlib.dumps({
            "Label": "org.stegverse.stegfin-continuity",
            "ProgramArguments": cmd,
            "RunAtLoad": True,
            "KeepAlive": {"SuccessfulExit": False},
            "ThrottleInterval": 60,
            "StandardOutPath": str(Path.home() / ".stegverse" / "continuity" / "executor.stdout.log"),
            "StandardErrorPath": str(Path.home() / ".stegverse" / "continuity" / "executor.stderr.log"),
        }).decode()
        activate = [["launchctl", "bootout", domain, str(path)], ["launchctl", "bootstrap", domain, str(path)]]
        kind = "launch-agent"
    else:
        raise RuntimeError(f"unsupported continuity host platform: {name}")
    if any(marker in content for marker in FORBIDDEN_TEXT):
        raise RuntimeError("service materialization contains forbidden credential marker")
    return {
        "schema": "stegverse.stegfin-continuity-machine-service/v1",
        "platform": name,
        "registration_kind": kind,
        "registration_path": str(path),
        "content": content,
        "activation_commands": activate,
        "root": str(root),
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_embedded": False,
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
        "native_process_supervision_only": True,
        "heartbeat_replacement": False,
        "execution_authority_created": False,
    }


def install(root: Path, *, runner: Runner = subprocess.run, system: str | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    service = materialize_service(root, system=system, env=env)
    path = Path(service["registration_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(service.pop("content"), encoding="utf-8")
    results = []
    for cmd in service["activation_commands"]:
        completed = runner(cmd, capture_output=True, text=True, check=False)
        results.append({"command": cmd, "returncode": completed.returncode})
    active = bool(results) and results[-1]["returncode"] == 0
    receipt = {**service, "activation_results": results, "active": active}
    receipt_path = Path.home() / ".stegverse" / "continuity" / "executor-activation.latest.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--materialize-only", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.materialize_only:
        result = materialize_service(root)
        print(json.dumps({k: v for k, v in result.items() if k != "content"}, indent=2, sort_keys=True))
        return 0
    if any(str(os.environ.get(name) or "").strip() for name in ("GITHUB_ACTIONS", "RENDER", "VERCEL", "CF_PAGES")):
        raise SystemExit("refusing continuity service activation from hosted environment")
    result = install(root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("active") else 1


if __name__ == "__main__":
    raise SystemExit(main())
