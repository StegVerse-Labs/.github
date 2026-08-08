from __future__ import annotations

from typing import Any

from .engine_v7 import HeartbeatRuntime as HeartbeatRuntimeV7, WorkerResponse


class HeartbeatRuntime(HeartbeatRuntimeV7):
    """v7 compatibility fix preserving the worker-returned checkpoint reference."""

    def _invoke(self, registry: dict[str, Any], task: dict[str, Any], epoch: int, cost_log: dict[str, Any], events: list[dict[str, Any]]) -> None:
        handoff = self._handoff(task)
        timing_before = dict(task.get("heartbeat_timing") or {})
        checkpoint_before = task.get("last_checkpoint_ref")
        snapshot = {
            "worker_id": task.get("worker_id"),
            "worker_instance_id": task.get("worker_instance_id"),
            "claim_id": task.get("claim_id"),
            "fencing_token": timing_before.get("fencing_token"),
            "worker_checkpoint_ref": checkpoint_before,
            "heartbeat_timing": timing_before,
        }

        if not self._apply_policy_rebind(task, handoff, epoch, events):
            self._hold_for_policy_rebind(task, handoff, epoch, events)
            return

        # Call the resource/lifecycle layer directly so v7 does not write its
        # checkpoint before we can capture the worker-returned checkpoint ref.
        from .engine_v6 import HeartbeatRuntime as HeartbeatRuntimeV6
        HeartbeatRuntimeV6._invoke(self, registry, task, epoch, cost_log, events)

        timing_after = task.get("heartbeat_timing") or {}
        responded = timing_after.get("last_response_epoch") == epoch
        if not responded:
            return
        if not all(isinstance(snapshot.get(key), str) and snapshot.get(key) for key in ("worker_id", "worker_instance_id", "claim_id")):
            return

        checkpoint_after = task.get("last_checkpoint_ref")
        if isinstance(checkpoint_after, str) and checkpoint_after and checkpoint_after != checkpoint_before:
            snapshot["worker_checkpoint_ref"] = checkpoint_after
        elif isinstance(checkpoint_before, str) and checkpoint_before.startswith("checkpoints/workers/"):
            # Do not recursively embed the previous canonical envelope as if it
            # were a new worker-provided checkpoint.
            snapshot["worker_checkpoint_ref"] = None

        self._write_canonical_checkpoint(task, handoff, epoch, snapshot, events)


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
