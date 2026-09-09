from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dispatched_control_consumer_preserves_fail_closed_prerequisite_gating() -> None:
    source = (ROOT / "control/resident-execution-request.d/consume-governed-multilane-manifold-activation.py").read_text()
    assert "CONDITIONAL_EXECUTE_DISPOSITIONS" in source
    assert "PREREQUISITES_NOT_QUALIFIED_FAIL_CLOSED" in source
    assert "result_has_qualifying_evidence" in source
    assert '"EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS"' in source
    assert '"qualifying_for_dependents"' in source


def test_dispatcher_still_targets_the_source_refresh_carried_control_consumer() -> None:
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    expected = '("governed_multilane_manifold_activation", "control/resident-execution-request.d/consume-governed-multilane-manifold-activation.py")'
    assert expected in dispatcher


def test_source_refresh_carries_runtime_dispatched_control_consumer() -> None:
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    assert 'Path("control/resident-execution-request.d")' in refresh
