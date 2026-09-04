from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from workers import legacy_continuity_validation_worker as worker


def materialize_tests(root: Path) -> None:
    for relative in worker.FOCUSED_TESTS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")


class LegacyContinuityValidationWorkerTests(unittest.TestCase):
    def test_missing_local_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt = worker.validate(Path(tmp) / "missing")
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "LOCAL_REPO_PATH_REQUIRED")
        self.assertFalse(receipt["network_fetch_used"])
        self.assertFalse(receipt["github_token_runtime_authority"])
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_source_binding_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_tests(root)
            with patch.object(
                worker,
                "_git",
                return_value=SimpleNamespace(returncode=0, stdout="wrong-head\n", stderr=""),
            ):
                receipt = worker.validate(root)
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "SOURCE_BINDING_MISMATCH")

    def test_dirty_worktree_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_tests(root)
            responses = [
                SimpleNamespace(returncode=0, stdout=worker.EXPECTED_HEAD + "\n", stderr=""),
                SimpleNamespace(returncode=0, stdout=" M changed\n", stderr=""),
            ]
            with patch.object(worker, "_git", side_effect=responses):
                receipt = worker.validate(root)
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "WORKTREE_NOT_CLEAN")

    def test_exact_source_pass_runs_all_four_tests_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_tests(root)
            responses = [
                SimpleNamespace(returncode=0, stdout=worker.EXPECTED_HEAD + "\n", stderr=""),
                SimpleNamespace(returncode=0, stdout="", stderr=""),
            ]
            pytest_result = SimpleNamespace(returncode=0, stdout="all passed\n", stderr="")
            with patch.object(worker, "_git", side_effect=responses), patch.object(
                worker.subprocess, "run", return_value=pytest_result
            ) as run, patch.dict(
                os.environ,
                {"GITHUB_TOKEN": "forbidden", "GH_TOKEN": "forbidden", "SAFE_VALUE": "kept"},
                clear=False,
            ):
                receipt = worker.validate(root, python_executable="python")

        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["reason"], "EXACT_BOUND_LEGACY_AND_FROZEN_SIMULATION_TESTS_PASS")
        self.assertEqual(receipt["focused_tests"], list(worker.FOCUSED_TESTS))
        self.assertEqual(len(receipt["focused_tests"]), 4)
        self.assertIn("tests/test_legacy_frozen_simulation.py", receipt["focused_tests"])
        self.assertFalse(receipt["death_determination_performed"])
        self.assertFalse(receipt["recipient_notification_performed"])
        self.assertFalse(receipt["capsule_arming_performed"])
        self.assertFalse(receipt["economic_transfer_performed"])
        self.assertFalse(receipt["authentic_tvc_authorization_created"])
        self.assertEqual(receipt["authority_effect"], "NONE")

        args, kwargs = run.call_args
        self.assertEqual(args[0], ["python", "-m", "pytest", *worker.FOCUSED_TESTS, "-q"])
        child_env = kwargs["env"]
        self.assertNotIn("GITHUB_TOKEN", child_env)
        self.assertNotIn("GH_TOKEN", child_env)
        self.assertEqual(child_env["SAFE_VALUE"], "kept")

    def test_focused_test_failure_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_tests(root)
            responses = [
                SimpleNamespace(returncode=0, stdout=worker.EXPECTED_HEAD + "\n", stderr=""),
                SimpleNamespace(returncode=0, stdout="", stderr=""),
            ]
            pytest_result = SimpleNamespace(returncode=1, stdout="failed\n", stderr="failure\n")
            with patch.object(worker, "_git", side_effect=responses), patch.object(
                worker.subprocess, "run", return_value=pytest_result
            ):
                receipt = worker.validate(root)
        self.assertEqual(receipt["state"], "FAIL_CLOSED")
        self.assertEqual(receipt["reason"], "FOCUSED_TESTS_FAILED")
        self.assertEqual(receipt["returncode"], 1)


if __name__ == "__main__":
    unittest.main()
