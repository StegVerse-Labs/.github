#!/usr/bin/env python3
"""Classify StegBrowser runtime-consumption resident receipt reachability.

This verifier is intentionally non-authorizing. It does not run a scheduler,
consume a request, mint WorkerCoordinator claim/fence state, invoke TV/TVC, or
promote source/CI state into runtime proof. It only inspects an existing resident
custody surface for the exact receipt paths required by
STEG-BROWSER-RUNTIME-CONSUMPTION-001 and returns a deterministic classification
that downstream handoff/task-record updates may use after authentic receipts
exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
TVC_TARGET_SHA = "aef6b6f5dc99d2a531718ca475d20858ae8e68a6"
TVC_ALLOWED_OUTCOMES = {"STAGED", "ALREADY_STAGED", "RESTAGED_EXACT_SOURCE"}

RELATIVE_RECEIPTS = {
    "canonical_work_consumption": Path("receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json"),
    "evidence_custody": Path("receipts/sovereign-host/stegbrowser-runtime-consumption-evidence-custody.latest.json"),
    "tvc_source_promotion": Path("receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json"),
    "skap_owner_ingress_relative": Path("var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json"),
}
ABSOLUTE_OWNER_INGRESS = Path("/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def classify_json_receipt(path: Path, validator) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "present": False, "valid": False, "reason": "MISSING"}
    value = load_json(path)
    if value is None:
        return {"path": str(path), "present": True, "valid": False, "sha256": sha256(path), "reason": "INVALID_JSON_OBJECT"}
    reason = validator(value)
    return {
        "path": str(path),
        "present": True,
        "valid": reason == "OK",
        "sha256": sha256(path),
        "reason": reason,
    }


def validate_consumption(value: dict[str, Any]) -> str:
    if value.get("schema") != "stegverse.canonical-work-bootstrap-request-consumption/v1":
        return "SCHEMA_MISMATCH"
    if value.get("state") != "COMPLETED":
        return "STATE_NOT_COMPLETED"
    if value.get("task_id") != TASK_ID:
        return "TASK_ID_MISMATCH"
    if value.get("credential_material_present") is not False:
        return "CREDENTIAL_BOUNDARY_MISMATCH"
    if value.get("github_token_runtime_authority") != "NONE":
        return "GITHUB_AUTHORITY_MISMATCH"
    if value.get("second_machine_required") is not False:
        return "SECOND_MACHINE_BOUNDARY_MISMATCH"
    return "OK"


def validate_custody(value: dict[str, Any]) -> str:
    if value.get("schema") != "stegverse.stegbrowser-runtime-consumption-evidence-custody/v1":
        return "SCHEMA_MISMATCH"
    if value.get("state") != "EXACT_EPHEMERAL_EVIDENCE_RETAINED_IN_EXISTING_RESIDENT_RUNTIME":
        return "STATE_MISMATCH"
    if value.get("task_id") != TASK_ID or value.get("cosv_task_vector") != COSV:
        return "TASK_OR_COSV_MISMATCH"
    evidence = value.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return "EVIDENCE_ROWS_MISSING"
    if any(not isinstance(row, dict) or row.get("exact_bytes_retained") is not True or not row.get("sha256") for row in evidence):
        return "EVIDENCE_ROW_INVALID"
    if value.get("credential_material_present") is not False:
        return "CREDENTIAL_BOUNDARY_MISMATCH"
    if value.get("github_token_runtime_authority") != "NONE":
        return "GITHUB_AUTHORITY_MISMATCH"
    return "OK"


def validate_tvc(value: dict[str, Any]) -> str:
    if value.get("state") != "ATTEMPT_RECORDED":
        return "STATE_MISMATCH"
    if value.get("outcome") not in TVC_ALLOWED_OUTCOMES:
        return "OUTCOME_NOT_ACCEPTED"
    if value.get("exact_sha") != TVC_TARGET_SHA:
        return "TVC_SHA_MISMATCH"
    if value.get("credential_material_present") is not False:
        return "CREDENTIAL_BOUNDARY_MISMATCH"
    if value.get("network_source_fetch_performed") is not False:
        return "NETWORK_SOURCE_FETCH_BOUNDARY_MISMATCH"
    return "OK"


def validate_owner_ingress(value: dict[str, Any]) -> str:
    if value.get("state") != "OWNER_INGRESS_READY_OBSERVED":
        return "STATE_MISMATCH"
    if value.get("simultaneous_listener_observation") is not True:
        return "SIMULTANEOUS_LISTENER_NOT_OBSERVED"
    return "OK"


def inspect(runtime_root: Path) -> dict[str, Any]:
    root = runtime_root.expanduser().resolve()
    checks = {
        "canonical_work_consumption": classify_json_receipt(root / RELATIVE_RECEIPTS["canonical_work_consumption"], validate_consumption),
        "evidence_custody": classify_json_receipt(root / RELATIVE_RECEIPTS["evidence_custody"], validate_custody),
        "tvc_source_promotion": classify_json_receipt(root / RELATIVE_RECEIPTS["tvc_source_promotion"], validate_tvc),
    }
    owner_candidates = [root / RELATIVE_RECEIPTS["skap_owner_ingress_relative"], ABSOLUTE_OWNER_INGRESS]
    owner_rows = [classify_json_receipt(candidate, validate_owner_ingress) for candidate in owner_candidates]
    owner_valid = next((row for row in owner_rows if row.get("valid") is True), None)
    checks["owner_ingress"] = owner_valid or owner_rows[0]
    missing = [name for name, row in checks.items() if row.get("present") is not True]
    invalid = [name for name, row in checks.items() if row.get("present") is True and row.get("valid") is not True]
    all_valid = not missing and not invalid
    return {
        "schema": "stegverse.stegbrowser-runtime-consumption-receipt-reachability/v1",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "state": "RUNTIME_RECEIPTS_VALID_AND_BINDABLE" if all_valid else "RUNTIME_RECEIPTS_NOT_BINDABLE",
        "runtime_root": str(root),
        "checks": checks,
        "owner_ingress_candidates": owner_rows,
        "missing_receipts": missing,
        "invalid_receipts": invalid,
        "completion_evidence_observed": all_valid,
        "claim_or_fence_minted": False,
        "scheduler_invoked": False,
        "runtime_request_consumed": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_RECEIPT_REACHABILITY_INSPECTION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.runtime_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["state"] == "RUNTIME_RECEIPTS_VALID_AND_BINDABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
