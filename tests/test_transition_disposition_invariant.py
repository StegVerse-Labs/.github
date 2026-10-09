"""Regression cases for source validation; fixtures are not runtime receipts."""
import unittest

from scripts.validate_transition_disposition import (
    master_records_evidence,
    validate_external_framework_finding,
    validate_transition_disposition,
)

D = "a" * 64
O = "sha256:" + "b" * 64


def organization_receipt(source=D, receipt=O):
    """The organization_receipt object submit_state_receipt() returns, as a record carries it."""
    return {"schema": "stegverse.organization-transition-receipt/v1",
            "receipt_sha256": receipt, "source_transition_sha256": "sha256:" + source}


def baseline(disposition="DENY", evidence_class="ATTEMPTED_INGRESS"):
    return {
        "task_id": "TASK-001", "correlation_id": "COR-001",
        "manifest_sha256": D, "processing_capability": "ecosystem_diagnostic",
        "route_id": "stegverse.route.ecosystem-diagnostic.v1",
        "producer": "sdk-boundary", "boundary": "SDK_TO_INTR_ATTACHMENT",
        "requested_action": "attach", "predecessor_state": "PROPOSED",
        "predecessor_state_sha256": D, "proposed_successor": "INGRESS_ADMITTED",
        "evaluated_constraint_ids": ["intr.url.present/v1"],
        "evidence_class": evidence_class, "disposition": disposition,
        "consequence_committed": False,
        "failure_code": "UNIVERSAL_INTR_INGRESS_NOT_CONFIGURED",
        "failed_predicate": "intr.url.present/v1",
        "required_evidence_or_repair": "Supply existing configured InTr endpoint",
        "retry_entrypoint": "SDK_TO_INTR_ATTACHMENT",
        "owning_existing_goal": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
        "next_attempt": "Retry exact manifest after endpoint is available",
        "evidence_refs": ["StegVerse-Labs/.github#1766"],
    }


def actual_allow():
    value = baseline("ALLOW", "ACTUAL_EXECUTION")
    value.update(consequence_committed=True, receipt_sha256=D,
                 immediate_predecessor_receipt_sha256=D,
                 organization_receipt=organization_receipt())
    return value


def actual_deny():
    value = baseline("DENY", "ACTUAL_EXECUTION")
    value.update(receipt_sha256=D, immediate_predecessor_receipt_sha256=D,
                 organization_receipt=organization_receipt())
    return value


def unobserved_effect():
    """An effect-transition record: the effect was invoked, its outcome not observed."""
    value = actual_allow()
    value.pop("consequence_committed")
    value.update(consequence_observation="NOT_AUTHENTICALLY_OBSERVED",
                 reconciliation_entrypoint="manifest:reconciliation-read/v1")
    return value


