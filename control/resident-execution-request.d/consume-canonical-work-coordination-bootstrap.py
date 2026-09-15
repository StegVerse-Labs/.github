#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE / "consume-canonical-work-coordination-bootstrap.legacy.py"
ACTIVE_TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
ACTIVE_SHARD = Path("data/canonical-task-records/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json")

spec = importlib.util.spec_from_file_location("canonical_work_consumer_legacy", LEGACY)
if spec is None or spec.loader is None:
    raise RuntimeError("legacy canonical work consumer loader unavailable")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Correct only the StegBrowser invocation owner. The retired task remains operation lineage.
mod.STEGBROWSER_RUNTIME_CONSUMPTION_SPEC["task_id"] = ACTIVE_TASK
if ACTIVE_SHARD not in mod.PRESERVE_IF_PRESENT:
    mod.PRESERVE_IF_PRESENT = tuple(mod.PRESERVE_IF_PRESENT) + (ACTIVE_SHARD,)

if __name__ == "__main__":
    raise SystemExit(mod.main())
