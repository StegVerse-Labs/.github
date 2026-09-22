from __future__ import annotations

import datetime as dt
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


def test_scheduler_contract_preserves_authority_owners_and_retry_semantics():
    contract = json.loads((ROOT / "data/reusable-task-scheduler-contract.json").read_text())
    inv = contract["invariants"]
    assert inv["neutral_owner"] is True
    assert inv["healer_is_consumer_not_owner"] is True
    assert inv["self_scheduling_prohibited"] is True
    assert inv["slot_idempotency_owned_by_scheduler"] is True
    assert inv["bounded_retry_backoff_owned_by_scheduler"] is True
    assert inv["worker_claim_fence_authority"] == "WorkerCoordinator"
    assert inv["transition_authority"] == "Interlock/InTr"
    assert inv["user_verification_authority"] == "KV/SKAP Vault"
    assert inv["retry_does_not_upgrade_child_boundary_to_success"] is True


def test_scheduler_selection_and_self_recursion_guard():
    mod = load("neutral_scheduler", "scripts/run_reusable_task_scheduler.py")
    now = mod.parse_now("2026-09-13T19:00:00Z")
    assert mod.due({"enabled": True, "run_hours_utc": [19]}, now) is True
    assert mod.due({"enabled": True, "run_hours_utc": [18]}, now) is False
    assert mod.selected({"reusable_task_id": "RT-X", "repository": "StegVerse-Labs/.github", "aliases": ["x"]}, "x") is True
    assert mod.selected({"reusable_task_id": "RT-X", "repository": "StegVerse-Labs/.github", "aliases": []}, ".github") is True
    source = (ROOT / "scripts/run_reusable_task_scheduler.py").read_text()
    assert 'child_id == SELF_ID' in source
    assert 'authority_effect": "NONE"' in source


def test_scheduler_owns_hour_slot_idempotency_and_bounded_retry_gate():
    mod = load("neutral_scheduler_retry", "scripts/run_reusable_task_scheduler.py")
    now = dt.datetime(2026, 9, 13, 19, 10, tzinfo=dt.timezone.utc)
    row = {"retry_interval_minutes": 15, "max_attempts_per_slot": 4}
    assert mod.slot_id("RT-NATIVE-EMAIL-ACTION-MONITOR-001", now) == "rt-native-email-action-monitor-001-20260913T19Z"
    assert mod.slot_id(
        "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001",
        now,
        "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001",
    ) == "steghealth-kv-interlock-production-endpoint-001-20260913T19Z"

    may_attempt, reason, retry_at = mod.retry_gate(row, {
        "attempt_count": 1,
        "last_attempt_at": "2026-09-13T19:00:00Z",
    }, now)
    assert may_attempt is False
    assert reason == "RETRY_BACKOFF_ACTIVE"
    assert retry_at == "2026-09-13T19:15:00Z"

    may_attempt, reason, retry_at = mod.retry_gate(row, {
        "attempt_count": 4,
        "last_attempt_at": "2026-09-13T19:45:00Z",
    }, dt.datetime(2026, 9, 13, 19, 55, tzinfo=dt.timezone.utc))
    assert may_attempt is False
    assert reason == "MAX_ATTEMPTS_REACHED_FOR_SLOT"
    assert retry_at is None


def test_boundary_receipt_is_not_a_successful_slot():
    mod = load("neutral_scheduler_boundary", "scripts/run_reusable_task_scheduler.py")
    assert "BOUNDARY_RECORDED" not in mod.SUCCESS_STATES
    assert "AUTOMATABLE_STEPS_EXHAUSTED" in mod.SUCCESS_STATES
    assert "ENTROPY_RECOVERY_RECORDED" in mod.SUCCESS_STATES


def test_reusable_registry_resolves_scheduler_shard_once():
    constructor = load("constructor", "scripts/materialize_reusable_task_construct.py")
    registry = constructor.load_reusable_task_registry()
    row = constructor.resolve_reusable_task(registry, "RT-REUSABLE-TASK-SCHEDULER-001")
    assert row["name"] == "Reusable Task Scheduler"


def test_scheduler_does_not_treat_deferred_child_as_advanced_transition():
    source = (ROOT / "scripts/run_reusable_task_scheduler.py").read_text()
    assert 'advanced_states = {"COMPLETE", "BOUNDARY_RECORDED"}' in source
    assert '"completion_predicates_satisfied": declared if all_advanced else []' in source
    assert '"all_due_tasks_advanced_to_completion_or_authentic_boundary": all_advanced' in source
    assert '"successor_admissible": all_advanced' in source
    assert 'return 0 if all_advanced else 3' in source
