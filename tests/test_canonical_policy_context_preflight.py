import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "session_build_preflight.py"

spec = importlib.util.spec_from_file_location("session_build_preflight", ENTRY)
preflight = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(preflight)


class CanonicalPolicyContextPreflightTests(unittest.TestCase):
    def test_global_policy_context_resolves_existing_canonical_sources(self):
        context, complete = preflight.resolve_canonical_policy_context(task_id=None, explicit_refs=[])
        self.assertTrue(complete)
        self.assertEqual(context["state"], "RESOLVED")
        refs = {row["ref"] for row in context["policy_refs"]}
        self.assertIn("data/task-coordination-policy.json", refs)
        self.assertIn("docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md", refs)
        self.assertIn("RUNNERS_EXPIRE_BEFORE_RECORDING_CONTINUITY", context["known_global_invariants"])
        self.assertIn("EPHEMERAL_CAPABILITY_DOES_NOT_MEAN_EPHEMERAL_ACCOUNTABILITY", context["known_global_invariants"])
        self.assertFalse(context["human_policy_restatement_required"])
        self.assertFalse(context["runtime_truth_inferred"])

    def test_missing_explicit_canonical_policy_fails_closed(self):
        context, complete = preflight.resolve_canonical_policy_context(
            task_id=None,
            explicit_refs=["docs/THIS_CANONICAL_POLICY_DOES_NOT_EXIST.md"],
        )
        self.assertFalse(complete)
        self.assertEqual(context["state"], "CANONICAL_POLICY_DEPENDENCY_UNRESOLVED")
        self.assertEqual(
            context["unresolved_policy_refs"],
            ["docs/THIS_CANONICAL_POLICY_DOES_NOT_EXIST.md"],
        )

    def test_task_declared_policy_refs_are_automatically_loaded(self):
        original_records = preflight.CANONICAL_TASK_RECORDS
        temp_parent = ROOT / ".tmp-policy-context-tests"
        temp_parent.mkdir(exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=temp_parent) as tmp:
                records = Path(tmp)
                record = {
                    "task_id": "TEST-POLICY-TASK",
                    "canonical_policy_refs": ["management/session-build-preflight-contract.json"],
                }
                (records / "TEST-POLICY-TASK.json").write_text(json.dumps(record), encoding="utf-8")
                preflight.CANONICAL_TASK_RECORDS = records
                context, complete = preflight.resolve_canonical_policy_context(
                    task_id="TEST-POLICY-TASK",
                    explicit_refs=[],
                )
                self.assertTrue(complete)
                self.assertTrue(context["task_record_ref"].endswith("TEST-POLICY-TASK.json"))
                task_rows = [row for row in context["policy_refs"] if row["source"] == "CANONICAL_TASK_RECORD"]
                self.assertEqual(len(task_rows), 1)
                self.assertEqual(task_rows[0]["ref"], "management/session-build-preflight-contract.json")
                self.assertTrue(task_rows[0]["resolved"])
        finally:
            preflight.CANONICAL_TASK_RECORDS = original_records
            try:
                temp_parent.rmdir()
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
