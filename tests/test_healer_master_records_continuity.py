from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_healer_handoff_does_not_make_master_records_a_general_transition_gate() -> None:
    handoff = json.loads((ROOT / "handoffs" / "SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))
    continuity = handoff["continuity"]
    assert continuity["checkpoint_ref"] == "receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json"
    assert continuity["master_records_required"] is True  # legacy field; bounded below by canonical contract
    refs = set(handoff["task"]["source_refs"])
    assert "control/canonical-master-records-state-transition-custody-contract.json" in refs
    assert "workers/canonical_state_transition_custody.py" in refs


def test_canonical_contract_restricts_master_records_to_organization_records_and_reconstruction() -> None:
    contract = json.loads((ROOT / "control" / "canonical-master-records-state-transition-custody-contract.json").read_text(encoding="utf-8"))
    invariants = contract["invariants"]
    assert invariants["every_observed_governed_state_transition_emits_state_receipt"] is True
    assert invariants["every_state_receipt_is_submitted_to_master_records"] is False
    assert invariants["only_organization_records_may_be_recorded_in_master_records"] is True
    assert invariants["reconstruction_is_the_only_other_permitted_master_records_reference"] is True
    assert invariants["master_records_may_not_gate_transition_execution"] is True
    assert invariants["master_records_may_not_be_general_state_transition_custody"] is True
    assert invariants["master_records_may_not_be_general_evidence_custody"] is True
    assert contract["transition_authority"] == "INTERLOCK_INTR"
    assert contract["authority_effect"] == "NONE_ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY"
