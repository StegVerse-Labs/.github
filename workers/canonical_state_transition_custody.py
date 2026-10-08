#!/usr/bin/env python3
"""Reusable canonical organization-record and reconstruction client.

Every observed governed transition may emit a canonical transition receipt into
the organization ledger. Master Records is not the general transition/evidence
custody path and is never a prerequisite for unrelated transition progression.
Master Records is used only for organization records and explicit reconstruction.

Legacy Master Records submission/query helpers remain temporarily for bounded
organization-record/reconstruction compatibility while call sites are repaired.
They grant no transition, execution, credential, routing, publication, runtime-
reality, or observability authority.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from heartbeat_runtime.independent_oscillator import current_reference

RECEIPT_SCHEMA = "stegverse.canonical-state-transition-receipt/v1"
SUBMISSION_SCHEMA = "stegverse.master-records.state-transition-submission/v1"
HB_CREATION_PROTOCOL = "STEGVERSE_HEARTBEAT_100HZ_OSCILLATOR_V1"
HB_REFERENCE_SCHEMA = "stegverse.heartbeat-reference/v1"
ORGANIZATION_RECORD_API_MODULE = "master_records_organization_record_api"
ORGANIZATION_RECORD_ORDINAL_FIELD = "master_records_organization_record_ordinal"
RECORD_REQUESTED_FIELD = "record_requested"
#: Master Records boundary migration: master-records/orchestration checkouts
#: from before the rename expose only the legacy API module, and reconstruction
#: results written before it carry the legacy ordinal field. Readers accept both.
LEGACY_ORGANIZATION_RECORD_API_MODULE = "master_records_custody_api"
LEGACY_ORGANIZATION_RECORD_ORDINAL_FIELD = "master_records_custody_ordinal"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _record_organization_transition(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Record the exact governed transition in the existing organization ledger."""
    module_path = Path(__file__).resolve().parents[1] / "resident-runtime" / "aggregate_repo_transition.py"
    if not module_path.is_file():
        return {"state": "BOUNDARY", "reason": "ORGANIZATION_TRANSITION_LEDGER_SURFACE_UNAVAILABLE", "authority_effect": "NONE"}
    try:
        spec = importlib.util.spec_from_file_location("stegverse_org_transition_ledger", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("organization_transition_ledger_import_unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        organization_receipt = module.aggregate_transition(
            dict(receipt),
            org_transition_class="ORGANIZATION_STATE_TRANSITION",
            boundary_evidence={
                "canonical_state_transition_receipt_sha256": sha256_uri(dict(receipt)),
                "ordering": "ORGANIZATION_RECORD_IS_CANONICAL_BEFORE_ANY_OPTIONAL_RECONSTRUCTION",
            },
            authority_effect="NONE",
        )
    except Exception as exc:
        return {
            "state": "BOUNDARY",
            "reason": f"ORGANIZATION_TRANSITION_RECEIPT_RECORDING_FAILED:{type(exc).__name__}",
            "authority_effect": "NONE",
        }
    expected_source = sha256_uri(dict(receipt))
    if (
        organization_receipt.get("schema") != "stegverse.organization-transition-receipt/v1"
        or organization_receipt.get("organization") != "StegVerse-Labs"
        or organization_receipt.get("source_receipt_schema") != RECEIPT_SCHEMA
        or organization_receipt.get("source_transition_sha256") != expected_source
        or organization_receipt.get("canonical_state_transition_receipt_sha256") != expected_source
        or not organization_receipt.get("receipt_sha256")
    ):
        return {"state": "BOUNDARY", "reason": "ORGANIZATION_TRANSITION_RECEIPT_BINDING_INVALID", "authority_effect": "NONE"}
    return {"state": "RECORDED", "organization_receipt": organization_receipt, "authority_effect": "NONE_ORGANIZATION_RECORDING_ONLY"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def current_hb_creation_reference(*, sampled_unix_ns: int | None = None) -> dict[str, Any]:
    """Return the current canonical HeartBeat reference as non-authorizing evidence."""
    sampled = time.time_ns() if sampled_unix_ns is None else int(sampled_unix_ns)
    ref = current_reference(now_ns=sampled)
    return {
        "schema": HB_REFERENCE_SCHEMA,
        "protocol": HB_CREATION_PROTOCOL,
        "heartbeat_id": ref["heartbeat_id"],
        "heartbeat_epoch": ref["epoch"],
        "heartbeat_generation": ref["generation"],
        "sampled_unix_ns": sampled,
        "reference_frame": f"heartbeat_epoch:{ref['epoch']}",
        "authority_effect": "NONE_REFERENCE_ONLY",
        "grants_execution_authority": False,
        "grants_transition_authority": False,
        "grants_custody_authority": False,
        "grants_credential_authority": False,
    }


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
    required_evidence_manifest: list[Mapping[str, Any]] | None = None,
    proof_scope: str = "THIS_TRANSITION_ONLY",
    proof_ceiling: str = "OBSERVED_STATE_TRANSITION_AND_ORGANIZATION_RECORD_ONLY",
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
    manifest = []
    for entry in required_evidence_manifest or []:
        if not isinstance(entry, Mapping):
            raise ValueError("required_evidence_manifest_entry_invalid")
        row = dict(entry)
        if row.get("origin_transition_id") != transition_id:
            raise ValueError("required_evidence_transition_binding_invalid")
        manifest.append(row)
    return {
        "schema": RECEIPT_SCHEMA,
        "transition_id": transition_id,
        "transition_sequence": transition_sequence,
        "subject_or_correlation_id": subject_or_correlation_id,
        "prior_state_ref_or_hash": prior_state_ref_or_hash,
        "resulting_state_ref_or_hash": resulting_state_ref_or_hash,
        "governance_decision_ref_where_applicable": governance_decision_ref_where_applicable,
        "transition_evidence": dict(transition_evidence),
        "required_evidence_manifest": manifest,
        "recorded_at": recorded_at or now(),
        "hb_creation_reference": current_hb_creation_reference(),
        "hb_creation_protocol": HB_CREATION_PROTOCOL,
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
        RECORD_REQUESTED_FIELD: True,
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
        return {"state":"BOUNDARY","reason":f"CANONICAL_MASTER_RECORDS_ORGANIZATION_RECORD_SUBMISSION_FAILED:{type(exc).__name__}","authority_effect":"NONE"}



ORGANIZATION_BATCH_SUBMISSION_SCHEMAS = (
    "stegverse.master-records.organization-batch-record-submission/v1",
    "stegverse.master-records.organization-batch-submission/v1",
)


def submit_organization_batch(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Carry one already-released batch as execution evidence, never as a governance decision."""
    def evidence_result(state: str, *, reason: str | None = None, batch_id: Any = None,
                        destination_response: Mapping[str, Any] | None = None,
                        authority_effect: str = "NONE") -> dict[str, Any]:
        row: dict[str, Any] = {
            "schema": "stegverse.organization-batch-custody-execution-result/v1",
            "state": state,
            "execution_result": state,
            "batch_id": batch_id,
            "governance_disposition": None,
            "authority_effect": authority_effect,
        }
        if reason is not None:
            row["reason"] = reason
        if destination_response is not None:
            row["destination_response"] = dict(destination_response)
        return row

    # The organization reports the batched record. The record-only envelope is
    # what carriage sends; the legacy contents-bearing envelope is still accepted
    # so an already-released batch prepared before this change can still be
    # carried, and so this client stays compatible with the merged Master Records
    # ingress until that side accepts the record-only form.
    if envelope.get("schema") not in ORGANIZATION_BATCH_SUBMISSION_SCHEMAS:
        return evidence_result("FAILED", reason="ORGANIZATION_BATCH_SUBMISSION_SCHEMA_MISMATCH")
    batch = envelope.get("batch")
    if not isinstance(batch, Mapping):
        return evidence_result("FAILED", reason="ORGANIZATION_BATCH_REQUIRED")
    batch_id = batch.get("batch_id")
    endpoint, token, timeout = _configuration()
    if endpoint:
        endpoint = endpoint.rsplit("/api/master-records/state-transitions", 1)[0] + "/api/master-records/organization-batches"
    if not endpoint or not token or not _endpoint_allowed(endpoint):
        return evidence_result("FAILED", reason="ORGANIZATION_BATCH_AUTHENTIC_CUSTODY_SURFACE_UNAVAILABLE",
                               batch_id=batch_id)
    request = Request(
        endpoint,
        data=canonical_json(dict(envelope)).encode("utf-8"),
        method="POST",
        headers={"Content-Type":"application/json", "Authorization":f"Bearer {token}"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload=json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return evidence_result("FAILED", reason=f"ORGANIZATION_BATCH_CUSTODY_SUBMISSION_FAILED:{type(exc).__name__}",
                               batch_id=batch_id)
    if not isinstance(payload, Mapping):
        return evidence_result("FAILED", reason="ORGANIZATION_BATCH_CUSTODY_RESULT_INVALID",
                               batch_id=batch_id)
    if payload.get("state") not in {"RECORDED","ALLOW"}:
        return evidence_result("FAILED",
                               reason=str(payload.get("reason") or "ORGANIZATION_BATCH_CUSTODY_NOT_RECORDED"),
                               batch_id=batch_id, destination_response=payload)
    if payload.get("batch_id") not in {None,batch_id}:
        return evidence_result("FAILED", reason="ORGANIZATION_BATCH_CUSTODY_ID_MISMATCH",
                               batch_id=batch_id, destination_response=payload)
    reconstruction = payload.get("reconstruction_status")
    evidence = payload.get("required_evidence_validation_status")
    if reconstruction not in {None,"PASS"} or evidence not in {None,"PASS"}:
        return evidence_result("FAILED", reason="ORGANIZATION_BATCH_CUSTODY_RECONSTRUCTION_NOT_PASS",
                               batch_id=batch_id, destination_response=payload)
    result = evidence_result("COMPLETED", batch_id=batch_id, destination_response=payload,
                             authority_effect="NONE_CUSTODY_ONLY")
    result["destination_state"] = payload.get("state")
    return result


def _repo_roots() -> dict[str, str]:
    raw = (os.getenv("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _local_binding() -> Path | None:
    roots = _repo_roots()
    raw = (
        (os.getenv("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT") or "").strip()
        or (os.getenv("STEGVERSE_MASTER_RECORDS_SOURCE_ROOT") or "").strip()
        or str(roots.get("master-records/orchestration") or "")
    )
    db_raw = (os.getenv("MASTER_RECORDS_DB") or "").strip()
    receipt_key = (os.getenv("MASTER_RECORDS_RECEIPT_KEY") or "").strip()
    durable = (os.getenv("MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS") or "").strip().lower() == "true"
    if not raw or not db_raw or not receipt_key or not durable:
        return None
    mr_root = Path(raw).expanduser().resolve()
    db_path = Path(db_raw).expanduser()
    if not db_path.is_absolute():
        return None
    db_path = db_path.resolve()
    try:
        db_path.relative_to(Path("/tmp"))
        return None
    except ValueError:
        pass
    if _organization_record_api_module(mr_root) is None:
        return None
    if not (mr_root / "services" / "canonical_state_transition_custody.py").is_file():
        return None
    return mr_root


def _organization_record_api_module(mr_root: Path) -> str | None:
    """Name of the Master Records organization-record API module in this checkout."""
    for name in (ORGANIZATION_RECORD_API_MODULE, LEGACY_ORGANIZATION_RECORD_API_MODULE):
        if (mr_root / "services" / f"{name}.py").is_file():
            return name
    return None


def organization_record_ordinal(result: Mapping[str, Any]) -> Any:
    """Read a reconstruction's organization record ordinal under the current or legacy name."""
    if ORGANIZATION_RECORD_ORDINAL_FIELD in result:
        return result[ORGANIZATION_RECORD_ORDINAL_FIELD]
    return result.get(LEGACY_ORGANIZATION_RECORD_ORDINAL_FIELD)


def _submit_local(receipt: Mapping[str, Any]) -> dict[str, Any] | None:
    mr_root = _local_binding()
    if mr_root is None:
        return None
    env = {
        key: os.environ[key]
        for key in (
            "PATH",
            "LANG",
            "LC_ALL",
            "MASTER_RECORDS_DB",
            "MASTER_RECORDS_RECEIPT_KEY",
            "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
        )
        if key in os.environ
    }
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(mr_root) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    authority_call = (
        "import json,sys\n"
        f"from services import {_organization_record_api_module(mr_root)} as base\n"
        "from services.canonical_state_transition_custody import record_receipt\n"
        "receipt=json.loads(sys.stdin.read())\n"
        "result=record_receipt(base, receipt)\n"
        "sys.stdout.write(json.dumps(result, sort_keys=True)+'\\n')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", authority_call],
        cwd=mr_root,
        env=env,
        input=canonical_json(dict(receipt)),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_AUTHORITY_CALL_FAILED",
            "stderr_tail": completed.stderr[-1000:],
            "authority_effect": "NONE",
        }
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_AUTHORITY_RESULT_INVALID",
            "authority_effect": "NONE",
        }
    if not isinstance(result, dict):
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_AUTHORITY_RESULT_INVALID",
            "authority_effect": "NONE",
        }
    return result


def _reconstruct_http(receipt_sha256: str) -> dict[str, Any] | None:
    endpoint, token, timeout = _configuration()
    if not endpoint or not token or not _endpoint_allowed(endpoint):
        return None
    url = endpoint.rstrip("/") + f"/{receipt_sha256}/reconstruction"
    request = Request(url, method="GET", headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "state": "BOUNDARY",
            "reason": f"CANONICAL_MASTER_RECORDS_RECONSTRUCTION_FAILED:{type(exc).__name__}",
            "authority_effect": "NONE",
        }


def _reconstruct_local(receipt_sha256: str) -> dict[str, Any] | None:
    mr_root = _local_binding()
    if mr_root is None:
        return None
    env = {
        key: os.environ[key]
        for key in (
            "PATH",
            "LANG",
            "LC_ALL",
            "MASTER_RECORDS_DB",
            "MASTER_RECORDS_RECEIPT_KEY",
            "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
        )
        if key in os.environ
    }
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(mr_root) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    authority_call = (
        "import hashlib,json,sys\n"
        f"from services import {_organization_record_api_module(mr_root)} as base\n"
        "from services import canonical_state_transition_custody as canonical\n"
        "receipt_sha256=sys.argv[1]\n"
        "canonical._initialize(base)\n"
        "with base._LOCK, base._connect() as connection:\n"
        " row=connection.execute('SELECT * FROM canonical_state_transition_receipts WHERE receipt_sha256 = ?', (receipt_sha256,)).fetchone()\n"
        "if row is None:\n"
        " sys.stdout.write(json.dumps({'state':'BOUNDARY','reason':'state_transition_receipt_not_found','authority_effect':'NONE'})+'\\n'); raise SystemExit(0)\n"
        "receipt=json.loads(row['canonical_receipt_json'])\n"
        "raw=canonical._canonical(receipt)\n"
        "rebuilt=hashlib.sha256(raw).hexdigest()\n"
        "required=canonical._require_evidence_manifest(receipt)\n"
        "with base._LOCK, base._connect() as connection:\n"
        " rows=connection.execute('SELECT canonical_entry_json,evidence_sha256 FROM canonical_state_transition_required_evidence WHERE receipt_sha256 = ? ORDER BY evidence_id', (receipt_sha256,)).fetchall()\n"
        " metadata=connection.execute('SELECT * FROM canonical_state_transition_hb_recording_metadata WHERE receipt_sha256 = ?', (receipt_sha256,)).fetchone()\n"
        "evidence_pass=len(rows)==len(required)\n"
        "for item in rows:\n"
        " entry=json.loads(item['canonical_entry_json']); evidence_pass=evidence_pass and hashlib.sha256(canonical._evidence_bytes(entry)).hexdigest()==item['evidence_sha256']\n"
        "hb_recording=json.loads(metadata['hb_recording_reference_json']) if metadata is not None else None\n"
        "if hb_recording is not None: canonical.validate_hb_reference(hb_recording)\n"
        "state='PASS' if rebuilt==receipt_sha256 and evidence_pass else 'FAIL_CLOSED'\n"
        "result={'state':state,'receipt_sha256':receipt_sha256,'reconstructed_receipt_sha256':rebuilt,'receipt':receipt,'required_evidence_validation_status':'PASS' if evidence_pass else 'FAIL_CLOSED','master_record_ref':row['master_record_ref'],'custody_receipt_id':row['custody_receipt_id'],'hb_recording_reference':hb_recording,'hb_recording_protocol':metadata['hb_recording_protocol'] if metadata is not None else None,'master_records_organization_record_ordinal':int(metadata['custody_ordinal']) if metadata is not None else None,'recorded_receipt_sha256':metadata['recorded_receipt_sha256'] if metadata is not None else None,'hb_evidence_class':'HB_BOUND_SUCCESSOR' if metadata is not None else 'SYSTEM_RELATIVE_CONTINUITY_ONLY','master_records_grants_transition_authority':False,'authority_effect':'NONE_RECONSTRUCTION_ONLY'}\n"
        "sys.stdout.write(json.dumps(result, sort_keys=True)+'\\n')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", authority_call, receipt_sha256],
        cwd=mr_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_RECONSTRUCTION_CALL_FAILED",
            "stderr_tail": completed.stderr[-1000:],
            "authority_effect": "NONE",
        }
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_RECONSTRUCTION_RESULT_INVALID",
            "authority_effect": "NONE",
        }
    return result if isinstance(result, dict) else None


