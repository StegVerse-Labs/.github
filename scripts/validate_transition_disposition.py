"""Source-level validator for the proposed ecosystem transition-disposition receipt.

This validates supplied records only. It never mints an InTr or Master Records
receipt, confers admission, or treats a simulated fixture as observed execution.
"""
from __future__ import annotations
from typing import Any, Mapping

NON_ALLOW = {"DENY", "FAIL_CLOSED", "STOP", "DEFER"}
DISPOSITIONS = NON_ALLOW | {"ALLOW"}
EVIDENCE_CLASSES = {
    "SOURCE_VALIDATION", "SYNTHETIC_TEST", "ATTEMPTED_INGRESS",
    "ACTUAL_EXECUTION", "PUBLIC_PUBLICATION",
}
REQUIRED = (
    "task_id", "correlation_id", "manifest_sha256", "processing_capability",
    "route_id", "producer", "boundary", "requested_action",
    "predecessor_state", "predecessor_state_sha256", "proposed_successor",
    "evaluated_constraint_ids", "evidence_class", "disposition",
    "consequence_committed",
)
NON_ALLOW_REQUIRED = (
    "failure_code", "failed_predicate", "required_evidence_or_repair",
    "retry_entrypoint", "owning_existing_goal", "next_attempt",
)
HEX = set("0123456789abcdef")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def validate_transition_disposition(record: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors, never an authorization decision."""
    errors: list[str] = []
    if not isinstance(record, Mapping):
        return ["RECEIPT_OBJECT_REQUIRED"]
    for key in REQUIRED:
        value = record.get(key)
        if value is None or value == "" or (key == "evaluated_constraint_ids" and not value):
            errors.append(f"REQUIRED:{key}")
    for key in ("manifest_sha256", "predecessor_state_sha256"):
        if not _digest(record.get(key)):
            errors.append(f"INVALID_SHA256:{key}")
    if record.get("evidence_class") not in EVIDENCE_CLASSES:
        errors.append("INVALID_EVIDENCE_CLASS")
    if not isinstance(record.get("evaluated_constraint_ids"), list) or not all(
        _nonempty(x) for x in record.get("evaluated_constraint_ids", [])
    ):
        errors.append("INVALID_CONSTRAINT_IDS")
    disposition = record.get("disposition")
    if disposition not in DISPOSITIONS:
        errors.append("UNDEFINED_DISPOSITION")
    committed = record.get("consequence_committed")
    if not isinstance(committed, bool):
        errors.append("CONSEQUENCE_COMMITTED_BOOLEAN_REQUIRED")
    if disposition in NON_ALLOW:
        if committed is not False:
            errors.append("NON_ALLOW_MUST_NOT_COMMIT")
        for key in NON_ALLOW_REQUIRED:
            if not _nonempty(record.get(key)):
                errors.append(f"NON_ALLOW_REPAIR_REQUIRED:{key}")
        if record.get("master_records_reconstruction_status") == "PASS" and not _nonempty(
            record.get("master_records_receipt_ref")
        ):
            errors.append("RECONSTRUCTION_REFERENCE_REQUIRED")
    if disposition == "ALLOW":
        if committed is not True:
            errors.append("ALLOW_COMMIT_EVIDENCE_REQUIRED")
        if record.get("evidence_class") != "ACTUAL_EXECUTION":
            errors.append("ALLOW_REQUIRES_ACTUAL_EXECUTION")
        if record.get("master_records_reconstruction_status") != "PASS":
            errors.append("ALLOW_RECONSTRUCTION_PASS_REQUIRED")
        if not _nonempty(record.get("master_records_receipt_ref")):
            errors.append("ALLOW_MASTER_RECORDS_REFERENCE_REQUIRED")
        if not _digest(record.get("receipt_sha256")):
            errors.append("ALLOW_RECEIPT_SHA256_REQUIRED")
        if record.get("receipt_sha256") != record.get("reconstructed_receipt_sha256"):
            errors.append("ALLOW_RECONSTRUCTED_DIGEST_MISMATCH")
    if record.get("evidence_class") == "ACTUAL_EXECUTION":
        if not _digest(record.get("immediate_predecessor_receipt_sha256")):
            errors.append("ACTUAL_EXECUTION_PREDECESSOR_RECEIPT_REQUIRED")
        if not _digest(record.get("receipt_sha256")):
            errors.append("ACTUAL_EXECUTION_RECEIPT_REQUIRED")
        if record.get("master_records_reconstruction_status") != "PASS":
            errors.append("ACTUAL_EXECUTION_RECONSTRUCTION_REQUIRED")
        if not _nonempty(record.get("master_records_receipt_ref")):
            errors.append("ACTUAL_EXECUTION_CUSTODY_REFERENCE_REQUIRED")
        if record.get("reconstructed_receipt_sha256") != record.get("receipt_sha256"):
            errors.append("ACTUAL_EXECUTION_RECONSTRUCTED_DIGEST_MISMATCH")
    return sorted(set(errors))


def validate_external_framework_finding(finding: Mapping[str, Any]) -> list[str]:
    """The external report must use the same actual transition receipt rules."""
    if not isinstance(finding, Mapping):
        return ["FINDING_OBJECT_REQUIRED"]
    errors = [
        f"FINDING_REQUIRED:{key}" for key in
        ("source_url", "source_version", "claim", "test_input_sha256")
        if not _nonempty(finding.get(key))
    ]
    if not _digest(finding.get("test_input_sha256")):
        errors.append("FINDING_TEST_INPUT_DIGEST_REQUIRED")
    receipt = finding.get("transition_disposition")
    if not isinstance(receipt, Mapping):
        errors.append("FINDING_TRANSITION_DISPOSITION_REQUIRED")
    else:
        errors.extend(validate_transition_disposition(receipt))
        if finding.get("execution_performed") is False and receipt.get("evidence_class") == "ACTUAL_EXECUTION":
            errors.append("FINDING_UNPERFORMED_TEST_CANNOT_CLAIM_EXECUTION")
        if finding.get("execution_performed") is False and receipt.get("disposition") == "ALLOW":
            errors.append("FINDING_UNPERFORMED_TEST_CANNOT_ALLOW")
    return sorted(set(errors))
