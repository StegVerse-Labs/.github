from __future__ import annotations

from typing import Any

from .engine_v12 import HeartbeatRuntime as HeartbeatRuntimeV12, WorkerResponse


class HeartbeatRuntime(HeartbeatRuntimeV12):
    """Separated carrier with fragment-aware assignment-trigger observation.

    v12 intentionally keeps the heartbeat carrier non-authorizing, but it loaded
    only the canonical registry before producing unassigned-task trigger packets.
    Repository-owned registry fragments are admitted by the worker coordinator,
    so a fragment-only HANDOFF_READY task could remain invisible to the carrier
    forever and therefore never produce the non-authorizing packet the worker
    coordinator requires before binding an authorized worker.

    v13 closes that observation gap by applying the existing append-only,
    authority-neutral registry-fragment admission logic to the carrier's
    in-memory registry view immediately before assignment triggers are derived.
    The carrier still grants no claim, fence, credential, execution, merge, or
    repository authority and does not persist worker lifecycle state.
    """

    def _assignment_triggers(self, registry: dict[str, Any], epoch: int) -> list[dict[str, Any]]:
        # `_apply_registry_fragments` is inherited from engine_v9. It accepts only
        # NONE_REGISTRATION_ONLY fragments, requires github_token_required=false,
        # validates handoff/worker references, and only appends IDs absent from
        # the canonical registry. It cannot overwrite live claim/fence state.
        self._apply_registry_fragments(registry)
        return super()._assignment_triggers(registry, epoch)


__all__ = ["HeartbeatRuntime", "WorkerResponse"]
