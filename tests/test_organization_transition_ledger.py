from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "resident-runtime" / "aggregate_repo_transition.py"
    spec = importlib.util.spec_from_file_location("aggregate_repo_transition_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_receipt():
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": "TEST_TRANSITION",
        "transition_sequence": 1,
        "subject_or_correlation_id": "subject-1",
        "prior_state_ref_or_hash": None,
        "resulting_state_ref_or_hash": "sha256:" + "1" * 64,
        "governance_decision_ref_where_applicable": "intr:test",
        "transition_evidence": {"state": "TEST"},
        "required_evidence_manifest": [],
        "recorded_at": "2026-09-21T00:00:00Z",
        "transition_outcome": "COMPLETED",
        "authority_effect": "NONE_STATE_RECEIPT_ONLY",
        "proof_scope": "THIS_TRANSITION_ONLY",
        "proof_ceiling": "OBSERVED_STATE_TRANSITION_AND_CUSTODY_ONLY",
        "master_records_may_grant_transition_authority": False,
        "master_records_may_grant_execution_authority": False,
    }


def test_canonical_transition_emits_org_receipt_without_fabricating_repo_receipt():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("STEGVERSE_ORG_LEDGER_ROOT")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = tmp
        try:
            source = canonical_receipt()
            record = module.aggregate_transition(source)
        finally:
            if old is None:
                os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = old
    expected = module.sha(source)
    assert record["schema"] == "stegverse.organization-transition-receipt/v1"
    assert record["organization"] == "StegVerse-Labs"
    assert record["source_receipt_schema"] == source["schema"]
    assert record["source_transition_sha256"] == expected
    assert record["canonical_state_transition_receipt_sha256"] == expected
    assert record["repo_receipt_sha256"] is None
    assert record["repo_transition_id"] is None
    assert record["authority_effect"] == "NONE"


def test_org_contract_applies_to_every_transition_inside_organization():
    contract = json.loads((ROOT / ".stegverse/transition-ledger/org-contract.json").read_text())
    assert contract["organization_scope_rule"] == "EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT"
    assert "stegverse.repo-transition-receipt/v1" in contract["consumes"]
    assert "stegverse.canonical-state-transition-receipt/v1" in contract["consumes"]


def test_canonical_custody_records_org_receipt_before_master_records():
    client = (ROOT / "workers/canonical_state_transition_custody.py").read_text()
    submit = client.index("def submit_state_receipt")
    org = client.index("organization = _record_organization_transition(receipt)", submit)
    master = client.index("payload = _submit_http(receipt)", submit)
    assert org < master
    assert "ORGANIZATION_TRANSITION_RECEIPT_BINDING_INVALID" in client


def test_worker_source_refresh_carries_org_ledger_dependencies():
    source = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    assert 'Path("resident-runtime/aggregate_repo_transition.py")' in source
    assert 'Path(".stegverse/transition-ledger/org-contract.json")' in source
