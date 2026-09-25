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
    if value.get("reconcile_master_records", False) not in {True, False}:
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


def consume(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source, runtime = Path(source_root).resolve(), Path(runtime_root).resolve()
    path = runtime / REQUEST_REL
    if not path.is_file():
        return {"schema": "stegverse.organization-custody-readback-result/v1",
                "state": "NO_REQUEST", "authority_effect": "NONE"}
    if any(os.environ.get(x, "").strip().lower() not in {"", "0", "false", "no"} for x in HOSTED_ENV):
        return {"schema": "stegverse.organization-custody-readback-result/v1",
                "state": "BOUNDARY", "reason": "HOSTED_ENVIRONMENT_FORBIDDEN",
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
                "master_records_reconstruction": "NOT_QUERIED",
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
    return 0 if result["state"] in {"RECORDED_LOCAL_READBACK", "NO_REQUEST"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
