from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_healer_handoff_requires_canonical_master_records_custody() -> None:
    handoff = json.loads((ROOT / "handoffs" / "SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))
    continuity = handoff["continuity"]
    assert continuity["checkpoint_ref"] == "receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json"
    assert continuity["master_records_required"] is True
    refs = set(handoff["task"]["source_refs"])
    assert "control/canonical-master-records-state-transition-custody-contract.json" in refs
    assert "workers/canonical_state_transition_custody.py" in refs


def test_canonical_contract_requires_every_observed_governed_transition_in_master_records() -> None:
    contract = json.loads((ROOT / "control" / "canonical-master-records-state-transition-custody-contract.json").read_text(encoding="utf-8"))
    invariants = contract["invariants"]
    assert invariants["every_observed_governed_state_transition_emits_state_receipt"] is True
    assert invariants["every_state_receipt_is_submitted_to_master_records"] is True
    assert invariants["master_records_reconstructs_current_state_from_retained_receipts"] is True
    assert contract["transition_authority"] == "INTERLOCK_INTR"
    assert contract["custody_reconstruction_authority"] == "MASTER_RECORDS"


def test_healer_consumer_carries_projected_checkpoint_identity_into_canonical_master_records() -> None:
    source = (ROOT / "scripts" / "consume_healer_sovereign_scheduler_request.py").read_text(encoding="utf-8")
    assert 'CHECKPOINT_REL = Path("receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json")' in source
    assert "custody_projected_checkpoint" in source
    assert "PROJECTED_HEALER_CHECKPOINT_FENCE_NOT_BOUND_TO_CURRENT_CYCLE" in source
    assert '"evidence_type": "HEALER_FENCED_CHECKPOINT"' in source
    assert 'required_evidence_manifest=[evidence]' in source
    assert '"transition_id": master_records.get("transition_id")' in source
    assert '"receipt_sha256": master_records.get("receipt_sha256")' in source
    assert '"master_record_ref": master_records.get("master_record_ref")' in source
    assert '"master_records_checkpoint_custody_complete": custody_complete' in source
    assert 'master_records.get("required_evidence_validation_status") == "PASS"' in source
    assert 'master_records.get("receipt_sha256") == master_records.get("reconstructed_receipt_sha256")' in source
