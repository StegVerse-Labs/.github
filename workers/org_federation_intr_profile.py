#!/usr/bin/env python3
"""Existing Universal InTr listener's organization-federation profile.

Transport admission and observed custody only: no local decision, worker or
gateway authority. A claimed ALLOW is never enough: reconstruct the exact
pre-existing external InTr decision from canonical Master Records.
"""
from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("stegverse_federation_existing_kernel", ROOT / "org-kernel/kernel.py")
K = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(K)
REQUEST_SCHEMA = "stegverse.org-federation-intr-admission-request/v1"
RECEIPT_SCHEMA = "stegverse.org-federation-intr-admission-receipt/v1"
REL = Path("receipts/sovereign-network/org-federation-intr-ingress")
AUTH_ENV = "STEGVERSE_TVC_RELAY_AUTHORIZATION_ID"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _write_once(path: Path, obj: dict[str, Any]) -> None:
    raw = json.dumps(obj, sort_keys=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_text() == raw, "federation_ingress_write_once_collision")
    else:
        path.write_text(raw)
    require(path.read_text() == raw, "federation_ingress_readback_failed")


def validate(*, body: bytes, headers: Mapping[str, str], transport_validator=None,
             decision_reconstructor=None) -> dict[str, Any]:
    # The existing relay ID is a resident-bound authorization *reference*,
    # not independent proof of TVC authorization or of an InTr decision.
    from scripts import serve_hil_intr_materialization_ingress as hil
    validator = hil.validate_transport_headers if transport_validator is None else transport_validator
    transport = validator(headers, body)
    require(transport.get("origin") == hil.ORIGIN_RELAY, "federation_tvc_relay_required")
    expected = os.environ.get(AUTH_ENV, "")
    observed = str(transport.get("authorization_id") or "")
    require(bool(expected) and hmac.compare_digest(expected, observed), "federation_tvc_relay_binding_unavailable_or_mismatch")
    request = json.loads(body.decode("utf-8"))
    require(isinstance(request, dict) and request.get("schema") == REQUEST_SCHEMA, "federation_request_schema_invalid")
    frame = request.get("frame")
    require(isinstance(frame, dict), "federation_frame_required")
    packet = K.recover_packet(frame)
    require(packet.get("intr_profile") == K.PACKET_SCHEMA, "federation_intr_profile_mismatch")
    require(frame.get("origin_org") == packet["origin"]["org"], "federation_origin_mismatch")
    require(packet["origin"]["org"] != packet["destination"]["org"], "federation_cross_organization_required")
    require(packet["destination"]["org"] == "StegVerse-Labs", "federation_local_organization_mismatch")
    require(isinstance(packet["origin"].get("service"), str) and bool(packet["origin"]["service"]), "federation_origin_service_missing")
    require(isinstance(packet["destination"].get("service"), str) and bool(packet["destination"]["service"]), "federation_destination_service_missing")
    transition = packet.get("transition") or {}
    require(isinstance(transition.get("reference"), str) and bool(transition["reference"]), "federation_transition_reference_missing")
    require(transition.get("authority_effect") == "NONE", "federation_carrier_must_not_claim_authority")
    require(request.get("packet_sha256") == frame["packet_sha256"], "federation_packet_binding_mismatch")
    require(request.get("frame_sha256") == frame["frame_sha256"], "federation_frame_binding_mismatch")
    require(request.get("payload_sha256") == K.sha(packet["payload"]), "federation_payload_binding_mismatch")
    source_org_receipt = request.get("source_organization_receipt_sha256")
    require(isinstance(source_org_receipt, str) and source_org_receipt.startswith("sha256:")
            and len(source_org_receipt) == 71
            and all(x in "0123456789abcdef" for x in source_org_receipt[7:]),
            "federation_source_org_receipt_required")
    decision_hash = request.get("intr_decision_receipt_sha256")
    require(isinstance(decision_hash, str) and len(decision_hash) == 64
            and all(x in "0123456789abcdef" for x in decision_hash), "federation_external_decision_receipt_required")
    if decision_reconstructor is None:
        from workers.canonical_state_transition_custody import reconstruct_state_receipt
        decision_reconstructor = reconstruct_state_receipt
    reconstructed = decision_reconstructor(decision_hash)
    require(reconstructed.get("state") == "PASS"
            and reconstructed.get("required_evidence_validation_status") == "PASS"
            and reconstructed.get("receipt_sha256") == decision_hash
            and reconstructed.get("reconstructed_receipt_sha256") == decision_hash
            and reconstructed.get("master_records_grants_transition_authority") is False,
            "federation_external_decision_reconstruction_failed")
    decision = reconstructed.get("receipt")
    require(isinstance(decision, dict)
            and decision.get("schema") == "stegverse.canonical-state-transition-receipt/v1"
            and decision.get("transition_outcome") == "ALLOW"
            and bool(decision.get("governance_decision_ref_where_applicable")),
            "federation_external_intr_allow_missing")
    evidence = decision.get("transition_evidence")
    require(isinstance(evidence, dict)
            and evidence.get("authority") in ("Interlock/InTr", "INTERLOCK_INTR")
            and evidence.get("disposition") == "ALLOW"
            and evidence.get("locally_generated_allow") is False
            and evidence.get("packet_sha256") == frame["packet_sha256"]
            and evidence.get("frame_sha256") == frame["frame_sha256"]
            and evidence.get("payload_sha256") == request["payload_sha256"]
            and evidence.get("source_organization_receipt_sha256") == source_org_receipt
            and evidence.get("origin_service") == packet["origin"]["service"]
            and evidence.get("destination_service") == packet["destination"]["service"]
            and evidence.get("origin_organization") == packet["origin"]["org"]
            and evidence.get("destination_organization") == packet["destination"]["org"]
            and evidence.get("transition_id") == transition["reference"],
            "federation_external_intr_decision_binding_mismatch")
    return {"request": request, "packet": packet, "decision_sha256": decision_hash,
            "transport_authorization_id": observed}


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str],
          transport_validator=None, decision_reconstructor=None,
          custody_submit=None) -> dict[str, Any]:
    validated = validate(body=body, headers=headers,
                         transport_validator=transport_validator,
                         decision_reconstructor=decision_reconstructor)
    packet = validated["packet"]
    request = validated["request"]
    frame_sha = request["frame_sha256"]
    path = runtime_root / REL / (frame_sha.split(":", 1)[1] + ".json")
    # A replay is observationally idempotent, not a fresh governed transition.
    if path.exists():
        existing = json.loads(path.read_text())
        require(existing.get("frame_sha256") == frame_sha
                and existing.get("intr_decision_receipt_sha256") == validated["decision_sha256"]
                and existing.get("packet_sha256") == request["packet_sha256"]
                and existing.get("source_organization_receipt_sha256") == request["source_organization_receipt_sha256"], "federation_ingress_replay_collision")
        return existing
    # Require an explicit exact organization HEAD. Canonical custody rechecks it
    # within the existing ledger writer lock, preventing a stale append.
    org_spec = importlib.util.spec_from_file_location(
        "stegverse_federation_existing_org_ledger", ROOT / "resident-runtime/aggregate_repo_transition.py")
    org_ledger = importlib.util.module_from_spec(org_spec)
    org_spec.loader.exec_module(org_ledger)
    ledger = org_ledger.ledger_root()
    head_path = ledger / "HEAD.json"
    head = json.loads(head_path.read_text()) if head_path.is_file() else None
    actual_previous = head.get("receipt_sha256") if isinstance(head, dict) else None
    requested_previous = request.get("predecessor_organization_receipt_sha256")
    require(requested_previous == (actual_previous or "GENESIS"),
            "federation_org_immediate_predecessor_mismatch")
    if actual_previous:
        prior_path = ledger / "receipts" / (actual_previous.split(":", 1)[1] + ".json")
        require(prior_path.is_file(), "federation_org_immediate_predecessor_missing")
        prior_org = json.loads(prior_path.read_text())
        body_prior = dict(prior_org)
        require(body_prior.pop("receipt_sha256", None) == actual_previous
                and org_ledger.sha(body_prior) == actual_previous,
                "federation_org_immediate_predecessor_invalid")
    transition_id = "ORG_FEDERATION_INTR_INGRESS:" + frame_sha.split(":", 1)[1]
    previous = request.get("predecessor_canonical_receipt_sha256")
    require(previous is not None, "federation_explicit_predecessor_required")
    from workers.canonical_state_transition_custody import (
        build_state_receipt, require_predecessor_master_records_closure,
        submit_state_receipt,
    )
    if custody_submit is None:
        custody_submit = submit_state_receipt
    prior, evidence = require_predecessor_master_records_closure(
        previous if previous != "GENESIS" else None, successor_transition_id=transition_id)
    receipt = build_state_receipt(
        transition_id=transition_id, transition_sequence=1,
        subject_or_correlation_id=str(packet["packet_id"]),
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=prior,
        resulting_state_ref_or_hash=frame_sha,
        governance_decision_ref_where_applicable=validated["decision_sha256"],
        transition_evidence={
            "expected_organization_previous_receipt_sha256": actual_previous,
            "packet_sha256": request["packet_sha256"],
            "frame_sha256": frame_sha,
            "source_organization_receipt_sha256": request["source_organization_receipt_sha256"],
            "origin_organization": packet["origin"]["org"],
            "destination_organization": packet["destination"]["org"],
            "destination_service": packet["destination"]["service"],
            "transition_id": packet["transition"]["reference"],
            "intr_decision_receipt_sha256": validated["decision_sha256"],
            "transport_authorization_reference_present": True,
            "receiver_execution_observed": False,
        }, required_evidence_manifest=evidence,
        proof_scope="EXACT_ORGANIZATION_FEDERATION_INTR_INGRESS_ONLY",
        proof_ceiling="CUSTODY_AND_OBSERVATION_NOT_RECEIVER_EXECUTION_OR_GOVERNANCE_AUTHORITY",
    )
    closure = custody_submit(receipt)
    digest = K.sha(receipt).split(":", 1)[1]
    require(closure.get("state") == "RECORDED"
            and closure.get("reconstruction_status") == "PASS"
            and closure.get("required_evidence_validation_status") == "PASS"
            and closure.get("receipt_sha256") == digest
            and closure.get("reconstructed_receipt_sha256") == digest,
            "federation_ingress_master_records_custody_incomplete")
    org = closure.get("organization_receipt")
    require(isinstance(org, dict)
            and org.get("source_receipt_schema") == "stegverse.canonical-state-transition-receipt/v1"
            and org.get("canonical_state_transition_receipt_sha256") == K.sha(receipt)
            and org.get("previous_receipt_sha256") == actual_previous
            and org.get("receipt_sha256") == K.sha({k: v for k, v in org.items() if k != "receipt_sha256"}),
            "federation_organization_receipt_binding_invalid")
    result = {
        "schema": RECEIPT_SCHEMA, "state": "INGRESS_RECORDED",
        "packet_id": packet["packet_id"], "packet_sha256": request["packet_sha256"],
        "source_organization_receipt_sha256": request["source_organization_receipt_sha256"],
        "frame_sha256": frame_sha, "intr_decision_receipt_sha256": validated["decision_sha256"],
        "canonical_receipt_sha256": digest, "organization_receipt_sha256": org["receipt_sha256"],
        "predecessor_organization_receipt_sha256": org.get("previous_receipt_sha256"),
        "master_records_state": "RECORDED", "master_records_reconstruction_status": "PASS",
        "master_records_required_evidence_validation_status": "PASS",
        "receiver_execution_observed": False,
        "external_intr_allow_authenticated_by_runtime": False,
        "external_intr_decision_reconstructed": True,
        "authority_effect": "NONE_INGRESS_AND_CUSTODY_ONLY",
    }
    _write_once(path, result)
    return result