def _checkpoint_set_http(floor: int, ceiling: int) -> dict[str, Any] | None:
    endpoint, token, timeout = _configuration()
    if not endpoint or not token or not _endpoint_allowed(endpoint):
        return None
    url = endpoint.rstrip("/") + "/checkpoint-set?" + urlencode({"floor": floor, "ceiling": ceiling})
    request = Request(url, method="GET", headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "state": "BOUNDARY",
            "reason": f"CANONICAL_MASTER_RECORDS_CHECKPOINT_SET_FAILED:{type(exc).__name__}",
            "authority_effect": "NONE",
        }


def _checkpoint_set_local(floor: int, ceiling: int) -> dict[str, Any] | None:
    mr_root = _local_binding()
    if mr_root is None:
        return None
    env = {
        key: os.environ[key]
        for key in (
            "PATH",
            "LANG",
            "LC_ALL",
            "MASTER_RECORDS_DB",
            "MASTER_RECORDS_RECEIPT_KEY",
            "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
        )
        if key in os.environ
    }
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(mr_root) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    authority_call = (
        "import json,sys\n"
        f"from services import {_organization_record_api_module(mr_root)} as base\n"
        "from services.canonical_state_transition_custody import build_receipt_set_commitment\n"
        "result=build_receipt_set_commitment(base, int(sys.argv[1]), int(sys.argv[2]))\n"
        "sys.stdout.write(json.dumps(result, sort_keys=True)+'\\n')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", authority_call, str(floor), str(ceiling)],
        cwd=mr_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        stderr = completed.stderr[-1000:]
        reason = "CANONICAL_MASTER_RECORDS_LOCAL_CHECKPOINT_SET_CALL_FAILED"
        if "checkpoint_receipt_range_not_contiguous" in stderr or "checkpoint_receipt_set_empty" in stderr:
            reason = "CANONICAL_MASTER_RECORDS_HB_SUCCESSOR_RANGE_NOT_AVAILABLE"
        return {"state": "BOUNDARY", "reason": reason, "stderr_tail": stderr, "authority_effect": "NONE"}
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_LOCAL_CHECKPOINT_SET_RESULT_INVALID", "authority_effect": "NONE"}
    return result if isinstance(result, dict) else None


