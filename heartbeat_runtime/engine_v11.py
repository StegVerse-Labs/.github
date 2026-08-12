from __future__ import annotations

from typing import Any
import hashlib
import json

from .engine_v9 import HeartbeatRuntime as HeartbeatRuntimeV9, WorkerResponse
from .engine_v10 import HeartbeatRuntime as HeartbeatRuntimeV10


class HeartbeatRuntime(HeartbeatRuntimeV10):
    """Compatibility activation of goal-preserving resolution escalation.

    Only a BLOCKED response that actually carries the machine-readable
    resolution contract is converted into a derived resolution task. Legacy
    internal lifecycle states that predate the contract remain observable under
    their existing semantics until migrated separately; this prevents a runtime
    upgrade from silently changing unrelated lifecycle authority behavior.
    """

    def _admit_resolution_task(
        self,
        registry: dict[str, Any],
        parent: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
        resolution_ref: str,
        contract: dict[str, Any],
    ) -> str:
        if self._persist:
            parent_priority = str(
                self._handoff(parent).get("task", {}).get("priority") or "critical"
            )
            task_id = super()._admit_resolution_task(
                registry, parent, epoch, events, resolution_ref, contract
            )
            # v10 historically emitted every resolution successor at `critical`.
            # v11 preserves the originating scheduler class so a release-priority
            # goal cannot be demoted merely because it entered RESOLVE/ESCALATE.
            handoff_path = self.root / "handoffs" / "generated" / f"{task_id}.json"
            if handoff_path.exists():
                generated = self._load(handoff_path)
                task = generated.get("task") or {}
                if task.get("priority") != parent_priority:
                    task["priority"] = parent_priority
                    generated["task"] = task
                    self._atomic_write(handoff_path, generated)
                    self._event(
                        events,
                        epoch,
                        "resolution_priority_inherited",
                        task_id=task_id,
                        parent_task_id=parent.get("task_id"),
                        inherited_priority=parent_priority,
                        authority_effect=False,
                    )
            return task_id

        # A dry-run must prove the transition without manufacturing generated
        # handoffs/cost bases that later phases of the same dry-run would try to
        # load from disk. Persisted cycles perform the full registry mutation.
        target_level = self._target_level(self._handoff(parent), contract)
        stable = {
            "parent_task_id": parent.get("task_id"),
            "dependency_class": contract.get("dependency_class"),
            "problem_statement": contract.get("problem_statement"),
            "target_level": target_level,
        }
        digest = hashlib.sha256(
            json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:12]
        task_id = f"DRYRUN-RESOLUTION-{parent['task_id']}-{digest}"
        self._event(
            events,
            epoch,
            "resolution_task_derivation_dry_run",
            task_id=task_id,
            parent_task_id=parent["task_id"],
            resolution_level=target_level,
            dependency_class=contract.get("dependency_class"),
            authority_effect=False,
            persisted=False,
        )
        return task_id

    def _invoke(
        self,
        registry: dict[str, Any],
        task: dict[str, Any],
        epoch: int,
        cost_log: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> None:
        # Bypass v10's strict missing-contract exception. ProcessWorkerAdapter
        # responses that pass blocker_policy always carry a resolution contract;
        # legacy in-process adapters may not yet do so.
        HeartbeatRuntimeV9._invoke(self, registry, task, epoch, cost_log, events)
        if task.get("state") != "BLOCKED":
            return
        found = self._latest_resolution_contract(task)
        if found is None:
            return
        resolution_ref, contract = found
        self._admit_resolution_task(registry, task, epoch, events, resolution_ref, contract)

    def _expire(
        self,
        registry: dict[str, Any],
        task: dict[str, Any],
        epoch: int,
        events: list[dict[str, Any]],
    ) -> None:
        # Expiry/orphan recovery is a distinct lifecycle contract. Preserve it
        # until its own migration is admitted rather than conflating it with a
        # worker-declared FAIL_CLOSED / conditional constraint.
        HeartbeatRuntimeV9._expire(self, registry, task, epoch, events)


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
