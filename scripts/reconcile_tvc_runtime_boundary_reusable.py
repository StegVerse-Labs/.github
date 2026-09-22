#!/usr/bin/env python3
"""Reusable TV/TVC runtime-boundary reconciler.

Consumes qualifying real provider-operation receipt evidence first. If that evidence
is absent, it may run the already-local TVC non-secret observer only as diagnostics.
It never creates runtime, claim/fence, credential, transition, or custody authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA = "stegverse.reusable-task-runner-result/v1"
EXPECTED_TASK = "RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001"
EXPECTED_INTR_COMPONENT = "RTC-INTERLOCK-INTR-TRANSPORT-008"
EXPECTED_SOURCE_SUBSYSTEM = "StegVerse-org/StegVerse-SDK"
EXPECTED_DESTINATION_SUBSYSTEM = "TVC:ProviderOperationBroker"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def env_json(name: str) -> Any:
    raw = os.environ.get(name, "")
    if not raw:
        raise RuntimeError(f"{name} is required")
    return json.loads(raw)


def _require_complete_intr_chain(receipt: dict[str, Any]) -> None:
    intr = receipt.get("intr_transport")
    if not isinstance(intr, dict):
        raise RuntimeError("canonical InTr provider-operation transport evidence missing")
    if intr.get("component_id") != EXPECTED_INTR_COMPONENT:
        raise RuntimeError("canonical InTr provider-operation component mismatch")
    for direction in ("request", "response"):
        lane = intr.get(direction)
        if not isinstance(lane, dict):
            raise RuntimeError(f"canonical InTr {direction} lane missing")
        result = lane.get("transport_result")
        receipts = lane.get("receipts")
        intent = lane.get("intent")
        if not isinstance(result, dict) or result.get("state") != "TRANSPORT_COMPLETE":
            raise RuntimeError(f"canonical InTr {direction} transport incomplete")
        if result.get("component_id") != EXPECTED_INTR_COMPONENT:
            raise RuntimeError(f"canonical InTr {direction} component mismatch")
        if not isinstance(receipts, list) or not receipts:
            raise RuntimeError(f"canonical InTr {direction} receipt chain missing")
        if not isinstance(intent, dict) or intent.get("protocol") != "InTr":
            raise RuntimeError(f"canonical InTr {direction} intent missing")
        expected_source = EXPECTED_SOURCE_SUBSYSTEM if direction == "request" else EXPECTED_DESTINATION_SUBSYSTEM
        expected_destination = EXPECTED_DESTINATION_SUBSYSTEM if direction == "request" else EXPECTED_SOURCE_SUBSYSTEM
        if intent.get("source") != {"boundary": "STEGOS_ECOSYSTEM", "subsystem": expected_source}:
            raise RuntimeError(f"canonical InTr {direction} source identity mismatch")
        if intent.get("destination") != {"boundary": "STEGOS_ECOSYSTEM", "subsystem": expected_destination}:
            raise RuntimeError(f"canonical InTr {direction} destination identity mismatch")
        if result.get("terminal_receipt_hash") != receipts[-1].get("receipt_hash"):
            raise RuntimeError(f"canonical InTr {direction} terminal receipt mismatch")
        if any(item.get("boundary_verification") != "VERIFIED" for item in receipts if isinstance(item, dict)):
            raise RuntimeError(f"canonical InTr {direction} boundary verification missing")
        if any(item.get("authority_transfer") is not False for item in receipts if isinstance(item, dict)):
            raise RuntimeError(f"canonical InTr {direction} authority-transfer invariant violated")


def qualified_real_receipt(receipt: dict[str, Any], *, tracking_task_id: str | None, expected_ready_state: str) -> None:
    if receipt.get("schema") != "stegverse.mir-tvc-provider-roundtrip-receipt/v1":
        raise RuntimeError("provider-operation receipt schema mismatch")
    if tracking_task_id and receipt.get("goal_task_id") != tracking_task_id:
        raise RuntimeError("provider-operation receipt task binding mismatch")
    if receipt.get("state") != "COMPLETED_PROVIDER_OPERATION_RECEIPT":
        raise RuntimeError("qualifying completed provider-operation receipt is absent")
    if receipt.get("provider_operation_completed") is not True:
        raise RuntimeError("provider operation completion not observed")
    if receipt.get("allow_operation_result_observed") is not True:
        raise RuntimeError("ALLOW_OPERATION_RESULT not observed")
    if receipt.get("use_receipt_observed") is not True:
        raise RuntimeError("exact use_receipt not observed")
    if receipt.get("ready_state") != expected_ready_state:
        raise RuntimeError("provider runtime ready-state mismatch")
    if receipt.get("secret_values_exported") is not False:
        raise RuntimeError("provider secret export invariant violated")
    if receipt.get("protected_values_exposed") is not False:
        raise RuntimeError("protected-value exposure invariant violated")
    if receipt.get("credential_material_retained") is not False:
        raise RuntimeError("credential retention invariant violated")
    claim_id = receipt.get("claim_id")
    fence = receipt.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int) or fence < 1:
        raise RuntimeError("fresh WorkerCoordinator claim/fence evidence missing")
    result = receipt.get("provider_operation_result")
    if not isinstance(result, dict) or result.get("decision") != "ALLOW_OPERATION_RESULT":
        raise RuntimeError("canonical provider-operation result mismatch")
    if not isinstance(result.get("use_receipt"), dict):
        raise RuntimeError("canonical provider-operation use_receipt missing")
    _require_complete_intr_chain(receipt)


def run_diagnostic(parameters: dict[str, Any]) -> int:
    fallback = str(parameters.get("diagnostic_fallback") or "")
    if fallback != "StegVerse-Labs/TVC:scripts/observe_tvc_runtime_boundary.py":
        return 3
    tvc_root_raw = (os.environ.get("STEGVERSE_TVC_ROOT") or "").strip()
    if not tvc_root_raw:
        print(json.dumps({"state": "BOUNDARY", "reason": "STEGVERSE_TVC_ROOT_NOT_MATERIALIZED"}, sort_keys=True))
        return 3
    observer = Path(tvc_root_raw).expanduser().resolve() / "scripts" / "observe_tvc_runtime_boundary.py"
    if not observer.is_file():
        print(json.dumps({"state": "BOUNDARY", "reason": "TVC_DIAGNOSTIC_RUNNER_NOT_MATERIALIZED"}, sort_keys=True))
        return 3
    completed = subprocess.run([sys.executable, str(observer)], cwd=observer.parents[1], text=True, capture_output=True, check=False)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode if completed.returncode != 0 else 3


def main() -> int:
    reusable_task_id = os.environ.get("STEGVERSE_REUSABLE_TASK_ID")
    invocation_id = os.environ.get("STEGVERSE_REUSABLE_TASK_INVOCATION_ID")
    manifest_path_raw = os.environ.get("STEGVERSE_REUSABLE_TASK_MANIFEST")
    result_path_raw = os.environ.get("STEGVERSE_REUSABLE_TASK_RESULT_PATH")
    tracking_task_id = os.environ.get("STEGVERSE_REUSABLE_TASK_TRACKING_TASK_ID")
    if reusable_task_id != EXPECTED_TASK or not invocation_id or not manifest_path_raw or not result_path_raw:
        raise RuntimeError("reusable invocation environment binding incomplete")

    parameters = env_json("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON")
    completion_predicates = env_json("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON")
    if not isinstance(parameters, dict) or not isinstance(completion_predicates, list):
        raise RuntimeError("reusable invocation parameters/predicates malformed")
    manifest = load_json(Path(manifest_path_raw))
    receipt_ref = str(parameters.get("provider_operation_receipt_ref") or "").strip()
    if not receipt_ref:
        print(json.dumps({"state": "BOUNDARY", "reason": "PROVIDER_OPERATION_RECEIPT_REF_NOT_BOUND"}, sort_keys=True))
        return run_diagnostic(parameters)
    receipt_path = (ROOT / receipt_ref).resolve()
    if ROOT not in receipt_path.parents:
        raise RuntimeError("provider-operation receipt reference escapes repository root")
    if not receipt_path.is_file():
        print(json.dumps({"state": "BOUNDARY", "reason": "QUALIFYING_REAL_PROVIDER_OPERATION_RECEIPT_ABSENT", "receipt_ref": receipt_ref}, sort_keys=True))
        return run_diagnostic(parameters)

    receipt = load_json(receipt_path)
    try:
        qualified_real_receipt(
            receipt,
            tracking_task_id=tracking_task_id,
            expected_ready_state=str(parameters.get("expected_ready_state") or "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND"),
        )
    except RuntimeError as exc:
        print(json.dumps({"state": "BOUNDARY", "reason": str(exc), "receipt_ref": receipt_ref}, sort_keys=True))
        return 4

    intr = receipt["intr_transport"]
    runner_result = {
        "schema": RESULT_SCHEMA,
        "invocation_id": invocation_id,
        "reusable_task_id": reusable_task_id,
        "manifest_hash": manifest.get("manifest_hash"),
        "completion_predicates_satisfied": completion_predicates,
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "primary_evidence_ref": receipt_ref,
        "primary_evidence_sha256": sha256_json(receipt),
        "ready_state": parameters.get("expected_ready_state"),
        "provider_operation_result_decision": "ALLOW_OPERATION_RESULT",
        "exact_use_receipt_observed": True,
        "intr_component_id": intr["component_id"],
        "intr_request_terminal_receipt_hash": intr["request"]["transport_result"]["terminal_receipt_hash"],
        "intr_response_terminal_receipt_hash": intr["response"]["transport_result"]["terminal_receipt_hash"],
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_effect": "NONE",
    }
    write_json(Path(result_path_raw), runner_result)
    print(json.dumps({"state": "QUALIFYING_REAL_PROVIDER_OPERATION_RECEIPT_RECONCILED", "receipt_ref": receipt_ref}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