def build_master_records_receipt_set_commitment(floor: int, ceiling: int) -> dict[str, Any]:
    """Return an exact non-authorizing bounded Master Records successor projection."""
    if not isinstance(floor, int) or not isinstance(ceiling, int) or floor < 1 or ceiling < floor:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_BOUNDS_INVALID", "authority_effect": "NONE"}
    payload = _checkpoint_set_http(floor, ceiling)
    if payload is None:
        payload = _checkpoint_set_local(floor, ceiling)
    if payload is None:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_SURFACE_UNAVAILABLE", "authority_effect": "NONE"}
    if payload.get("state") == "BOUNDARY":
        return payload
    if payload.get("schema") != "stegverse.master-records.receipt-set-commitment/v1":
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_SCHEMA_INVALID", "authority_effect": "NONE"}
    if payload.get("master_records_commitment_profile") != "ORDERED_CANONICAL_RECEIPT_SHA256_BOUNDED_RANGE_V1":
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_PROFILE_INVALID", "authority_effect": "NONE"}
    if payload.get("master_records_query_floor") != floor or payload.get("master_records_query_ceiling") != ceiling:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_BOUNDS_MISMATCH", "authority_effect": "NONE"}
    if payload.get("master_records_receipt_count") != ceiling - floor + 1:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_COUNT_MISMATCH", "authority_effect": "NONE"}
    identities = payload.get("ordered_receipt_identities")
    if not isinstance(identities, list) or len(identities) != payload.get("master_records_receipt_count"):
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_CHECKPOINT_IDENTITIES_INVALID", "authority_effect": "NONE"}
    return {**payload, "state": "PASS", "authority_effect": "NONE_CUSTODY_COMMITMENT_ONLY"}


