from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from workers import stegfin_early_adopter_contribution_validation_worker as worker


def materialize_required_paths(root: Path) -> None:
    (root / "stegwallet").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / worker.LEDGER_PATH).write_text("ledger\n", encoding="utf-8")
    (root / worker.TEST_PATH).write_text("tests\n", encoding="utf-8")


def test_missing_local_source_fails_closed(tmp_path):
    receipt = worker.validate(tmp_path / "missing")
    assert receipt["state"] == "FAIL_CLOSED"
    assert receipt["reason"] == "LOCAL_SOURCE_INCOMPLETE"
    assert receipt["network_fetch_used"] is False
    assert receipt["github_token_runtime_authority"] is False


def test_source_binding_mismatch_fails_closed(tmp_path):
    materialize_required_paths(tmp_path)
    with patch.object(worker, "_git_blob_sha", side_effect=["wrong-ledger", "wrong-test"]):
        receipt = worker.validate(tmp_path)
    assert receipt["state"] == "FAIL_CLOSED"
    assert receipt["reason"] == "SOURCE_BINDING_MISMATCH"


def test_exact_bound_passing_test_emits_non_authorizing_pass(tmp_path):
    materialize_required_paths(tmp_path)
    completed = SimpleNamespace(returncode=0, stdout="12 passed\n", stderr="")
    with patch.object(
        worker,
        "_git_blob_sha",
        side_effect=[worker.EXPECTED_LEDGER_BLOB, worker.EXPECTED_TEST_BLOB],
    ), patch.object(worker.subprocess, "run", return_value=completed) as run:
        receipt = worker.validate(tmp_path, python_executable="python")

    assert receipt["state"] == "PASS"
    assert receipt["reason"] == "EXACT_BOUND_FOCUSED_TESTS_PASS"
    assert receipt["external_provider_contacted"] is False
    assert receipt["trade_execution_attempted"] is False
    assert receipt["wallet_signing_attempted"] is False
    assert receipt["broadcast_attempted"] is False
    assert receipt["credential_authority"] == "TV/TVC"
    assert receipt["github_token_runtime_authority"] is False
    args, kwargs = run.call_args
    assert args[0] == ["python", "-m", "pytest", str(worker.TEST_PATH), "-q"]
    child_env = kwargs["env"]
    assert "GITHUB_TOKEN" not in child_env
    assert "GH_TOKEN" not in child_env


def test_exact_bound_failed_test_fails_closed(tmp_path):
    materialize_required_paths(tmp_path)
    completed = SimpleNamespace(returncode=1, stdout="1 failed\n", stderr="failure\n")
    with patch.object(
        worker,
        "_git_blob_sha",
        side_effect=[worker.EXPECTED_LEDGER_BLOB, worker.EXPECTED_TEST_BLOB],
    ), patch.object(worker.subprocess, "run", return_value=completed):
        receipt = worker.validate(tmp_path)
    assert receipt["state"] == "FAIL_CLOSED"
    assert receipt["reason"] == "FOCUSED_TESTS_FAILED"
    assert receipt["returncode"] == 1
