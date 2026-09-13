import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_source_mutation_preflight.py"
spec = importlib.util.spec_from_file_location("source_mutation_guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class SourceMutationPreflightGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "control").mkdir()
        (self.root / "data" / "canonical-task-records").mkdir(parents=True)
        (self.root / "receipts" / "preflight").mkdir(parents=True)
        (self.root / "control" / "canonical-policy-context-registry.json").write_text(
            json.dumps({"required_global_sources": [{"ref": "docs/GLOBAL.md", "required": True}]}),
            encoding="utf-8",
        )
        (self.root / "data" / "canonical-task-records" / "TASK-1.json").write_text(
            json.dumps({"task_id": "TASK-1", "canonical_policy_refs": ["docs/DOMAIN.md"]}),
            encoding="utf-8",
        )
        self.receipt_rel = "receipts/preflight/TASK-1.json"
        self.receipt_path = self.root / self.receipt_rel
        self.receipt_path.write_text(
            json.dumps(
                {
                    "schema": guard.EXPECTED_SCHEMA,
                    "state": "PASS_FUNCTIONAL_MUTATION_ADMISSIBLE",
                    "preflight_completed_before_source_mutation": True,
                    "base_commit": "base",
                    "goal_task_id": "TASK-1",
                    "canonical_sources_resolved": ["docs/GLOBAL.md", "docs/DOMAIN.md"],
                    "authorized_mutation_scope": ["src/"],
                }
            ),
            encoding="utf-8",
        )
        self.patches = [
            mock.patch.object(guard, "ROOT", self.root),
            mock.patch.object(guard, "POLICY_REGISTRY", self.root / "control" / "canonical-policy-context-registry.json"),
            mock.patch.object(guard, "TASK_SHARDS", self.root / "data" / "canonical-task-records"),
            mock.patch.object(guard, "TASK_REGISTRY", self.root / "data" / "canonical-task-registry.json"),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def test_scope_supports_exact_and_prefix_paths(self):
        self.assertTrue(guard.path_authorized("scripts/a.py", ["scripts/"]))
        self.assertTrue(guard.path_authorized("README.md", ["README.md"]))
        self.assertFalse(guard.path_authorized("workers/a.py", ["scripts/"]))

    def test_receipt_must_precede_first_protected_mutation(self):
        with mock.patch.object(guard, "first_change_commit", return_value="same"):
            findings = guard.validate_receipt(
                self.receipt_rel, base_sha="base", protected_paths=["src/change.py"]
            )
        self.assertTrue(any("same commit" in finding for finding in findings))

    def test_prior_receipt_with_complete_policy_and_scope_passes(self):
        def first_change(base, path):
            return "receipt-commit" if path.startswith("receipts/preflight/") else "source-commit"

        with mock.patch.object(guard, "first_change_commit", side_effect=first_change), mock.patch.object(
            guard, "is_ancestor", side_effect=lambda older, newer: older == "receipt-commit" and newer == "source-commit"
        ):
            findings = guard.validate_receipt(
                self.receipt_rel, base_sha="base", protected_paths=["src/change.py"]
            )
        self.assertEqual(findings, [])

    def test_missing_task_policy_ref_fails_closed(self):
        payload = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        payload["canonical_sources_resolved"] = ["docs/GLOBAL.md"]
        self.receipt_path.write_text(json.dumps(payload), encoding="utf-8")
        with mock.patch.object(guard, "first_change_commit", return_value="receipt-commit"):
            findings = guard.validate_receipt(
                self.receipt_rel, base_sha="base", protected_paths=["src/change.py"]
            )
        self.assertTrue(any("required canonical policy sources not resolved" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