def _query_http(subject_or_correlation_id: str, transition_id: str | None) -> dict[str, Any] | None:
    endpoint, token, timeout = _configuration()
    if not endpoint or not token or not _endpoint_allowed(endpoint):
        return None
    params = {"subject_or_correlation_id": subject_or_correlation_id}
    if transition_id:
        params["transition_id"] = transition_id
    url = endpoint.rstrip("/") + "/query?" + urlencode(params)
    request = Request(url, method="GET", headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "state": "BOUNDARY",
            "reason": f"CANONICAL_MASTER_RECORDS_QUERY_FAILED:{type(exc).__name__}",
            "authority_effect": "NONE",
        }


def _query_local(subject_or_correlation_id: str, transition_id: str | None) -> dict[str, Any] | None:
    mr_root = _local_binding()
    if mr_root is None:
        return None
    env = {
        key: os.environ[key]
        for key in (
            "PATH",
            "LANG",
            "LC_ALL",
            "MASTER_RECORDS_DB",
            "MASTER_RECORDS_RECEIPT_KEY",
            "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
        )
        if key in os.environ
    }
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(mr_root) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    authority_call = (
        "import json,sys\n"
        f"from services import {_organization_record_api_module(mr_root)} as base\n"
        "from services import canonical_state_transition_custody as canonical\n"
        "subject=sys.argv[1]; transition=sys.argv[2] or None\n"
        "canonical._initialize(base)\n"
        "with base._LOCK, base._connect() as connection:\n"
        " rows=connection.execute('SELECT receipt_sha256 FROM canonical_state_transition_receipts WHERE subject_or_correlation_id = ? AND (? IS NULL OR transition_id = ?) ORDER BY transition_sequence, recorded_at, receipt_sha256', (subject, transition, transition)).fetchall()\n"
        "sys.stdout.write(json.dumps({'schema':'stegverse.master-records.state-transition-query/v1','subject_or_correlation_id':subject,'transition_id':transition,'receipt_sha256s':[row['receipt_sha256'] for row in rows],'master_records_grants_transition_authority':False,'authority_effect':'NONE_QUERY_ONLY'}, sort_keys=True)+'\\n')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", authority_call, subject_or_correlation_id, transition_id or ""],
        cwd=mr_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_QUERY_CALL_FAILED",
            "stderr_tail": completed.stderr[-1000:],
            "authority_effect": "NONE",
        }
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        return {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_LOCAL_QUERY_RESULT_INVALID",
            "authority_effect": "NONE",
        }
    return result if isinstance(result, dict) else None


