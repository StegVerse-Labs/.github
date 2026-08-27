from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from workers import stegfin_early_adopter_contribution_validation_worker as worker


def materialize_required_paths(root: Path) -> None:
    (root / "stegwallet").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / worker.LEDGER_PATH).write_text("ledger\n", encoding="utf-8")
    (root / worker.TEST_PATH).write_text("tests\n", encoding="utf-8")


class StegFinEarlyAdopterContributionValidationWorkerTests(unittest.TestCase):
    def test_missing_local_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt = worker.validate(Path(tmp) / "missing")
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "LOCAL_SOURCE_INCOMPLETE")
        self.assertFalse(receipt["network_fetch_used"])
        self.assertFalse(receipt["github_token_runtime_authority"])

    def test_source_binding_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            materialize_required_paths(root)
            with patch.object(worker, "_git_blob_sha", side_effect=["wrong-ledger", "wrong-test"]):
                receipt = worker.validate(root)
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "SOURCE_BINDING_MISMATCH")

    def test_exact_bound_passing_test_emits_non_authorizing_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            materialize_required_paths(root)
            completed = SimpleNamespace(returncode=0, stdout="12 passed\n", stderr="")
            with patch.object(
                worker,
                "_git_blob_sha",
                side_effect=[worker.EXPECTED_LEDGER_BLOB, worker.EXPECTED_TEST_BLOB],
            ), patch.object(worker.subprocess, "run", return_value=completed) as run:
                receipt = worker.validate(root, python_executable="python")

        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["reason"], "EXACT_BOUND_FOCUSED_TESTS_PASS")
        self.assertFalse(receipt["external_provider_contacted"])
        self.assertFalse(receipt["trade_execution_attempted"])
        self.assertFalse(receipt["wallet_signing_attempted"])
        self.assertFalse(receipt["broadcast_attempted"])
        self.assertEqual(receipt["credential_authority"], "TV/TVC")
        self.assertFalse(receipt["github_token_runtime_authority"])
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["python", "-m", "pytest", str(worker.TEST_PATH), "-q"])
        child_env = kwargs["env"]
        self.assertNotIn("GITHUB_TOKEN", child_env)
        self.assertNotIn("GH_TOKEN", child_env)

    def test_exact_bound_failed_test_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            materialize_required_paths(root)
            completed = SimpleNamespace(returncode=1, stdout="1 failed\n", stderr="failure\n")
            with patch.object(
                worker,
                "_git_blob_sha",
                side_effect=[worker.EXPECTED_LEDGER_BLOB, worker.EXPECTED_TEST_BLOB],
            ), patch.object(worker.subprocess, "run", return_value=completed):
                receipt = worker.validate(root)
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "FOCUSED_TESTS_FAILED")
        self.assertEqual(receipt["returncode"], 1)


if __name__ == "__main__":
    unittest.main()
