"""Regression cases for source validation; fixtures are not runtime receipts."""
import unittest

from scripts.validate_transition_disposition import (
    validate_external_framework_finding,
    validate_transition_disposition,
)

D = "a" * 64


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
    }


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
                     master_records_receipt_ref="master-records:exact:1")
        self.assertEqual(validate_transition_disposition(value), [])

    def test_actual_deny_without_custody_is_rejected(self):
        value = baseline("DENY", "ACTUAL_EXECUTION")
        value.update(immediate_predecessor_receipt_sha256=D, receipt_sha256=D)
        self.assertIn("ACTUAL_EXECUTION_RECONSTRUCTION_REQUIRED",
                      validate_transition_disposition(value))

    def test_actual_deny_with_matching_custody(self):
        value = baseline("DENY", "ACTUAL_EXECUTION")
        value.update(immediate_predecessor_receipt_sha256=D,
                     receipt_sha256=D, reconstructed_receipt_sha256=D,
                     master_records_reconstruction_status="PASS",
                     master_records_receipt_ref="master-records:exact:denied")
        self.assertEqual(validate_transition_disposition(value), [])

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
