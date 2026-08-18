#!/usr/bin/env python3
"""Fail-closed production entrypoint for the canonical G18 activation worker.

The underlying worker owns the existing G18 behavior. This entrypoint narrows its
completion semantics so carrier observation alone cannot terminalize G18. A real
task-capable WorkerCoordinator cycle must be observable at or after the target
carrier epoch. No credential, claim, fence, carrier, or scheduler authority is
created here.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path.cwd().resolve()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load("sovereign_runtime_activation_worker_base", ROOT / "workers" / "sovereign_runtime_activation_worker.py")
release = _load("heartbeat_transition_release_guard", ROOT / "scripts" / "refresh_heartbeat_transition_receipt.py")
_base_state_transition_status = base.state_transition_status


def guarded_state_transition_status() -> dict:
    status = _base_state_transition_status()
    transition = base.load_json(base.TRANSITION_RECEIPT) or {}
    worker_state = base.load_json(ROOT / "control" / "worker-runtime-state.json") or {}
    target_epoch = transition.get("carrier_epoch_after")
    task_capable = (
        isinstance(target_epoch, int)
        and target_epoch >= 30
        and release.task_capable_worker_cycle_observed(ROOT, worker_state, target_epoch)
    )
    predicates = dict(status.get("predicates") or {})
    predicates["worker_task_capable_cycle_observed"] = task_capable
    status["predicates"] = predicates
    status["worker_observation_mode"] = worker_state.get("observation_mode")
    status["worker_runtime_tick"] = worker_state.get("runtime_tick")
    status["complete"] = bool(status.get("complete")) and task_capable
    return status


base.state_transition_status = guarded_state_transition_status


def main() -> int:
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
