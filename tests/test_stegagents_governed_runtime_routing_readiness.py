from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = ROOT / "data/canonical-task-records/STEGAGENTS-GOVERNED-RUNTIME-001.json"
MAP_PATH = ROOT / "control/runtime-profile-map.json"
READINESS = ROOT / "scripts/evaluate_task_runtime_routing_readiness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("runtime_readiness", READINESS)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_governed_stegagents_runtime_resolves_before_workercoordinator_claim():
    task = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    runtime_map = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    module = _load_module()

    assert task["runtime_requirements"] == {
        "capabilities": [
            "task_registry_reconciliation",
            "worker_claim_projection",
            "intr_task_admission",
            "canonical_artifact_validation",
            "master_records_reconciliation",
        ],
        "environment": "SOVEREIGN_RESIDENT",
        "direction": "INTERNAL",
        "mutation_required": True,
        "deployment_required": False,
        "current_observation_required": False,
    }

    projected = module.resolve_routing_projection(task, runtime_map)
    assert projected["candidate_profile_ids"] == ["canonical-work-coordination-runtime-v1"]
    assert projected["candidate_count"] == 1
    assert projected["selection_grants_authority"] is False
    assert projected["workercoordinator_admission_still_required"] is True
    assert projected["interlock_intr_transition_admission_still_required"] is True
    assert projected["master_records_reconciliation_still_required"] is True

    stored = task["runtime_resolution"]
    assert stored["map_ref"] == "control/runtime-profile-map.json"
    assert stored["map_generation"] == runtime_map["generation"]
    assert stored["candidate_profile_ids"] == projected["candidate_profile_ids"]
    assert stored["projection_only"] is True
    assert stored["selection_grants_authority"] is False

    claim = task["worker_claim"]
    assert claim["claim_ref"] is None
    assert claim["fence_ref"] is None
    assert task["completion"]["claimed"] is False
    assert task["completion"]["validated"] is False
