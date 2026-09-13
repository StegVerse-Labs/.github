from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_source_refresh_reusable_runner_extends_canonical_refresh_only():
    module = load("refresh_reusable", "scripts/refresh_sovereign_worker_runtime_source_reusable.py")
    assert Path("scripts/run_reusable_task_scheduler.py") in module.EXTRA_STATIC_FILES
    assert Path("data/reusable-task-scheduler-contract.json") in module.EXTRA_STATIC_FILES
    assert Path("scripts/refresh_sovereign_worker_runtime_source_reusable.py") in module.EXTRA_STATIC_FILES
    source = (ROOT / "scripts" / "refresh_sovereign_worker_runtime_source_reusable.py").read_text(encoding="utf-8")
    assert "base.refresh(" in source
    assert "network" not in source.lower() or "no second refresh algorithm" in source.lower()


def test_source_refresh_reusable_identity_requires_neutral_scheduler_materialization_dependencies():
    shard = json.loads((ROOT / "source-bundles" / "reusable-task-registry.d" / "RT-SOVEREIGN-SOURCE-REFRESH-001.json").read_text(encoding="utf-8"))
    assert shard["runner_templates"][0] == "scripts/refresh_sovereign_worker_runtime_source_reusable.py"
    assert "scripts/refresh_sovereign_worker_runtime_source.py" in shard["runner_templates"]
    assert "scripts/run_reusable_task_scheduler.py" in shard["runner_templates"]
    assert shard["authority_effect"] == "NONE_LOCAL_SOURCE_REFRESH"
