#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_TASK = "DATA-CONTINUATION-STEGCLAW-P4"
ORG_TASK = "ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001"
ORG_VECTOR = "50000000101000"
PACKET_ID = "stegclaw-p4-runtime-profile"
PACKET_REL = Path("spool/organization-local-boundary/ingress") / f"{PACKET_ID}.json"
ORG_RECEIPT_REL = Path("receipts/organization-local-boundary") / f"{PACKET_ID}.json"
OUTPUT_REL = Path("receipts/sovereign-host/stegclaw-p4-resident-execution.latest.json")
TARGETED = Path("scripts/refresh_and_execute_resident_task.py")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def packet() -> dict[str, Any]:
    payload = {
        "subject_task_id": SUBJECT_TASK,
        "subject_repository": "Data-Continuation/StegClaw",
        "runtime_node_profile_id": "runtime-node:data-continuation-stegclaw-p4",
        "purpose": "STEGCLAW_P4_RUNTIME_PATH_ATTRIBUTION",
        "expected_runtime_predicate": "AUTHENTIC_RESIDENT_REQUEST_CONSUMPTION_AND_EXECUTION_RECEIPT_ATTRIBUTABLE_TO_STEGCLAW_PATH",
    }
    return {
        "schema": "stegverse.organization-local-boundary.packet/v1",
        "profile_id": "stegverse.organization-local-intr/v1",
        "direction": "INGRESS",
        "packet_id": PACKET_ID,
        "payload": payload,
        "payload_hash": sha256_uri(payload),
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "carrier_grants_execution_authority": False,
        "canonical_state_change_authorized": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        "transition_basis": {"subject_task_id": SUBJECT_TASK, "authority_effect": "NONE_EVIDENCE_ONLY"},
    }


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required: {path}")
    return value


def verified(receipt: dict[str, Any], expected_packet: dict[str, Any]) -> bool:
    claim = receipt.get("claim_id")
    fence = receipt.get("fencing_token")
    return (
        receipt.get("schema") == "stegverse.organization-local-boundary.receipt/v1"
        and receipt.get("task_id") == ORG_TASK
        and receipt.get("packet_id") == PACKET_ID
        and receipt.get("payload_hash") == expected_packet["payload_hash"]
        and receipt.get("ingress_packet_sha256") == sha256_uri(expected_packet)
        and receipt.get("disposition") == "ACCEPTED_LOCAL_BOUNDARY"
        and receipt.get("credential_authority") == "TV/TVC"
        and receipt.get("github_token_runtime_authority") == "NONE"
        and receipt.get("canonical_state_changed") is False
        and receipt.get("external_side_effect_performed") is False
        and receipt.get("authority_effect") == "NONE"
        and isinstance(fence, int) and fence >= 1
        and isinstance(claim, str) and claim.endswith(f"-G{fence}")
    )


def execute(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    expected = packet()
    ingress = runtime / PACKET_REL
    receipt_path = runtime / ORG_RECEIPT_REL
    ingress.parent.mkdir(parents=True, exist_ok=True)
    if ingress.is_file() and load(ingress) != expected:
        raise RuntimeError("StegClaw P4 ingress packet collision")
    if not receipt_path.is_file():
        ingress.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        runner = runtime / TARGETED
        if not runner.is_file():
            runner = source / TARGETED
        command = [sys.executable, str(runner), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", ORG_TASK, "--cosv-task-vector", ORG_VECTOR]
        completed = subprocess.run(command, cwd=runtime, capture_output=True, text=True, check=False, timeout=1200, env=os.environ.copy())
        if completed.returncode != 0 and not receipt_path.is_file():
            return {"state":"STEGCLAW_P4_RESIDENT_EXECUTION_ATTEMPT_FAILED","returncode":completed.returncode,"stderr_tail":completed.stderr[-1200:]}
    if not receipt_path.is_file():
        return {"state":"STEGCLAW_P4_RESIDENT_EXECUTION_RECEIPT_PENDING"}
    receipt = load(receipt_path)
    if not verified(receipt, expected):
        raise RuntimeError("StegClaw P4 organization-local receipt failed exact verification")
    result = {
        "schema":"stegverse.stegclaw-p4-resident-execution/v1",
        "state":"STEGCLAW_P4_RESIDENT_EXECUTION_OBSERVED",
        "subject_task_id":SUBJECT_TASK,
        "runtime_node_profile_id":"runtime-node:data-continuation-stegclaw-p4",
        "executor_task_id":ORG_TASK,
        "organization_local_receipt_ref":str(ORG_RECEIPT_REL),
        "claim_id":receipt["claim_id"],
        "fencing_token":receipt["fencing_token"],
        "p4_executor_receipt_predicate_satisfied":True,
        "stegclaw_path_attribution":True,
        "activation_effect":False,
        "authority_effect":"NONE_EVIDENCE_ONLY",
    }
    out = runtime / OUTPUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, default=ROOT)
    p.add_argument("--runtime-root", type=Path, default=ROOT)
    args = p.parse_args()
    result = execute(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
