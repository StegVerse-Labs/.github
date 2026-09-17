#!/usr/bin/env python3
"""Reusable canonical state-transition custody client.

Every observed governed transition can be wrapped in one canonical receipt and
submitted to the existing Master Records custody authority. This module grants no
transition, execution, credential, routing, or publication authority.

The preferred path is the canonical Master Records state-transition API. When a
resident execution is operating with the canonical Master Records repository
mounted locally, the existing exact-byte lifecycle ingest/reconstruction scripts
are an admissible local adapter to the same custody authority; they are not a
second custody authority or a task-specific diagnostic path.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
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


def _submit_http(receipt: Mapping[str, Any]) -> dict[str, Any] | None:
    endpoint, token, timeout = _configuration()
    if not endpoint or not token or not _endpoint_allowed(endpoint):
        return None
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
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"state":"BOUNDARY","reason":f"CANONICAL_MASTER_RECORDS_CUSTODY_SUBMISSION_FAILED:{type(exc).__name__}","authority_effect":"NONE"}


def _repo_roots() -> dict[str, str]:
    raw = (os.getenv("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _local_binding() -> tuple[Path, Path] | None:
    roots = _repo_roots()
    raw = (
        (os.getenv("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT") or "").strip()
        or (os.getenv("STEGVERSE_MASTER_RECORDS_SOURCE_ROOT") or "").strip()
        or str(roots.get("master-records/orchestration") or "")
    )
    runtime_raw = (os.getenv("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    if not raw or not runtime_raw:
        return None
    mr_root = Path(raw).expanduser().resolve()
    runtime_root = Path(runtime_raw).expanduser().resolve()
    if not (mr_root / "scripts/ingest_reusable_task_lifecycle.py").is_file():
        return None
    if not (mr_root / "scripts/reconstruct_reusable_task_lifecycle.py").is_file():
        return None
    return mr_root, runtime_root / "master-records" / "canonical-state-transitions"


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _submit_local(receipt: Mapping[str, Any]) -> dict[str, Any] | None:
    binding = _local_binding()
    if binding is None:
        return None
    mr_root, custody_root = binding
    canonical = canonical_json(dict(receipt)) + "\n"
    digest = hashlib.sha256(canonical_json(dict(receipt)).encode("utf-8")).hexdigest()
    subject = hashlib.sha256(str(receipt["subject_or_correlation_id"]).encode("utf-8")).hexdigest()[:16]
    request_path = custody_root / "requests" / subject / f"{int(receipt['transition_sequence']):06d}-{digest}.json"
    reconstructed = request_path.with_name(request_path.stem + ".reconstructed.json")
    _atomic_text(request_path, canonical)
    env = {key: os.environ[key] for key in ("PATH","PYTHONPATH","LANG","LC_ALL") if key in os.environ}
    ingest = subprocess.run(
        [sys.executable, str(mr_root / "scripts/ingest_reusable_task_lifecycle.py"), "--request", str(request_path), "--custody-root", str(custody_root)],
        cwd=mr_root, env=env, capture_output=True, text=True, check=False, timeout=60,
    )
    if ingest.returncode != 0:
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_LOCAL_INGEST_FAILED","stderr_tail":ingest.stderr[-1000:],"authority_effect":"NONE"}
    try:
        ingest_result = json.loads(ingest.stdout.strip().splitlines()[-1])
        custody_ref = Path(str(ingest_result["custody_ref"]))
    except Exception:
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_LOCAL_INGEST_RESULT_INVALID","authority_effect":"NONE"}
    reconstruction = subprocess.run(
        [sys.executable, str(mr_root / "scripts/reconstruct_reusable_task_lifecycle.py"), "--record", str(custody_ref), "--custody-root", str(custody_root), "--output", str(reconstructed)],
        cwd=mr_root, env=env, capture_output=True, text=True, check=False, timeout=60,
    )
    if reconstruction.returncode != 0 or not reconstructed.is_file():
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_LOCAL_RECONSTRUCTION_FAILED","stderr_tail":reconstruction.stderr[-1000:],"authority_effect":"NONE"}
    if reconstructed.read_bytes() != request_path.read_bytes():
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_LOCAL_RECONSTRUCTION_BYTES_MISMATCH","authority_effect":"NONE"}
    return {
        "schema":"stegverse.master-records.state-transition-custody-receipt/local-v1",
        "state":"RECORDED",
        "transition_id":receipt["transition_id"],
        "transition_sequence":receipt["transition_sequence"],
        "subject_or_correlation_id":receipt["subject_or_correlation_id"],
        "receipt_sha256":digest,
        "reconstructed_receipt_sha256":digest,
        "custody_ref":str(custody_ref),
        "reconstructed_ref":str(reconstructed),
        "reconstruction_status":"PASS",
        "custody_adapter":"MASTER_RECORDS_LOCAL_EXACT_BYTE_LIFECYCLE",
        "master_records_grants_transition_authority":False,
        "master_records_grants_execution_authority":False,
        "authority_effect":"NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }


def submit_state_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Submit one canonical receipt and require exact reconstruction."""
    if receipt.get("schema") != RECEIPT_SCHEMA:
        return {"state":"BOUNDARY","reason":"CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH","authority_effect":"NONE"}
    payload = _submit_http(receipt)
    if payload is None:
        payload = _submit_local(receipt)
    if payload is None:
        return {"state":"BOUNDARY","reason":"CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE","authority_effect":"NONE"}
    if payload.get("state") == "BOUNDARY":
        return payload
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
        self.records: list[dict[str, Any]] = []

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
        row = {"receipt":receipt, "master_records":result}
        self.records.append(row)
        if require_return and result.get("state") != "RECORDED":
            raise RuntimeError(str(result.get("reason") or "canonical_master_records_custody_not_returned"))
        if result.get("state") == "RECORDED":
            self.last_state_ref = resulting_state_ref_or_hash or sha256_uri(receipt)
        return row


__all__ = ["CanonicalTransitionCustody", "build_state_receipt", "submit_state_receipt", "sha256_uri"]
