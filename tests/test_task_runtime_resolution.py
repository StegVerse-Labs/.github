from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import datetime, timezone
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
build_mod = load_module("build_runtime_profile_map", "scripts/build_runtime_profile_map.py")


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

    def test_generated_map_preserves_sovereign_environment_candidate(self):
        generated = build_mod.build(ROOT, now=datetime(2026, 9, 4, 20, 0, tzinfo=timezone.utc))
        sovereign = next(p for p in generated["profiles"] if p["profile_id"] == "sovereign-runtime-worker-v1")
        self.assertIn("SOVEREIGN_RESIDENT", sovereign["declared"]["environment_classes"])
        task = resolve_mod.find_task(self.registry, "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001")
        result = resolve_mod.resolve(task, generated, "control/runtime-profile-map.json")
        self.assertIn("sovereign-runtime-worker-v1", result["candidate_profile_ids"])
        self.assertFalse(result["selection_grants_authority"])

    def test_standalone_projection_persists_without_aggregate_insertion_or_authority(self):
        task_id = "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
        task = resolve_mod.find_task(
            self.registry,
            task_id,
            ROOT / "data/canonical-task-records",
        )
        result = resolve_mod.resolve(task, self.runtime_map, "control/runtime-profile-map.json")
        before_aggregate = [row for row in self.registry.get("tasks", []) if row.get("task_id") == task_id]
        proposed = apply_mod.project_task_record(task, self.runtime_map, result, "control/runtime-profile-map.json")

        self.assertEqual(before_aggregate, [])
        self.assertEqual(proposed["task_id"], task_id)
        self.assertEqual(proposed["coordination_state"], task["coordination_state"])
        self.assertEqual(proposed["worker_claim"], task["worker_claim"])
        self.assertEqual(proposed["completion"], task["completion"])
        self.assertEqual(proposed["runtime_resolution"]["candidate_profile_ids"], ["canonical-work-coordination-runtime-v1"])
        self.assertTrue(proposed["runtime_resolution"]["projection_only"])
        self.assertFalse(proposed["runtime_resolution"]["selection_grants_authority"])

    def test_persisted_canonical_work_projection_matches_native_resolver(self):
        task_id = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
        receipt_path = ROOT / "receipts/runtime-profile-map/task-resolutions" / (task_id + ".json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        task = resolve_mod.find_task(self.registry, task_id)
        recomputed = resolve_mod.resolve(task, self.runtime_map, "control/runtime-profile-map.json")
        self.assertEqual(receipt["schema"], recomputed["schema"])
        self.assertEqual(receipt["task_id"], task_id)
        self.assertEqual(receipt["requirements"], task["runtime_requirements"])
        self.assertEqual(receipt["map_generation"], self.runtime_map["generation"])
        self.assertEqual(receipt["candidate_profile_ids"], recomputed["candidate_profile_ids"])
        self.assertEqual(receipt["evaluated"], recomputed["evaluated"])
        self.assertEqual(receipt["candidate_profile_ids"], ["canonical-work-coordination-runtime-v1"])
        projected = task["runtime_resolution"]
        self.assertEqual(projected["candidate_profile_ids"], receipt["candidate_profile_ids"])
        self.assertEqual(projected["resolved_at"], receipt["resolved_at"])
        self.assertEqual(projected["map_generation"], self.runtime_map["generation"])
        self.assertTrue(projected["projection_only"])
        self.assertFalse(projected["selection_grants_authority"])
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])

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
