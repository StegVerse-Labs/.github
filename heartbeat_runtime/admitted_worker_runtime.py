"""Canonical WorkerCoordinator wrapper with mandatory pre-initiation packet review."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .coordination_graph import review_coordination_preflight
from .worker_runtime_legacy import WorkerCoordinator as LegacySeparatedWorkerCoordinator, ProcessWorkerAdapter
from .worker_task_admission import persist_admission_receipt, review_worker_task_admission


class WorkerCoordinator(LegacySeparatedWorkerCoordinator):
    """Require fresh fail-closed coordination and task-admission review.

    Cross-task coordination is mandatory for autonomous augmentation. Neither
    coordination review nor task-admission review grants authority. Only passing
    reviews permit the existing separated WorkerCoordinator to continue into
    assignment/claim/fence/timer creation under authority it independently verifies.
    """

    def _coordination_review(
        self,
        task: dict[str, Any],
        carrier_epoch: int,
        events: list[dict[str, Any]],
    ) -> bool:
        root = Path(self.root)
        ledger_path = root / "control" / "cross-task-coordination.json"
        ledger: dict[str, Any] | None = None
        if ledger_path.exists():
            try:
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            except Exception as exc:
                self._event(
                    events,
                    carrier_epoch,
                    "cross_task_coordination_blocked",
                    task_id=task.get("task_id"),
                    reason="COORDINATION_LEDGER_UNREADABLE",
                    detail=type(exc).__name__,
                    authority_effect=False,
                )
                return False

        ledger_task = None
        if ledger is not None:
            ledger_task = next(
                (item for item in ledger.get("tasks", []) if item.get("task_id") == task.get("task_id")),
                None,
            )
        autonomous = bool(task.get("autonomous_augmentation")) or bool(
            isinstance(ledger_task, dict) and ledger_task.get("autonomous_augmentation")
        )
        if not autonomous:
            return True

        if ledger is None:
            self._event(
                events,
                carrier_epoch,
                "cross_task_coordination_blocked",
                task_id=task.get("task_id"),
                reason="COORDINATION_LEDGER_REQUIRED_FOR_AUTONOMOUS_AUGMENTATION",
                authority_effect=False,
            )
            task["last_coordination_preflight"] = {
                "verdict": "BLOCK_COORDINATION",
                "reasons": ["COORDINATION_LEDGER_REQUIRED_FOR_AUTONOMOUS_AUGMENTATION"],
                "authority_effect": "NONE",
            }
            return False

        preflight = review_coordination_preflight(ledger=ledger, task=task)
        receipt_ref = None
        if self._persist:
            task_id = str(task.get("task_id") or "UNKNOWN").replace("/", "_")
            receipt = root / "receipts" / "cross-task-coordination" / f"{task_id}-hb{int(carrier_epoch):08d}.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            receipt_ref = str(receipt.relative_to(root))

        self._event(
            events,
            carrier_epoch,
            "cross_task_coordination_reviewed",
            task_id=task.get("task_id"),
            verdict=preflight.get("verdict"),
            reasons=preflight.get("reasons"),
            collision_claims=[item.get("claim_id") for item in preflight.get("collisions", [])],
            newly_unblocked_tasks=preflight.get("newly_unblocked_tasks", []),
            coordination_receipt_ref=receipt_ref,
            authority_effect=False,
        )
        task["last_coordination_preflight"] = {
            "verdict": preflight.get("verdict"),
            "reasons": preflight.get("reasons"),
            "receipt_ref": receipt_ref,
            "authority_effect": "NONE",
        }
        if preflight.get("verdict") != "ADMIT_COORDINATION":
            task["reconciliation_disposition"] = "BLOCK_COORDINATION"
            task["reconciliation_reason"] = ",".join(preflight.get("reasons") or [])
            return False
        return True

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

        if not self._coordination_review(task, carrier_epoch, events):
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
