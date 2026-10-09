#!/usr/bin/env python3
"""Optional resident-local organization custody readback via existing dispatcher.

A request must be deposited in the already-authorized *resident runtime* by
its existing trusted caller. A source-tree request cannot trigger readback.
The dispatcher is not a remote-access service and this consumer never treats
a caller-authored origin string as session or TV/TVC attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "ORGANIZATION-BATCH-CUSTODY-REPLAY-001"
COSV = "10000000100000"
MODE = "READ_ONLY_ORGANIZATION_CUSTODY_REPLAY"
REQUEST_REL = Path("control/resident-execution-request.d/organization-custody-readback-001.json")
OUTPUT_REL = Path("receipts/sovereign-host/organization-custody-readback")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
              "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
ID = re.compile(r"[A-Za-z0-9_.:/-]{1,150}\Z")
SCHEMA = "stegverse.organization-custody-readback-request/v1"
ATTEMPT_SCHEMA = "stegverse.organization-custody-readback-governed-attempt/v1"
ATTEMPT_REL = Path("runtime-state/organization-custody-readback/governed-attempt.json")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _load_readback(source: Path, runtime: Path):
    module_path = runtime / "resident-runtime/organization_custody_readback.py"
    if not module_path.is_file():
        module_path = source / "resident-runtime/organization_custody_readback.py"
    if not module_path.is_file():
        raise ValueError("READBACK_MODULE_NOT_MATERIALIZED")
    module_dir = str(module_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    spec = importlib.util.spec_from_file_location("existing_org_custody_readback", module_path)
    if spec is None or spec.loader is None:
        raise ValueError("READBACK_MODULE_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_request(value: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    if value.get("schema") != SCHEMA or value.get("task_id") != TASK_ID:
        raise ValueError("READBACK_REQUEST_TASK_IDENTITY_INVALID")
    if value.get("cosv_task_vector") != COSV or value.get("mode") != MODE:
        raise ValueError("READBACK_REQUEST_OWNER_OR_MODE_INVALID")
    if value.get("state") != "REQUESTED":
        raise ValueError("READBACK_REQUEST_NOT_REQUESTED")
    if value.get("credential_authority") != "TV/TVC" or value.get("request_grants_authority") is not False:
        raise ValueError("READBACK_REQUEST_AUTHORITY_BOUNDARY_INVALID")
    request_id = value.get("request_id")
    correlations = value.get("correlation_ids")
    if not isinstance(request_id, str) or not ID.fullmatch(request_id):
        raise ValueError("READBACK_REQUEST_ID_INVALID")
    if (not isinstance(correlations, list) or not 1 <= len(correlations) <= 16
            or any(not isinstance(x, str) or not ID.fullmatch(x) for x in correlations)
            or len(set(correlations)) != len(correlations)):
        raise ValueError("READBACK_CORRELATION_SCOPE_INVALID")
    if type(value.get("reconcile_master_records", False)) is not bool:
        raise ValueError("MASTER_RECORDS_RECONCILIATION_MODE_INVALID")
    return request_id, tuple(correlations)


def _private_write(path: Path, value: dict[str, Any]) -> str:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = canon(value)
    digest = hashlib.sha256(raw).hexdigest()
    if path.exists():
        if path.read_bytes() != raw + b"\n":
            raise ValueError("READBACK_REQUEST_REUSED_WITH_DIFFERENT_HEAD")
        return digest
    fd, tmp = tempfile.mkstemp(prefix=".readback-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(raw)
            output.write(b"\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return digest


#: Master Records boundary migration: governed attempts written before the rename carry these legacy fields.
LEGACY_INTR_ORGANIZATION_RECORD_FIELD = "intr_master_records_closure"
LEGACY_PREDECESSOR_ORGANIZATION_RECORD_FIELD = "predecessor_master_records_closure"


def _recorded_master_records(value: Any, label: str) -> dict[str, Any]:
    """The submit_state_receipt() result, admitted on its verified Organization receipt.

    The Organization ledger append is the transition's runtime reality. The
    receipt is read back with organization_batch_custody.verified_organization_record();
    Master Records reconstruction fields on the result are evidence only and
    never consulted (master_records_may_gate_organization_runtime_reality=false).
    A refusal is an OrganizationReceiptRefused (a ValueError), which the caller
    turns into a FAIL_CLOSED result with nothing committed.
    """
    if not isinstance(value, dict):
        raise ValueError(label + "_MISSING")
    resident = str(ROOT / "resident-runtime")
    if resident not in sys.path:
        sys.path.insert(0, resident)
    from importlib import import_module
    custody = import_module("organization_batch_custody")
    row = custody.verified_organization_record(None, value)
    return {**value, "verified_organization_receipt_sha256": row["receipt_sha256"],
            custody.READBACK_CUSTODY_BASIS_KEY: custody.readback_custody_basis(row)}


def _governed_attempt(source: Path, runtime: Path, attempt: dict[str, Any]) -> dict[str, Any]:
    if attempt.get("schema") != ATTEMPT_SCHEMA:
        raise ValueError("GOVERNED_ATTEMPT_SCHEMA_INVALID")
    if attempt.get("task_id") != TASK_ID or attempt.get("cosv_task_vector") != COSV:
        raise ValueError("GOVERNED_ATTEMPT_OWNER_INVALID")
    if attempt.get("presented_to_intr") is not True:
        raise ValueError("GOVERNED_ATTEMPT_NOT_PRESENTED_TO_INTR")
    disposition = attempt.get("intr_disposition")
    if disposition not in {"ALLOW", "DENY", "FAIL_CLOSED"}:
        raise ValueError("GOVERNED_ATTEMPT_DISPOSITION_INVALID")
    if attempt.get("authentic_intr_disposition_observed") is not True:
        raise ValueError("GOVERNED_ATTEMPT_INTR_EVIDENCE_NOT_OBSERVED")
    intr_closure = _recorded_master_records(
        attempt.get("intr_master_records_organization_record", attempt.get(LEGACY_INTR_ORGANIZATION_RECORD_FIELD)),
        "INTR_MASTER_RECORDS_ORGANIZATION_RECORD")
    predecessor = _recorded_master_records(
        attempt.get("predecessor_master_records_organization_record", attempt.get(LEGACY_PREDECESSOR_ORGANIZATION_RECORD_FIELD)),
        "PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD")
    request = attempt.get("readback_request")
    if not isinstance(request, dict):
        raise ValueError("GOVERNED_ATTEMPT_READBACK_REQUEST_MISSING")
    request_id, _ = _validate_request(request)
    if attempt.get("request_id") != request_id:
        raise ValueError("GOVERNED_ATTEMPT_REQUEST_ID_MISMATCH")
    if disposition != "ALLOW":
        return {
            "schema": "stegverse.organization-custody-readback-result/v1",
            "state": disposition, "disposition": disposition,
            "task_id": TASK_ID, "cosv_task_vector": COSV, "request_id": request_id,
            "failed_predicate": attempt.get("failed_predicate"),
            "intr_master_records_receipt_sha256": intr_closure["receipt_sha256"],
            "predecessor_master_records_receipt_sha256": predecessor["receipt_sha256"],
            "intr_organization_receipt_sha256": intr_closure["verified_organization_receipt_sha256"],
            "predecessor_organization_receipt_sha256": predecessor["verified_organization_receipt_sha256"],
            "intr_organization_readback_custody_basis": intr_closure["organization_readback_custody_basis"],
            "predecessor_organization_readback_custody_basis": predecessor["organization_readback_custody_basis"],
            "readback_executed": False,
            "authority_effect": "NONE_GOVERNED_DISPOSITION_PRESERVED",
        }
    path = runtime / REQUEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n"
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != request:
        raise ValueError("GOVERNED_ATTEMPT_REQUEST_COLLISION")
    path.write_text(raw, encoding="utf-8")
    result = consume(source, runtime, _from_governed_attempt=True)
    result["governed_intr_disposition"] = "ALLOW"
    result["intr_master_records_receipt_sha256"] = intr_closure["receipt_sha256"]
    result["predecessor_master_records_receipt_sha256"] = predecessor["receipt_sha256"]
    result["intr_organization_receipt_sha256"] = intr_closure["verified_organization_receipt_sha256"]
    result["predecessor_organization_receipt_sha256"] = predecessor["verified_organization_receipt_sha256"]
    result["intr_organization_readback_custody_basis"] = intr_closure["organization_readback_custody_basis"]
    result["predecessor_organization_readback_custody_basis"] = predecessor["organization_readback_custody_basis"]
    return result


def consume(source_root: Path, runtime_root: Path, *, _from_governed_attempt: bool = False) -> dict[str, Any]:
    source, runtime = Path(source_root).resolve(), Path(runtime_root).resolve()
    if not _from_governed_attempt:
        attempt_path = runtime / ATTEMPT_REL
        if attempt_path.is_file():
            try:
                attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
                if not isinstance(attempt, dict):
                    raise ValueError("GOVERNED_ATTEMPT_MUST_BE_OBJECT")
                return _governed_attempt(source, runtime, attempt)
            except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
                return {
                    "schema": "stegverse.organization-custody-readback-result/v1",
                    "state": "FAIL_CLOSED", "disposition": "FAIL_CLOSED",
                    "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                    "task_id": TASK_ID, "cosv_task_vector": COSV,
                    "failed_predicate": "GOVERNED_MANIFEST_ATTEMPT_BINDING_AND_CUSTODY",
                    "authority_effect": "NONE_FAIL_CLOSED",
                }
    path = runtime / REQUEST_REL
    if not path.is_file():
        return {"schema": "stegverse.organization-custody-readback-result/v1",
                "state": "NO_REQUEST", "attempted": False, "authority_effect": "NONE"}
    if (not _from_governed_attempt and
            any(os.environ.get(x, "").strip().lower() not in {"", "0", "false", "no"} for x in HOSTED_ENV)):
        return {"schema": "stegverse.organization-custody-readback-result/v1",
                "state": "BOUNDARY", "reason": "LEGACY_OPTIONAL_DIAGNOSTIC_HOSTED_ENVIRONMENT",
                "runtime_execution_proven": False, "authority_effect": "NONE"}
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(request, dict):
            raise ValueError("READBACK_REQUEST_MUST_BE_OBJECT")
        request_id, correlations = _validate_request(request)
        request_sha = "sha256:" + hashlib.sha256(canon(request)).hexdigest()
        private_path = runtime / OUTPUT_REL / (request_sha[7:] + ".json")
        if private_path.is_file():
            previous_bytes = private_path.read_bytes()
            previous = json.loads(previous_bytes)
            if (previous.get("request_id") != request_id
                    or previous.get("request_sha256") != request_sha
                    or previous.get("state") != "VERIFIED_LOCAL_READBACK"):
                raise ValueError("EXISTING_READBACK_ARTIFACT_REQUEST_CONFLICT")
            return {
                "schema": "stegverse.organization-custody-readback-result/v1",
                "state": "ALREADY_CONSUMED", "request_id": request_id,
                "request_sha256": request_sha,
                "task_id": TASK_ID, "cosv_task_vector": COSV,
                "head_receipt_sha256": previous["head_receipt_sha256"],
                "receipt_count": previous["receipt_count"],
                "match_count": previous["match_count"],
                "private_artifact_sha256": "sha256:" + hashlib.sha256(canon(previous)).hexdigest(),
                "private_artifact_location": str(OUTPUT_REL / (request_sha[7:] + ".json")),
                "master_records_reconstruction": previous.get("master_records_reconstruction", "NOT_QUERIED"),
                "runtime_admission_inferred": False,
                "authority_effect": "NONE_READBACK_ONLY",
            }
        module = _load_readback(source, runtime)
        # Reuse existing resident ledger-root configuration, not a request path.
        result = module.readback(module.org.ledger_root(),
                                 correlation_ids=correlations, include_exact=True)
        if request.get("reconcile_master_records") is True:
            from urllib.parse import urlencode
            from urllib.request import Request, urlopen
            workers = str(runtime / "workers") if (runtime / "workers").is_dir() else str(source / "workers")
            if workers not in sys.path:
                sys.path.insert(0, workers)
            from canonical_state_transition_custody import _configuration, _endpoint_allowed
            endpoint, token, timeout = _configuration()
            if not endpoint or not token or not _endpoint_allowed(endpoint):
                raise ValueError("MASTER_RECORDS_AUTHENTIC_CONFIGURATION_NOT_AVAILABLE")
            base = endpoint.removesuffix("/api/master-records/state-transitions")
            def get_json(path: str, parameters: dict[str, str]) -> dict[str, Any]:
                url = base + path + (("?" + urlencode(parameters)) if parameters else "")
                http_request = Request(url, method="GET", headers={
                    "Authorization": "Bearer " + token, "Accept": "application/json",
                })
                try:
                    with urlopen(http_request, timeout=timeout) as response:
                        return json.loads(response.read().decode("utf-8"))
                except Exception as exc:
                    raise ValueError("MASTER_RECORDS_AUTHENTIC_QUERY_FAILED:" + type(exc).__name__) from exc
            comparison = module.reconcile_master_records(result, get_json=get_json)
            result["master_records_reconstruction"] = comparison["state"]
            result["master_records_comparison"] = comparison
        latest = {
            "schema": "stegverse.organization-custody-readback-result/v1",
            "state": "RECORDED_LOCAL_READBACK",
            "request_id": request_id,
            "request_sha256": "sha256:" + hashlib.sha256(canon(request)).hexdigest(),
            "task_id": TASK_ID,
            "cosv_task_vector": COSV,
            "head_receipt_sha256": result["head_receipt_sha256"],
            "receipt_count": result["receipt_count"],
            "batch_count": result["batch_count"],
            "match_count": result["match_count"],
            "matching_receipt_hashes": [
                item["organization_receipt_sha256"] for item in result["matching_transitions"]
            ],
            "complete_organization_chain": result["complete_organization_chain"],
            "all_source_digests_and_required_evidence": result["all_source_digests_and_required_evidence"],
            "master_records_reconstruction": result["master_records_reconstruction"],
            "master_records_matching_transition_count": sum(
                x["state"] == "MATCHING_INDEPENDENT_RECONSTRUCTION_PASS"
                for x in result.get("master_records_comparison", {}).get("canonical_transition_results", [])
            ),
            "runtime_admission_inferred": False,
            "session_origin_authenticated_by_this_consumer": False,
            "private_exact_artifact_requires_authorized_return_transport": True,
            "authority_effect": "NONE_READBACK_ONLY",
        }
        full = dict(result)
        full["request_id"] = request_id
        full["request_sha256"] = latest["request_sha256"]
        digest = _private_write(runtime / OUTPUT_REL / (latest["request_sha256"][7:] + ".json"), full)
        latest["private_artifact_sha256"] = "sha256:" + digest
        latest["private_artifact_location"] = str(OUTPUT_REL / (latest["request_sha256"][7:] + ".json"))
        return latest
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        return {"schema": "stegverse.organization-custody-readback-result/v1",
                "state": "BOUNDARY", "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                "task_id": TASK_ID, "cosv_task_vector": COSV,
                "next_action": "REPAIR_EXACT_RESIDENT_SOURCE_OR_REQUEST_AND_RETRY_SAME_EXISTING_OWNER",
                "master_records_reconstruction": "NOT_QUERIED",
                "runtime_execution_proven": False, "authority_effect": "NONE_READBACK_ONLY"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"RECORDED_LOCAL_READBACK", "ALREADY_CONSUMED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