def query_state_receipts(subject_or_correlation_id: str, transition_id: str | None = None) -> dict[str, Any]:
    """Discover retained receipt identities without granting any transition authority."""
    if not isinstance(subject_or_correlation_id, str) or not subject_or_correlation_id:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_QUERY_SUBJECT_INVALID", "authority_effect": "NONE"}
    payload = _query_http(subject_or_correlation_id, transition_id)
    if payload is None:
        payload = _query_local(subject_or_correlation_id, transition_id)
    if payload is None:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_QUERY_SURFACE_UNAVAILABLE", "authority_effect": "NONE"}
    if payload.get("state") == "BOUNDARY":
        return payload
    if payload.get("master_records_grants_transition_authority") is not False:
        return {"state": "BOUNDARY", "reason": "MASTER_RECORDS_AUTHORITY_ESCALATION_DETECTED", "authority_effect": "NONE"}

    hashes = payload.get("receipt_sha256s")
    if hashes is None:
        records = payload.get("records")
        if not isinstance(records, list):
            return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_QUERY_RESULT_INVALID", "authority_effect": "NONE"}
        hashes = [row.get("receipt_sha256") for row in records if isinstance(row, dict)]
    if not isinstance(hashes, list) or any(not isinstance(value, str) or len(value) != 64 for value in hashes):
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_QUERY_RECEIPT_IDENTITIES_INVALID", "authority_effect": "NONE"}

    reconstructed = []
    for receipt_sha256 in hashes:
        row = reconstruct_state_receipt(receipt_sha256)
        if row.get("state") != "PASS":
            return {
                "state": "BOUNDARY",
                "reason": str(row.get("reason") or "CANONICAL_MASTER_RECORDS_QUERY_RECONSTRUCTION_FAILED"),
                "receipt_sha256": receipt_sha256,
                "authority_effect": "NONE",
            }
        reconstructed.append(row)
    return {
        "state": "PASS",
        "subject_or_correlation_id": subject_or_correlation_id,
        "transition_id": transition_id,
        "count": len(reconstructed),
        "records": reconstructed,
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE_QUERY_RECONSTRUCTION_ONLY",
    }


