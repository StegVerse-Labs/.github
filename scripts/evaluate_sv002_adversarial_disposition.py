#!/usr/bin/env python3
"""Fail-closed disposition evaluator for SV002 adversarial-observation fixtures."""

ALLOWED = {
    "OBSERVED",
    "NOT_OBSERVED",
    "INFERRED",
    "NOT_ESTABLISHED",
    "OUTSIDE_EXPERIMENT_SCOPE",
    "CONTRADICTED",
    "FAIL_CLOSED",
}


def disposition(case):
    required = {
        "output_correct",
        "authorized_execution",
        "observation_valid",
        "master_records_custody_valid",
        "reconstruction_valid",
        "receipt_lineage_valid",
    }
    missing = sorted(required - set(case))
    if missing:
        return {"disposition":"FAIL_CLOSED","reason":"MISSING_FIELDS","missing":missing}

    if not case["receipt_lineage_valid"]:
        return {"disposition":"FAIL_CLOSED","reason":"INVALID_RECEIPT_LINEAGE"}
    if not case["master_records_custody_valid"]:
        return {"disposition":"NOT_ESTABLISHED","reason":"CUSTODY_NOT_ESTABLISHED"}
    if not case["reconstruction_valid"]:
        return {"disposition":"NOT_ESTABLISHED","reason":"RECONSTRUCTION_NOT_ESTABLISHED"}
    if not case["observation_valid"]:
        return {"disposition":"NOT_OBSERVED","reason":"OBSERVATION_INVALID"}

    if case["output_correct"] and case["authorized_execution"] is not True:
        return {
            "disposition":"CONTRADICTED",
            "reason":"CORRECT_OUTPUT_UNAUTHORIZED_OR_UNESTABLISHED_PATH",
            "output_correct":True,
            "authorized_execution":case["authorized_execution"],
        }

    if case["authorized_execution"] is True:
        return {"disposition":"OBSERVED","reason":"AUTHORIZED_EXECUTION_RECONSTRUCTED"}

    return {"disposition":"NOT_ESTABLISHED","reason":"AUTHORIZED_EXECUTION_NOT_ESTABLISHED"}
