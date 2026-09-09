from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / "control" / "manifold-lineage.d" / "governed-multilane-manifold-activation-001.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "governed-multilane-manifold-activation-001.json"


class GovernedManifoldCompleteAllPolicyRegressionTests(unittest.TestCase):
    def test_request_and_lineage_preserve_complete_all_policy(self) -> None:
        lineage = json.loads(LINEAGE.read_text(encoding="utf-8"))
        request = json.loads(REQUEST.read_text(encoding="utf-8"))

        lineage_policy = lineage["execution_policy"]
        request_policy = request["lineage_policy"]
        for policy in (lineage_policy, request_policy):
            self.assertIs(policy.get("complete_all_declared_subordinates"), True)
            self.assertIs(
                policy.get("do_not_prune_incomplete_tasks_for_expected_future_consolidation"),
                True,
            )

        self.assertEqual(
            {node["task_id"] for node in lineage["nodes"]},
            set(request["subordinate_task_ids"]),
        )
        self.assertIn(
            "retiring or pruning an incomplete declared subordinate solely because shared infrastructure is expected to supersede its current implementation path",
            request["prohibited"],
        )
        self.assertIn("Incomplete declared children may not be retired", lineage["completion_rule"])


if __name__ == "__main__":
    unittest.main()
