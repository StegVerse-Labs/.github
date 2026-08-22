#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

from workers.hil_sovereign_receiver_bridge import (
    credential_free_receiver_env,
    find_hil_receiver_root,
    receiver_command,
    verify_receiver,
)

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
RECEIPT = ROOT / "receipts" / "hil-sovereign-receiver" / f"{TASK_ID}.json"
DEFAULT_PORT = 8765


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def worker_response(
    *,
    state: str,
    transition: str,
    sequence: int,
    epoch: int,
    next_transition: str | None,
    blocker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": sequence,
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None if next_transition is None else epoch + 1,
        "expected_next_latest_epoch": None if next_transition is None else epoch + 4,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [
            str(RECEIPT.relative_to(ROOT)),
            "workers/hil_sovereign_receiver_worker.py",
            "workers/hil_sovereign_receiver_bridge.py",
            "docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md",
            "StegVerse-Labs/.github#246",
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "hil_sovereign_receiver_activation",
        },
    }
    if blocker is not None:
        result["blocker"] = blocker
    return result


def solution_required(problem: str, action: str, release_condition: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "workaround_candidates": [
            action,
            "Use another already-admitted StegVerse sovereign carrier with the same merged receiver contract; do not substitute participant hardware or a third-party production authority.",
        ],
        "next_solution_action": action,
        "machine_observable_release_condition": release_condition,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "third_party_blocker": False,
        "human_action_required": False,
    }


