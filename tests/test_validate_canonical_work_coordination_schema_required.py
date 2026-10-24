"""validate_canonical_work_coordination.py takes row-required fields from the schema.

Q-R-k feedback output. The canonical task schema ``required`` list is the single
source; ``runtime_requirements`` (validator-required, not schema-required) stays
FAIL_CLOSED as an explicit six-field schema/validator discrepancy until Q-R-k is
answered. Fixture-only: the live registry and schema are never written. Stdlib only.
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
spec = importlib.util.spec_from_file_location("validate_canonical_work_coordination_schema_required", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)

SIX_FIELDS = (
    "failure_code:", "failed_predicate:", "required_evidence_or_repair:",
    "retry_entrypoint:", "owning_existing_goal:", "next_attempt:",
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


class SchemaRequiredSourceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        live_registry = json.loads(validator.REGISTRY.read_text(encoding="utf-8"))
        self.registry_head = {k: v for k, v in live_registry.items() if k != "tasks"}
        self.schema = json.loads(validator.TASK_SCHEMA.read_text(encoding="utf-8"))
        self.registry_path = self.dir / "canonical-task-registry.json"
        self.schema_path = self.dir / "canonical-task-record.schema.json"
        # The live handoff currently lacks the validator's required statements
        # (a separate, pre-existing finding); a fixture handoff isolates this test.
        self.handoff_path = self.dir / "handoff.md"
        self.handoff_path.write_text(
            "One canonical work truth and many projections. "
            "WorkerCoordinator remains authoritative for executable claim/fence ownership. "
            "Task Registry and Master Records are intentionally comparable but not interchangeable. "
            "A human action is represented once as a canonical dependency object. "
            "Handoffs become projections of canonical coordination state.\n",
            encoding="utf-8",
        )
        for name, path in (("REGISTRY", self.registry_path), ("TASK_SCHEMA", self.schema_path),
                           ("HANDOFF", self.handoff_path)):
            patcher = mock.patch.object(validator, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_with(self, tasks, schema=None):
        self.schema_path.write_text(json.dumps(schema if schema is not None else self.schema), encoding="utf-8")
        self.registry_path.write_text(json.dumps({**self.registry_head, "tasks": tasks}), encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = validator.main()
            except SystemExit as exc:
                return exc.code, out.getvalue()
        return code, out.getvalue()

    def task(self, **changes):
        task = copy.deepcopy(VALID_TASK)
        for key, value in changes.items():
            if value is ...:
                task.pop(key, None)
            else:
                task[key] = value
        return task

    def test_live_schema_declares_the_discrepancy_this_validator_reports(self):
        self.assertNotIn("runtime_requirements", self.schema["required"])
        for field in ("task_id", "correlation_id", "worker_claim"):
            self.assertIn(field, self.schema["required"])
        self.assertEqual(validator.DECLARED_SCHEMA_VALIDATOR_DISCREPANCIES, {"runtime_requirements": "Q-R-k"})

    def test_valid_fixture_passes(self):
        code, out = self.run_with([self.task()])
        self.assertEqual(code, 0)
        self.assertIn("PASS: canonical work coordination source contract is internally consistent", out)

    def test_missing_runtime_requirements_is_six_field_discrepancy_naming_both_sources_and_q_r_k(self):
        code, _ = self.run_with([self.task(runtime_requirements=...)])
        self.assertIsInstance(code, str)
        lines = code.splitlines()
        self.assertEqual(lines[0], "FAIL_CLOSED: FIXTURE-TASK-001: runtime requirements missing")
        for prefix in SIX_FIELDS:
            self.assertEqual(sum(1 for line in lines if line.startswith(prefix)), 1, prefix)
        self.assertIn(f"failure_code: {validator.DISCREPANCY_FAILURE_CODE}", lines)
        text = "\n".join(lines)
        self.assertIn("scripts/validate_canonical_work_coordination.py", text)
        self.assertIn("schemas/canonical-task-record.schema.json", text)
        self.assertGreaterEqual(text.count("Q-R-k"), 3)

    def test_non_object_runtime_requirements_is_also_the_discrepancy(self):
        code, _ = self.run_with([self.task(runtime_requirements=None)])
        self.assertIn(validator.DISCREPANCY_FAILURE_CODE, code)

    def test_discrepancy_resolves_when_schema_adds_the_field(self):
        schema = copy.deepcopy(self.schema)
        schema["required"] = schema["required"] + ["runtime_requirements"]
        code, _ = self.run_with([self.task(runtime_requirements=...)], schema)
        self.assertEqual(code, "FAIL_CLOSED: FIXTURE-TASK-001: runtime requirements missing")

    def test_existing_messages_unchanged(self):
        cases = {
            "FAIL_CLOSED: FIXTURE-TASK-001: claim authority drift": self.task(worker_claim={"authority": "X", "projection_only": True}),
            "FAIL_CLOSED: FIXTURE-TASK-001: registry claim must be projection-only": self.task(
                worker_claim={"authority": "WORKERCOORDINATOR", "projection_only": False}),
            "FAIL_CLOSED: correlation_id missing for FIXTURE-TASK-001": self.task(correlation_id=...),
            "FAIL_CLOSED: task_id missing": self.task(task_id=...),
            "FAIL_CLOSED: FIXTURE-TASK-001: runtime capabilities missing": self.task(
                runtime_requirements={k: v for k, v in VALID_TASK["runtime_requirements"].items() if k != "capabilities"}),
            "FAIL_CLOSED: FIXTURE-TASK-001: runtime requirement deployment_required must be boolean": self.task(
                runtime_requirements={**VALID_TASK["runtime_requirements"], "deployment_required": "no"}),
        }
        for expected, task in cases.items():
            with self.subTest(expected=expected):
                code, _ = self.run_with([task])
                self.assertEqual(code, expected)

    def test_nested_runtime_requirement_flags_come_from_schema(self):
        schema = copy.deepcopy(self.schema)
        schema["properties"]["runtime_requirements"]["required"].remove("deployment_required")
        task = self.task(runtime_requirements={**VALID_TASK["runtime_requirements"], "deployment_required": "no"})
        code, _ = self.run_with([task], schema)
        self.assertEqual(code, 0)
        schema["properties"]["runtime_requirements"]["properties"]["mutation_required"]["type"] = "string"
        code, _ = self.run_with([self.task()], schema)
        self.assertEqual(code, "FAIL_CLOSED: task schema runtime_requirements.mutation_required type is not supported by this validator")

    def test_undeclared_validator_field_absent_from_schema_fails_closed(self):
        schema = copy.deepcopy(self.schema)
        schema["required"] = [f for f in schema["required"] if f != "worker_claim"]
        code, _ = self.run_with([self.task()], schema)
        self.assertIn("without a declared discrepancy: ['worker_claim']", code)

    def test_malformed_schema_required_fails_closed(self):
        for bad in ("task_id", None, [1]):
            with self.subTest(bad=bad):
                schema = copy.deepcopy(self.schema)
                schema["required"] = bad
                code, _ = self.run_with([self.task()], schema)
                self.assertIsInstance(code, str)
                self.assertTrue(code.startswith("FAIL_CLOSED:"), code)


if __name__ == "__main__":
    unittest.main()
