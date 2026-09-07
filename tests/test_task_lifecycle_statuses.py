from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_goal_resolution_continuation.py"
SPEC = importlib.util.spec_from_file_location("evaluate_goal_resolution_continuation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CONTRACT = {
    "goal_resolution_continuation": {"default_report_interval_iterations": 5},
    "credential_authority": "TV/TVC",
}


class TaskLifecycleStatusTests(unittest.TestCase):
    def test_active_continues_when_next_work_exists(self) -> None:
        result = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{
                "task_id": "A",
                "state": "ACTIVE",
                "next_admissible_work": {"kind": "EXISTING_EXECUTION_REQUEST", "ref": "control/request.json"},
            }],
        }, CONTRACT)
        self.assertTrue(result["continue_machine_work"])
        self.assertEqual(len(result["continuation_requests"]), 1)

    def test_completed_allows_only_closure_work(self) -> None:
        allowed = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{
                "task_id": "C",
                "state": "COMPLETED",
                "next_admissible_work": {"kind": "RETIREMENT_VERIFICATION", "ref": "receipt"},
            }],
        }, CONTRACT)
        self.assertTrue(allowed["continue_machine_work"])
        self.assertEqual(len(allowed["continuation_requests"]), 1)

        denied = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{
                "task_id": "C",
                "state": "COMPLETED",
                "next_admissible_work": {"kind": "FEATURE_IMPLEMENTATION", "ref": "x"},
            }],
        }, CONTRACT)
        self.assertEqual(denied["disposition"], "COMPLETED_CLOSURE_RESOLUTION_INCOMPLETE")
        self.assertFalse(denied["continue_machine_work"])

    def test_completed_ready_to_retire_stops_normal_continuation(self) -> None:
        result = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{
                "task_id": "C",
                "state": "COMPLETED",
                "closure_predicates_satisfied": True,
            }],
        }, CONTRACT)
        self.assertEqual(result["disposition"], "COMPLETED_READY_TO_RETIRE")
        self.assertFalse(result["continue_machine_work"])

    def test_retired_is_terminal(self) -> None:
        result = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{"task_id": "R", "state": "RETIRED"}],
        }, CONTRACT)
        self.assertEqual(result["disposition"], "RETIRED_TERMINAL")
        self.assertFalse(result["continue_machine_work"])
        self.assertEqual(result["continuation_requests"], [])

    def test_superseded_redirects_without_executing_source(self) -> None:
        result = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{
                "task_id": "OLD",
                "state": "SUPERSEDED",
                "successor_task_id": "NEW",
                "successor_cosv_task_vector": "10100000100000",
            }],
        }, CONTRACT)
        self.assertEqual(result["disposition"], "SUPERSEDED_REDIRECT")
        self.assertFalse(result["continue_machine_work"])
        self.assertEqual(result["superseded_redirects"][0]["to_task_id"], "NEW")

    def test_unknown_state_is_invalid_and_fails_closed(self) -> None:
        result = MODULE.evaluate({
            "goal_id": "G",
            "returned_tasks": [{"task_id": "X", "state": "MYSTERY"}],
        }, CONTRACT)
        self.assertEqual(result["disposition"], "INVALID_CANONICAL_TASK_STATE")
        self.assertFalse(result["continue_machine_work"])


if __name__ == "__main__":
    unittest.main()
