from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


resolve_mod = load_module("resolve_task_runtime_candidates", "scripts/resolve_task_runtime_candidates.py")
apply_mod = load_module("apply_task_runtime_resolution_projection", "scripts/apply_task_runtime_resolution_projection.py")


class RuntimeResolutionTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text(encoding="utf-8"))
        self.runtime_map = json.loads((ROOT / "control/runtime-profile-map.json").read_text(encoding="utf-8"))

    def test_canonical_work_resolves_only_as_non_authorizing_candidate(self):
        task = resolve_mod.find_task(self.registry, "STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        result = resolve_mod.resolve(task, self.runtime_map, "control/runtime-profile-map.json")
        self.assertFalse(result["selection_grants_authority"])
        self.assertTrue(result["projection_only"])
        self.assertIn("canonical-work-coordination-runtime-v1", result["candidate_profile_ids"])
        self.assertTrue(result["workercoordinator_admission_still_required"])
        self.assertTrue(result["interlock_intr_transition_admission_still_required"])

    def test_profile_map_build_has_sovereign_candidate_in_bootstrap_map(self):
        task = resolve_mod.find_task(self.registry, "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001")
        result = resolve_mod.resolve(task, self.runtime_map, "control/runtime-profile-map.json")
        self.assertIn("sovereign-runtime-worker-v1", result["candidate_profile_ids"])
        self.assertFalse(result["selection_grants_authority"])

    def test_projection_does_not_change_coordination_or_claim_state(self):
        task = resolve_mod.find_task(self.registry, "STEGVERSE-CANONICAL-WORK-COORDINATION-001")
        result = resolve_mod.resolve(task, self.runtime_map, "control/runtime-profile-map.json")
        before = resolve_mod.find_task(self.registry, task["task_id"])
        proposed = apply_mod.project(self.registry, self.runtime_map, result, "control/runtime-profile-map.json")
        after = resolve_mod.find_task(proposed, task["task_id"])
        self.assertEqual(before["coordination_state"], after["coordination_state"])
        self.assertEqual(before["worker_claim"], after["worker_claim"])
        self.assertTrue(after["runtime_resolution"]["projection_only"])
        self.assertFalse(after["runtime_resolution"]["selection_grants_authority"])


if __name__ == "__main__":
    unittest.main()
