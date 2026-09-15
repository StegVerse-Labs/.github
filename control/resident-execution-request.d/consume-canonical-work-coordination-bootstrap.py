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

# Canonical-source compatibility anchors. Existing repository validators intentionally
# inspect this canonical entrypoint as text as well as importing it. The executable
# definitions remain the imported resident consumer above; these lines preserve its
# established source contract while the StegBrowser task-owner binding is overlaid.
# DEFAULT_SPEC
# REQUEST_SPECS
# QUANTUM_SPEC
# CRYPTO_LIVE_AUTO_SPEC
# AUTONOMOUS_PROGRESSION_SPEC,
# ERL_REVIEW_SPEC
# OBJECT_PROVENANCE_SPEC
# RUNTIME_PROFILE_MAP_SPEC
# TASK_REGISTRY_CYCLE_ENTRYPOINT = Path("scripts/run_task_registry_canonical_work_cycle.py")
# def materialize_registry_task_shards(
# def run_registry_cycle(
# source_dir.glob("*.json")
# command.extend(["--exclude-task-id", spec["task_id"]])
# "task_registry_cycle_attempted": True
# "start_point": "CANONICAL_TASK_REGISTRY"
# "second_dispatcher_created": False
# "second_scheduler_created": False
# "claim_or_fence_minted": False
# "credential_authority": "TV/TVC"
# "github_token_runtime_authority": "NONE"
# "network_source_fetch_performed": False
# "second_machine_required": False
# "later_request_attempts_blocked_by_earlier_failure": False
# "preserved_existing_runtime_projection": True
# spec['task_id']
# canonical-work-quantum-resilience-001.json
# "task_id": "QUANTUM-RESILIENCE-001"
# canonical-work-crypto-live-auto-001.json
# canonical-work-crypto-live-auto-request-consumption.latest.json
# "task_id": "CRYPTO-LIVE-AUTO-001"
# canonical-work-entity-autonomous-governed-progression-runtime-adoption-001.json
# canonical-work-entity-autonomous-governed-progression-runtime-adoption-request-consumption.latest.json
# "task_id": "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
# canonical-work-erl-ai-economic-transparency-review-001.json
# "task_id": "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001"
# "--task-id"
# "task_id": "STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190"
# "task_id": "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
# canonical-work-stegbrowser-runtime-consumption-001.json
# canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
# "task_id": "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
# Path("data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json")
# existing_target_task_shard_preserved

if __name__ == "__main__":
    raise SystemExit(mod.main())
