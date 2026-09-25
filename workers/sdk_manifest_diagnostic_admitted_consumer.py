"""Consume an already-admitted SDK diagnostic in the existing event-ephemeral StegOS.

This is a non-authorizing component of the installed generic Universal InTr
profile. A locator or TVC authorization-id string is never admission proof:
both ingress ALLOW and runtime materialization must independently reconstruct
through existing canonical Master Records before any processor is invoked.
No listener, host, scheduler, credential mechanism, ledger or device is added.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

GOAL = "MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003"
COSV = "50000000100000"
FROZEN_FILE_SHA256 = "e1b05a082ce19d3d254e3cde1dced03019174a94287724959672c9e65510c8f3"
ADMITTED_REL = Path("runtime-state/sdk-manifest-state-transition/admitted")
BINDING_TRANSITION = "SDK_ECOSYSTEM_DIAGNOSTIC_EVENT_EPHEMERAL_BOUND"
EXECUTION_TRANSITION = "SDK_ECOSYSTEM_DIAGNOSTIC_EXECUTED"
ALLOWED_INGRESS_TRANSITIONS = {"STEGCORE_INTR_MATERIALIZATION_ADMITTED", "SDK_MANIFEST_INTR_ADMITTED"}


class DiagnosticAdmissionError(ValueError):
    def __init__(self, predicate: str):
        super().__init__(predicate)
        self.predicate = predicate

class DiagnosticExecutionFailClosed(RuntimeError):
    """The admitted execution has begun; this attempt is terminal."""

    def __init__(self, predicate: str):
        super().__init__(predicate)
        self.predicate = predicate


def require(ok: bool, predicate: str) -> None:
    if not ok:
        raise DiagnosticAdmissionError(predicate)


def sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    require(path.is_file(), "AUTHENTIC_EVENT_EPHEMERAL_BINDING_LOCATOR_REQUIRED")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "EVENT_EPHEMERAL_BINDING_LOCATOR_INVALID")
    return value


def _reconstruct(reconstruct, digest: str) -> dict[str, Any]:
    require(isinstance(digest, str) and len(digest) == 64 and all(x in "0123456789abcdef" for x in digest),
            "CANONICAL_PREDECESSOR_RECEIPT_DIGEST_REQUIRED")
    response = reconstruct(digest)
    require(response.get("state") == "PASS"
            and response.get("required_evidence_validation_status") == "PASS"
            and response.get("receipt_sha256") == digest
            and response.get("reconstructed_receipt_sha256") == digest,
            "MASTER_RECORDS_EXACT_RECEIPT_RECONSTRUCTION_REQUIRED")
    receipt = response.get("receipt")
    require(isinstance(receipt, Mapping), "MASTER_RECORDS_ORIGINAL_RECEIPT_REQUIRED")
    return dict(receipt)


def _prove_ancestry(reconstruct, leaf: str, ancestor: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Every immediate predecessor must reconstruct, ending at exact ingress ALLOW."""
    seen: set[str] = set()
    current = leaf
    binding = None
    for _ in range(32):
        require(current not in seen, "CANONICAL_PREDECESSOR_CYCLE")
        seen.add(current)
        receipt = _reconstruct(reconstruct, current)
        if binding is None:
            binding = receipt
        if current == ancestor:
            return binding, receipt
        prior = receipt.get("prior_state_ref_or_hash")
        require(isinstance(prior, str) and prior.startswith("sha256:"),
                "CANONICAL_IMMEDIATE_PREDECESSOR_REQUIRED")
        current = prior[7:]
    raise DiagnosticAdmissionError("CANONICAL_PREDECESSOR_DEPTH_EXCEEDED")


def _installed_sdk_root(control_root: Path) -> Path:
    try:
        roots = json.loads(os.environ.get("STEGVERSE_REPO_ROOTS_JSON", "{}"))
    except (ValueError, TypeError):
        roots = {}
    raw = (roots.get("StegVerse-org/StegVerse-SDK") if isinstance(roots, dict) else None) or os.environ.get("STEGVERSE_SDK_ROOT", "")
    require(bool(raw), "INSTALLED_SDK_SOURCE_BINDING_REQUIRED")
    root = Path(str(raw)).expanduser().resolve()
    require((root / "stegverse/ecosystem_diagnostic_cli.py").is_file()
            and (root / "stegverse/manifest_contract.py").is_file(),
            "INSTALLED_SDK_DIAGNOSTIC_PROCESSOR_REQUIRED")
    return root


