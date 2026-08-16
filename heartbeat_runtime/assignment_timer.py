from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json


TRIGGER_SCHEMA = "stegverse.worker-assignment-trigger/v1"
TIMER_SCHEMA = "stegverse.worker-assignment-timer/v1"
RECORD_SCHEMA = "stegverse.master-records-worker-assignment-record/v1"


def _sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AssignmentTimer:
    task_id: str
    worker_id: str
    worker_instance_id: str
    claim_id: str
    fencing_token: int
    allocated_hb_units: int
    remaining_hb_units: int
    cost_basis_ref: str | None
    expiry_basis: str
    runtime_tick: int = 0

    def tick(self, count: int = 1) -> "AssignmentTimer":
        if count < 0:
            raise ValueError("timer tick count must be non-negative")
        return AssignmentTimer(
            task_id=self.task_id,
            worker_id=self.worker_id,
            worker_instance_id=self.worker_instance_id,
            claim_id=self.claim_id,
            fencing_token=self.fencing_token,
            allocated_hb_units=self.allocated_hb_units,
            remaining_hb_units=max(0, self.remaining_hb_units - count),
            cost_basis_ref=self.cost_basis_ref,
            expiry_basis=self.expiry_basis,
            runtime_tick=self.runtime_tick + count,
        )

    @property
    def expired(self) -> bool:
        return self.remaining_hb_units <= 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": TIMER_SCHEMA,
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "worker_instance_id": self.worker_instance_id,
            "claim_id": self.claim_id,
            "fencing_token": self.fencing_token,
            "allocated_hb_units": self.allocated_hb_units,
            "remaining_hb_units": self.remaining_hb_units,
            "timer_unit": "HB_UNIT",
            "timer_clock": "WORKER_RUNTIME_INTERNAL",
            "carrier_epoch_controls_expiry": False,
            "carrier_presence_controls_expiry": False,
            "cost_basis_ref": self.cost_basis_ref,
            "expiry_basis": self.expiry_basis,
            "runtime_tick": self.runtime_tick,
            "expired": self.expired,
        }


def assignment_trigger_packet(*, carrier_epoch: int, task: dict[str, Any]) -> dict[str, Any]:
    """Build the non-authorizing carrier state that may transition into MR custody."""
    stable = {
        "carrier_epoch": carrier_epoch,
        "task_id": task.get("task_id"),
        "goal_id": task.get("goal_id"),
        "handoff_ref": task.get("handoff_ref"),
        "executor_binding": task.get("executor_binding"),
        "cost_basis_ref": task.get("cost_basis_ref"),
    }
    return {
        "schema": TRIGGER_SCHEMA,
        **stable,
        "packet_id": "HBTRIG-" + _sha256(stable)[:20],
        "state": "CARRIED_UNASSIGNED_TASK_OBSERVATION",
        "observation": "UNASSIGNED_TASK_PRESENT",
        "authority_effect": "NONE",
        "execution_authority": False,
        "claim_authority": False,
        "timer_authority": False,
        "single_use_transition": True,
        "terminal_destination": "MASTER_RECORDS",
    }


def bind_assignment_from_trigger(
    *,
    trigger: dict[str, Any],
    worker_id: str,
    worker_instance_id: str,
    claim_id: str,
    fencing_token: int,
    allocated_hb_units: int,
    expiry_basis: str,
) -> tuple[AssignmentTimer, dict[str, Any]]:
    """Transition the carried packet into the durable Master Records state.

    There is no second packet. The carrier packet's identity is preserved while
    its state changes from an unassigned-task observation into the durable bound
    worker-assignment record retained by Master Records. Authorization and worker
    selection must already have been established outside the carrier.
    """
    if trigger.get("schema") != TRIGGER_SCHEMA:
        raise ValueError("unsupported assignment trigger schema")
    if trigger.get("authority_effect") != "NONE" or trigger.get("execution_authority") is not False:
        raise ValueError("carrier trigger may not grant authority")
    if allocated_hb_units < 1:
        raise ValueError("allocated_hb_units must be >= 1")

    timer = AssignmentTimer(
        task_id=str(trigger["task_id"]),
        worker_id=worker_id,
        worker_instance_id=worker_instance_id,
        claim_id=claim_id,
        fencing_token=fencing_token,
        allocated_hb_units=allocated_hb_units,
        remaining_hb_units=allocated_hb_units,
        cost_basis_ref=trigger.get("cost_basis_ref"),
        expiry_basis=expiry_basis,
    )

    record = {
        "schema": RECORD_SCHEMA,
        "packet_id": trigger.get("packet_id"),
        "prior_schema": trigger.get("schema"),
        "prior_state": trigger.get("state", "CARRIED_UNASSIGNED_TASK_OBSERVATION"),
        "state": "MASTER_RECORDS_BOUND_WORKER_ASSIGNMENT",
        "state_transition": "CARRIED_UNASSIGNED_TASK_OBSERVATION_TO_BOUND_WORKER_ASSIGNMENT",
        "carrier_epoch_observed": trigger.get("carrier_epoch"),
        "task_id": timer.task_id,
        "goal_id": trigger.get("goal_id"),
        "handoff_ref": trigger.get("handoff_ref"),
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "claim_id": claim_id,
        "fencing_token": fencing_token,
        "assignment_timer": timer.as_dict(),
        "custodian": "master-records/orchestration",
        "master_records_binding_required": True,
        "recording_effect": "STATE_TRANSITION_CUSTODY",
        "carrier_packet_continues_after_transition": False,
        "separate_transition_packet_created": False,
        "carrier_granted_authority": False,
        "carrier_controls_timer": False,
        "authority_effect": "NONE_FROM_CARRIER",
    }
    record["record_sha256"] = _sha256(record)
    return timer, record


__all__ = [
    "AssignmentTimer",
    "assignment_trigger_packet",
    "bind_assignment_from_trigger",
    "TRIGGER_SCHEMA",
    "TIMER_SCHEMA",
    "RECORD_SCHEMA",
]
