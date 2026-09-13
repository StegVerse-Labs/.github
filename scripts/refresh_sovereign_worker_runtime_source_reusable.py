#!/usr/bin/env python3
"""Reusable-task adapter for sovereign source refresh.

Extends the proven local-only source refresh with the neutral reusable-task scheduler
artifacts required by reusable scheduling, then delegates to the canonical refresh()
implementation. No second refresh algorithm, network source transport, credential
route, or runtime authority is introduced.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import refresh_sovereign_worker_runtime_source as base

EXTRA_STATIC_FILES = (
    Path("scripts/refresh_sovereign_worker_runtime_source_reusable.py"),
    Path("scripts/run_reusable_task_scheduler.py"),
    Path("data/reusable-task-scheduler-contract.json"),
)


def parameters() -> dict[str, object]:
    raw = os.environ.get("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "{}")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("reusable source-refresh parameters must be an object")
    return value


def main() -> int:
    value = parameters()
    source_raw = str(value.get("source_root") or "").strip()
    runtime_raw = str(value.get("runtime_root") or "").strip()
    if not source_raw or not runtime_raw:
        raise RuntimeError("reusable source refresh requires source_root and runtime_root")

    for rel in EXTRA_STATIC_FILES:
        if rel not in base.STATIC_FILES:
            base.STATIC_FILES = base.STATIC_FILES + (rel,)

    receipt = base.refresh(Path(source_raw), Path(runtime_raw))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
