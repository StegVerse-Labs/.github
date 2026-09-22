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
