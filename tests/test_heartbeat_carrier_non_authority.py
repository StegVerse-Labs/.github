import inspect
from pathlib import Path

from heartbeat_runtime import HeartbeatRuntime
from heartbeat_runtime.worker_runtime import WorkerCoordinator


def test_canonical_heartbeat_is_v12_carrier_only():
    assert HeartbeatRuntime.__module__ == "heartbeat_runtime.engine_v12"
    source = inspect.getsource(HeartbeatRuntime.cycle)
    forbidden = (
        "issue_claim_assertions",
        "_invoke(",
        "_activate_one(",
        "_expire(",
        "_apply_registry_fragments(",
        "_reconcile_orphan_recovery_quarantines(",
    )
    for token in forbidden:
        assert token not in source
    assert '"claims_issued": 0' in source
    assert '"workers_invoked": 0' in source
    assert '"tasks_activated": 0' in source
    assert '"leases_expired": 0' in source
    assert '"authority_effect": "NONE_CARRIER_ONLY"' in source


def test_worker_coordinator_is_separate_legacy_lifecycle_surface():
    assert WorkerCoordinator.__module__ == "heartbeat_runtime.engine_v11"
    assert WorkerCoordinator is not HeartbeatRuntime


def test_public_heartbeat_runner_does_not_load_worker_adapters():
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts" / "run_heartbeat_runtime.py").read_text(encoding="utf-8")
    assert "ProcessWorkerAdapter" not in source
    assert "load_adapters" not in source
    assert "WorkerCoordinator" not in source


def test_worker_runner_is_explicitly_separate():
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts" / "run_worker_runtime.py").read_text(encoding="utf-8")
    assert "WorkerCoordinator" in source
    assert "ProcessWorkerAdapter" in source
