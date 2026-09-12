from pathlib import Path

from scripts.dispatch_resident_execution_requests import CONSUMERS
from scripts.refresh_and_dispatch_resident_requests import ALLOWED_TARGET_CONSUMERS
from scripts.refresh_sovereign_worker_runtime_source import CONTROL_DIRS, STATIC_DIRS, STATIC_FILES


ROOT = Path(__file__).resolve().parents[1]


def test_gadi_runtime_observation_is_exact_portable_selector():
    names = [name for name, _ in CONSUMERS]
    assert "gadi_runtime_observation" in names
    assert "gadi_runtime_observation" in ALLOWED_TARGET_CONSUMERS


def test_gadi_runtime_observation_source_is_carried_by_local_refresh():
    assert Path("workers") in STATIC_DIRS
    assert Path("control/resident-execution-request.d") in CONTROL_DIRS
    assert Path("scripts/dispatch_resident_execution_requests.py") in STATIC_FILES
    assert Path("scripts/refresh_and_dispatch_resident_requests.py") in STATIC_FILES

    assert (ROOT / "workers/gadi_runtime_observation_request_consumer.py").is_file()
    assert (ROOT / "control/resident-execution-request.d/gadi-runtime-observation-001.json").is_file()
