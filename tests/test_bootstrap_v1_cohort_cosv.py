from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001": ("50000000102000", "control/worker-registry.d/bootstrap-v1-source-identity-freeze-001.json", "handoffs/BOOTSTRAP-V1-SOURCE-IDENTITY-FREEZE-001.json", 2),
    "BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001": ("50000000102000", "control/worker-registry.d/bootstrap-v1-release-candidate-freeze-001.json", "handoffs/BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001.json", 2),
    "BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001": ("50000000103000", "control/worker-registry.d/bootstrap-v1-distributable-bundle-001.json", "handoffs/BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001.json", 3),
    "BOOTSTRAP-V1-MATERIALIZATION-EVIDENCE-INTAKE-001": ("50000000102000", "control/worker-registry.d/bootstrap-v1-materialization-evidence-intake-001.json", "handoffs/BOOTSTRAP-V1-MATERIALIZATION-EVIDENCE-INTAKE-001.json", 2),
    "BOOTSTRAP-V1-RELEASE-GATE-001": ("50000000101000", "control/worker-registry.d/bootstrap-v1-release-gate-001.json", "handoffs/BOOTSTRAP-V1-RELEASE-GATE-001.json", 1),
    "BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001": ("50000000102000", "control/worker-registry.d/bootstrap-v1-source-package-production-001.json", "handoffs/BOOTSTRAP-V1-SOURCE-PACKAGE-PRODUCTION-001.json", 2),
    "BOOTSTRAP-V1-INTR-BUNDLE-DELIVERY-001": ("50000000103000", "control/worker-registry.d/bootstrap-v1-intr-bundle-delivery-001.json", "handoffs/BOOTSTRAP-V1-INTR-BUNDLE-DELIVERY-001.json", 3),
}

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class BootstrapV1CohortCOSVTests(unittest.TestCase):
    def test_vectors_recompute_and_match_exact_blocker_counts(self):
        for task_id, (expected, frag_path, hand_path, blocker_count) in TASKS.items():
            record = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text(encoding="utf-8"))
            fragment = json.loads((ROOT / frag_path).read_text(encoding="utf-8"))
            handoff = json.loads((ROOT / hand_path).read_text(encoding="utf-8"))
            task = next(x for x in fragment["tasks"] if x["task_id"] == task_id)
            self.assertTrue(cosv.validate_record(record), task_id)
            self.assertEqual(cosv.encode_task(record["exact_metrics"]), expected, task_id)
            self.assertEqual(record["vector"], expected, task_id)
            self.assertEqual(record["exact_metrics"]["blocker_count"], blocker_count, task_id)
            self.assertEqual(task["admissible_existence"]["blockers"], handoff["admissible_existence"]["blockers"], task_id)
            self.assertEqual(len(task["admissible_existence"]["blockers"]), blocker_count, task_id)

    def test_all_tasks_are_machine_owned_and_non_promoting(self):
        for task_id, (_, frag_path, hand_path, _) in TASKS.items():
            record = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text(encoding="utf-8"))
            fragment = json.loads((ROOT / frag_path).read_text(encoding="utf-8"))
            handoff = json.loads((ROOT / hand_path).read_text(encoding="utf-8"))
            task = next(x for x in fragment["tasks"] if x["task_id"] == task_id)
            self.assertFalse(task["archive_eligible"], task_id)
            self.assertEqual(handoff["state"], "HANDOFF_READY_MACHINE_OWNED", task_id)
            self.assertFalse(handoff["task"]["manual_execution_allowed"], task_id)
            self.assertIsNone(task["admissible_existence"]["activation_proof_ref"], task_id)
            self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"], task_id)
            self.assertFalse(handoff["authority"]["github_token_required"], task_id)
            self.assertFalse(record["exact_metrics"]["evidence_complete"], task_id)
            self.assertFalse(record["exact_metrics"]["activated"], task_id)
            self.assertFalse(record["exact_metrics"]["propagated"], task_id)
            self.assertEqual(record["authority_effect"], "NONE", task_id)

    def test_index_and_coverage_partition_are_exact(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        indexed = {row["task_id"]: row for row in index["tasks"]}
        for task_id, (expected, _, _, _) in TASKS.items():
            self.assertEqual(indexed[task_id]["vector"], expected)
            self.assertNotIn(task_id, coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertGreaterEqual(index["coverage"]["indexed_vectorized_tasks"], len(TASKS))
        self.assertGreaterEqual(coverage["worker_registry_summary"]["canonically_indexed_task_ids"], len(TASKS))
        self.assertEqual(
            coverage["organization_registry_summary"]["active_unvectorized_task_ids"],
            len(coverage["active_organization_task_ids_missing_canonical_cosv"]),
        )
        self.assertEqual(
            coverage["total_active_unvectorized_unique_task_ids"],
            coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"]
            + coverage["organization_registry_summary"]["active_unvectorized_task_ids"],
        )

    def test_bootstrap_runtime_and_release_claims_remain_false(self):
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        state = coverage["bootstrap_v1_cosv_cohort"]
        for key in (
            "runtime_activation_claimed",
            "source_identity_frozen",
            "release_candidate_frozen",
            "distributable_bundle_built",
            "source_packages_produced",
            "device_materialization_proof_observed",
            "intr_browser_delivery_observed",
            "release_authorized",
            "publication_performed",
        ):
            self.assertFalse(state[key], key)
        self.assertEqual(state["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
