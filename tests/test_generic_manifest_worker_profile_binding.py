from __future__ import annotations

import json
from pathlib import Path

from heartbeat_runtime.admitted_worker_runtime import WorkerCoordinator
from scripts.run_worker_runtime import load_adapters

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"
TASK_FRAGMENT = ROOT / "control" / "worker-registry.d" / "sdk-tt-purpose-bound-worker-runtime-proof-001.json"
PROVIDER_FRAGMENT = ROOT / "control" / "worker-registry.d" / "stegagents-governed-runtime-001.json"
PROFILE_REGISTRY = ROOT / "control" / "worker-capability-profiles.json"


def test_manifest_bound_task_resolves_shared_provider_generically() -> None:
    runtime = WorkerCoordinator(ROOT, adapters=load_adapters(ROOT))
    registry = {
        "schema": "stegverse.heartbeat-worker-registry/v0.1",
        "generation": 0,
        "tasks": [],
        "workers": [],
    }

    applied = runtime._apply_registry_fragments(registry, task_id_filter=TASK_ID)
    task = next(row for row in registry["tasks"] if row["task_id"] == TASK_ID)

    assert str(TASK_FRAGMENT.relative_to(ROOT)) in applied
    assert str(PROVIDER_FRAGMENT.relative_to(ROOT)) in applied
    assert task["claim_id"] is None
    assert task["worker_id"] is None
    assert task["worker_instance_id"] is None

    worker = runtime._worker_for(task, registry)
    assert worker is not None
    assert worker["worker_id"] == "stegagents-governed-runtime-worker"
    assert worker["capability_profile_ref"] == (
        "control/worker-capability-profiles.json#stegagents-governed-runtime-v1"
    )

    profiles = json.loads(PROFILE_REGISTRY.read_text(encoding="utf-8"))
    profile = next(
        row for row in profiles["profiles"]
        if row["profile_id"] == "stegagents-governed-runtime-v1"
    )
    assert profile["availability_grants_authority"] is False
    assert profile["capability_match_grants_authority"] is False
    assert profile["mutation_allowed"] is False
    assert profile["deployment_allowed"] is False
