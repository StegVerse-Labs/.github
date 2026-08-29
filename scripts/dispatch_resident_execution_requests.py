#!/usr/bin/env python3
"""Dispatch every bounded resident execution request independently.

This dispatcher is transport-free and non-authorizing. It does not mint claims,
fences, credentials, heartbeat authority, publication authority, or runtime
authority. Each request-specific consumer remains responsible for validating its
own request and invoking only its already-admitted execution path.

A failed or blocked request never prevents later independent requests from being
visited. Consumers retain their own exactly-once semantics.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_REL = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
HOSTED_ENV = (
    "GITHUB_ACTIONS",
    "CI",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "VERCEL_ENV",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
NONSECRET_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "XDG_STATE_HOME",
    "XDG_CONFIG_HOME",
    "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_TV_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_HIL_STATE_ROOT",
    "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_VAULT_AGENT_SOCKET",
    "STEGVERSE_ARA_MAIL_RECIPIENT",
    "STEGVERSE_ARA_MAIL_SENDER",
    "STEGVERSE_SV_DN1_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT",
    "STEGVERSE_SV_DN1_INTR_STATE_ROOT",
    "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_STEGOS_ROOT",
    "STEGVERSE_RELAY_RUNTIME_BASE",
)
CONSUMERS = (
    ("ecosystem_chat", "scripts/consume_resident_execution_request.py"),
    ("g18", "scripts/consume_g18_resident_execution_request.py"),
    ("hil", "scripts/consume_hil_resident_execution_request.py"),
    ("ara_graph", "scripts/consume_ara_graph_resident_execution_request.py"),
    ("sv_dn1", "scripts/consume_sv_dn1_resident_execution_request.py"),
    ("tvc_broker_validation", "scripts/consume_tvc_broker_validation_request.py"),
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError(
            "hosted environment may not dispatch sovereign resident requests: "
            + ",".join(sorted(hosted))
        )
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def dispatch(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    safe_env = clean_exec_env(env)
    outcomes: list[dict[str, Any]] = []

    for name, rel in CONSUMERS:
        consumer = runtime / rel
        if not consumer.is_file():
            outcomes.append({
                "consumer": name,
                "consumer_ref": rel,
                "state": "CONSUMER_NOT_MATERIALIZED",
                "returncode": None,
                "result": None,
                "attempted": False,
            })
            continue
        command = [
            sys.executable,
            str(consumer),
            "--source-root",
            str(source),
            "--runtime-root",
            str(runtime),
        ]
        try:
            completed = runner(
                command,
                cwd=runtime,
                capture_output=True,
                text=True,
                check=False,
                env=safe_env,
                timeout=1200,
            )
            result = parse_last_json(completed.stdout)
            outcomes.append({
                "consumer": name,
                "consumer_ref": rel,
                "state": result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT",
                "returncode": completed.returncode,
                "result": result,
                "attempted": True,
            })
        except Exception as exc:
            outcomes.append({
                "consumer": name,
                "consumer_ref": rel,
                "state": "DISPATCH_EXCEPTION",
                "returncode": None,
                "result": None,
                "attempted": True,
                "error_type": type(exc).__name__,
            })

    missing = [row["consumer"] for row in outcomes if row["state"] == "CONSUMER_NOT_MATERIALIZED"]
    exceptions = [row["consumer"] for row in outcomes if row["state"] == "DISPATCH_EXCEPTION"]
    request_failures = [
        row["consumer"]
        for row in outcomes
        if row["state"] not in {
            "NO_REQUEST",
            "ALREADY_CONSUMED",
            "ATTEMPT_RECORDED",
            "COMPLETED",
        }
    ]
    receipt = {
        "schema": "stegverse.resident-request-dispatch/v1",
        "state": "DISPATCH_COMPLETE" if not missing and not exceptions else "DISPATCH_INCOMPLETE",
        "source_root": str(source),
        "runtime_root": str(runtime),
        "consumer_count": len(CONSUMERS),
        "consumers_visited": len(outcomes),
        "missing_consumers": missing,
        "dispatch_exceptions": exceptions,
        "request_failures": request_failures,
        "outcomes": outcomes,
        "request_failure_blocks_later_requests": False,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_dispatch_grants_authority": False,
        "second_machine_required": False,
        "authority_effect": "NONE_DISPATCH_ONLY",
    }
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch all bounded resident execution requests.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = dispatch(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "DISPATCH_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