def state_root() -> Path:
    explicit = os.environ.get("STEGVERSE_HIL_STATE_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (Path.home() / ".stegverse" / "hil" / "sovereign-receiver").resolve()


def receiver_port() -> int:
    raw = os.environ.get("STEGVERSE_HIL_RECEIVER_PORT", str(DEFAULT_PORT))
    try:
        port = int(raw)
    except ValueError as exc:
        raise RuntimeError("invalid_hil_receiver_port") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("invalid_hil_receiver_port")
    return port


def launch_detached(adapter_root: Path, durable_root: Path, port: int) -> subprocess.Popen[bytes]:
    durable_root.mkdir(parents=True, exist_ok=True)
    env = credential_free_receiver_env(adapter_root, durable_root)
    return subprocess.Popen(
        receiver_command(port),
        cwd=adapter_root,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def observe_ready(base_url: str, attempts: int = 20, delay_seconds: float = 0.5) -> dict[str, Any] | None:
    for _ in range(attempts):
        try:
            observed = verify_receiver(base_url)
        except Exception:
            observed = None
        if isinstance(observed, dict) and observed.get("state") == "READY":
            return observed
        time.sleep(delay_seconds)
    return None


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2

    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 3

    execution = handoff.get("execution") or {}
    required = {"runtime_observation", "bounded_process_execution", "sovereign_hil_receiver_activation"}
    if not required.issubset(set(execution.get("required_capabilities") or [])):
        return 4
    if "receipts/hil-sovereign-receiver/**" not in set(execution.get("allowed_paths") or []):
        return 5

    adapter_root = find_hil_receiver_root(ROOT)
    base_receipt: dict[str, Any] = {
        "schema": "stegverse.hil.sovereign-receiver-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "github_token_used": False,
        "non_tv_tvc_secret_or_token_used": False,
        "participant_machine_required": False,
        "developer_machine_required": False,
        "current_user_iphone_required": False,
        "hb30_browser_capsule_required": False,
        "third_party_runtime_required": False,
        "execution_authority": False,
        "review_authority": False,
        "publication_authority": False,
        "master_records_authority": False,
    }

    if adapter_root is None:
        blocker = solution_required(
            "The merged LLM-adapter HIL receiver tree is not materialized on this sovereign carrier.",
            "Resolve the released LLM-adapter receiver into an admitted local StegVerse workload/source location without network credential checkout.",
            "find_hil_receiver_root resolves combined_gateway.py, HIL intake/profile source, task 021, and HIL_RUNTIME_MIRROR_HANDOFF.md",
        )
        receipt = dict(base_receipt)
        receipt.update({
            "state": "ACTIVE",
            "transition_id": "HIL_RECEIVER_SOURCE_MATERIALIZATION_REQUIRED",
            "receiver_ready": False,
            "blocker": blocker,
        })
        atomic_write(RECEIPT, receipt)
        json.dump(worker_response(state="ACTIVE", transition=receipt["transition_id"], sequence=1, epoch=epoch, next_transition="HIL_RECEIVER_LOCAL_READY", blocker=blocker), sys.stdout)
        print()
        return 0

    durable_root = state_root()
    port = receiver_port()
    base_url = f"http://127.0.0.1:{port}"
    observation = observe_ready(base_url, attempts=2, delay_seconds=0.15)
    process: subprocess.Popen[bytes] | None = None
    if observation is None:
        try:
            process = launch_detached(adapter_root, durable_root, port)
        except Exception as exc:
            blocker = solution_required(
                f"The sovereign carrier could not launch the merged HIL receiver: {type(exc).__name__}.",
                "Repair the local carrier launch condition or move this same admitted workload to another StegVerse sovereign carrier without changing authority boundaries.",
                "a detached local receiver process starts and exact profile/readiness verification returns READY",
            )
            receipt = dict(base_receipt)
            receipt.update({
                "state": "ACTIVE",
                "transition_id": "HIL_RECEIVER_LOCAL_LAUNCH_REPAIR_REQUIRED",
                "receiver_ready": False,
                "adapter_root": str(adapter_root),
                "durable_state_root": str(durable_root),
                "blocker": blocker,
            })
            atomic_write(RECEIPT, receipt)
            json.dump(worker_response(state="ACTIVE", transition=receipt["transition_id"], sequence=2, epoch=epoch, next_transition="HIL_RECEIVER_LOCAL_READY", blocker=blocker), sys.stdout)
            print()
            return 0
        observation = observe_ready(base_url)

    if observation is None:
        if process is not None and process.poll() is None:
            process.terminate()
        blocker = solution_required(
            "The local sovereign HIL receiver process started but exact profile/readiness proof did not reach READY.",
            "Inspect the bounded local receiver state and repair configuration until exact HIL v1.1 profile/readiness verification succeeds.",
            "verify_receiver returns READY with exact Primary/prompt hashes and all authority/dependency flags fail-closed",
        )
        receipt = dict(base_receipt)
        receipt.update({
            "state": "ACTIVE",
            "transition_id": "HIL_RECEIVER_READINESS_REPAIR_REQUIRED",
            "receiver_ready": False,
            "adapter_root": str(adapter_root),
            "durable_state_root": str(durable_root),
            "base_url": base_url,
            "blocker": blocker,
        })
        atomic_write(RECEIPT, receipt)
        json.dump(worker_response(state="ACTIVE", transition=receipt["transition_id"], sequence=3, epoch=epoch, next_transition="HIL_RECEIVER_LOCAL_READY", blocker=blocker), sys.stdout)
        print()
        return 0

    blocker = solution_required(
        "The StegVerse carrier receiver is locally READY, but public HTTPS rendezvous, browser receipt, restart-byte proof, and TVC lifecycle handoff are not yet established.",
        "Bind an admitted public HTTPS rendezvous to this already-ready loopback receiver without granting transport execution authority, then observe the Site browser submission and downstream evidence chain.",
        "public HTTPS readiness is directly observed, Site returns HIL-RECEIVER-RECEIPT-v2, exact bytes survive controlled restart/replacement, and TVC accepts lifecycle continuation",
    )
    receipt = dict(base_receipt)
    receipt.update({
        "state": "ACTIVE",
        "transition_id": "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED",
        "receiver_ready": True,
        "adapter_root": str(adapter_root),
        "durable_state_root": str(durable_root),
        "base_url": base_url,
        "receiver_pid": process.pid if process is not None and process.poll() is None else None,
        "observation": observation,
        "public_https_rendezvous_proven": False,
        "browser_submission_proven": False,
        "post_restart_exact_byte_proven": False,
        "tvc_lifecycle_handoff_proven": False,
        "blocker": blocker,
    })
    atomic_write(RECEIPT, receipt)
    json.dump(worker_response(state="ACTIVE", transition=receipt["transition_id"], sequence=4, epoch=epoch, next_transition="HIL_PUBLIC_HTTPS_RENDEZVOUS", blocker=blocker), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
