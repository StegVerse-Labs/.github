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


def test_scheduler_identity_is_neutral_and_executable():
    shard = json.loads((ROOT / "source-bundles/reusable-task-registry.d/RT-REUSABLE-TASK-SCHEDULER-001.json").read_text())
    assert shard["reusable_task_id"] == "RT-REUSABLE-TASK-SCHEDULER-001"
    assert shard["runner_templates"] == ["scripts/run_reusable_task_scheduler.py"]
    assert shard["authority_effect"] == "NONE_SCHEDULING_ONLY"
    assert "Healer and other systems may consume it" in shard["reuse_instructions"]


def test_scheduler_contract_preserves_authority_owners():
    contract = json.loads((ROOT / "data/reusable-task-scheduler-contract.json").read_text())
    inv = contract["invariants"]
    assert inv["neutral_owner"] is True
    assert inv["healer_is_consumer_not_owner"] is True
    assert inv["self_scheduling_prohibited"] is True
    assert inv["worker_claim_fence_authority"] == "WorkerCoordinator"
    assert inv["transition_authority"] == "Interlock/InTr"
    assert inv["user_verification_authority"] == "KV/SKAP Vault"


def test_scheduler_selection_and_self_recursion_guard():
    mod = load("neutral_scheduler", "scripts/run_reusable_task_scheduler.py")
    now = mod.parse_now("2026-09-13T19:00:00Z")
    assert mod.due({"enabled": True, "run_hours_utc": [19]}, now) is True
    assert mod.due({"enabled": True, "run_hours_utc": [18]}, now) is False
    assert mod.selected({"reusable_task_id": "RT-X", "aliases": ["x"]}, "x") is True
    source = (ROOT / "scripts/run_reusable_task_scheduler.py").read_text()
    assert 'child_id == SELF_ID' in source
    assert 'authority_effect": "NONE"' in source


def test_reusable_registry_resolves_scheduler_shard_once():
    constructor = load("constructor", "scripts/materialize_reusable_task_construct.py")
    registry = constructor.load_reusable_task_registry()
    row = constructor.resolve_reusable_task(registry, "RT-REUSABLE-TASK-SCHEDULER-001")
    assert row["name"] == "Reusable Task Scheduler"
