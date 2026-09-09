#!/usr/bin/env python3
"""Validate exact physical HIL browser evidence and build canonical request-consumption evidence.

This module does not discover, synthesize, or infer runtime evidence. The caller must
supply the exact JSON artifact exported by the current-iPhone HIL browser receiver.
Screenshots, CI, source state, and deployment state are not accepted as substitutes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
REQUEST_ID = "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002"
REQUEST_SHA256 = "6bf940fb920f672111ba1040fd0bf9bf7016d6bf032bbcfd164a1a2347ee7038"
MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TRANSITION = "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED"
CLAIM_RE = re.compile(r"^SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G([0-9]+)$")
HEX64_RE = re.compile(r"^[a-f0-9]{64}$")
CONTEXT_RE = re.compile(r"^ctx_[a-f0-9]{32}$")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def validate_request(request: dict[str, Any]) -> str:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": REQUEST_ID,
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": "scripts/refresh_and_execute_resident_task.py",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PARTICIPANT_INTAKE",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"HIL resident request {key} mismatch")
    digest = stable_hash(request)
    if digest != REQUEST_SHA256:
        raise RuntimeError("HIL resident request stable hash mismatch")
    return digest


def validate_browser_evidence(evidence: dict[str, Any], request_hash: str) -> dict[str, Any]:
    # These are fields emitted by the service-worker activation-result artifact itself.
    # Credential/HB/GitHub boundaries are taken from the exact canonical request and are
    # not fabricated into the component artifact by this intake.
    required = {
        "schema": "stegos.hil_browser_receiver_activation_result/v1",
        "state": "BROWSER_HIL_LOCAL_READY_OBSERVED",
        "resident_request_id": REQUEST_ID,
        "resident_request_sha256": request_hash,
        "task_id": TASK_ID,
        "transition": TRANSITION,
        "journal_replay_state": "PASS",
        "browser_receiver_execution_observed": True,
        "installed_native_app_required": False,
        "second_claim_minted": False,
        "request_consumption_claimed": False,
        "authority_effect": "NONE_COMPONENT_EVIDENCE_ONLY",
    }
    for key, expected in required.items():
        if evidence.get(key) != expected:
            raise RuntimeError(f"HIL browser evidence {key} mismatch")

    context_id = evidence.get("browser_context_id")
    if not isinstance(context_id, str) or not CONTEXT_RE.fullmatch(context_id):
        raise RuntimeError("HIL browser context id invalid")

    fence = evidence.get("fencing_token")
    if not isinstance(fence, int) or fence <= 24:
        raise RuntimeError("HIL browser fence must be greater than G24")
    claim_id = evidence.get("claim_id")
    match = CLAIM_RE.fullmatch(str(claim_id or ""))
    if not match or int(match.group(1)) != fence:
        raise RuntimeError("HIL browser claim/fence binding mismatch")

    for key in ("execution_entry_sha256", "journal_replay_tail_sha256"):
        value = evidence.get(key)
        if not isinstance(value, str) or not HEX64_RE.fullmatch(value):
            raise RuntimeError(f"HIL browser evidence {key} invalid")

    reused = evidence.get("continuation_reused_existing_checkout")
    if reused not in {True, False}:
        raise RuntimeError("HIL browser continuation reuse flag missing")
    return evidence


def build_consumption_receipt(request: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    request_hash = validate_request(request)
    validated = validate_browser_evidence(evidence, request_hash)
    evidence_hash = stable_hash(validated)
    return {
        "schema": "stegverse.hil-resident-execution-request-consumption/v1",
        "state": "COMPLETED",
        "request_id": REQUEST_ID,
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "mode": MODE,
        "route_materialization": {
            "schema": "stegverse.hil-intr-route-config-materialization/v1",
            "state": "NOT_REQUIRED_SAME_DEVICE",
            "reason": "physical current-iPhone portable browser successor produced exact bound local-ready evidence",
            "public_gateway_required_for_lease_open": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE",
        },
        "command": [],
        "execution_returncode": 0,
        "execution_result_observed": True,
        "execution_result": validated,
        "runtime_execution_attempted": True,
        "runtime_execution_surface": "CURRENT_USER_IPHONE_BROWSER",
        "browser_component_evidence_observed": True,
        "browser_component_evidence_sha256": evidence_hash,
        "browser_context_id": validated["browser_context_id"],
        "claim_id": validated["claim_id"],
        "fencing_token": validated["fencing_token"],
        "terminal_hil_transition": TRANSITION,
        "terminal_hil_transition_observed": True,
        "broader_hil_lifecycle_complete": False,
        "retry_allowed": False,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PARTICIPANT_INTAKE",
        "second_machine_required": False,
        "public_gateway_required_for_lease_open": False,
        "g18_completion_required": False,
        "network_source_fetch_performed": False,
        "evidence_transport": "EXACT_USER_EXPORTED_COMPONENT_JSON",
        "screenshot_substitution_allowed": False,
        "component_claimed_request_consumption": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate exact HIL browser evidence and emit canonical consumption JSON")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_consumption_receipt(load_json(args.request), load_json(args.evidence))
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
