from __future__ import annotations

from typing import Any

from .engine_v3 import HeartbeatRuntime as HeartbeatRuntimeV3, WorkerResponse


class HeartbeatRuntime(HeartbeatRuntimeV3):
    """Single-heartbeat runtime with blocked-work and human-boundary semantics."""

    def _human_boundary_valid(self, task: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
        ref = task.get("block_ref")
        if not isinstance(ref, str) or not ref or "#" in ref:
            return False, None
        path = self.root / ref
        if not path.exists():
            return False, None
        try:
            record = self._load(path)
        except Exception:
            return False, None
        valid = all([
            record.get("schema") == "stegverse.human-authority-boundary/v0.1",
            record.get("task_id") == task.get("task_id"),
            isinstance(record.get("requested_decision"), str) and bool(record.get("requested_decision")),
            isinstance(record.get("authority_source"), str) and bool(record.get("authority_source")),
            isinstance(record.get("evidence_refs"), list) and bool(record.get("evidence_refs")),
            isinstance(record.get("resume_trigger"), str) and bool(record.get("resume_trigger")),
            record.get("status") in {"PENDING", "RESOLVED", "WITHDRAWN"},
            record.get("automation_terminal") is True,
        ])
        return valid, record

    def _recheck_blocked_tasks(self, registry: dict[str, Any], epoch: int, events: list[dict[str, Any]]) -> None:
        by_id = {task.get("task_id"): task for task in registry.get("tasks", [])}
        for task in list(registry.get("tasks", [])):
            state = task.get("state")
            if state == "HUMAN_AUTHORITY_REQUIRED":
                valid, boundary = self._human_boundary_valid(task)
                self._event(
                    events,
                    epoch,
                    "human_authority_required",
                    task_id=task.get("task_id"),
                    boundary_ref=task.get("block_ref"),
                    boundary_valid=valid,
                    requested_decision=boundary.get("requested_decision") if boundary else None,
                    resume_trigger=boundary.get("resume_trigger") if boundary else None,
                    automation_terminal=True,
                )
                task["archive_eligible"] = False
                task["archive_reason_codes"] = sorted(set(task.get("archive_reason_codes", []) + [
                    "HUMAN_AUTHORITY_REQUIRED",
                    "AUTOMATION_TERMINAL_UNTIL_HUMAN_DECISION",
                ]))
                continue

            if state != "BLOCKED" or task.get("worker_id"):
                continue
            handoff = self._handoff(task)
            block = handoff.get("block")
            if not isinstance(block, dict):
                self._event(events, epoch, "block_recheck_deferred", task_id=task.get("task_id"), reason="BLOCK_CONTRACT_MISSING")
                continue
            dependency = block.get("dependency")
            observer = block.get("observer")
            trigger = block.get("recheck_trigger")
            if not isinstance(observer, str) or not observer or not isinstance(trigger, str) or not trigger:
                self._event(events, epoch, "block_recheck_deferred", task_id=task.get("task_id"), reason="BLOCK_OBSERVER_OR_TRIGGER_MISSING")
                continue

            dependency_task = by_id.get(dependency) if isinstance(dependency, str) else None
            released = dependency_task is not None and dependency_task.get("state") == "COMPLETED"
            self._event(
                events,
                epoch,
                "block_rechecked",
                task_id=task.get("task_id"),
                dependency=dependency,
                observer=observer,
                recheck_trigger=trigger,
                released=released,
            )
            if not released:
                continue

            task["state"] = "HANDOFF_READY"
            task["block_ref"] = None
            task["archive_eligible"] = False
            task["archive_reason_codes"] = [
                code for code in task.get("archive_reason_codes", [])
                if not code.startswith("BLOCKED_") and code != "BLOCKED"
            ]
            handoff["state"] = "HANDOFF_READY"
            handoff["block"] = None
            self._atomic_write(self.root / task["handoff_ref"], handoff)
            self._event(
                events,
                epoch,
                "block_released",
                task_id=task.get("task_id"),
                dependency=dependency,
                new_state="HANDOFF_READY",
            )

    def _activate_one(self, registry: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> bool:
        self._recheck_blocked_tasks(registry, epoch, events)
        return super()._activate_one(registry, epoch, cost_log, events)


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
