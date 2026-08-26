"""Canonical WorkerCoordinator wrapper with mandatory pre-initiation packet review."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .worker_runtime_legacy import WorkerCoordinator as LegacySeparatedWorkerCoordinator, ProcessWorkerAdapter
from .worker_task_admission import persist_admission_receipt, review_worker_task_admission


class WorkerCoordinator(LegacySeparatedWorkerCoordinator):
    """Require a fresh fail-closed task admission review before worker initiation.

    The review itself grants no authority. Only an ADMIT verdict permits the
    existing separated WorkerCoordinator to continue into assignment/claim/fence/
    timer creation under authority it independently verifies.
    """

    def _activate_from_trigger(
        self,
        registry: dict[str, Any],
        trigger: dict[str, Any],
        carrier_epoch: int,
        cost_log: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> bool:
        task_id = trigger.get("task_id")
        task = next((item for item in registry.get("tasks", []) if item.get("task_id") == task_id), None)
        if task is None:
            self._event(events, carrier_epoch, "worker_task_admission_blocked", task_id=task_id, reason="TASK_NOT_FOUND", authority_effect=False)
            return False

        try:
            handoff = self._handoff(task)
        except Exception as exc:
            self._event(events, carrier_epoch, "worker_task_admission_blocked", task_id=task_id, reason="HANDOFF_UNREADABLE", detail=type(exc).__name__, authority_effect=False)
            return False

        state_current, _ = self._semantic_state_preclaim(task)
        by_id = {item["task_id"]: item for item in registry.get("tasks", []) if item.get("task_id")}
        dependencies_complete = self._dependencies_complete(task, by_id)
        execution_authorized = self._execution_authorized(handoff)
        worker_resolved = self._worker_for(task, registry) is not None
        source = str(trigger.get("source") or "HEARTBEAT_CARRIER_OBSERVATION")

        packet = review_worker_task_admission(
            root=Path(self.root),
            task=task,
            handoff=handoff,
            registry=registry,
            carrier_epoch=carrier_epoch,
            trigger_source=source,
            execution_authorized=execution_authorized,
            dependencies_complete=dependencies_complete,
            worker_resolved=worker_resolved,
            semantic_state_current=state_current,
        )
        receipt_ref = None
        if self._persist:
            receipt = persist_admission_receipt(Path(self.root), packet)
            receipt_ref = str(receipt.relative_to(Path(self.root)))
        verdict = packet["review"]["verdict"]
        self._event(
            events,
            carrier_epoch,
            "worker_task_admission_reviewed",
            task_id=task_id,
            packet_id=trigger.get("packet_id"),
            heartbeat_id=packet["heartbeat_id"],
            admission_packet_sha256=packet["packet_sha256"],
            admission_receipt_ref=receipt_ref,
            verdict=verdict,
            reasons=packet["review"]["reasons"],
            authority_effect=False,
        )
        task["last_worker_task_admission"] = {
            "verdict": verdict,
            "packet_sha256": packet["packet_sha256"],
            "heartbeat_id": packet["heartbeat_id"],
            "receipt_ref": receipt_ref,
            "authority_effect": "NONE",
        }
        if verdict != "ADMIT":
            task["reconciliation_disposition"] = verdict
            task["reconciliation_reason"] = ",".join(packet["review"]["reasons"])
            return False

        return super()._activate_from_trigger(registry, trigger, carrier_epoch, cost_log, events)


__all__ = ["WorkerCoordinator", "ProcessWorkerAdapter"]
