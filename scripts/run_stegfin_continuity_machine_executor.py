#!/usr/bin/env python3
"""Run the existing StegFin continuity worker on an already-authorized local StegVerse node.

This adapter is intentionally not a heartbeat, claim issuer, credential broker, runtime
observer, or wallet executor.  It validates local node posture and the canonical HANDOFF /
worker-registry contract, strips credential-like environment variables, and invokes the
existing self-claiming continuity worker exactly once.  The worker remains responsible
for acquiring the canonical collision-safe continuity claim.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable

TASK_ID = "STEGFIN-CONTINUITY-CARRIER-007"
WORKER_ID = "stegfin-continuity-carrier-worker"
HANDOFF_REL = Path("handoffs/STEGFIN-CONTINUITY-CARRIER-007.json")
REGISTRY_REL = Path("control/worker-registry.d/stegfin-continuity-carrier-007.json")
WORKER_REL = Path("workers/stegfin_continuity_carrier_worker_v3.py")
DURABLE_WORKER_RECEIPT_REL = Path("receipts/stegfin-continuity/STEGFIN-CONTINUITY-CARRIER-007.json")
RECEIPT_REL = Path("receipts/stegfin-continuity-machine-executor/latest.json")
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV_VARS = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CHILD_ENV_MARKERS = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "API_KEY", "PRIVATE_KEY",
    "MNEMONIC", "SEED", "PASSWORD", "BEARER", "AUTHORIZATION", "WALLET_KEY",
    "SECRET", "TOKEN", "AWS_", "AZURE_", "GOOGLE_APPLICATION_CREDENTIALS",
)
ALLOWED_CHILD_ENV = (
    "PATH", "HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "LANG", "LC_ALL",
    "STEGVERSE_STEGFIN_SOURCE_ROOT", "STEGVERSE_TV_SOURCE_ROOT",
    "STEGVERSE_TVC_SOURCE_ROOT", "STEGVERSE_TV_TVC_BROKER_ENDPOINT",
)
Runner = Callable[..., subprocess.CompletedProcess[str]]


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in HOSTED_ENV_VARS)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def validate_node_declaration(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if value.get("schema") not in {
        "stegverse.sovereign-node-declaration/v0.1",
        "stegverse.sovereign-node-declaration/v0.2",
    }:
        raise RuntimeError("unsupported sovereign-node declaration schema")
    if value.get("declared") is not True:
        raise RuntimeError("sovereign node is not declared")
    if value.get("credential_authority") != "TV/TVC":
        raise RuntimeError("sovereign node credential authority is not TV/TVC")
    if value.get("github_token_required") is not False:
        raise RuntimeError("sovereign node may not require a GitHub token")
    return value


def find_node_declaration(explicit: Path | None = None) -> tuple[Path, dict[str, Any]]:
    candidates = (explicit,) if explicit is not None else NODE_MARKERS
    for candidate in candidates:
        if candidate is None:
            continue
        path = candidate.expanduser().resolve()
        if path.is_file():
            return path, validate_node_declaration(path)
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_contract(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    handoff = read_json(root / HANDOFF_REL)
    registry = read_json(root / REGISTRY_REL)
    if handoff.get("state") != "HANDOFF_READY_MACHINE_OWNED_TRANSPORT_SELECTION_AT_EXECUTION":
        raise RuntimeError("StegFin continuity handoff is not machine HANDOFF_READY")
    task = handoff.get("task") or {}
    activation = handoff.get("activation") or {}
    authority = handoff.get("authority") or {}
    if task.get("task_id") != TASK_ID or task.get("manual_execution_allowed") is not False:
        raise RuntimeError("StegFin handoff execution ownership drift")
    if activation.get("executor_binding") != "MACHINE_SCHEDULER_ONLY":
        raise RuntimeError("StegFin handoff no longer requires machine scheduler execution")
    if activation.get("claim_issuer") != "scripts/acquire_stegfin_continuity_claim.py":
        raise RuntimeError("canonical continuity claim issuer drift")
    if authority.get("credential_authority") != "TV/TVC" or authority.get("github_token_required") is not False:
        raise RuntimeError("StegFin handoff credential authority drift")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("StegFin handoff permits non-TV/TVC secret/token")

    tasks = registry.get("tasks") or []
    workers = registry.get("workers") or []
    task_row = next((x for x in tasks if x.get("task_id") == TASK_ID), None)
    worker_row = next((x for x in workers if x.get("worker_id") == WORKER_ID), None)
    if not isinstance(task_row, dict) or not isinstance(worker_row, dict):
        raise RuntimeError("canonical continuity task/worker registration missing")
    if task_row.get("state") != "HANDOFF_READY" or task_row.get("claim_id") is not None:
        raise RuntimeError("continuity task is not claim-free HANDOFF_READY")
    if worker_row.get("status") != "AVAILABLE":
        raise RuntimeError("continuity worker is not AVAILABLE")
    if worker_row.get("adapter_ref") != "process:stegfin-continuity-carrier-v1":
        raise RuntimeError("continuity worker adapter binding drift")
    if registry.get("credential_authority") != "TV/TVC" or registry.get("github_token_required") is not False:
        raise RuntimeError("continuity registry authority drift")
    if not (root / WORKER_REL).is_file():
        raise RuntimeError("canonical continuity worker source is missing")
    return handoff, task_row


def child_environment(env: dict[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if env is None else env)
    child: dict[str, str] = {}
    for key in ALLOWED_CHILD_ENV:
        if key in source:
            child[key] = source[key]
    child.setdefault("PATH", "/usr/bin:/bin")
    child.setdefault("HOME", str(Path.home()))
    child.setdefault("LANG", "C.UTF-8")
    child.setdefault("LC_ALL", "C.UTF-8")
    for key in child:
        upper = key.upper()
        if any(marker in upper for marker in FORBIDDEN_CHILD_ENV_MARKERS):
            raise RuntimeError(f"forbidden child environment key: {key}")
    return child


def terminal_receipt_ok(root: Path) -> bool:
    path = root / DURABLE_WORKER_RECEIPT_REL
    if not path.is_file():
        return False
    value = read_json(path)
    return (
        value.get("state") == "COMPLETE"
        and value.get("transition_id") == "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY"
        and value.get("credential_authority") == "TV/TVC"
        and value.get("non_tv_tvc_secret_or_token_used") is False
        and value.get("provider_secret_exported") is False
        and value.get("signed") is False
        and value.get("broadcast") is False
    )


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temp_name = stream.name
    os.replace(temp_name, path)


def execute_once(
    root: Path,
    *,
    node_declaration: Path | None = None,
    env: dict[str, str] | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    root = root.resolve()
    values = dict(os.environ if env is None else env)
    if hosted_environment(values):
        raise RuntimeError("hosted environments are validation-only and cannot execute StegFin continuity")
    node_path, node = find_node_declaration(node_declaration)
    handoff, _task_row = validate_contract(root)
    instance = f"stegfin-continuity-{node_path.parent.name or 'node'}"
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 0,
        "task": {
            "task_id": TASK_ID,
            "worker_id": WORKER_ID,
            "worker_instance_id": instance,
            "claim_id": None,
            "heartbeat_timing": None,
        },
        "handoff": handoff,
        "scope": handoff.get("execution") or {},
        "authority_effect": "NONE_EXECUTOR_ADAPTER_EXISTING_WORKER_SELF_CLAIMS",
    }
    completed = runner(
        [sys.executable, str(root / WORKER_REL)],
        cwd=root,
        input=json.dumps(invocation, sort_keys=True) + "\n",
        text=True,
        capture_output=True,
        timeout=480,
        check=False,
        env=child_environment(values),
    )
    if completed.returncode != 0:
        raise RuntimeError(f"continuity worker exited {completed.returncode}: {completed.stderr.strip()[-1000:]}")
    try:
        response = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("continuity worker did not emit one valid JSON response") from exc
    if not isinstance(response, dict) or response.get("schema") != "stegverse.worker-response/v0.1":
        raise RuntimeError("continuity worker response schema invalid")
    state = response.get("state")
    if state not in {"BLOCKED", "FAILED", "REVIEW_REQUIRED", "COMPLETE"}:
        raise RuntimeError("continuity worker returned unsupported terminal state")
    if state == "COMPLETE" and (
        response.get("transition_id") != "STEGFIN_CONTINUITY_WALLET_HANDOFF_READY"
        or not terminal_receipt_ok(root)
    ):
        raise RuntimeError("COMPLETE response lacks exact WALLET_HANDOFF_READY durable proof")

    receipt = {
        "schema": "stegverse.stegfin-continuity-machine-executor-receipt/v1",
        "task_id": TASK_ID,
        "state": state,
        "transition_id": response.get("transition_id"),
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "worker": str(WORKER_REL),
        "worker_self_claims": True,
        "executor_minted_claim_or_fence": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "non_tv_tvc_secret_or_token_used": False,
        "provider_secret_exported": False,
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
        "signed": False,
        "broadcast": False,
        "evidence_refs": response.get("evidence_refs") or [],
        "authority_effect": "EXECUTOR_ADAPTER_ONLY_EXISTING_HANDOFF_AND_WORKER_AUTHORITY",
    }
    atomic_write(root / RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--node-declaration", type=Path)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    try:
        if args.probe:
            if hosted_environment():
                raise RuntimeError("hosted environment rejected")
            node_path, _ = find_node_declaration(args.node_declaration)
            validate_contract(args.root.resolve())
            print(json.dumps({
                "schema": "stegverse.stegfin-continuity-machine-executor-probe/v1",
                "state": "READY_FOR_MACHINE_EXECUTION_ATTEMPT",
                "node_declaration_ref": str(node_path),
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": False,
                "execution_authority_effect": "NONE_PROBE_ONLY",
            }, sort_keys=True))
            return 0
        result = execute_once(args.root, node_declaration=args.node_declaration)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["state"] == "COMPLETE" else 75
    except Exception as exc:
        print(json.dumps({
            "schema": "stegverse.stegfin-continuity-machine-executor-error/v1",
            "state": "BLOCKED",
            "error": str(exc),
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "non_tv_tvc_secret_or_token_used": False,
            "signed": False,
            "broadcast": False,
        }, sort_keys=True))
        return 75


if __name__ == "__main__":
    raise SystemExit(main())
