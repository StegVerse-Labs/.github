from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/canonical-task-registry.json"
SYSTEM_HANDOFF = ROOT / "docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md"
RUNTIME_HANDOFF = ROOT / "docs/CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md"
TASK_ID = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"


def task():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return registry, next(row for row in registry["tasks"] if row["task_id"] == TASK_ID)


def test_parent_has_no_duplicate_runtime_proof_dependencies():
    registry, row = task()
    assert registry["generation"] >= 130
    assert row["dependencies"] == []
    assert "INGRESS_ADMITTED" in row["allowed_next_transitions"]


def test_parent_completion_is_terminal_state_plus_master_records_closure():
    _, row = task()
    completion = row["completion"]
    assert completion["completion_semantics"] == "TERMINAL_CANONICAL_STATE_WITH_MASTER_RECORDS_TRANSITION_CLOSURE"
    assert completion["duplicate_runtime_proof_required"] is False
    assert completion["separate_authentic_runtime_evidence_class_required"] is False
    assert completion["terminal_state_is_completion_truth"] is True


def test_parent_expected_predicates_are_transition_closure_not_runtime_observers():
    _, row = task()
    predicates = set(row["expected_evidence_predicates"])
    forbidden = {
        "AUTHENTIC_TASK_INGRESS_OBSERVED",
        "AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED",
        "AUTHENTIC_MASTER_RECORDS_RECONCILIATION_OBSERVED",
        "AUTHENTIC_TASK_EGRESS_OR_CLOSURE_OBSERVED",
    }
    assert predicates.isdisjoint(forbidden)
    assert {
        "CANONICAL_STATE_TRANSITION_SEQUENCE_RECORDED",
        "EVERY_GOVERNED_TRANSITION_MASTER_RECORDS_RECORDED",
        "EVERY_GOVERNED_TRANSITION_RECONSTRUCTION_PASS",
        "EVERY_GOVERNED_TRANSITION_REQUIRED_EVIDENCE_VALIDATION_PASS",
        "EVERY_GOVERNED_TRANSITION_RECEIPT_RECONSTRUCTION_DIGEST_EQUAL",
        "TERMINAL_CANONICAL_STATE_REACHED",
    }.issubset(predicates)


def test_interlock_and_master_records_are_path_and_consequence_not_preconditions():
    _, row = task()
    model = row["authority_model"]
    assert model["interlock_intr_is_transition_path_not_precondition"] is True
    assert model["master_records_is_transition_custody_not_precondition"] is True
    assert model["separate_runtime_observer_is_completion_authority"] is False


def test_canonical_handoffs_do_not_restore_second_proof_layer():
    system = SYSTEM_HANDOFF.read_text(encoding="utf-8")
    runtime = RUNTIME_HANDOFF.read_text(encoding="utf-8")
    assert "There is no separate post-transition requirement" in system
    assert "No separate runtime-proof class is required." in runtime
    assert "AUTHENTIC_END_TO_END_LIFECYCLE_PENDING" not in system
    assert "AUTHENTIC_LIFECYCLE_PENDING" not in runtime