def consume(
    control_root: Path,
    resident_root: Path,
    request: Mapping[str, Any],
    *,
    reconstruct=None,
    runner=None,
    submit=None,
) -> dict[str, Any]:
    """Execute only inside the existing, authentically bound ephemeral lease.

    Injected callbacks in unit tests are SOURCE TEST DOUBLES, never runtime proof.
    Production reconstruct/submit use existing organization-first Master Records.
    """
    from workers.canonical_state_transition_custody import (
        build_state_receipt, reconstruct_state_receipt, require_predecessor_master_records_closure,
        submit_state_receipt, sha256_uri,
    )
    source_test_doubles = any(x is not None for x in (reconstruct, runner, submit))
    reconstruct = reconstruct or reconstruct_state_receipt
    submit = submit or submit_state_receipt
    runner = runner or subprocess.run
    require(request.get("processing_capability") == "ecosystem_diagnostic"
            and request.get("canonical_task_id") is None
            and request.get("requires_workercoordinator_claim_fence") is False,
            "DIAGNOSTIC_NONWORKER_GRAPH_REQUIRED")
    manifest = request.get("canonical_manifest")
    require(isinstance(manifest, Mapping), "FROZEN_ORIGINAL_MANIFEST_REQUIRED")
    require(sha256(manifest) == request.get("wire_manifest_sha256"), "ORIGINAL_WIRE_DIGEST_MISMATCH")
    payload = manifest.get("payload") or {}
    require(isinstance(payload, Mapping), "SOURCE_PAYLOAD_REQUIRED")
    require(payload.get("goal_task_id") == GOAL and payload.get("cosv") == COSV,
            "EXPERIMENT_3_GOAL_COSV_MISMATCH")
    require(((manifest.get("completion") or {}).get("publisher") or {}).get("required") is True,
            "ORIGINAL_PUBLISHER_REQUIRED_PREDICATE")
    request_hash = request.get("request_sha256")
    require(isinstance(request_hash, str) and len(request_hash) == 64,
            "IMMUTABLE_REQUEST_HASH_REQUIRED")
    resident = resident_root.expanduser().resolve()
    locator = _read(resident / ADMITTED_REL / f"{request_hash}.json")
    require(locator.get("schema") == "stegverse.sdk.admitted-ephemeral-receipt-locator/v1"
            and locator.get("request_sha256") == request_hash
            and locator.get("wire_manifest_sha256") == request["wire_manifest_sha256"],
            "ADMITTED_RUNTIME_LOCATOR_BINDING_MISMATCH")
    binding_digest = locator.get("runtime_binding_receipt_sha256")
    ingress_digest = locator.get("intr_admission_receipt_sha256")
    require(isinstance(binding_digest, str) and isinstance(ingress_digest, str),
            "AUTHENTIC_INTR_AND_RUNTIME_MASTER_RECORDS_RECEIPTS_REQUIRED")
    binding_receipt, admission_receipt = _prove_ancestry(reconstruct, binding_digest, ingress_digest)
    require(admission_receipt.get("transition_id") in ALLOWED_INGRESS_TRANSITIONS
            and admission_receipt.get("transition_outcome") == "ALLOW",
            "CANONICAL_INTR_ADMISSION_ALLOW_REQUIRED")
    ingress_evidence = admission_receipt.get("transition_evidence") or {}
    require(ingress_evidence.get("request_sha256") == request_hash
            and ingress_evidence.get("wire_manifest_sha256") == request["wire_manifest_sha256"],
            "INTR_ADMISSION_EXACT_MANIFEST_PACKET_BINDING_REQUIRED")
    require(binding_receipt.get("transition_id") == BINDING_TRANSITION
            and binding_receipt.get("transition_outcome") in {"OBSERVED", "COMPLETED"},
            "CANONICAL_EVENT_EPHEMERAL_RUNTIME_BINDING_REQUIRED")
    evidence = binding_receipt.get("transition_evidence") or {}
    binding = evidence.get("runtime_binding") or {}
    require(isinstance(binding, Mapping)
            and binding.get("runtime_class") == "EVENT_EPHEMERAL"
            and binding.get("lease_state") == "LEASE_OPEN"
            and binding.get("goal_task_id") == GOAL and binding.get("cosv") == COSV
            and binding.get("request_sha256") == request_hash
            and binding.get("wire_manifest_sha256") == request["wire_manifest_sha256"]
            and all(isinstance(binding.get(k), str) and binding[k]
                    for k in ("node_id", "interlock_id", "lease_id", "runtime_id")),
            "ADMITTED_NODE_INTERLOCK_LEASE_RUNTIME_CORRELATION_REQUIRED")
    ephemeral_root = Path(str(binding.get("runtime_root") or "")).expanduser().resolve()
    require(ephemeral_root.is_dir() and ephemeral_root != resident
            and ephemeral_root.is_relative_to(resident),
            "ADMITTED_EVENT_EPHEMERAL_RUNTIME_ROOT_REQUIRED")
    # Fixed installed processor only: never load a callable or command from a
    # manifest payload, review document, untrusted binding or provider response.
    sdk_root = _installed_sdk_root(control_root)
    outdir = ephemeral_root / "receipts/sdk-manifest-state-transition" / request_hash
    outdir.mkdir(parents=True, exist_ok=True)
    original_path = outdir / "original.manifest.json"
    result_path = outdir / "diagnostic.result.json"
    original_bytes = (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if original_path.exists():
        require(original_path.read_bytes() == original_bytes, "FROZEN_ORIGINAL_MANIFEST_COLLISION")
    else:
        original_path.write_bytes(original_bytes)
    # Immutable original artifact file SHA-256; canonical JSON root is distinct.
    require(hashlib.sha256(original_bytes).hexdigest() == FROZEN_FILE_SHA256,
            "FROZEN_EXPERIMENT_3_FILE_HASH_MISMATCH")
    require(not result_path.exists(), "DIAGNOSTIC_RESULT_ALREADY_EXISTS_REQUIRE_READBACK")
    child_env = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL") if key in os.environ}
    child_env["PYTHONPATH"] = str(sdk_root)
    child_env["STEGVERSE_EVENT_EPHEMERAL_RUNTIME_ROOT"] = str(ephemeral_root)
    child_env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    try:
        proc = runner([sys.executable, "-m", "stegverse.ecosystem_diagnostic_cli",
                       "--manifest", str(original_path), "--output", str(result_path)],
                      cwd=ephemeral_root, env=child_env, capture_output=True, text=True,
                      check=False, timeout=120)
    except Exception as exc:
        raise DiagnosticExecutionFailClosed(
            "ADMITTED_SDK_DIAGNOSTIC_PROCESS_INVOCATION_FAILED:" + type(exc).__name__) from exc
    if proc.returncode != 0 or not result_path.is_file():
        raise DiagnosticExecutionFailClosed("ADMITTED_SDK_DIAGNOSTIC_PROCESS_EXECUTION_FAILED")
    try:
        diagnostic = _read(result_path)
    except Exception as exc:
        raise DiagnosticExecutionFailClosed("ADMITTED_SDK_DIAGNOSTIC_RESULT_INVALID") from exc
    if not (diagnostic.get("schema") == "stegverse.ecosystem-diagnostic-result.v1"
            and diagnostic.get("processing_capability") == "ecosystem_diagnostic"
            and diagnostic.get("route_id") == request.get("route_id")
            and diagnostic.get("authority_effect") == "NONE_DIAGNOSTIC_ONLY"
            and diagnostic.get("mutation_performed") is False
            and diagnostic.get("diagnostic_request_id") == (request.get("state_graph", {}).get("request") or {}).get("diagnostic_request_id")):
        raise DiagnosticExecutionFailClosed("EXACT_INSTALLED_DIAGNOSTIC_OUTPUT_INVALID")
    result_bytes = result_path.read_bytes()
    result_sha = hashlib.sha256(result_bytes).hexdigest()
    if submit is submit_state_receipt:
        prior, predecessor_evidence = require_predecessor_master_records_closure(
            binding_digest, successor_transition_id=EXECUTION_TRANSITION)
    else:
        prior = "sha256:" + binding_digest
        predecessor_evidence = []  # Test doubles do not prove authentic custody.
    diagnostic_evidence = {
        "request_sha256": request_hash,
        "wire_manifest_sha256": request["wire_manifest_sha256"],
        "diagnostic_result_sha256": result_sha,
        "runtime_id": binding["runtime_id"],
        "lease_id": binding["lease_id"],
        "node_id": binding["node_id"],
        "interlock_id": binding["interlock_id"],
        "original_file_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "result_ref": str(result_path),
        "publisher_required": True,
        "publisher_executed": False,
        "far_side_transition_observed": False,
    }
    transition = build_state_receipt(
        transition_id=EXECUTION_TRANSITION,
        transition_sequence=int(binding_receipt.get("transition_sequence", 0)) + 1,
        subject_or_correlation_id=GOAL,
        transition_outcome="EXECUTED",
        prior_state_ref_or_hash=prior,
        resulting_state_ref_or_hash="sha256:" + result_sha,
        governance_decision_ref_where_applicable="sha256:" + ingress_digest,
        transition_evidence=diagnostic_evidence,
        required_evidence_manifest=predecessor_evidence,
        proof_scope="ADMITTED_DIAGNOSTIC_PROCESSING_ONLY_NOT_PUBLISHER_OR_FAR_SIDE",
        proof_ceiling="AUTHENTIC_PROCESSING_ONLY_IF_EXISTING_MASTER_RECORDS_CLOSURE_PASS",
    )
    try:
        closure = submit(transition)
    except Exception as exc:
        raise DiagnosticExecutionFailClosed(
            "ORGANIZATION_AND_MASTER_RECORDS_CUSTODY_SUBMISSION_FAILED:" + type(exc).__name__) from exc
    if not (closure.get("state") == "RECORDED"
            and closure.get("reconstruction_status") == "PASS"
            and closure.get("required_evidence_validation_status") == "PASS"
            and closure.get("receipt_sha256") == closure.get("reconstructed_receipt_sha256")
            and closure.get("organization_previous_receipt_sha256") is not None):
        raise DiagnosticExecutionFailClosed("ORGANIZATION_AND_MASTER_RECORDS_EXACT_CLOSURE_REQUIRED")
    if source_test_doubles:
        return {
            "schema": "stegverse.sdk.manifest-state-transition-source-simulation/v1",
            "state": "SOURCE_SIMULATION_ONLY",
            "disposition": "SIMULATED",
            "authentic_intr_disposition_observed": False,
            "organization_master_records_closure_observed": False,
            "request_sha256": request_hash,
            "wire_manifest_sha256": request["wire_manifest_sha256"],
            "diagnostic_result_sha256": result_sha,
            "authority_effect": "NONE_SOURCE_TEST_ONLY",
        }
    return {
        "schema": "stegverse.sdk.manifest-state-transition-progress/v1",
        "state": "PROCESSING_RECORDED_PUBLISHER_REQUIRED",
        "disposition": "ALLOW",
        "terminal": False,
        "communication_terminal": False,
        "request_sha256": request_hash,
        "wire_manifest_sha256": request["wire_manifest_sha256"],
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "goal_task_id": GOAL,
        "cosv": COSV,
        "processing_capability": "ecosystem_diagnostic",
        "graph_id": request["graph_id"],
        "diagnostic_result_ref": str(result_path),
        "diagnostic_result": diagnostic,
        "diagnostic_result_sha256": result_sha,
        "diagnostic_result_file_encoding": "utf8-json-indent2-sortkeys-newline",
        "source_manifest_file_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "runtime_id": binding["runtime_id"],
        "lease_id": binding["lease_id"],
        "node_id": binding["node_id"],
        "interlock_id": binding["interlock_id"],
        "intr_admission_master_records_receipt_sha256": ingress_digest,
        "runtime_binding_master_records_receipt_sha256": binding_digest,
        "diagnostic_master_records_receipt_sha256": closure["receipt_sha256"],
        "organization_receipt_sha256": closure.get("organization_receipt_sha256"),
        "organization_previous_receipt_sha256": closure["organization_previous_receipt_sha256"],
        "publisher_required": True,
        "publisher_executed": False,
        "far_side_transition_observed": False,
        "external_master_records_independently_read_back": False,
        "next_transition_id": "RTC-PUBLISHER-005",
        "publisher_package_profile": "stegverse.publisher.evidence-report-package/v1",
        "authority_effect": "NONE_PROCESSING_RESULT_ONLY",
    }
