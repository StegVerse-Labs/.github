#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from heartbeat_runtime.orphan_recovery import (
    independent_orphan_recovery_contract_valid,
    reconcile_quarantined_orphan_recoveries,
)
from heartbeat_runtime.process_adapter import ProcessWorkerAdapter

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ID = "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"
PARENT_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECOVERY_WORKER_ID = "ecosystem-chat-orphan-recovery-worker"
RECOVERY_ADAPTER_REF = "process:ecosystem-chat-orphan-recovery-v1"
RECOVERY_COMMAND = ["python", "workers/ecosystem_chat_orphan_recovery_worker.py"]
REGISTRY_PATH = Path("control/worker-registry.json")
FRAGMENT_PATH = Path("control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json")
CARRIER_PATH = Path("control/heartbeat-carrier-runtime-state.json")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temp_name = stream.name
    os.replace(temp_name, path)


def task_by_id(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    task = next((row for row in registry.get("tasks", []) if row.get("task_id") == task_id), None)
    if not isinstance(task, dict):
        raise RuntimeError(f"task not present in canonical registry: {task_id}")
    return task


def max_projected_fence(registry: dict[str, Any]) -> int:
    maximum = int(registry.get("generation", 0) or 0)
    for task in registry.get("tasks", []):
        if not isinstance(task, dict):
            continue
        timing = task.get("heartbeat_timing") or {}
        timer = task.get("assignment_timer") or {}
        for value in (timing.get("fencing_token"), timer.get("fencing_token")):
            if isinstance(value, int):
                maximum = max(maximum, value)
    return maximum


def current_reference_epoch(root: Path) -> int:
    state = load_json(root / CARRIER_PATH)
    epoch = state.get("epoch")
    if not isinstance(epoch, int):
        raise RuntimeError("carrier reference is missing an integer epoch")
    return epoch


def validate_registered_executor(root: Path) -> None:
    fragment = load_json(root / FRAGMENT_PATH)
    task = next((row for row in fragment.get("tasks", []) if row.get("task_id") == RECOVERY_ID), None)
    worker = next((row for row in fragment.get("workers", []) if row.get("worker_id") == RECOVERY_WORKER_ID), None)
    if not isinstance(task, dict) or task.get("state") != "HANDOFF_READY":
        raise RuntimeError("recovery registry fragment is not HANDOFF_READY")
    if task.get("executor_binding") != "AUTHORIZED":
        raise RuntimeError("recovery registry fragment executor is not AUTHORIZED")
    admission = task.get("admission") or {}
    if admission.get("authority_domain") != "INDEPENDENT_TASK_CONTROL":
        raise RuntimeError("recovery registry fragment is not bound to independent task control")
    if admission.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant recovery execution authority")
    if admission.get("g18_terminalization_required") is not False:
        raise RuntimeError("G18 terminalization may not gate recovery")
    if admission.get("minimum_fencing_token_exclusive") != 20:
        raise RuntimeError("recovery fresh-fence floor is not bound to ended fence 20")
    if not isinstance(worker, dict) or worker.get("status") != "AVAILABLE":
        raise RuntimeError("recovery worker is not AVAILABLE")
    if worker.get("adapter_ref") != RECOVERY_ADAPTER_REF:
        raise RuntimeError("recovery worker adapter binding mismatch")
    if set(worker.get("capabilities") or []) != {"orphan_lifecycle_reconstruction"}:
        raise RuntimeError("recovery worker capability binding mismatch")


def acquire_recovery_claim(
    root: Path,
    registry: dict[str, Any],
    *,
    reference_epoch: int,
) -> tuple[dict[str, Any], int]:
    task = task_by_id(registry, RECOVERY_ID)
    parent = task_by_id(registry, PARENT_ID)

    # A previous bounded attempt may have released back to BLOCKED. Reconcile only
    # the already-admitted continuity contract; this never mints authority.
    if task.get("state") in {"BLOCKED", "QUARANTINED"}:
        reconcile_quarantined_orphan_recoveries(root, registry, epoch=reference_epoch)
        task = task_by_id(registry, RECOVERY_ID)

    valid, reason = independent_orphan_recovery_contract_valid(
        root,
        registry_task=task,
        registry=registry,
    )
    if not valid:
        raise RuntimeError(f"independent recovery contract rejected: {reason}")
    if task.get("state") != "HANDOFF_READY" or task.get("claim_id") is not None or task.get("worker_id") is not None:
        raise RuntimeError("recovery task is not atomically claimable")
    if parent.get("claim_id") is not None or parent.get("worker_id") is not None:
        raise RuntimeError("parent old authority is not fully ended")

    fence = max(20, max_projected_fence(registry)) + 1
    claim_id = f"SHWP-{RECOVERY_ID}-G{fence}"
    worker_instance_id = f"{RECOVERY_WORKER_ID}-REF{reference_epoch}-G{fence}"
    registry["generation"] = fence
    task.update({
        "state": "ACTIVE",
        "executor_binding": "BOUND",
        "worker_id": RECOVERY_WORKER_ID,
        "worker_instance_id": worker_instance_id,
        "claim_id": claim_id,
        "archive_eligible": False,
        "archive_reason_codes": [],
        "block_ref": None,
        "lease": None,
        "heartbeat_timing": {
            "start_epoch": reference_epoch,
            "last_response_epoch": reference_epoch,
            "last_transition_epoch": reference_epoch,
            "current_transition": "INDEPENDENT_RECOVERY_EXECUTION",
            "transition_sequence": 0,
            "expected_next_transition": "ORPHAN_LIFECYCLE_RECONSTRUCTED",
            "expected_next_earliest_epoch": None,
            "expected_next_latest_epoch": None,
            "expiry_epoch": None,
            "expiry_basis": "BOUNDED_INDEPENDENT_TASK_CONTROL_ATTEMPT",
            "fencing_token": fence,
        },
        "independent_task_control": {
            "authority_domain": "INDEPENDENT_TASK_CONTROL",
            "authorization_ref": "authorizations/RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28.json",
            "heartbeat_reference_only": True,
            "heartbeat_granted_authority": False,
            "g18_authority_used": False,
            "g20_authority_reused": False,
            "parent_authority_granted": False,
        },
    })
    return task, fence


def release_recovery_claim(
    registry: dict[str, Any],
    *,
    response_state: str,
    transition_id: str,
    transition_sequence: int,
    evidence_refs: list[str],
) -> dict[str, Any]:
    task = task_by_id(registry, RECOVERY_ID)
    parent = task_by_id(registry, PARENT_ID)
    old_claim = task.get("claim_id")
    old_fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(old_claim, str) or not isinstance(old_fence, int) or old_fence <= 20:
        raise RuntimeError("cannot release recovery without a valid fresh claim/fence")

    task.setdefault("evidence_refs", [])
    for ref in evidence_refs:
        if ref not in task["evidence_refs"]:
            task["evidence_refs"].append(ref)
    task.setdefault("transition_history", []).append({
        "response_state": response_state,
        "transition_id": transition_id,
        "transition_sequence": transition_sequence,
        "released_claim_id": old_claim,
        "released_fencing_token": old_fence,
        "authority_effect": "NONE_AFTER_ATTEMPT",
    })

    if response_state == "COMPLETED":
        task["state"] = "COMPLETED"
        task["archive_reason_codes"] = []
        task["block_ref"] = None
    elif response_state == "BLOCKED":
        task["state"] = "BLOCKED"
        task["archive_reason_codes"] = [transition_id]
        task["block_ref"] = task.get("handoff_ref")
    else:
        task["state"] = "HANDOFF_READY"
        task["archive_reason_codes"] = [f"RECOVERY_ATTEMPT_{response_state or 'UNKNOWN'}"]
        task["block_ref"] = None

    # Every bounded attempt releases its authority. A future retry must acquire a
    # new generation. The parent remains untouched and receives no authority.
    task["executor_binding"] = "AUTHORIZED" if task["state"] != "COMPLETED" else "UNBOUND"
    task["worker_id"] = None
    task["worker_instance_id"] = None
    task["claim_id"] = None
    task["lease"] = None
    task["heartbeat_timing"] = None
    task["independent_task_control"] = {
        "last_released_claim_id": old_claim,
        "last_released_fencing_token": old_fence,
        "heartbeat_granted_authority": False,
        "g18_authority_used": False,
        "g20_authority_reused": False,
        "parent_authority_granted": False,
    }
    if parent.get("claim_id") is not None or parent.get("worker_id") is not None:
        raise RuntimeError("recovery attempt unexpectedly altered parent authority")
    return task


def execute_once(root: Path, *, reference_epoch: int | None = None) -> dict[str, Any]:
    validate_registered_executor(root)
    registry_path = root / REGISTRY_PATH
    registry = load_json(registry_path)
    epoch = current_reference_epoch(root) if reference_epoch is None else int(reference_epoch)
    task, fence = acquire_recovery_claim(root, registry, reference_epoch=epoch)
    atomic_write(registry_path, registry)

    handoff = load_json(root / str(task["handoff_ref"]))
    adapter = ProcessWorkerAdapter(
        RECOVERY_COMMAND,
        cwd=root,
        timeout_seconds=30,
        env_allowlist=("STEGVERSE_MASTER_RECORDS_ROOT",),
    )
    try:
        response = adapter(task, handoff, epoch)
    except Exception:
        # Fail closed without stranding authority. The same admitted task may be
        # retried only after a fresh claim/fence is acquired.
        registry = load_json(registry_path)
        release_recovery_claim(
            registry,
            response_state="FAILED",
            transition_id="INDEPENDENT_RECOVERY_EXECUTOR_ERROR",
            transition_sequence=0,
            evidence_refs=[],
        )
        atomic_write(registry_path, registry)
        raise

    registry = load_json(registry_path)
    released = release_recovery_claim(
        registry,
        response_state=response.state,
        transition_id=response.transition_id,
        transition_sequence=response.transition_sequence,
        evidence_refs=list(response.evidence_refs),
    )
    atomic_write(registry_path, registry)
    return {
        "schema": "stegverse.independent-orphan-recovery-execution/v1",
        "task_id": RECOVERY_ID,
        "reference_epoch": epoch,
        "fencing_token": fence,
        "response_state": response.state,
        "transition_id": response.transition_id,
        "task_state_after_release": released.get("state"),
        "claim_active_after_attempt": released.get("claim_id") is not None,
        "parent_authority_granted": False,
        "heartbeat_granted_authority": False,
        "g18_authority_used": False,
        "github_token_required": False,
        "credential_authority": "TV/TVC",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one independently admitted Ecosystem Chat orphan-recovery attempt.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--reference-epoch", type=int, default=None)
    args = parser.parse_args()
    result = execute_once(Path(args.root).expanduser().resolve(), reference_epoch=args.reference_epoch)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["response_state"] in {"COMPLETED", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
