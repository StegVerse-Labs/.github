from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "workers/stegnutrition_continuation_entrypoint_v2.py"


def _module():
    spec = importlib.util.spec_from_file_location("stegnutrition_entrypoint_v2_test", ENTRYPOINT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_preflight_requires_unified_release_projection_surfaces() -> None:
    module = _module()
    required = set(module.base.CURRENT_REQUIRED_SURFACES)
    assert {
        "scripts/run_full_validation_no_network.py",
        "src/stegnutrition/release.py",
        "src/stegnutrition/release_projection.py",
        "tests/test_full_validation_orchestrator.py",
        "tests/test_release.py",
        "tests/test_release_projection.py",
        "tasks/STEGNUTRITION-RELEASE-PROPAGATION-017.json",
    } <= required
    assert module.base.WORKER.name == "stegnutrition_continuation_worker_v2.py"
