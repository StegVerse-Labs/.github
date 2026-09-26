#!/usr/bin/env python3
"""Run the existing Experiment 3 non-worker consumer only from retained resident input.

This is a selector for the ALREADY AUTHORIZED resident dispatcher, not a session
origin validator, InTr issuer, lease mint, ledger or remote-access endpoint.
An original InTr/ESRL/organization/Master Records gap yields a precise source
predicate and cannot be converted into runtime ALLOW by a caller's request file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOAL = "MIR-SV-CAPABILITY-BOUNDARY-EXPERIMENT-003"
COSV = "50000000100000"
ORIGINAL_WIRE = "ad9b8b8aab2beeea04bff2aac34fd2e7bfa5915133bcaef9209c16de7d9bea68"
SCHEMA = "stegverse.mir-exp3-original-resident-attempt/v1"
REQUEST_REL = Path("control/resident-execution-request.d/mir-exp3-original-001.json")
RESULT_REL = Path("receipts/sovereign-host/mir-exp3-original")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
              "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
HEX = re.compile(r"[0-9a-f]{64}\Z")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def boundary(reason: str, *, request_sha256: str | None = None) -> dict:
    return {"schema": "stegverse.mir-exp3-resident-attempt-result/v1",
            "state": "SOURCE_BOUNDARY", "reason": reason, "task_id": GOAL,
            "cosv_task_vector": COSV, "request_sha256": request_sha256,
            "authentic_intr_disposition_observed": False,
            "runtime_execution_proven": False, "authority_effect": "NONE"}


def consume(source_root: Path, runtime_root: Path) -> dict:
    source, runtime = Path(source_root).resolve(), Path(runtime_root).resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.mir-exp3-resident-attempt-result/v1",
                "state": "NO_REQUEST", "task_id": GOAL,
                "runtime_execution_proven": False, "authority_effect": "NONE"}
    if any(os.environ.get(key, "").lower() not in {"", "0", "false", "no"}
           for key in HOSTED_ENV):
        return boundary("HOSTED_ENVIRONMENT_FORBIDDEN")
    ticket: dict | None = None
    try:
        ticket = json.loads(request_path.read_text(encoding="utf-8"))
        if (not isinstance(ticket, dict)
                or ticket.get("schema") != SCHEMA or ticket.get("task_id") != GOAL
                or ticket.get("cosv_task_vector") != COSV
                or ticket.get("state") != "REQUESTED"
                or ticket.get("credential_authority") != "TV/TVC"
                or ticket.get("request_grants_authority") is not False
                or ticket.get("wire_manifest_sha256") != ORIGINAL_WIRE):
            return boundary("ORIGINAL_RESIDENT_REQUEST_CONTRACT_INVALID")
        digest = ticket.get("request_sha256")
        if not isinstance(digest, str) or not HEX.fullmatch(digest):
            return boundary("ORIGINAL_REQUEST_SHA256_REQUIRED")
        output = runtime / RESULT_REL / (digest + ".json")
        if output.is_file():
            retained = json.loads(output.read_text(encoding="utf-8"))
            if retained.get("request_sha256") != digest:
                return boundary("ORIGINAL_RESULT_IMMUTABLE_COLLISION", request_sha256=digest)
            return {"schema": "stegverse.mir-exp3-resident-attempt-result/v1",
                    "state": "ALREADY_RECORDED", "task_id": GOAL,
                    "request_sha256": digest, "private_result_ref": str(output.relative_to(runtime)),
                    "private_result_sha256": hashlib.sha256(canon(retained)).hexdigest(),
                    "original_state": retained.get("state"),
                    "runtime_execution_proven": retained.get("runtime_execution_proven") is True,
                    "authority_effect": "NONE_READBACK_ONLY"}
        # The existing authenticated host/resident caller owns deposition. The
        # ticket is a selector only: a caller-authored origin cannot issue ALLOW.
        if str(source) not in sys.path:
            sys.path.insert(0, str(source))
        from workers.manifest_state_transition_intr_ingress import (
            validate_request, execute, REQUEST_DIR, IMMUTABLE_DIR,
        )
        root = runtime / REQUEST_DIR / IMMUTABLE_DIR
        matches = list(root.glob("*/" + digest + ".json"))
        if len(matches) != 1 or not matches[0].resolve().is_relative_to(root.resolve()):
            return boundary("ORIGINAL_IMMUTABLE_REQUEST_NOT_UNIQUELY_RETAINED",
                            request_sha256=digest)
        original = json.loads(matches[0].read_text(encoding="utf-8"))
        validated = validate_request(original)
        payload = (validated.get("canonical_manifest") or {}).get("payload") or {}
        publisher = ((validated.get("canonical_manifest") or {}).get("completion") or {}).get("publisher") or {}
        if (validated.get("request_sha256") != digest
                or validated.get("wire_manifest_sha256") != ORIGINAL_WIRE
                or validated.get("canonical_task_id") is not None
                or validated.get("processing_capability") != "ecosystem_diagnostic"
                or validated.get("requires_workercoordinator_claim_fence") is not False
                or payload.get("goal_task_id") != GOAL
                or payload.get("cosv") != COSV or publisher.get("required") is not True):
            return boundary("FROZEN_ORIGINAL_EXPERIMENT_3_REQUEST_MISMATCH",
                            request_sha256=digest)
        # Calls ONLY the already merged native non-worker consumer. That consumer
        # must derive ORIGINAL org/MR-closed InTr+binding receipts and check the
        # current authorized ESRL before it may execute the unchanged manifest.
        result = execute(runtime, validated)
        state = result.get("state")
        is_live = (state == "PROCESSING_RECORDED_PUBLISHER_REQUIRED"
                   and result.get("disposition") == "ALLOW"
                   and result.get("organization_receipt_sha256")
                   and result.get("diagnostic_master_records_receipt_sha256"))
        record = {"schema": "stegverse.mir-exp3-resident-attempt-result/v1",
                  "state": "PROCESSING_ALLOW_PUBLISHER_PENDING" if is_live else "SOURCE_PROFILE_DISPOSITION",
                  "task_id": GOAL, "cosv_task_vector": COSV, "request_sha256": digest,
                  "wire_manifest_sha256": ORIGINAL_WIRE,
                  "producer_result": result, "runtime_execution_proven": bool(is_live),
                  "authority_effect": "NONE_RESIDENT_RESULT_RETENTION_ONLY"}
        # A correctable SOURCE_ONLY DENY must be re-evaluated after the existing
        # owner repairs native admission. Caching it as the request's terminal
        # result would prevent progression and misclassify source evidence.
        # The existing ingress already retains its exact write-once source disposition.
        terminal_local = result.get("terminal") is True
        if not is_live and not terminal_local:
            return {"schema": record["schema"], "state": "SOURCE_PROFILE_DISPOSITION",
                    "task_id": GOAL, "cosv_task_vector": COSV,
                    "request_sha256": digest, "wire_manifest_sha256": ORIGINAL_WIRE,
                    "original_disposition": result.get("disposition"),
                    "first_failed_predicate": result.get("failed_predicate"),
                    "source_disposition_ref": result.get("source_disposition_ref"),
                    "authentic_intr_disposition_observed": False,
                    "runtime_execution_proven": False,
                    "authority_effect": "NONE_SOURCE_PROFILE_ONLY"}
        if terminal_local and not is_live:
            record["state"] = "ADMITTED_DIAGNOSTIC_LOCAL_FAIL_CLOSED"
        output.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        with output.open("x", encoding="utf-8") as handle:
            handle.write(raw)
        return {"schema": record["schema"], "state": record["state"],
                "task_id": GOAL, "cosv_task_vector": COSV, "request_sha256": digest,
                "original_disposition": result.get("disposition"),
                "first_failed_predicate": result.get("failed_predicate"),
                "authentic_intr_disposition_observed": result.get("authentic_intr_disposition_observed", False),
                "runtime_execution_proven": bool(is_live),
                "private_result_ref": str(output.relative_to(runtime)),
                "private_result_sha256": hashlib.sha256(canon(record)).hexdigest(),
                "authority_effect": "NONE_RESIDENT_RESULT_RETENTION_ONLY"}
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return boundary("ORIGINAL_RESIDENT_ATTEMPT_BOUNDARY:" + str(exc),
                        request_sha256=ticket.get("request_sha256") if isinstance(ticket, dict) else None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST", "ALREADY_RECORDED", "PROCESSING_ALLOW_PUBLISHER_PENDING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
