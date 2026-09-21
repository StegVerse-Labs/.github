from __future__ import annotations

from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS
from workers.canonical_state_transition_custody import (
    HB_CREATION_PROTOCOL,
    build_state_receipt,
    current_hb_creation_reference,
)


def test_creation_reference_matches_canonical_hb_known_vector() -> None:
    ref = current_hb_creation_reference(sampled_unix_ns=PROTOCOL_ANCHOR_UNIX_NS + 680_000_000)
    assert ref["heartbeat_epoch"] == 100
    assert ref["heartbeat_generation"] == 100
    assert ref["heartbeat_id"] == "HB-0000002S"
    assert ref["protocol"] == HB_CREATION_PROTOCOL
    assert ref["authority_effect"] == "NONE_REFERENCE_ONLY"
    assert ref["grants_execution_authority"] is False
    assert ref["grants_transition_authority"] is False
    assert ref["grants_custody_authority"] is False
    assert ref["grants_credential_authority"] is False


def test_new_canonical_receipt_freezes_hb_creation_reference_before_hashing() -> None:
    receipt = build_state_receipt(
        transition_id="TEST-HB-CREATION-REFERENCE",
        transition_sequence=1,
        subject_or_correlation_id="TEST-HB-CREATION-REFERENCE",
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=None,
        resulting_state_ref_or_hash="state:test",
        governance_decision_ref_where_applicable=None,
        transition_evidence={"source_validation_only": True},
        required_evidence_manifest=[],
        recorded_at="2026-09-21T00:00:00Z",
    )
    assert receipt["hb_creation_protocol"] == HB_CREATION_PROTOCOL
    assert receipt["hb_creation_reference"]["protocol"] == HB_CREATION_PROTOCOL
    assert receipt["hb_creation_reference"]["authority_effect"] == "NONE_REFERENCE_ONLY"
    assert receipt["authority_effect"] == "NONE_STATE_RECEIPT_ONLY"
