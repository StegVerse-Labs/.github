from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile

# Initialize the existing WorkerCoordinator import graph before importing its custody client.
# Importing the custody client first triggers the pre-existing package circular import.
from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator as _WorkerCoordinatorImportOrder


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
    assert 'Path("resident-runtime/organization_batch_custody.py")' in source
    assert 'Path(".stegverse/transition-ledger/org-contract.json")' in source


def test_exact_source_retry_reuses_org_receipt_after_intervening_transition():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("STEGVERSE_ORG_LEDGER_ROOT")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = tmp
        try:
            source = canonical_receipt()
            first = module.aggregate_transition(source)
            second_source = {**source, "transition_id": "UNRELATED_TRANSITION", "transition_sequence": 2}
            unrelated = module.aggregate_transition(second_source)
            head_before = json.loads((Path(tmp) / "HEAD.json").read_text())
            retry = module.aggregate_transition(source)
            assert retry == first
            assert retry["receipt_sha256"] != unrelated["receipt_sha256"]
            assert json.loads((Path(tmp) / "HEAD.json").read_text()) == head_before
            assert len(list((Path(tmp) / "receipts").glob("*.json"))) == 2
        finally:
            if old is None:
                os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = old


def test_exact_source_retry_rejects_changed_context_without_appending():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("STEGVERSE_ORG_LEDGER_ROOT")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = tmp
        try:
            source = canonical_receipt()
            module.aggregate_transition(source, boundary_evidence={"scope": "original"})
            try:
                module.aggregate_transition(source, boundary_evidence={"scope": "changed"})
            except ValueError as exc:
                assert "context conflict" in str(exc)
            else:
                assert False, "same source with conflicting organization context must fail closed"
            assert len(list((Path(tmp) / "receipts").glob("*.json"))) == 1
        finally:
            if old is None:
                os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = old


def test_exact_source_retry_rejects_tampered_existing_receipt():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("STEGVERSE_ORG_LEDGER_ROOT")
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = tmp
        try:
            source = canonical_receipt()
            first = module.aggregate_transition(source)
            path = Path(tmp) / "receipts" / (first["receipt_sha256"].split(":", 1)[1] + ".json")
            tampered = json.loads(path.read_text())
            tampered["boundary_evidence"] = {"tampered": True}
            path.write_text(json.dumps(tampered))
            try:
                module.aggregate_transition(source)
            except ValueError as exc:
                assert "integrity invalid" in str(exc)
            else:
                assert False, "tampered prior receipt must not be reused"
        finally:
            if old is None:
                os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT", None)
            else:
                os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = old


def test_master_records_unavailable_keeps_exact_organization_receipt_correlation():
    from unittest.mock import patch
    from workers import canonical_state_transition_custody as client
    source = canonical_receipt()
    organization = {
        "schema": "stegverse.organization-transition-receipt/v1",
        "receipt_sha256": "sha256:" + "a" * 64,
        "previous_receipt_sha256": "sha256:" + "b" * 64,
        "source_transition_sha256": client.sha256_uri(source),
        "source_transition_id": source["transition_id"],
    }
    with patch.object(client, "_record_organization_transition",
                      return_value={"state": "RECORDED", "organization_receipt": organization}), \
         patch.object(client, "_submit_http", return_value=None), \
         patch.object(client, "_submit_local", return_value=None):
        result = client.submit_state_receipt(source)
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE"
    assert result["organization_receipt_sha256"] == organization["receipt_sha256"]
    assert result["organization_previous_receipt_sha256"] == organization["previous_receipt_sha256"]
    assert result["organization_source_transition_sha256"] == organization["source_transition_sha256"]
    assert result["organization_source_transition_id"] == source["transition_id"]
    assert result["organization_custody_state"] == "RECORDED"
    assert result["authority_effect"] == "NONE"


def test_master_records_boundary_retains_exact_failure_and_org_identity():
    from unittest.mock import patch
    from workers import canonical_state_transition_custody as client
    source = canonical_receipt()
    organization = {"receipt_sha256": "sha256:" + "a" * 64,
                    "previous_receipt_sha256": None,
                    "source_transition_sha256": client.sha256_uri(source),
                    "source_transition_id": source["transition_id"]}
    failure = {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_LOCAL_AUTHORITY_CALL_FAILED",
               "authority_effect": "NONE"}
    with patch.object(client, "_record_organization_transition",
                      return_value={"state": "RECORDED", "organization_receipt": organization}), \
         patch.object(client, "_submit_http", return_value=failure):
        result = client.submit_state_receipt(source)
    assert result["reason"] == failure["reason"]
    assert result["master_records_response"] == failure
    assert result["organization_receipt_sha256"] == organization["receipt_sha256"]
    assert result["state"] == "BOUNDARY"
    assert result["authority_effect"] == "NONE"


def test_failed_organization_recording_does_not_fabricate_correlation():
    from unittest.mock import patch
    from workers import canonical_state_transition_custody as client
    with patch.object(client, "_record_organization_transition",
                      return_value={"state": "BOUNDARY", "reason": "ORGANIZATION_TRANSITION_LEDGER_SURFACE_UNAVAILABLE",
                                    "authority_effect": "NONE"}):
        result = client.submit_state_receipt(canonical_receipt())
    assert result["state"] == "BOUNDARY"
    assert "organization_receipt_sha256" not in result


def test_worker_assignment_event_carries_failed_master_records_org_correlation():
    source = (ROOT / "heartbeat_runtime/worker_runtime_legacy.py").read_text()
    start = source.index('"worker_assignment_master_records_blocked"')
    event = source[start:source.index("return False", start)]
    assert 'organization_receipt_sha256=assignment_custody.get("organization_receipt_sha256")' in event
    assert 'organization_previous_receipt_sha256=assignment_custody.get("organization_previous_receipt_sha256")' in event
    assert 'organization_source_transition_sha256=assignment_custody.get("organization_source_transition_sha256")' in event
    assert 'organization_custody_state=assignment_custody.get("organization_custody_state")' in event
