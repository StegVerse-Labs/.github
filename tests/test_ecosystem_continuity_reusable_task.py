import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class EcosystemContinuityReusableTaskTests(unittest.TestCase):
    def test_reusable_identity_resolves_once_and_uses_bounded_runner(self):
        registry = json.loads((ROOT / "data" / "reusable-task-registry.json").read_text(encoding="utf-8"))
        rows = [row for row in registry["tasks"] if row.get("reusable_task_id") == "RT-ECOSYSTEM-CONTINUITY-EVALUATION-001"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("existing_task_ref"), "ECOSYSTEM-CONTINUITY-EVALUATOR-001")
        self.assertEqual(row.get("runner_templates"), ["scripts/run_ecosystem_continuity_reusable_task.py"])
        self.assertIn("RECOVERY_NOT_SELF_CERTIFIED", row.get("completion_predicates", []))
        self.assertTrue((ROOT / row["runner_templates"][0]).is_file())

    def test_parent_task_and_cosv_remain_canonical(self):
        record = json.loads((ROOT / "data" / "canonical-task-records" / "ECOSYSTEM-CONTINUITY-EVALUATOR-001.json").read_text(encoding="utf-8"))
        vector = json.loads((ROOT / "control" / "task-vectors" / "ECOSYSTEM-CONTINUITY-EVALUATOR-001.json").read_text(encoding="utf-8"))
        self.assertEqual(record["coordination_state"], "ACTIVE")
        self.assertEqual(record["cosv_task_vector"], "71000000100111")
        self.assertEqual(vector["vector"], "71000000100111")
        self.assertEqual(vector["task_id"], "ECOSYSTEM-CONTINUITY-EVALUATOR-001")


if __name__ == "__main__":
    unittest.main()
