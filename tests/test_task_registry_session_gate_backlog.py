"""Adversarial source-only tests for shared component-010 backlog diagnosis."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/audit_task_registry_session_gate_backlog.py"
spec = importlib.util.spec_from_file_location("component010_backlog", SOURCE)
audit_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit_mod)


def fixture(tmp_path):
    registry = tmp_path / "registry.json"
    shards = tmp_path / "shards"
    shards.mkdir()
    registry.write_text(json.dumps({
        "generation": 88,
        "tasks": [
            {"task_id": "TASK-A", "coordination_state": "PROPOSED",
             "checkout_state": "UNCLAIMED", "cosv_task_vector": None,
             "blockers": ["AUTHENTIC_AI_SESSION_GATE_DISPOSITION_NOT_OBTAINED"]},
            {"task_id": "TASK-B", "coordination_state": "ACTIVE",
             "checkout_state": "CHECKED_OUT", "correlation_id": "TASK-B",
             "targets": {"components": ["unrelated"]}}
        ]}), encoding="utf-8")
    (shards / "TASK-B.json").write_text(json.dumps({
        "task_id": "TASK-B", "correlation_id": "TASK-B",
        "coordination_state": "ACTIVE", "checkout_state": "CHECKED_OUT"
    }), encoding="utf-8")
    return registry, shards


def test_source_only_work_is_separate_from_authentic_ai_session_execution(tmp_path):
    registry, shards = fixture(tmp_path)
    result = audit_mod.audit(registry, shards)
    task = result["gate_blocked_registry_tasks"][0]
    assert result["registry_generation"] == 88
    assert task["task_id"] == "TASK-A"
    assert task["source_only_gate_requirement"] == "NONE"
    assert task["authentic_disposition_observed"] is False
    assert task["cosv_derivation_authorized_by_this_audit"] is False
    assert result["authority_effect"] == "NONE"
    assert result["projection_complete_for_checked_out_shards"] is True


def test_missing_checked_out_owner_is_reported_not_silently_admitted(tmp_path):
    registry, shards = fixture(tmp_path)
    (shards / "GATE-OWNER.json").write_text(json.dumps({
        "task_id": "GATE-OWNER", "coordination_state": "ACTIVE",
        "checkout_state": "CHECKED_OUT", "issue_ref": "existing#1"
    }), encoding="utf-8")
    before = registry.read_bytes()
    result = audit_mod.audit(registry, shards)
    assert result["projection_complete_for_checked_out_shards"] is False
    assert result["omitted_checked_out_owner_shards"][0]["task_id"] == "GATE-OWNER"
    assert registry.read_bytes() == before


def test_retired_shard_is_not_reintroduced_into_active_registry(tmp_path):
    registry, shards = fixture(tmp_path)
    (shards / "RETIRED-OLD.json").write_text(json.dumps({
        "task_id": "RETIRED-OLD", "coordination_state": "RETIRED",
        "checkout_state": "CHECKED_OUT"
    }), encoding="utf-8")
    assert audit_mod.audit(registry, shards)["projection_complete_for_checked_out_shards"] is True


def test_mismatched_registered_shard_identity_is_reported(tmp_path):
    registry, shards = fixture(tmp_path)
    (shards / "TASK-B.json").write_text(json.dumps({
        "task_id": "TASK-B", "correlation_id": "FORGED",
        "coordination_state": "ACTIVE", "checkout_state": "CHECKED_OUT"
    }), encoding="utf-8")
    result = audit_mod.audit(registry, shards)
    assert any(x.get("field") == "correlation_id" for x in result["mismatched_identity_shards"])


def test_duplicate_canonical_identity_fails_closed(tmp_path):
    registry, shards = fixture(tmp_path)
    current = json.loads(registry.read_text())
    current["tasks"].append(dict(current["tasks"][0]))
    registry.write_text(json.dumps(current), encoding="utf-8")
    try:
        audit_mod.audit(registry, shards)
    except ValueError as exc:
        assert "duplicated" in str(exc)
    else:
        raise AssertionError("duplicate source task must fail")


def test_unreadable_shards_are_visible_projection_defects(tmp_path):
    registry, shards = fixture(tmp_path)
    (shards / "corrupt.json").write_text("{", encoding="utf-8")
    result = audit_mod.audit(registry, shards)
    assert not result["projection_complete_for_checked_out_shards"]
    assert result["unreadable_shards"][0]["path"] == "corrupt.json"


def test_shard_without_exact_filename_identity_cannot_fake_owner(tmp_path):
    registry, shards = fixture(tmp_path)
    (shards / "SOMEONE-ELSE.json").write_text(json.dumps({
        "task_id": "GATE-OWNER", "coordination_state": "ACTIVE",
        "checkout_state": "CHECKED_OUT"
    }), encoding="utf-8")
    result = audit_mod.audit(registry, shards)
    assert result["mismatched_identity_shards"][0]["declared_task_id"] == "GATE-OWNER"


def test_source_gate_is_not_a_second_runtime_or_authorizing_caller():
    policy = json.loads((ROOT / "data/task-registry-ai-ingress-policy.json").read_text(encoding="utf-8"))
    source = policy["source_only_coordination_boundary"]
    assert source["authority_effect"] == "NONE"
    assert source["classification"] == "NONAUTHORITATIVE_SOURCE_WORK_DOES_NOT_REQUIRE_AN_AUTHENTIC_AI_SESSION_DISPOSITION"
    assert "NO_FAKE_AI_SESSION_OR_CHECKIN_LEDGER_EVENT" in source["constraints"]
    assert "AUTHENTIC_AI_SESSION_GATE_REMAINS_REQUIRED_WHEN_ACTUAL_AI_SESSION_ADMISSION_IS_NEEDED" in source["constraints"]


def test_existing_resident_refresh_materializes_entire_source_gate_dependency_closure():
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
    for required in (
        "scripts/evaluate_task_registry_ai_session_checkin.py",
        "scripts/evaluate_task_registry_collision_checkin.py",
        "scripts/task_registry_checkin_event_history.py",
        "scripts/validate_task_registration_substrate_resolution.py",
        "scripts/audit_task_registry_session_gate_backlog.py",
        "data/canonical-task-registry.json",
        "data/task-registry-ai-ingress-policy.json",
        "data/task-registry-general-checkin-caller-policy.json",
        "data/task-registry-global-invariants.json",
    ):
        assert f'Path("{required}")' in refresh
    # Source refresh must never copy the mutable session ledger.
    assert 'Path("runtime/task-registry/checkin-events.jsonl")' not in refresh


# The repository's hosted Cross-Task CI runs unittest, so execute the same
# adversarial functions there rather than silently collecting zero tests.
import tempfile
import unittest


class TestComponent010BatchAudit(unittest.TestCase):
    def _with_tmp(self, test):
        with tempfile.TemporaryDirectory() as directory:
            test(Path(directory))

    def test_source_only_work_is_separate_from_authentic_ai_session_execution(self):
        self._with_tmp(test_source_only_work_is_separate_from_authentic_ai_session_execution)

    def test_missing_checked_out_owner_is_reported_not_silently_admitted(self):
        self._with_tmp(test_missing_checked_out_owner_is_reported_not_silently_admitted)

    def test_retired_shard_is_not_reintroduced_into_active_registry(self):
        self._with_tmp(test_retired_shard_is_not_reintroduced_into_active_registry)

    def test_mismatched_registered_shard_identity_is_reported(self):
        self._with_tmp(test_mismatched_registered_shard_identity_is_reported)

    def test_duplicate_canonical_identity_fails_closed(self):
        self._with_tmp(test_duplicate_canonical_identity_fails_closed)

    def test_unreadable_shards_are_visible_projection_defects(self):
        self._with_tmp(test_unreadable_shards_are_visible_projection_defects)

    def test_shard_without_exact_filename_identity_cannot_fake_owner(self):
        self._with_tmp(test_shard_without_exact_filename_identity_cannot_fake_owner)

    def test_source_gate_is_not_a_second_runtime_or_authorizing_caller(self):
        test_source_gate_is_not_a_second_runtime_or_authorizing_caller()

    def test_existing_resident_refresh_materializes_entire_source_gate_dependency_closure(self):
        test_existing_resident_refresh_materializes_entire_source_gate_dependency_closure()


def test_exact_checked_out_gate_and_custody_owner_shards_are_projected():
    registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text(encoding="utf-8"))
    assert registry["generation"] >= 224
    rows = {row["task_id"]: row for row in registry["tasks"]}
    for tid in (
        "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001",
        "TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001",
    ):
        shard = json.loads((ROOT / "data/canonical-task-records" / (tid + ".json")).read_text(encoding="utf-8"))
        row = rows[tid]
        assert row["task_id"] == shard["task_id"]
        assert row["checkout_state"] == shard["checkout_state"] == "CHECKED_OUT"
        assert row["coordination_state"] == shard["coordination_state"] == "ACTIVE"
        assert row.get("cosv_task_vector") == shard.get("cosv_task_vector")
        for key in ("correlation_id", "root_correlation_id", "parent_task_id", "targets"):
            assert row.get(key) == shard.get(key)
    assert len(rows) == len(registry["tasks"])


def _test_exact_owner_projection(self):
    test_exact_checked_out_gate_and_custody_owner_shards_are_projected()


TestComponent010BatchAudit.test_exact_owner_projection = _test_exact_owner_projection
