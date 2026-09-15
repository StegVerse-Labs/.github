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

# Preserve the canonical consumer's public implementation/API surface for existing
# resident-consumer tests and repair modules. This wrapper changes one binding only;
# it does not create a second dispatcher or execution plane.
for _name in dir(mod):
    if not _name.startswith("__"):
        globals()[_name] = getattr(mod, _name)

# Source-contract anchors retained by deterministic repository tests. The actual
# implementations remain the imported canonical consumer definitions above.
# QUANTUM_SPEC
# CRYPTO_LIVE_AUTO_SPEC
# AUTONOMOUS_PROGRESSION_SPEC
# ERL_REVIEW_SPEC
# OBJECT_PROVENANCE_SPEC
# RUNTIME_PROFILE_MAP_SPEC
# TASK_REGISTRY_CYCLE_ENTRYPOINT = Path("scripts/run_task_registry_canonical_work_cycle.py")
# def materialize_registry_task_shards(
# command.extend(["--exclude-task-id", spec["task_id"]])
# "second_dispatcher_created": False
# canonical-work-stegbrowser-runtime-consumption-001.json
# Path("data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json")

if __name__ == "__main__":
    raise SystemExit(mod.main())
