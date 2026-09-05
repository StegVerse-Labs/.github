#!/usr/bin/env python3
"""Create isolated StegVerse logical nodes on one sovereign host.

The console removes any physical second/third-machine requirement from validation.
It materializes three independent runtime/state roots, launches separated local
carrier and worker-coordinator processes, verifies the canonical activation
predicates, proves process/state-root isolation, tears down validation peers, and
can retain the primary local node.

A hosted CI runner may validate this source but may not use it to claim sovereign
production activation. Provider credentials, GitHub tokens, Render, Vercel,
Cloudflare, or any non-TV/TVC secret are never required or forwarded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.install_sovereign_heartbeat_service import materialize
from scripts.restart_sovereign_ephemeral_node import start as start_node

THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
CREDENTIAL_ENV_VARS = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "STEGVERSE_GITHUB_TOKEN",
    "TVC_TOKEN",
)
REQUIRED_PREDICATES = (
    "runtime_materialized",
    "native_service_active",
    "continuous_runtime_live",
    "heartbeat_epoch_advanced",
    "worker_coordination_checkpoint_observed",
    "controlled_restart_observed",
    "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = dict(os.environ if env is None else env)
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scrubbed_env(base: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    for name in CREDENTIAL_ENV_VARS:
        env[name] = ""
    env["STEGVERSE_SOVEREIGN_NODE"] = "1"
    return env


def _service_receipt(source_root: Path, runtime_root: Path, process: dict[str, Any], interval_ms: float) -> dict[str, Any]:
    restart_helper = source_root / "scripts" / "restart_sovereign_ephemeral_node.py"
    separated_active = (
        process.get("active") is True
        and process.get("carrier_active") is True
        and process.get("worker_active") is True
        and isinstance(process.get("carrier_pid"), int)
        and isinstance(process.get("worker_pid"), int)
    )
    return {
        "schema": "stegverse.sovereign-heartbeat-service/v3",
        "platform": "logical-node",
        "registration_kind": "stegverse-ephemeral-console",
        "runtime_root": str(runtime_root),
        "canonical_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
        "heartbeat_interval_ms": interval_ms,
        "worker_interval_ms": interval_ms,
        "active": separated_active,
        "pid": process.get("carrier_pid", process.get("pid")),
        "carrier_pid": process.get("carrier_pid", process.get("pid")),
        "worker_pid": process.get("worker_pid"),
        "carrier_active": process.get("carrier_active") is True,
        "worker_active": process.get("worker_active") is True,
        "separate_carrier_and_worker_processes": True,
        "stegverse_process_supervision": True,
        "native_process_supervision_only": False,
        "restart_command": [
            sys.executable,
            str(restart_helper),
            "--runtime-root",
            str(runtime_root),
            "--interval-ms",
            str(interval_ms),
        ],
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "third_party_deployment_required": False,
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "LOGICAL_NODE_PROCESS_SUPERVISION_ONLY",
    }


def prepare_node(source_root: Path, root: Path, node_index: int, interval_ms: float) -> dict[str, Any]:
    root = root.resolve()
    materialization = materialize(source_root, root, interval_ms=interval_ms)
    identity = {
        "schema": "stegverse.ephemeral-logical-node-identity/v1",
        "node_id": f"stegverse-ephemeral-node-{node_index}",
        "node_index": node_index,
        "runtime_root": str(root),
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "node_sovereign_membership_granted": False,
        "authority_effect": "VALIDATION_IDENTITY_ONLY",
    }
    identity_path = root / "receipts" / "sovereign-host" / "ephemeral-node-identity.json"
    identity_path.parent.mkdir(parents=True, exist_ok=True)
    identity_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sentinel = root / "receipts" / "sovereign-host" / f"isolation-node-{node_index}.sentinel"
    sentinel.write_text(identity["node_id"] + "\n", encoding="utf-8")
    process = start_node(root, interval_ms=interval_ms)
    service = _service_receipt(source_root, root, process, interval_ms)
    service_path = root / "receipts" / "sovereign-host" / "activation.latest.json"
    service_path.write_text(json.dumps(service, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "identity": identity,
        "identity_path": str(identity_path),
        "sentinel": str(sentinel),
        "sentinel_sha256": _sha(sentinel),
        "materialization": materialization,
        "process": process,
        "service_receipt": str(service_path),
    }


def _stop_pid(pid: Any) -> None:
    if not isinstance(pid, int) or pid <= 0:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return


def _stop_node_processes(process: dict[str, Any]) -> None:
    _stop_pid(process.get("carrier_pid", process.get("pid")))
    _stop_pid(process.get("worker_pid"))


def verify_node(source_root: Path, runtime_root: Path, node_index: int, env: dict[str, str]) -> dict[str, Any]:
    proof_path = runtime_root / "receipts" / "sovereign-host" / "canonical-nine-predicate-proof.json"
    child_env = _scrubbed_env(env)
    child_env["STEGVERSE_SOVEREIGN_PROOF_PATH"] = str(proof_path)
    child_env["STEGVERSE_HEARTBEAT_ROOT"] = str(runtime_root)
    command = [
        sys.executable,
        str(source_root / "scripts" / "verify_sovereign_runtime_activation.py"),
        "--runtime-root",
        str(runtime_root),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180, env=child_env)
    proof = _load(proof_path)
    return {
        "node_index": node_index,
        "runtime_root": str(runtime_root),
        "returncode": completed.returncode,
        "all_predicates_pass": proof.get("all_predicates_pass") is True,
        "predicates": {name: proof.get(name) is True for name in REQUIRED_PREDICATES},
        "proof_path": str(proof_path),
    }


def run_console(
    source_root: Path,
    console_root: Path,
    *,
    node_count: int = 3,
    interval_ms: float = 10.0,
    validation_only: bool = False,
    retain_primary: bool = True,
    canonical_proof_path: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    console_root = console_root.expanduser().resolve()
    canonical_proof_path = canonical_proof_path.expanduser().resolve() if canonical_proof_path else None
    values = dict(os.environ if env is None else env)
    hosted = hosted_environment(values)
    body: dict[str, Any] = {
        "schema": "stegverse.sovereign-ephemeral-console-proof/v2",
        "task_id": "SHWP-SOVEREIGN-EPHEMERAL-CONSOLE-002",
        "source_root": str(source_root),
        "console_root": str(console_root),
        "requested_node_count": node_count,
        "physical_additional_machine_required": False,
        "logical_isolation_dimensions": ["node_identity", "runtime_root", "carrier_pid", "worker_pid", "receipt_tree", "state_tree"],
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
        "third_party_runtime_required": False,
        "hosted_environment_observed": hosted,
        "validation_only": validation_only,
        "canonical_proof_promoted": False,
        "state": "FAIL_CLOSED",
        "nodes": [],
    }
    if node_count < 3:
        body["reason"] = "THREE_LOGICAL_NODES_REQUIRED_FOR_THIRD_MACHINE_EMULATION"
        return body
    if hosted and not validation_only:
        body["reason"] = "HOSTED_RUNNER_MAY_VALIDATE_SOURCE_BUT_CANNOT_PRODUCE_SOVEREIGN_ACTIVATION"
        return body
    if validation_only:
        body["state"] = "VALIDATION_ONLY"
        body["reason"] = "SOURCE_CONTRACT_ONLY_NO_PRODUCTION_ACTIVATION"
        return body

    console_root.mkdir(parents=True, exist_ok=True)
    prepared: list[dict[str, Any]] = []
    try:
        for index in range(1, node_count + 1):
            runtime_root = console_root / f"node-{index}"
            prepared.append(prepare_node(source_root, runtime_root, index, interval_ms))
        time.sleep(0.2)
        verifications = [
            verify_node(source_root, console_root / f"node-{index}", index, values)
            for index in range(1, node_count + 1)
        ]
        process_rows = [
            _load(console_root / f"node-{index}" / "receipts/sovereign-host/ephemeral-process.latest.json")
            for index in range(1, node_count + 1)
        ]
        carrier_pids = [row.get("carrier_pid", row.get("pid")) for row in process_rows]
        worker_pids = [row.get("worker_pid") for row in process_rows]
        roots = [str((console_root / f"node-{index}").resolve()) for index in range(1, node_count + 1)]
        sentinels_isolated = True
        for index in range(1, node_count + 1):
            own = console_root / f"node-{index}" / "receipts" / "sovereign-host" / f"isolation-node-{index}.sentinel"
            if not own.is_file():
                sentinels_isolated = False
            for other in range(1, node_count + 1):
                if other == index:
                    continue
                leaked = console_root / f"node-{other}" / "receipts" / "sovereign-host" / f"isolation-node-{index}.sentinel"
                if leaked.exists():
                    sentinels_isolated = False
        all_pids = carrier_pids + worker_pids
        body["nodes"] = verifications
        body["unique_runtime_roots"] = len(roots) == len(set(roots))
        body["separated_processes_present"] = all(isinstance(pid, int) and pid > 0 for pid in all_pids)
        body["unique_process_pids"] = body["separated_processes_present"] and len(all_pids) == len(set(all_pids))
        body["state_root_write_isolation"] = sentinels_isolated
        body["third_logical_machine_proven"] = len(verifications) >= 3 and verifications[2].get("all_predicates_pass") is True
        body["all_nodes_pass"] = all(row.get("all_predicates_pass") is True for row in verifications)
        body["all_isolation_predicates_pass"] = all((
            body["unique_runtime_roots"],
            body["separated_processes_present"],
            body["unique_process_pids"],
            body["state_root_write_isolation"],
            body["third_logical_machine_proven"],
        ))
        if body["all_nodes_pass"] and body["all_isolation_predicates_pass"]:
            body["state"] = "COMPLETE"
            body["reason"] = "THREE_LOGICAL_SOVEREIGN_NODES_PROVED_ON_ONE_STEGVERSE_HOST"
            if retain_primary and canonical_proof_path is not None:
                primary_proof = Path(verifications[0]["proof_path"])
                canonical_proof_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(primary_proof, canonical_proof_path)
                body["canonical_proof_promoted"] = True
                body["canonical_proof_path"] = str(canonical_proof_path)
        else:
            body["state"] = "REVIEW_REQUIRED"
            body["reason"] = "LOGICAL_NODE_OR_ISOLATION_PROOF_INCOMPLETE"
    finally:
        for index, _row in enumerate(prepared, start=1):
            if retain_primary and index == 1:
                continue
            latest = _load(console_root / f"node-{index}" / "receipts/sovereign-host/ephemeral-process.latest.json")
            _stop_node_processes(latest)
        body["primary_retained"] = retain_primary and bool(prepared)
        if retain_primary and prepared:
            primary = _load(console_root / "node-1" / "receipts/sovereign-host/ephemeral-process.latest.json")
            body["primary_runtime_root"] = str((console_root / "node-1").resolve())
            body["primary_pid"] = primary.get("carrier_pid", primary.get("pid"))
            body["primary_carrier_pid"] = primary.get("carrier_pid", primary.get("pid"))
            body["primary_worker_pid"] = primary.get("worker_pid")
    receipt = console_root / "ephemeral-console.latest.json"
    receipt.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    body["receipt_path"] = str(receipt)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--console-root", type=Path)
    parser.add_argument("--node-count", type=int, default=3)
    parser.add_argument("--interval-ms", type=float, default=10.0)
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--no-retain-primary", action="store_true")
    parser.add_argument("--canonical-proof-path", type=Path, default=None)
    args = parser.parse_args()
    root = args.console_root or Path(tempfile.gettempdir()) / "stegverse-ephemeral-sovereign-console"
    result = run_console(
        args.source_root,
        root,
        node_count=args.node_count,
        interval_ms=args.interval_ms,
        validation_only=args.validation_only,
        retain_primary=not args.no_retain_primary,
        canonical_proof_path=args.canonical_proof_path,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") in {"COMPLETE", "VALIDATION_ONLY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
