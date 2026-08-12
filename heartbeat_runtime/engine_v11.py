from __future__ import annotations

from typing import Any

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
