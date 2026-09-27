import unittest
import importlib.util
import json
import subprocess
import tempfile
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
SELECTOR = ROOT / "scripts" / "run_task_registry_canonical_work_cycle.py"


class CanonicalWorkRegistryReturnLoopTests(unittest.TestCase):
    def test_existing_resident_consumer_runs_registry_cycle(self):
        text = CONSUMER.read_text(encoding="utf-8")
        self.assertIn('TASK_REGISTRY_CYCLE_ENTRYPOINT = Path("scripts/run_task_registry_canonical_work_cycle.py")', text)
        self.assertIn("def run_registry_cycle(", text)
        self.assertIn('"task_registry_cycle_attempted": True', text)
        self.assertIn('"start_point": "CANONICAL_TASK_REGISTRY"', text)

    def test_runtime_task_state_is_preserved_while_missing_source_shards_are_materialized(self):
        text = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("def materialize_registry_task_shards(", text)
        self.assertIn('"preserved_existing_runtime_projection": True', text)
        self.assertIn('source_dir.glob("*.json")', text)

    def test_explicit_request_tasks_are_not_reselected_by_registry_cycle(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        selector = SELECTOR.read_text(encoding="utf-8")
        self.assertIn('command.extend(["--exclude-task-id", spec["task_id"]])', consumer)
        self.assertIn('parser.add_argument("--exclude-task-id", action="append", default=[])', selector)
        self.assertIn("PROGRESSION_CONTROLLER_TASK_ID", selector)

    def test_current_goal_context_is_threaded_without_new_dispatcher(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        selector = SELECTOR.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--goal-task-id")', consumer)
        self.assertIn('parser.add_argument("--goal-task-id")', selector)
        self.assertIn('"current_goal_task_id": args.goal_task_id', consumer)
        self.assertIn('"progression_controller_lineage_goal_id": controller_lineage_goal_id', selector)

    def test_no_parallel_authority_or_scheduler_is_created(self):
        text = CONSUMER.read_text(encoding="utf-8")
        self.assertIn('"second_dispatcher_created": False', text)
        self.assertIn('"second_scheduler_created": False', text)
        self.assertIn('"claim_or_fence_minted": False', text)
        self.assertIn('"credential_authority": "TV/TVC"', text)
        self.assertIn('"github_token_runtime_authority": "NONE"', text)


class RegistryCycleDelegationReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = CONSUMER.with_name("consume-canonical-work-coordination-bootstrap.legacy.py")
        spec = importlib.util.spec_from_file_location("registry_return_consumer", path)
        cls.consumer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.consumer)

    def consume_result(self, result, returncode=0):
        consumer = self.consumer
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = mock.Mock(return_value=subprocess.CompletedProcess(
                [], returncode, json.dumps(result), ""))
            with mock.patch.object(consumer, "resolve_local_canonical_source", return_value=root), \
                 mock.patch.object(consumer, "materialize", return_value=[]), \
                 mock.patch.object(consumer, "materialize_registry_task_shards", return_value=[]), \
                 mock.patch.object(consumer, "clean_env", return_value={}):
                receipt = consumer.run_registry_cycle(root, root, runner=runner)
            retained = json.loads((root / consumer.TASK_REGISTRY_CYCLE_RECEIPT).read_text())
            self.assertEqual(receipt, retained)
            self.assertEqual(retained["result"], result)
            self.assertFalse(retained["claim_or_fence_minted"])
            self.assertEqual(retained["authority_effect"], "NONE_REGISTRY_SELECTION_AND_DELEGATION_EVIDENCE_ONLY")
            return retained

    def test_both_existing_delegation_modes_are_retained_as_completed_consumption(self):
        for state in ("DELEGATED_TO_EXISTING_CANONICAL_WORK_PATH",
                      "DELEGATED_TO_EXISTING_WORKERCOORDINATOR_STATE_TRANSITION",
                      "NO_ADMISSIBLE_NONCOLLIDING_TASK"):
            with self.subTest(state=state):
                result = {"schema": "stegverse.task-registry-canonical-work-cycle/v1", "state": state}
                self.assertEqual(self.consume_result(result)["state"], "COMPLETED")

    def test_failed_and_unknown_delegation_never_becomes_completed_consumption(self):
        for state, returncode in (("DELEGATED_TO_EXISTING_WORKERCOORDINATOR_STATE_TRANSITION", 1),
                                  ("EXISTING_PATH_DELEGATION_RECORDED_FAILURE", 0),
                                  ("UNKNOWN", 0)):
            with self.subTest(state=state, returncode=returncode):
                result = {"schema": "stegverse.task-registry-canonical-work-cycle/v1", "state": state}
                self.assertEqual(self.consume_result(result, returncode)["state"], "ATTEMPT_RECORDED")


if __name__ == "__main__":
    unittest.main()
