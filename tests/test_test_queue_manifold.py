import json
from pathlib import Path

import pytest

from state_language.test_queue_manifold import (
    apply_test_disposition,
    build_queue_manifold,
    select_candidate_bundle,
    validate_bundle_instruction,
    validate_descriptor,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "test_queue_manifold.v1.json"


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _snapshot(version=1, heartbeat=None):
    data = _fixture()
    return build_queue_manifold(
        data["tests"],
        manifold_version=version,
        available_capabilities=data["available_capabilities"],
        available_evidence=data["available_evidence"],
        heartbeat_observation=heartbeat,
    )


def _test(test_id):
    return next(item for item in _fixture()["tests"] if item["test_id"] == test_id)


def test_individual_queue_projection_is_heartbeat_independent():
    snapshot = _snapshot()
    assert snapshot["heartbeat_observation"] is None
    assert snapshot["direct_test_execution_heartbeat_dependency"] is False
    assert snapshot["execution_authority"] == "INDEPENDENT_ADMITTED_CLAIM_FENCE"
    assert snapshot["credential_authority"] == "TV/TVC"
    assert snapshot["authority_effect"] == "NONE"


def test_heartbeat_reference_is_optional_and_non_authorizing():
    snapshot = _snapshot(
        heartbeat={
            "schema": "stegverse.heartbeat-governed-manifold-observation/v1",
            "carrier_epoch": 45,
            "carrier_generation": 9,
            "authority_effect": "NONE_OBSERVATION_ONLY",
        }
    )
    assert snapshot["heartbeat_observation"]["reference_only"] is True
    assert snapshot["heartbeat_observation"]["carrier_epoch"] == 45
    assert snapshot["execution_authority"] == "INDEPENDENT_ADMITTED_CLAIM_FENCE"

    with pytest.raises(ValueError, match="cannot grant queue authority"):
        _snapshot(heartbeat={"authority_effect": "EXECUTE"})


def test_readiness_and_dependency_projection_is_deterministic():
    first = _snapshot()
    second = _snapshot()
    assert first == second

    states = {
        row["test_id"]: row["projected_lifecycle_state"]
        for row in first["tests"]
    }
    assert states == {
        "TQ-001": "READY",
        "TQ-002": "READY",
        "TQ-003": "READY",
        "TQ-004": "READY",
        "TQ-005": "EXECUTED",
    }
    assert first["coherency_groups"] == {
        "integration": ["TQ-004", "TQ-005"],
        "route-validation": ["TQ-001", "TQ-002"],
        "schema-validation": ["TQ-003"],
    }


def test_missing_capability_or_evidence_blocks_without_dropping_test():
    data = _fixture()
    snapshot = build_queue_manifold(
        data["tests"],
        manifold_version=1,
        available_capabilities=["python"],
        available_evidence=["evidence:baseline"],
    )
    rows = {row["test_id"]: row for row in snapshot["tests"]}
    assert rows["TQ-001"]["projected_lifecycle_state"] == "BLOCKED"
    assert "capabilities:network-observation" in rows["TQ-001"]["readiness_blockers"]
    assert "evidence:evidence:route" in rows["TQ-001"]["readiness_blockers"]
    assert {row["test_id"] for row in snapshot["tests"]} == {
        "TQ-001", "TQ-002", "TQ-003", "TQ-004", "TQ-005"
    }


def test_minimum_distinguishing_bundle_defers_equivalent_test_explicitly():
    snapshot = _snapshot()
    bundle = select_candidate_bundle(snapshot, capacity_units=3)
    assert bundle["selected_test_ids"] == ["TQ-001", "TQ-003"]
    assert bundle["deferred_equivalent_tests"] == [{
        "test_id": "TQ-002",
        "reason": "AWAIT_BUNDLE_EVIDENCE_FOR_EQUIVALENT_DISTINGUISHING_SIGNATURE",
        "distinguishing_signature": bundle["deferred_equivalent_tests"][0]["distinguishing_signature"],
    }]
    assert bundle["unselected_ready_test_ids"] == ["TQ-004"]
    assert bundle["execution_authority_granted"] is False
    assert bundle["claim_or_fence_minted"] is False
    assert bundle["heartbeat_authority_granted"] is False
    assert bundle["authority_effect"] == "NONE"


def test_bundle_does_not_silently_terminalize_equivalent_test():
    snapshot = _snapshot()
    bundle = select_candidate_bundle(snapshot, capacity_units=3)
    row = next(row for row in snapshot["tests"] if row["test_id"] == "TQ-002")
    assert row["projected_lifecycle_state"] == "READY"
    assert any(item["test_id"] == "TQ-002" for item in bundle["deferred_equivalent_tests"])


def test_stale_bundle_invalidated_by_version_change():
    snapshot = _snapshot(version=1)
    bundle = select_candidate_bundle(snapshot, capacity_units=3)
    current = _snapshot(version=2)
    with pytest.raises(ValueError, match="STALE_MANIFOLD_VERSION"):
        validate_bundle_instruction(bundle, current)


def test_stale_bundle_invalidated_by_state_hash_change():
    data = _fixture()
    snapshot = _snapshot(version=1)
    bundle = select_candidate_bundle(snapshot, capacity_units=3)
    changed_tests = json.loads(json.dumps(data["tests"]))
    changed_tests[0]["urgency"] = 91
    current = build_queue_manifold(
        changed_tests,
        manifold_version=1,
        available_capabilities=data["available_capabilities"],
        available_evidence=data["available_evidence"],
    )
    with pytest.raises(ValueError, match="STALE_MANIFOLD_HASH"):
        validate_bundle_instruction(bundle, current)


def test_terminal_disposition_requires_evidence_and_never_grants_authority():
    descriptor = _test("TQ-001")
    with pytest.raises(ValueError, match="requires evidence"):
        apply_test_disposition(descriptor, new_state="EXECUTED", evidence_refs=[])

    receipt = apply_test_disposition(
        descriptor,
        new_state="EXECUTED",
        evidence_refs=["receipt:test-run-001"],
    )
    assert receipt["new_state"] == "EXECUTED"
    assert receipt["silent_drop"] is False
    assert receipt["execution_authority_granted"] is False
    assert receipt["credential_authority"] == "TV/TVC"
    assert receipt["authority_effect"] == "NONE"


def test_satisfied_by_bundle_requires_bundle_identity():
    descriptor = _test("TQ-002")
    with pytest.raises(ValueError, match="requires bundle_id"):
        apply_test_disposition(
            descriptor,
            new_state="SATISFIED_BY_BUNDLE",
            evidence_refs=["receipt:bundle-evidence"],
        )
    receipt = apply_test_disposition(
        descriptor,
        new_state="SATISFIED_BY_BUNDLE",
        evidence_refs=["receipt:bundle-evidence"],
        bundle_id="bundle-abc",
    )
    assert receipt["bundle_id"] == "bundle-abc"


def test_person_specific_route_and_authority_escalation_fail_closed():
    descriptor = _test("TQ-001")
    bad = dict(descriptor)
    bad["person_specific_route"] = True
    with pytest.raises(ValueError, match="person-specific"):
        validate_descriptor(bad)

    bad = dict(descriptor)
    bad["authority_effect"] = "EXECUTE"
    with pytest.raises(ValueError, match="cannot grant authority"):
        validate_descriptor(bad)


def test_claimed_test_requires_independent_claim_ref():
    descriptor = _test("TQ-001")
    bad = dict(descriptor)
    bad["lifecycle_state"] = "CLAIMED"
    bad["execution_claim_ref"] = None
    with pytest.raises(ValueError, match="independently admitted"):
        validate_descriptor(bad)


def test_capacity_scaling_does_not_change_authority_semantics():
    snapshot = _snapshot()
    small = select_candidate_bundle(snapshot, capacity_units=1)
    large = select_candidate_bundle(snapshot, capacity_units=100)
    for bundle in (small, large):
        assert bundle["execution_authority_granted"] is False
        assert bundle["claim_or_fence_minted"] is False
        assert bundle["heartbeat_authority_granted"] is False
        assert bundle["credential_authority"] == "TV/TVC"
        assert bundle["authority_effect"] == "NONE"
    assert len(large["selected_test_ids"]) >= len(small["selected_test_ids"])