class TestDisposition(unittest.TestCase):
    def test_actionable_ingress_deny(self):
        self.assertEqual(validate_transition_disposition(baseline()), [])

    def test_unknown_not_terminal(self):
        value = baseline()
        value["disposition"] = "UNKNOWN"
        self.assertIn("UNDEFINED_DISPOSITION", validate_transition_disposition(value))

    def test_missing_repair_rejected(self):
        value = baseline()
        value.pop("failed_predicate")
        self.assertIn("NON_ALLOW_REPAIR_REQUIRED:failed_predicate",
                      validate_transition_disposition(value))

    def test_non_allow_evidence_refs_missing(self):
        value = baseline()
        value.pop("evidence_refs")
        self.assertIn("NON_ALLOW_REPAIR_REQUIRED:evidence_refs",
                      validate_transition_disposition(value))

    def test_non_allow_evidence_refs_malformed(self):
        for refs in ([], [""], ["ref", "  "], "StegVerse-Labs/.github#1766", None, [1]):
            with self.subTest(evidence_refs=refs):
                value = baseline("FAIL_CLOSED")
                value["evidence_refs"] = refs
                self.assertIn("NON_ALLOW_REPAIR_REQUIRED:evidence_refs",
                              validate_transition_disposition(value))

    def test_non_allow_evidence_refs_well_formed(self):
        value = baseline("FAIL_CLOSED")
        value["evidence_refs"] = [
            "SOURCE_RECORD_ONLY:data/canonical-task-records/TASK-001.json",
            "https://github.com/StegVerse-Labs/.github/pull/1766",
        ]
        self.assertEqual(validate_transition_disposition(value), [])

    def test_allow_does_not_require_evidence_refs(self):
        value = baseline("ALLOW", "ACTUAL_EXECUTION")
        value.pop("evidence_refs")
        value.update(consequence_committed=True,
                     receipt_sha256=D, reconstructed_receipt_sha256=D,
                     immediate_predecessor_receipt_sha256=D,
                     master_records_reconstruction_status="PASS",
                     master_records_receipt_ref="master-records:exact:1",
                     organization_receipt=organization_receipt())
        self.assertEqual(validate_transition_disposition(value), [])

    def test_deny_cannot_commit(self):
        value = baseline()
        value["consequence_committed"] = True
        self.assertIn("NON_ALLOW_MUST_NOT_COMMIT",
                      validate_transition_disposition(value))

    def test_source_only_cannot_allow(self):
        value = baseline("ALLOW", "SOURCE_VALIDATION")
        value["consequence_committed"] = True
        self.assertIn("ALLOW_REQUIRES_ACTUAL_EXECUTION",
                      validate_transition_disposition(value))

    def test_evidenced_allow(self):
        value = baseline("ALLOW", "ACTUAL_EXECUTION")
        value.update(consequence_committed=True,
                     receipt_sha256=D, reconstructed_receipt_sha256=D,
                     immediate_predecessor_receipt_sha256=D,
                     master_records_reconstruction_status="PASS",
                     master_records_receipt_ref="master-records:exact:1",
                     organization_receipt=organization_receipt())
        self.assertEqual(validate_transition_disposition(value), [])

    def test_actual_deny_without_master_records_validates_with_organization_receipt(self):
        # Inverted (#3012 V1/V5): Master Records reconstruction never gates the
        # Organization's runtime reality; the Organization receipt is the reference.
        value = baseline("DENY", "ACTUAL_EXECUTION")
        value.update(immediate_predecessor_receipt_sha256=D, receipt_sha256=D,
                     organization_receipt=organization_receipt())
        self.assertEqual(validate_transition_disposition(value), [])

    def test_actual_deny_with_matching_custody(self):
        value = baseline("DENY", "ACTUAL_EXECUTION")
        value.update(immediate_predecessor_receipt_sha256=D,
                     receipt_sha256=D, reconstructed_receipt_sha256=D,
                     master_records_reconstruction_status="PASS",
                     master_records_receipt_ref="master-records:exact:denied",
                     organization_receipt=organization_receipt())
        self.assertEqual(validate_transition_disposition(value), [])

    def test_allow_without_master_records_fields_validates(self):
        value = actual_allow()
        for key in ("master_records_reconstruction_status", "master_records_receipt_ref",
                    "reconstructed_receipt_sha256"):
            self.assertNotIn(key, value)
        self.assertEqual(validate_transition_disposition(value), [])

    def test_reconstruction_mismatch_is_evidence_not_error(self):
        for disposition in ("ALLOW", "DENY"):
            with self.subTest(disposition=disposition):
                value = actual_allow() if disposition == "ALLOW" else actual_deny()
                value.update(reconstructed_receipt_sha256="c" * 64,
                             master_records_reconstruction_status="FAILED")
                self.assertEqual(validate_transition_disposition(value), [])
                evidence = master_records_evidence(value)
                self.assertIs(evidence["reconstructed_receipt_sha256_matches"], False)
                self.assertEqual(evidence["master_records_reconstruction_status"], "FAILED")
                self.assertIs(evidence["transition_gate"], False)

    def test_reconstruction_pass_without_reference_is_evidence_not_error(self):
        value = baseline()
        value["master_records_reconstruction_status"] = "PASS"
        self.assertEqual(validate_transition_disposition(value), [])
        self.assertIsNone(master_records_evidence(value)["master_records_receipt_ref"])

    def test_reconstruction_evidence_absent(self):
        evidence = master_records_evidence(actual_allow())
        self.assertIsNone(evidence["reconstructed_receipt_sha256_matches"])
        self.assertIsNone(evidence["master_records_reconstruction_status"])

    def test_actual_execution_missing_organization_receipt_rejected(self):
        for value in (actual_allow(), actual_deny()):
            with self.subTest(disposition=value["disposition"]):
                value.pop("organization_receipt")
                # Master Records fields do not substitute for the Organization receipt.
                value.update(reconstructed_receipt_sha256=D,
                             master_records_reconstruction_status="PASS",
                             master_records_receipt_ref="master-records:exact:1")
                self.assertIn("ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_REQUIRED",
                              validate_transition_disposition(value))

    def test_organization_receipt_malformed_rejected(self):
        bad = (
            "sha256:" + "b" * 64,
            {**organization_receipt(), "schema": "stegverse.customer-local-receipt/v1"},
            {**organization_receipt(), "receipt_sha256": "b" * 64},
            {**organization_receipt(), "receipt_sha256": None},
        )
        for receipt in bad:
            with self.subTest(organization_receipt=receipt):
                value = actual_allow()
                value["organization_receipt"] = receipt
                self.assertIn("ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_INVALID",
                              validate_transition_disposition(value))

    def test_organization_receipt_must_bind_this_receipt(self):
        value = actual_allow()
        value["organization_receipt"] = organization_receipt(source="c" * 64)
        self.assertIn("ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_NOT_BOUND",
                      validate_transition_disposition(value))

    def test_organization_receipt_projection_must_agree(self):
        value = actual_allow()
        value["organization_receipt_sha256"] = O
        self.assertEqual(validate_transition_disposition(value), [])
        value["organization_receipt_sha256"] = "sha256:" + "c" * 64
        self.assertIn("ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_CONFLICT",
                      validate_transition_disposition(value))

    def test_unobserved_effect_allow_validates_without_committed_boolean(self):
        value = unobserved_effect()
        self.assertEqual(validate_transition_disposition(value), [])

    def test_unobserved_effect_must_not_assert_committed(self):
        for committed in (True, False):
            with self.subTest(consequence_committed=committed):
                value = unobserved_effect()
                value["consequence_committed"] = committed
                self.assertIn("UNOBSERVED_EFFECT_MUST_NOT_ASSERT_COMMITTED",
                              validate_transition_disposition(value))

    def test_unobserved_effect_requires_reconciliation_edge(self):
        for edge in (None, "", "  "):
            with self.subTest(reconciliation_entrypoint=edge):
                value = unobserved_effect()
                value["reconciliation_entrypoint"] = edge
                self.assertIn("UNOBSERVED_EFFECT_RECONCILIATION_ENTRYPOINT_REQUIRED",
                              validate_transition_disposition(value))

    def test_invoked_effect_not_relabelled_non_allow(self):
        for disposition in ("DENY", "FAIL_CLOSED"):
            with self.subTest(disposition=disposition):
                value = unobserved_effect()
                value["disposition"] = disposition
                self.assertIn("INVOKED_EFFECT_NOT_RELABELLED_NON_ALLOW",
                              validate_transition_disposition(value))

    def test_consequence_observation_values(self):
        value = unobserved_effect()
        value["consequence_observation"] = "UNKNOWN"
        self.assertIn("INVALID_CONSEQUENCE_OBSERVATION", validate_transition_disposition(value))
        observed = actual_allow()
        observed["consequence_observation"] = "OBSERVED"
        self.assertEqual(validate_transition_disposition(observed), [])
        observed["consequence_committed"] = False
        self.assertIn("ALLOW_COMMIT_EVIDENCE_REQUIRED", validate_transition_disposition(observed))

    def test_observed_non_allow_commit_still_refused(self):
        value = actual_deny()
        value.update(consequence_observation="OBSERVED", consequence_committed=True)
        self.assertIn("NON_ALLOW_MUST_NOT_COMMIT", validate_transition_disposition(value))

    def test_decision_record_requires_committed_boolean(self):
        for committed in (None, "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"):
            with self.subTest(consequence_committed=committed):
                value = baseline()
                value["consequence_committed"] = committed
                self.assertIn("CONSEQUENCE_COMMITTED_BOOLEAN_REQUIRED",
                              validate_transition_disposition(value))
        value = baseline()
        value.pop("consequence_committed")
        self.assertIn("CONSEQUENCE_COMMITTED_BOOLEAN_REQUIRED",
                      validate_transition_disposition(value))

    def test_external_unperformed_no_runtime_claim(self):
        value = baseline("DENY", "ACTUAL_EXECUTION")
        value.update(immediate_predecessor_receipt_sha256=D, receipt_sha256=D)
        finding = dict(source_url="https://example.test/source", source_version="v1",
                       claim="X", test_input_sha256=D,
                       execution_performed=False, transition_disposition=value)
        self.assertIn("FINDING_UNPERFORMED_TEST_CANNOT_CLAIM_EXECUTION",
                      validate_external_framework_finding(finding))

    def test_external_source_finding_same_validator(self):
        finding = dict(source_url="https://example.test/source", source_version="v1",
                       claim="X", test_input_sha256=D,
                       execution_performed=False, transition_disposition=baseline())
        self.assertEqual(validate_external_framework_finding(finding), [])


if __name__ == "__main__":
    unittest.main()
