"""Source-level validator for the proposed ecosystem transition-disposition receipt.

This validates supplied records only. It never mints an InTr or Master Records
receipt, confers admission, or treats a simulated fixture as observed execution.

An actual transition is real when its Organization receipt exists: the
manifest-directed append to the Organization ledger under its lock
(data/task-registry-global-invariants.json runtime_reality_authority).
Master Records reconstruction fields are optional downstream evidence
(master_records_may_gate_organization_runtime_reality=false); they are
reported by master_records_evidence() and never produce a validation error.
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
)
NON_ALLOW_REQUIRED = (
    "failure_code", "failed_predicate", "required_evidence_or_repair",
    "retry_entrypoint", "owning_existing_goal", "next_attempt",
    "evidence_refs",
)
# Non-ALLOW fields that carry a list of references rather than one string.
NON_ALLOW_LIST_FIELDS = frozenset({"evidence_refs"})
HEX = set("0123456789abcdef")
# An effect-transition record states whether its consequence was observed.
# The governance decision is a separate manifest transition, observed at its
# own append, so decision records leave this field out.
CONSEQUENCE_OBSERVATIONS = {"OBSERVED", "NOT_AUTHENTICALLY_OBSERVED"}
# Shape of the organization_receipt object submit_state_receipt() returns.
ORGANIZATION_RECEIPT_SCHEMA = "stegverse.organization-transition-receipt/v1"


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_refs(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty(x) for x in value)


def non_allow_missing(record: Mapping[str, Any]) -> list[str]:
    """Return the NON_ALLOW_REQUIRED fields a non-ALLOW record fails to carry.

    `evidence_refs` must be a non-empty list of non-empty strings: a refusal
    names the evidence it rests on. A record whose only evidence is itself says
    so as `SOURCE_RECORD_ONLY:<path>` rather than leaving the list empty.
    """
    return [
        key for key in NON_ALLOW_REQUIRED
        if not (_nonempty_refs if key in NON_ALLOW_LIST_FIELDS else _nonempty)(record.get(key))
    ]


def _digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def _sha256_uri(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and _digest(value[7:])


def organization_receipt_errors(record: Mapping[str, Any]) -> list[str]:
    """Errors in the Organization receipt reference an actual transition must carry.

    The reference is the existing `organization_receipt` object returned by
    submit_state_receipt(): it must name this record's receipt as its source
    transition. A top-level `organization_receipt_sha256` projection, where
    present, must agree with it. This checks shape and binding only; reading the
    receipt back from the ledger is organization_batch_custody.verified_organization_record().
    """
    receipt = record.get("organization_receipt")
    if receipt is None:
        return ["ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_REQUIRED"]
    if (not isinstance(receipt, Mapping)
            or receipt.get("schema") != ORGANIZATION_RECEIPT_SCHEMA
            or not _sha256_uri(receipt.get("receipt_sha256"))):
        return ["ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_INVALID"]
    errors = []
    if receipt.get("source_transition_sha256") != "sha256:" + str(record.get("receipt_sha256")):
        errors.append("ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_NOT_BOUND")
    projected = record.get("organization_receipt_sha256")
    if projected is not None and projected != receipt.get("receipt_sha256"):
        errors.append("ACTUAL_EXECUTION_ORGANIZATION_RECEIPT_CONFLICT")
    return errors


def master_records_evidence(record: Mapping[str, Any]) -> dict[str, Any]:
    """Master Records reconstruction as recorded evidence, never a gate.

    A missing, failed or mismatched reconstruction is a value here; it does not
    make the record invalid and does not authorize anything.
    """
    receipt = record.get("receipt_sha256")
    reconstructed = record.get("reconstructed_receipt_sha256")
    return {
        "master_records_reconstruction_status": record.get("master_records_reconstruction_status"),
        "master_records_receipt_ref": record.get("master_records_receipt_ref"),
        "reconstructed_receipt_sha256_matches": (
            None if reconstructed is None else reconstructed == receipt),
        "transition_gate": False,
    }


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
    observation = record.get("consequence_observation")
    unobserved = observation == "NOT_AUTHENTICALLY_OBSERVED"
    if observation is not None and observation not in CONSEQUENCE_OBSERVATIONS:
        errors.append("INVALID_CONSEQUENCE_OBSERVATION")
    committed = record.get("consequence_committed")
    if unobserved:
        # The effect was invoked and its outcome is not known: no boolean is asserted,
        # and the next edge is a separately manifested reconciliation read.
        if "consequence_committed" in record:
            errors.append("UNOBSERVED_EFFECT_MUST_NOT_ASSERT_COMMITTED")
        if not _nonempty(record.get("reconciliation_entrypoint")):
            errors.append("UNOBSERVED_EFFECT_RECONCILIATION_ENTRYPOINT_REQUIRED")
        # An invoked effect is never relabelled as a refusal.
        if disposition in NON_ALLOW:
            errors.append("INVOKED_EFFECT_NOT_RELABELLED_NON_ALLOW")
    elif not isinstance(committed, bool):
        errors.append("CONSEQUENCE_COMMITTED_BOOLEAN_REQUIRED")
    if disposition in NON_ALLOW:
        if committed is not False and not unobserved:
            errors.append("NON_ALLOW_MUST_NOT_COMMIT")
        for key in non_allow_missing(record):
            errors.append(f"NON_ALLOW_REPAIR_REQUIRED:{key}")
    if disposition == "ALLOW":
        if committed is not True and not unobserved:
            errors.append("ALLOW_COMMIT_EVIDENCE_REQUIRED")
        if record.get("evidence_class") != "ACTUAL_EXECUTION":
            errors.append("ALLOW_REQUIRES_ACTUAL_EXECUTION")
        if not _digest(record.get("receipt_sha256")):
            errors.append("ALLOW_RECEIPT_SHA256_REQUIRED")
    if record.get("evidence_class") == "ACTUAL_EXECUTION":
        if not _digest(record.get("immediate_predecessor_receipt_sha256")):
            errors.append("ACTUAL_EXECUTION_PREDECESSOR_RECEIPT_REQUIRED")
        if not _digest(record.get("receipt_sha256")):
            errors.append("ACTUAL_EXECUTION_RECEIPT_REQUIRED")
        errors.extend(organization_receipt_errors(record))
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
