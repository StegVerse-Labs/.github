#!/usr/bin/env python3
"""Refresh already-local resident WorkerCoordinator source, then execute one bounded task.

This bridge is intentionally transport-free and scheduler-neutral. It consumes only an
already-local canonical source tree, preserves mutable resident runtime state through
refresh_sovereign_worker_runtime_source.refresh(), strips GitHub/hosted authority
environment variables, and invokes exactly one admitted execution entrypoint.

It supports:
- generic independently admitted task control via run_worker_runtime.py --task-id
- the dedicated Ecosystem Chat parent executor, which retains its stronger G20/G22
  recovery/fence semantics and is never routed through generic --task-id mode.

Running this script on a sovereign resident surface may produce real runtime evidence.
Merely merging or validating this source does not.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from refresh_sovereign_worker_runtime_source import refresh

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERIC_RUNNER = Path("scripts/run_worker_runtime.py")
ECOSYSTEM_CHAT_PARENT_RUNNER = Path("scripts/run_independent_ecosystem_chat_parent.py")
CARRIER_REF = Path("control/heartbeat-carrier-runtime-state.json")
RECEIPT_REL = Path("receipts/sovereign-host/resident-targeted-execution.latest.json")

GITHUB_AUTH_ENV = {
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
}
HOSTED_MARKERS = {
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "VERCEL_ENV",
    "CLOUDFLARE_API_TOKEN",
}
NONSECRET_FORWARD = {
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "XDG_STATE_HOME",
    "XDG_CONFIG_HOME",
    "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_TV_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_HIL_STATE_ROOT",
    "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_STEGOS_ROOT",
    "STEGVERSE_RELAY_RUNTIME_BASE",
}
Runner = Callable[..., subprocess.CompletedProcess[str]]


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def clean_exec_env(source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {name: values[name] for name in NONSECRET_FORWARD if name in values}
    for name in GITHUB_AUTH_ENV | HOSTED_MARKERS:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def _parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def execution_command(
    runtime_root: Path,
    *,
    task_id: str | None,
    ecosystem_chat_parent: bool,
) -> list[str]:
    runtime = runtime_root.expanduser().resolve()
    if ecosystem_chat_parent:
        if task_id is not None:
            raise ValueError("task_id and ecosystem_chat_parent are mutually exclusive")
        script = runtime / ECOSYSTEM_CHAT_PARENT_RUNNER
        return [sys.executable, str(script), "--root", str(runtime)]
    if not task_id:
        raise ValueError("task_id is required for generic targeted execution")
    script = runtime / GENERIC_RUNNER
    return [
        sys.executable,
        str(script),
        "--root",
        str(runtime),
        "--task-id",
        task_id,
    ]


def refresh_and_execute(
    source_root: Path,
    runtime_root: Path,
    *,
    task_id: str | None = None,
    ecosystem_chat_parent: bool = False,
    runner: Runner = subprocess.run,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    refresh_receipt = refresh(source, runtime)

    command = execution_command(
        runtime,
        task_id=task_id,
        ecosystem_chat_parent=ecosystem_chat_parent,
    )
    executable = Path(command[1])
    if not executable.is_file():
        raise RuntimeError(f"refreshed execution entrypoint missing: {executable}")
    if not ecosystem_chat_parent and not (runtime / CARRIER_REF).is_file():
        raise RuntimeError(
            "targeted independent execution requires the preserved separated carrier reference"
        )

    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=clean_exec_env(env),
    )
    result = _parse_last_json(completed.stdout)
    receipt = {
        "schema": "stegverse.resident-refresh-targeted-execution/v1",
        "source_root": str(source),
        "runtime_root": str(runtime),
        "mode": (
            "DEDICATED_ECOSYSTEM_CHAT_PARENT"
            if ecosystem_chat_parent
            else "TARGETED_INDEPENDENT_TASK_CONTROL"
        ),
        "task_id": "SHWP-ECOSYSTEM-CHAT-INFERENCE-001" if ecosystem_chat_parent else task_id,
        "command": command,
        "refresh_receipt": refresh_receipt,
        "execution_returncode": completed.returncode,
        "execution_result": result,
        "execution_result_observed": isinstance(result, dict),
        "runtime_execution_attempted": True,
        "source_refresh_is_runtime_execution": False,
        "network_fetch_performed": False,
        "third_party_scheduler_required": False,
        "systemd_required_for_one_shot": False,
        "second_machine_required": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_value_exposed": False,
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
    }
    receipt_path = runtime / RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh resident WorkerCoordinator source and execute exactly one admitted task."
    )
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--runtime-root", type=Path, default=default_runtime_root())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--task-id")
    mode.add_argument("--ecosystem-chat-parent", action="store_true")
    args = parser.parse_args()

    receipt = refresh_and_execute(
        args.source_root,
        args.runtime_root,
        task_id=args.task_id,
        ecosystem_chat_parent=args.ecosystem_chat_parent,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["execution_returncode"] == 0 and receipt["execution_result_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