def reconstruct_state_receipt(receipt_sha256: str) -> dict[str, Any]:
    """Reconstruct a retained canonical transition receipt by exact digest."""
    if not isinstance(receipt_sha256, str) or len(receipt_sha256) != 64:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_RECEIPT_SHA_INVALID", "authority_effect": "NONE"}
    payload = _reconstruct_http(receipt_sha256)
    if payload is None:
        payload = _reconstruct_local(receipt_sha256)
    if payload is None:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_RECONSTRUCTION_SURFACE_UNAVAILABLE", "authority_effect": "NONE"}
    if payload.get("state") == "BOUNDARY":
        return payload
    if payload.get("state") != "PASS":
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_RECONSTRUCTION_NOT_PASS", "response": payload, "authority_effect": "NONE"}
    if payload.get("receipt_sha256") != receipt_sha256 or payload.get("reconstructed_receipt_sha256") != receipt_sha256:
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_RECONSTRUCTION_HASH_MISMATCH", "response": payload, "authority_effect": "NONE"}
    if payload.get("required_evidence_validation_status") != "PASS":
        return {"state": "BOUNDARY", "reason": "CANONICAL_MASTER_RECORDS_REQUIRED_EVIDENCE_NOT_VALIDATED", "response": payload, "authority_effect": "NONE"}
    if payload.get("master_records_grants_transition_authority") is not False:
        return {"state": "BOUNDARY", "reason": "MASTER_RECORDS_AUTHORITY_ESCALATION_DETECTED", "authority_effect": "NONE"}
    return {**payload, "authority_effect": "NONE_RECONSTRUCTION_ONLY"}

