"""Fail-closed projection repair for the pre-#2531 HIL browser G25 registry.

This does not execute a worker, issue a new claim/fence, alter a receipt, or
close a governed transition. A genuine machine-worker assignment must still
pass ordinary WorkerCoordinator admission and Master Records custody.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
BROWSER_CLAIM = "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25"
BROWSER_FENCE = 25
WORKER_ID = "hil-sovereign-receiver-worker"
REQUEST_ID = "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002"
LEASE_ID = "HIL-BROWSER-ESRL-7bafde4a280e847758da157e"
FRAGMENT = Path("control/worker-registry.d/hil-sovereign-receiver-001.json")
REQUEST = Path("receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json")
ESRL = Path("receipts/sovereign-host/hil-browser-esrl-evidence-intake.latest.json")
ASSIGNMENT_EVENTS = Path("events/master-records-worker-assignment.jsonl")


def _read(root: Path, relative: Path) -> tuple[dict[str, Any], str] | None:
    path = root / relative
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    return value, hashlib.sha256(raw).hexdigest()


def reconcile_legacy_hil_registration(root: Path, registry: dict[str, Any]) -> bool:
    """Repair *only* legacy static G25/worker slots after exact predecessor proof.

    Unknown, missing, contradictory or prior machine-assignment evidence leaves
    the registry untouched. Caller runs under the existing WorkerCoordinator
    lock; persistence is the caller's standard atomic registry write.
    """
    tasks = [row for row in registry.get("tasks", []) if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    workers = [row for row in registry.get("workers", []) if isinstance(row, dict) and row.get("worker_id") == WORKER_ID]
    if len(tasks) != 1 or len(workers) != 1:
        return False
    task, worker = tasks[0], workers[0]
    if not (
        task.get("state") == "HANDOFF_READY"
        and task.get("claim_id") == BROWSER_CLAIM
        and task.get("worker_id") == WORKER_ID
        and task.get("worker_instance_id") in (None, "")
        and task.get("heartbeat_timing") in (None, {})
        and task.get("assignment_timer") in (None, {})
        and task.get("lease") in (None, {})
        and task.get("handoff_ref") == "handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json"
        and task.get("authorized_policy_version") == "hil-sovereign-receiver-v0.1"
        and worker.get("status") == "AVAILABLE"
        and worker.get("adapter_ref") == "process:hil-sovereign-receiver-v1"
    ):
        return False
    # Never erase anything that could represent a genuine machine claim.
    if any(task.get(k) not in (None, "", {}, []) for k in (
        "claim_fence_master_records_transition", "atomic_activation_transition_receipt_sha256",
        "assignment_evidence_ref", "assignment_record", "constitutive_activation_receipt_ref",
    )):
        return False
    assignment_path = root / ASSIGNMENT_EVENTS
    if assignment_path.exists():
        try:
            for line in assignment_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    return False
                if row.get("task_id") == TASK_ID or row.get("claim_id") == BROWSER_CLAIM:
                    return False
        except (OSError, ValueError):
            return False

    source = _read(root, FRAGMENT)
    request = _read(root, REQUEST)
    esrl = _read(root, ESRL)
    if not source or not request or not esrl:
        return False
    fragment, fragment_sha = source
    req, request_sha = request
    lease, lease_sha = esrl
    declared = [row for row in fragment.get("tasks", []) if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    if len(declared) != 1:
        return False
    canonical = declared[0]
    canonical_lineage = (canonical.get("machine_readable_state") or {}).get("browser_predecessor_lineage") or {}
    current_state = task.get("machine_readable_state") or {}
    old_request = current_state.get("resident_request_consumption") or {}
    old_esrl = current_state.get("esrl_lease_open") or {}
    if not (
        fragment.get("schema") == "stegverse.worker-registry-fragment/v0.1"
        and canonical.get("state") == "HANDOFF_READY"
        and canonical.get("claim_id") is None
        and canonical.get("worker_id") is None
        and canonical.get("worker_instance_id") is None
        and canonical.get("handoff_ref") == task.get("handoff_ref")
        and canonical.get("authorized_policy_version") == task.get("authorized_policy_version")
        and canonical.get("admission", {}).get("minimum_fencing_token_exclusive") == BROWSER_FENCE
        and canonical_lineage.get("claim_id") == BROWSER_CLAIM
        and canonical_lineage.get("fencing_token") == BROWSER_FENCE
        and canonical_lineage.get("lease_id") == LEASE_ID
        and canonical_lineage.get("request_id") == REQUEST_ID
        and canonical_lineage.get("state") == "SATISFIED_PREDECESSOR_ONLY"
        and canonical_lineage.get("machine_worker_claim_reuse_allowed") is False
        and old_request.get("state") == "SATISFIED"
        and old_request.get("claim_id") == BROWSER_CLAIM
        and old_request.get("fencing_token") == BROWSER_FENCE
        and old_request.get("request_id") == REQUEST_ID
        and old_esrl.get("state") == "SATISFIED"
        and old_esrl.get("claim_id") == BROWSER_CLAIM
        and old_esrl.get("fencing_token") == BROWSER_FENCE
        and old_esrl.get("lease_id") == LEASE_ID
        and req.get("schema") == "stegverse.hil-resident-execution-request-consumption/v1"
        and req.get("state") == "COMPLETED"
        and req.get("task_id") == TASK_ID
        and req.get("claim_id") == BROWSER_CLAIM
        and req.get("fencing_token") == BROWSER_FENCE
        and req.get("request_id") == REQUEST_ID
        and esrl.get("schema") == "stegverse.hil-browser-esrl-evidence-intake/v1"
        and esrl.get("state") == "ACCEPTED"
        and esrl.get("esrl_lease_open_observed") is True
        and esrl.get("task_id") == TASK_ID
        and esrl.get("claim_id") == BROWSER_CLAIM
        and esrl.get("fencing_token") == BROWSER_FENCE
        and esrl.get("lease_id") == LEASE_ID
    ):
        return False
    # Preserve all existing historical evidence/functional-memory fields;
    # only static registration slots and the current admission declaration move.
    task["claim_id"] = None
    task["worker_id"] = None
    task["worker_instance_id"] = None
    task["admission"] = dict(canonical["admission"])
    task.setdefault("machine_readable_state", {})["browser_predecessor_lineage"] = dict(canonical_lineage)
    task["legacy_hil_registration_reconciliation"] = {
        "state": "STATIC_PROJECTION_RECONCILED_PRECLAIM",
        "previous_browser_claim_id": BROWSER_CLAIM,
        "previous_browser_fencing_token": BROWSER_FENCE,
        "canonical_fragment_sha256": fragment_sha,
        "retained_request_receipt_sha256": request_sha,
        "retained_esrl_receipt_sha256": lease_sha,
        "machine_claim_minted": False,
        "master_records_assignment_inferred": False,
        "authority_effect": "NONE_STATIC_PROJECTION_ONLY",
    }
    return True
