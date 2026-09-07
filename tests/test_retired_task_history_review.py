from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_goal_resolution_continuation.py"
SPEC = importlib.util.spec_from_file_location("evaluate_goal_resolution_continuation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RetiredTaskHistoryReviewTests(unittest.TestCase):
    def test_retired_is_terminal_and_never_emits_continuation(self) -> None:
        payload = {
            "goal_id": "GOAL-1",
            "returned_tasks": [{
                "task_id": "TASK-RETIRED",
                "cosv_task_vector": "10100000100000",
                "state": "RETIRED",
                "handoff": "docs/TASK_RETIRED_MIRROR_HANDOFF.md",
                "receipts": ["receipts/task-retired.json"],
                "next_admissible_work": {"kind": "SHOULD_NEVER_RUN", "ref": "x"},
            }],
        }
        result = MODULE.evaluate(payload, {
            "goal_resolution_continuation": {"default_report_interval_iterations": 5},
            "credential_authority": "TV/TVC",
        })
        self.assertEqual(result["disposition"], "RETIRED_TERMINAL")
        self.assertFalse(result["continue_machine_work"])
        self.assertEqual(result["continuation_requests"], [])
        self.assertTrue(result["retired_is_terminal"])

    def test_resurrection_is_history_review_only(self) -> None:
        payload = {
            "goal_id": "GOAL-1",
            "history_review": True,
            "returned_tasks": [{
                "task_id": "TASK-RETIRED",
                "cosv_task_vector": "10100000100000",
                "state": "RETIRED",
                "applicable_handoffs": ["docs/TASK_RETIRED_MIRROR_HANDOFF.md"],
                "receipts": ["receipts/task-retired.json"],
            }],
        }
        result = MODULE.evaluate(payload, {
            "goal_resolution_continuation": {"default_report_interval_iterations": 5},
            "credential_authority": "TV/TVC",
        })
        self.assertEqual(result["disposition"], "RETIRED_HISTORY_REVIEW")
        self.assertFalse(result["continue_machine_work"])
        self.assertEqual(result["continuation_requests"], [])
        review = result["history_review"][0]
        self.assertTrue(review["review_only"])
        self.assertFalse(review["execution_permitted"])
        self.assertFalse(review["continuation_permitted"])
        self.assertFalse(review["claim_or_fence_permitted"])
        self.assertFalse(review["transition_permitted"])
        self.assertTrue(review["new_work_requires_new_task_id"])


if __name__ == "__main__":
    unittest.main()
