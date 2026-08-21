from __future__ import annotations

from pathlib import Path
from typing import Any
import json

TASK_CAPABLE_EVENT_TYPES = {
    "worker_registry_fragments_applied",
    "worker_response_observed",
    "worker_assignment_bound_from_carrier_packet",
    "worker_assignment_bound_from_independent_task_control",
    "worker_assignment_timer_expired",
    "worker_assignment_timer_reached_zero",
    "successor_reconstruction_accepted",
}


def task_capable_worker_cycle_observed(root: Path, worker_state: dict[str, Any], target_epoch: int) -> bool:
    """Observe downstream task-capable worker activity without gating heartbeat.

    This helper exists only for runtime-goal evidence such as G18 completion. It
    never participates in oscillator progression or heartbeat release. Canonical
    worker events may use ``epoch``; historical events may use ``carrier_epoch``.
    The observer-only shim event is intentionally insufficient.
    """
    if not isinstance(target_epoch, int) or target_epoch < 0:
        return False

    mode = str(worker_state.get("observation_mode") or "")
    observed = worker_state.get("last_observed_carrier_epoch")
    if (
        mode == "TASK_CAPABLE_WORKER_COORDINATOR"
        and isinstance(observed, int)
        and observed >= target_epoch
        and int(worker_state.get("runtime_tick", 0) or 0) > 0
    ):
        return True

    path = Path(root) / "events" / "worker-runtime.jsonl"
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("event_type") not in TASK_CAPABLE_EVENT_TYPES:
            continue
        event_epoch = event.get("epoch", event.get("carrier_epoch"))
        if isinstance(event_epoch, int) and event_epoch >= target_epoch:
            return True
    return False


__all__ = ["task_capable_worker_cycle_observed", "TASK_CAPABLE_EVENT_TYPES"]
