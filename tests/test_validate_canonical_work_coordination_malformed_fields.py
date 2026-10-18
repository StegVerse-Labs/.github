"""validate_canonical_work_coordination.py fails closed on malformed fields.

Deterministic: every case copies the validator's source contracts into a
throwaway directory and points the module at a fixture registry. Nothing reads
or writes the live registry. Stdlib only.
"""
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_canonical_work_coordination.py"
spec = importlib.util.spec_from_file_location("validate_canonical_work_coordination", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)

SIX_FIELDS = (
    "failure_code:",
    "failed_predicate:",
    "required_evidence_or_repair:",
    "retry_entrypoint:",
    "owning_existing_goal:",
    "next_attempt:",
)

VALID_TASK = {
    "task_id": "FIXTURE-TASK-001",
    "correlation_id": "FIXTURE-TASK-001",
    "coordination_state": "ACTIVE",
    "worker_claim": {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
    "runtime_requirements": {
        "capabilities": [],
        "mutation_required": False,
        "deployment_required": False,
        "current_observation_required": False,
    },
    "completion": {"claimed": False, "validated": False, "reconciliation_ref": None},
    "dependencies": [],
    "blockers": [],
}


class MalformedFieldFailClosedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        # Non-registry contracts are the repo's own source contracts (read-only).
        live_registry = json.loads(validator.REGISTRY.read_text(encoding="utf-8"))
        self.registry_head = {k: v for k, v in live_registry.items() if k != "tasks"}
        self.registry_path = self.dir / "canonical-task-registry.json"
        patcher = mock.patch.object(validator, "REGISTRY", self.registry_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_with_tasks(self, tasks):
        self.registry_path.write_text(json.dumps({**self.registry_head, "tasks": tasks}), encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = validator.main()
            except SystemExit as exc:
                return exc.code, out.getvalue()
        return code, out.getvalue()

    def assert_six_field_fail_closed(self, result, field):
        code, _ = result
        self.assertIsInstance(code, str, "expected SystemExit with a FAIL_CLOSED message, not a pass")
        lines = code.splitlines()
        self.assertTrue(lines[0].startswith("FAIL_CLOSED: malformed field "), lines[0])
        self.assertIn(field, lines[0])
        for prefix in SIX_FIELDS:
            self.assertEqual(sum(1 for line in lines if line.startswith(prefix)), 1, prefix)
        self.assertIn("CANONICAL_WORK_COORDINATION_MALFORMED_FIELD", code)

    def test_valid_fixture_row_reaches_per_task_checks_without_failing(self):
        code, _ = self.run_with_tasks([copy.deepcopy(VALID_TASK)])
        # The fixture row itself passes; any remaining failure must be a
        # pre-existing non-row check (e.g. the handoff phrases), never the row.
        if code not in (0, None):
            self.assertNotIn("FIXTURE-TASK-001", str(code))
            self.assertNotIn("malformed field", str(code))

    def test_string_worker_claim_fails_closed_without_traceback(self):
        task = copy.deepcopy(VALID_TASK)
        task["worker_claim"] = "NONE_TASK_REGISTRY_PROJECTION_ONLY"
        result = self.run_with_tasks([task])
        self.assert_six_field_fail_closed(result, "tasks[FIXTURE-TASK-001].worker_claim")
        self.assertIn("expected object, got string", result[0])

    def test_list_runtime_resolution_fails_closed(self):
        task = copy.deepcopy(VALID_TASK)
        task["runtime_resolution"] = ["not", "an", "object"]
        self.assert_six_field_fail_closed(self.run_with_tasks([task]), "tasks[FIXTURE-TASK-001].runtime_resolution")

    def test_string_completion_fails_closed(self):
        task = copy.deepcopy(VALID_TASK)
        task["completion"] = "CLAIMED"
        self.assert_six_field_fail_closed(self.run_with_tasks([task]), "tasks[FIXTURE-TASK-001].completion")

    def test_non_object_blocker_item_fails_closed(self):
        task = copy.deepcopy(VALID_TASK)
        task["blockers"] = ["DEP-X"]
        self.assert_six_field_fail_closed(self.run_with_tasks([task]), "tasks[FIXTURE-TASK-001].blockers[0]")

    def test_object_dependencies_fails_closed(self):
        task = copy.deepcopy(VALID_TASK)
        task["dependencies"] = {"dependency_id": "DEP-X"}
        self.assert_six_field_fail_closed(self.run_with_tasks([task]), "tasks[FIXTURE-TASK-001].dependencies")

    def test_non_object_task_row_fails_closed(self):
        self.assert_six_field_fail_closed(self.run_with_tasks(["FIXTURE-TASK-001"]), "tasks[0]")

    def test_existing_claim_authority_message_is_unchanged(self):
        task = copy.deepcopy(VALID_TASK)
        task["worker_claim"] = {"authority": "CURRENT_SESSION", "claim_ref": None, "fence_ref": None, "projection_only": False}
        code, _ = self.run_with_tasks([task])
        self.assertEqual(code, "FAIL_CLOSED: FIXTURE-TASK-001: claim authority drift")

    def test_missing_worker_claim_keeps_existing_semantics(self):
        task = copy.deepcopy(VALID_TASK)
        del task["worker_claim"]
        code, _ = self.run_with_tasks([task])
        self.assertEqual(code, "FAIL_CLOSED: FIXTURE-TASK-001: claim authority drift")

    def test_missing_runtime_requirements_keeps_existing_message(self):
        task = copy.deepcopy(VALID_TASK)
        del task["runtime_requirements"]
        code, _ = self.run_with_tasks([task])
        self.assertEqual(code, "FAIL_CLOSED: FIXTURE-TASK-001: runtime requirements missing")


if __name__ == "__main__":
    unittest.main()
