from __future__ import annotations

import unittest

from scripts.estimate_worker_cost_basis import build


class WorkerCostBasisEstimatorTests(unittest.TestCase):
    def test_incomplete_samples_do_not_create_expiry(self):
        log = {
            "records": [
                {"heartbeat_epoch": 1, "task_id": "A", "transition_id": "WORK", "cost": {"task_class": "repo_change", "compute_units": 2}}
            ]
        }
        record = build(log)["repo_change"]
        self.assertEqual(record["sample_count"], 0)
        self.assertEqual(record["hb_estimate"]["confidence"], "NONE")
        self.assertIsNone(record["hb_estimate"]["expiry_candidate_beats"])

    def test_completed_samples_create_conservative_expiry(self):
        log = {"records": []}
        for task_id, finish in (("A", 3), ("B", 5), ("C", 4)):
            log["records"].append({
                "heartbeat_epoch": 1,
                "task_id": task_id,
                "transition_id": "WORK",
                "cost": {"task_class": "repo_change", "compute_units": 1, "external_cost_usd": 0}
            })
            log["records"].append({
                "heartbeat_epoch": finish,
                "task_id": task_id,
                "transition_id": "COMPLETE",
                "cost": {"task_class": "repo_change", "completed": True, "compute_units": 2, "external_cost_usd": 0, "evidence_refs": [f"evidence:{task_id}"]}
            })
        record = build(log)["repo_change"]
        self.assertEqual(record["sample_count"], 3)
        self.assertEqual(record["hb_estimate"]["confidence"], "LOW")
        self.assertEqual(record["hb_estimate"]["expected_completion_beats"], 4.0)
        self.assertEqual(record["hb_estimate"]["expiry_candidate_beats"], 7.0)
        self.assertTrue(record["selection_guidance"]["cost_never_overrides_admissibility"])

    def test_external_entity_class_is_retained_when_consistent(self):
        log = {"records": [
            {"heartbeat_epoch": 2, "task_id": "EXT-1", "transition_id": "WORK", "cost": {"task_class": "external_audit", "external_entity_class": "enterprise", "external_cost_usd": 3.0}},
            {"heartbeat_epoch": 4, "task_id": "EXT-1", "transition_id": "COMPLETE", "cost": {"task_class": "external_audit", "external_entity_class": "enterprise", "external_cost_usd": 5.0, "completed": True}}
        ]}
        record = build(log)["external_audit"]
        self.assertEqual(record["external_entity_class"], "enterprise")
        self.assertEqual(record["sample_count"], 1)
        self.assertEqual(record["cost_estimate"]["external_cost_usd"], 4.0)


if __name__ == "__main__":
    unittest.main()
