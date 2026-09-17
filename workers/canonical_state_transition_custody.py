#!/usr/bin/env python3
"""Reusable canonical state-transition custody client.

Every observed governed transition can be wrapped in one canonical receipt and
submitted to the existing Master Records custody authority. This module grants no
transition, execution, credential, routing, or publication authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

RECEIPT_SCHEMA = "stegverse.canonical-state-transition-receipt/v1"
SUBMISSION_SCHEMA = "stegverse.master-records.state-transition-submission/v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_state_receipt(
    *,
    transition_id: str,
    transition_sequence: int,
    subject_or_correlation_id: str,
    transition_outcome: str,
    prior_state_ref_or_hash: str | None,
    resulting_state_ref_or_hash: str | None,
    governance_decision_ref_where_applicable: str | None,
    transition_evidence: Mapping[str, Any],
    proof_scope: str = "THIS_TRANSITION_ONLY",
    proof_ceiling: str = "OBSERVED_STATE_TRANSITION_AND_CUSTODY_ONLY",
    recorded_at: str | None = None,
) -> dict[str, Any]:
    if not transition_id or not subject_or_correlation_id:
        raise ValueError("transition_identity_required")
    if not isinstance(transition_sequence, int) or transition_sequence < 0:
        raise ValueError("transition_sequence_invalid")
    if transition_outcome not in {"ALLOW","DENY","EXECUTED","COMPLETED","PARTIAL","FAILED","FAIL_CLOSED","OBSERVED","NO_CHANGE"}:
        raise ValueError("transition_outcome_invalid")
    if not isinstance(transition_evidence, Mapping):
        raise ValueError("transition_evidence_required")
    return {
        "schema": RECEIPT_SCHEMA,
        "transition_id": transition_id,
        "transition_sequence": transition_sequence,
        "subject_or_correlation_id": subject_or_correlation_id,
        "prior_state_ref_or_hash": prior_state_ref_or_hash,
        "resulting_state_ref_or_hash": resulting_state_ref_or_hash,
        "governance_decision_ref_where_applicable": governance_decision_ref_where_applicable,
        "transition_evidence": dict(transition_evidence),
        "recorded_at": recorded_at or now(),
        "transition_outcome": transition_outcome,
        "authority_effect": "NONE_STATE_RECEIPT_ONLY",
        "proof_scope": proof_scope,
        "proof_ceiling": proof_ceiling,
        "master_records_may_grant_transition_authority": False,
        "master_records_may_grant_execution_authority": False,
    }


def _configuration() -> tuple[str, str, float]:
    endpoint = (os.getenv("STEGVERSE_MASTER_RECORDS_ENDPOINT") or "").strip().rstrip("/")
    if endpoint and not endpoint.endswith("/api/master-records/state-transitions"):
        endpoint += "/api/master-records/state-transitions"
    token = (os.getenv("STEGVERSE_MASTER_RECORDS_TOKEN") or "").strip()
    timeout = float(os.getenv("STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS", "10"))
    return endpoint, token, timeout


def _endpoint_allowed(endpoint: str) -> bool:
    try:
        parsed = urlparse(endpoint)
    except Exception:
        return False
    if parsed.scheme == "https":
        return bool(parsed.hostname)
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return True
    return False


def submit_state_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Submit one canonical receipt; fail closed when custody is unreachable."""
    if receipt.get("schema") != RECEIPT_SCHEMA:
        return {"state":"BOUNDARY","reason":"CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH","authority_effect":"NONE"}
    endpoint, token, timeout = _configuration()
    if not endpoint or not token or not _endpoint_allowed(endpoint):
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_CUSTODY_ENDPOINT_UNAVAILABLE","authority_effect":"NONE"}
    body = {
        "schema": SUBMISSION_SCHEMA,
        "receipt": dict(receipt),
        "authority_requested": False,
        "custody_requested": True,
        "reconstruction_requested": True,
    }
    request = Request(
        endpoint,
        data=canonical_json(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type":"application/json", "Authorization":f"Bearer {token}"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"state":"BOUNDARY","reason":f"CANONICAL_MASTER_RECORDS_CUSTODY_SUBMISSION_FAILED:{type(exc).__name__}","authority_effect":"NONE"}
    expected_hash = sha256_uri(dict(receipt)).split(":", 1)[1]
    if payload.get("state") != "RECORDED" or payload.get("reconstruction_status") != "PASS":
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_CUSTODY_NOT_RECORDED","response":payload,"authority_effect":"NONE"}
    if payload.get("receipt_sha256") != expected_hash or payload.get("reconstructed_receipt_sha256") != expected_hash:
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_RECONSTRUCTION_HASH_MISMATCH","response":payload,"authority_effect":"NONE"}
    if payload.get("master_records_grants_transition_authority") is not False:
        return {"state":"BOUNDARY","reason":"MASTER_RECORDS_AUTHORITY_ESCALATION_DETECTED","authority_effect":"NONE"}
    return {**payload, "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY"}


class CanonicalTransitionCustody:
    """Sequence-aware helper used by governed transition consumers."""
    def __init__(self, subject_or_correlation_id: str) -> None:
        if not subject_or_correlation_id:
            raise ValueError("subject_or_correlation_id_required")
        self.subject = subject_or_correlation_id
        self.sequence = 0
        self.last_state_ref: str | None = None

    def record(
        self,
        transition_id: str,
        *,
        outcome: str,
        evidence: Mapping[str, Any],
        resulting_state_ref_or_hash: str | None = None,
        governance_decision_ref: str | None = None,
        require_return: bool = True,
    ) -> dict[str, Any]:
        self.sequence += 1
        receipt = build_state_receipt(
            transition_id=transition_id,
            transition_sequence=self.sequence,
            subject_or_correlation_id=self.subject,
            transition_outcome=outcome,
            prior_state_ref_or_hash=self.last_state_ref,
            resulting_state_ref_or_hash=resulting_state_ref_or_hash,
            governance_decision_ref_where_applicable=governance_decision_ref,
            transition_evidence=evidence,
        )
        result = submit_state_receipt(receipt)
        if require_return and result.get("state") != "RECORDED":
            raise RuntimeError(str(result.get("reason") or "canonical_master_records_custody_not_returned"))
        if result.get("state") == "RECORDED":
            self.last_state_ref = resulting_state_ref_or_hash or sha256_uri(receipt)
        return {"receipt":receipt, "master_records":result}


__all__ = ["CanonicalTransitionCustody", "build_state_receipt", "submit_state_receipt", "sha256_uri"]