def record_organization_runtime_reality(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Append one canonical state receipt to the organization ledger and stop there.

    ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001 makes the organization the
    runtime_reality_authority, with the organization ledger root under the
    organization ledger lock as its locus. This entry point establishes that
    reality on its own: it performs no outbound submission, awaits no receiver,
    and returns an organization-level disposition that does not depend on the
    Master Records released-batch recording lane.

    It is not a Master Records organization record and may not be promoted to one. Explicit
    reconstruction is a separate diagnostic/readback operation and is never a
    progression prerequisite for an unrelated transition.
    """
    if receipt.get("schema") != RECEIPT_SCHEMA:
        return {"state": "BOUNDARY", "reason": "CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH", "authority_effect": "NONE"}
    organization = _record_organization_transition(receipt)
    if organization.get("state") != "RECORDED":
        return organization
    return {
        **organization,
        "runtime_reality_authority": "Organization",
        "runtime_reality_locus": "ORGANIZATION_LEDGER_ROOT",
        "runtime_reality_lock": "ORGANIZATION_LEDGER_LOCK",
        "runtime_reality_write_mode": "MANIFEST_DIRECTED_APPEND",
        "master_records_role": "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER",
        "master_records_gates_organization_runtime_reality": False,
        "master_records_organization_record_claimed": False,
        "master_records_reconstructed_evidence_class_claimed": False,
        "authority_effect": "NONE_ORGANIZATION_RECORDING_ONLY",
    }


def submit_state_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Compatibility entry point: record the transition in the organization ledger only.

    The legacy function name is retained while callers migrate. It MUST NOT submit
    a general state-transition receipt to Master Records. Master Records may receive
    organization records through the bounded organization-batch lane, and may be
    queried for explicit reconstruction separately.
    """
    if receipt.get("schema") != RECEIPT_SCHEMA:
        return {"state": "BOUNDARY", "reason": "CANONICAL_STATE_RECEIPT_SCHEMA_MISMATCH", "authority_effect": "NONE"}
    organization = _record_organization_transition(receipt)
    if organization.get("state") != "RECORDED":
        return organization
    receipt_sha256 = sha256_uri(dict(receipt)).split(":", 1)[1]
    return {
        "state": "RECORDED",
        "receipt_sha256": receipt_sha256,
        "organization_receipt": organization["organization_receipt"],
        "organization_runtime_reality": "RECORDED",
        "organization_runtime_reality_locus": "ORGANIZATION_LEDGER_ROOT",
        "master_records_submission_performed": False,
        "master_records_role": "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY",
        "reconstruction_status": "NOT_REQUESTED",
        "required_evidence_validation_status": "ORGANIZATION_RECORD_ONLY",
        "authority_effect": "NONE_ORGANIZATION_RECORDING_ONLY",
    }


def require_predecessor_master_records_organization_record(
    receipt_sha256: str | None,
    *,
    successor_transition_id: str,
) -> tuple[str | None, list[dict[str, Any]]]:
    """Legacy-name reconstruction helper; never a transition-progression gate.

    If a predecessor digest is supplied, preserve it as the prior-state reference.
    An available Master Records reconstruction may be attached as non-authorizing
    reconstruction evidence. Reconstruction absence or failure must not prevent an
    otherwise governed successor transition from being evaluated or executed.
    """
    if receipt_sha256 is None:
        return None, []
    if not isinstance(receipt_sha256, str) or not receipt_sha256:
        raise RuntimeError("canonical_predecessor_receipt_sha_invalid")
    raw = receipt_sha256.split(":", 1)[1] if receipt_sha256.startswith("sha256:") else receipt_sha256
    reconstruction = reconstruct_state_receipt(raw)
    reconstruction_pass = (
        reconstruction.get("state") == "PASS"
        and reconstruction.get("receipt_sha256") == raw
        and reconstruction.get("reconstructed_receipt_sha256") == raw
    )
    content = {
        "receipt_sha256": raw,
        "reconstruction_status": "PASS" if reconstruction_pass else "NOT_AUTHENTICALLY_OBSERVED",
        "master_records_role": "RECONSTRUCTION_ONLY",
        "transition_gate": False,
        "authority_effect": "NONE_RECONSTRUCTION_ONLY",
    }
    if reconstruction_pass:
        content["master_record_ref"] = reconstruction.get("master_record_ref")
    evidence = {
        "evidence_id": f"predecessor-reconstruction:{successor_transition_id}",
        "evidence_type": "PREDECESSOR_RECONSTRUCTION_STATUS",
        "origin_transition_id": successor_transition_id,
        "encoding": "canonical-json",
        "sha256": sha256_uri(content).split(":", 1)[1],
        "content": content,
    }
    return f"sha256:{raw}", [evidence]


#: Master Records boundary migration: StegVerse-Labs/StegAgents and older callers
#: look this helper up under its legacy name; it stays bound to the same function.
LEGACY_PREDECESSOR_RECONSTRUCTION_HELPER = "require_predecessor_master_records_closure"
globals()[LEGACY_PREDECESSOR_RECONSTRUCTION_HELPER] = require_predecessor_master_records_organization_record


class CanonicalTransitionCustody:
    """Sequence-aware organization-record helper used by governed consumers.

    Transition progression follows governed state and organization-ledger state.
    Master Records is not a progression dependency. Explicit reconstruction may be
    requested independently where reconstruction is the actual operation.
    """
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
        required_evidence_manifest: list[Mapping[str, Any]] | None = None,
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
            required_evidence_manifest=[dict(item) for item in (required_evidence_manifest or [])],
        )
        result = submit_state_receipt(receipt)
        row = {"receipt": receipt, "organization_recording": result}
        self.records.append(row)
        recorded = (
            result.get("state") == "RECORDED"
            and isinstance(result.get("organization_receipt"), Mapping)
            and bool(result.get("receipt_sha256"))
        )
        if require_return and not recorded:
            raise RuntimeError(str(result.get("reason") or "canonical_organization_record_not_returned"))
        if recorded:
            self.last_state_ref = f"sha256:{result['receipt_sha256']}"
        return row


__all__ = ["CanonicalTransitionCustody", "build_master_records_receipt_set_commitment", "build_state_receipt", "current_hb_creation_reference", "query_state_receipts", "reconstruct_state_receipt", "require_predecessor_master_records_organization_record", LEGACY_PREDECESSOR_RECONSTRUCTION_HELPER, "submit_state_receipt", "sha256_uri"]
