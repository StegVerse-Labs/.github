"""Synthetic organization receipt-chain checks; no claim of authentic runtime."""
from __future__ import annotations
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("org_transition_audit_test",ROOT/"resident-runtime/aggregate_repo_transition.py")
LEDGER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LEDGER)


def canonical_receipt(transition_id="TEST_START", outcome="OBSERVED", reason=None):
    return {
        "schema":"stegverse.canonical-state-transition-receipt/v1",
        "transition_id":transition_id,"transition_sequence":1,
        "subject_or_correlation_id":"source-test-task",
        "transition_outcome":outcome,
        "transition_evidence":{"reason":reason} if reason else {},
        "required_evidence_manifest":[],
        "authority_effect":"NONE_STATE_RECEIPT_ONLY",
    }


class ExistingOrganizationLedgerAuditTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        env=patch.dict(os.environ,{"STEGVERSE_ORG_LEDGER_ROOT":str(self.root)})
        env.start()
        self.addCleanup(env.stop)

    def test_source_retained_for_genesis_and_exact_replay(self):
        first=canonical_receipt()
        row=LEDGER.aggregate_transition(first)
        self.assertTrue((self.root/row["source_receipt_ref"]).is_file())
        self.assertEqual(json.loads((self.root/row["source_receipt_ref"]).read_text()),first)
        report=LEDGER.audit_chain()
        self.assertEqual(report["state"],"RECONSTRUCTED_PASS")
        self.assertEqual(report["reconstructed_receipt_count"],1)
        self.assertEqual(report["head_receipt_sha256"],row["receipt_sha256"])

    def test_failed_transition_visible_without_inventing_success(self):
        genesis=LEDGER.aggregate_transition(canonical_receipt())
        failure=LEDGER.aggregate_transition(canonical_receipt("TEST_IRRECOVERABLE","FAIL_CLOSED","AUTHORITATIVE_DENY"))
        report=LEDGER.audit_chain()
        self.assertEqual(report["state"],"RECONSTRUCTED_WITH_FAILURE_TRANSITIONS")
        self.assertEqual(report["reconstructed_receipt_count"],2)
        self.assertEqual(report["failure_transitions"][0]["source_transition_id"],"TEST_IRRECOVERABLE")
        self.assertEqual(report["failure_transitions"][0]["reason"],"AUTHORITATIVE_DENY")
        self.assertEqual(failure["previous_receipt_sha256"],genesis["receipt_sha256"])

    def test_same_exact_source_after_master_records_boundary_is_idempotent(self):
        receipt=canonical_receipt("RETRY_AFTER_CUSTODY_BOUNDARY")
        first=LEDGER.aggregate_transition(receipt)
        original_head=(self.root/"HEAD.json").read_text()
        replay=LEDGER.aggregate_transition(receipt)
        self.assertEqual(first,replay)
        self.assertEqual((self.root/"HEAD.json").read_text(),original_head)
        self.assertEqual(len(list((self.root/"receipts").glob("*.json"))),1)

    def test_duplicate_same_source_with_different_authority_binding_rejected(self):
        receipt=canonical_receipt()
        LEDGER.aggregate_transition(receipt)
        with self.assertRaisesRegex(ValueError,"organization_duplicate_source_binding_mismatch"):
            LEDGER.aggregate_transition(receipt,authority_effect="ALLOW")

    def test_missing_retained_source_reports_integrity_failure(self):
        first=LEDGER.aggregate_transition(canonical_receipt())
        (self.root/first["source_receipt_ref"]).unlink()
        report=LEDGER.audit_chain()
        self.assertEqual(report["state"],"INTEGRITY_FAILURE")
        self.assertTrue(any(x.startswith("SOURCE_RECEIPT_MISSING") for x in report["integrity_errors"]))

    def test_corrupt_head_and_orphan_are_not_promoted(self):
        first=LEDGER.aggregate_transition(canonical_receipt())
        (self.root/"HEAD.json").write_text(json.dumps({"organization":"StegVerse-Labs","receipt_sha256":"sha256:"+"0"*64}))
        report=LEDGER.audit_chain()
        self.assertEqual(report["state"],"INTEGRITY_FAILURE")
        self.assertIn("ORPHAN_ORGANIZATION_RECEIPTS",report["integrity_errors"])
        self.assertEqual(report["reconstructed_receipt_count"],0)

    def test_legacy_org_receipt_without_source_never_claims_full_replay(self):
        first=LEDGER.aggregate_transition(canonical_receipt())
        path=self.root/"receipts"/(first["receipt_sha256"].split(":",1)[1]+".json")
        legacy=dict(first)
        legacy.pop("source_receipt_ref")
        legacy.pop("receipt_sha256")
        legacy_sha=LEDGER.sha(legacy)
        legacy["receipt_sha256"]=legacy_sha
        target=self.root/"receipts"/(legacy_sha.split(":",1)[1]+".json")
        target.write_text(json.dumps(legacy))
        path.unlink()
        (self.root/"HEAD.json").write_text(json.dumps({"organization":"StegVerse-Labs","receipt_sha256":legacy_sha}))
        report=LEDGER.audit_chain()
        self.assertEqual(report["state"],"RECONSTRUCTED_WITH_LEGACY_SOURCE_GAPS")
        self.assertEqual(report["unknown_source_receipts"],[legacy_sha])

    def test_stale_pinned_predecessor_fails_without_advancing_head(self):
        LEDGER.aggregate_transition(canonical_receipt())
        original=(self.root/"HEAD.json").read_bytes()
        with self.assertRaisesRegex(ValueError,"organization_expected_immediate_predecessor_mismatch"):
            LEDGER.aggregate_transition(canonical_receipt("UNAUTHORIZED_STALE"),
                                        expected_previous_receipt_sha256=None,
                                        enforce_expected_previous=True)
        self.assertEqual((self.root/"HEAD.json").read_bytes(),original)


if __name__=="__main__":
    unittest.main()
