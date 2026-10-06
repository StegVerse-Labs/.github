#!/usr/bin/env python3
"""`stegverse-labs.governance` -- decide a governance request that crossed into this organization.

StegCore is a StegVerse-Labs repository, so a governance decision is made here,
inside the organization that owns the evaluator, and nowhere else. Another
organization does not import StegCore and decide for itself: it emits the
request through its own `.github` egress, the request crosses Interlock/InTr on
the federation mesh, and this organization's `.github` receives it. The answer
returns the same way.

The kernel runs this adapter for a packet addressed to `stegverse-labs.governance`
and carries its result back to the origin on the acknowledgement. The decision
is the transition that occurred here, so it is recorded here, at both ledger
levels -- the repository receipt first and the organization receipt consuming
it -- under `organization_scope_rule`. Organization records are the custody of
that decision; nothing here submits it anywhere else or waits on anything.

A request this adapter cannot evaluate is still decided: FAIL_CLOSED, naming
why, and recorded. A refusal is a disposition, not an absence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ORGANIZATION = "StegVerse-Labs"
SERVICE_ID = "stegverse-labs.governance"
REQUEST_SCHEMA = "stegverse.org-governance-decision-request/v1"
DECISION_SCHEMA = "stegverse.org-governance-decision/v1"
DECISION_AUTHORITY = "stegcore.steggate.evaluate_admissibility"
DECISION_AUTHORITY_REPOSITORY = "StegVerse-Labs/StegCore"
TRANSITION_CLASS = "ORGANIZATION_GOVERNANCE_DECISION"


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate(request: Mapping[str, Any]) -> dict[str, Any]:
    """StegGate's disposition for the request, or FAIL_CLOSED naming why there is none.

    No evaluator is substituted. Without StegCore there is no decision to make,
    and the request is decided FAIL_CLOSED rather than guessed.
    """
    try:
        from stegcore.steggate import AdmissibilityRequest, evaluate_admissibility
    except ImportError:
        return {"disposition": "FAIL_CLOSED", "reason": "GOVERNANCE_RUNTIME_STEGCORE_UNAVAILABLE",
                "evaluation": None}
    try:
        admissibility = AdmissibilityRequest(**dict(request))
    except Exception as exc:  # the request's shape is the requester's, not ours to repair
        return {"disposition": "FAIL_CLOSED",
                "reason": "GOVERNANCE_REQUEST_NOT_EVALUABLE:" + type(exc).__name__,
                "evaluation": None}
    body = evaluate_admissibility(admissibility).model_dump(mode="json")
    disposition = body.get("disposition")
    if disposition not in {"ALLOW", "DENY", "FAIL_CLOSED"}:
        return {"disposition": "FAIL_CLOSED",
                "reason": "GOVERNANCE_EVALUATOR_RETURNED_NO_DISPOSITION", "evaluation": body}
    return {"disposition": disposition, "reason": body.get("canonical_three_layer_reason"),
            "evaluation": body}


def decide(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Decide the governance request a packet carries."""
    if (packet.get("destination") or {}).get("service") != SERVICE_ID:
        raise SystemExit("wrong-governance-destination")
    payload = packet.get("payload") or {}
    body = payload.get("body") or {}
    request = body.get("governance_request")
    declared = body.get("governance_request_sha256")
    decision: dict[str, Any] = {
        "schema": DECISION_SCHEMA,
        "service_id": SERVICE_ID,
        "deciding_organization": ORGANIZATION,
        "decision_authority": DECISION_AUTHORITY,
        "decision_authority_repository": DECISION_AUTHORITY_REPOSITORY,
        "request_packet_id": packet.get("packet_id"),
        "origin_organization": (packet.get("origin") or {}).get("org"),
        "sdk_request_sha256": body.get("sdk_request_sha256"),
        "governance_request_sha256": declared,
        "external_side_effect": False,
        "authority_effect": "NONE_DECISION_ONLY",
    }
    if body.get("schema") != REQUEST_SCHEMA:
        decision.update(disposition="FAIL_CLOSED", evaluation=None,
                        reason="GOVERNANCE_REQUEST_SCHEMA_NOT_RECEIVED:" + str(body.get("schema")))
    elif not isinstance(request, dict):
        decision.update(disposition="FAIL_CLOSED", evaluation=None,
                        reason="GOVERNANCE_REQUEST_ABSENT")
    elif hashlib.sha256(canon(request)).hexdigest() != declared:
        # The digest binds the request the origin recorded emitting to the one
        # decided here. A request that does not recompute is not that request.
        decision.update(disposition="FAIL_CLOSED", evaluation=None,
                        reason="GOVERNANCE_REQUEST_DIGEST_MISMATCH")
    else:
        decision.update(evaluate(request))
    return decision


def record(packet: Mapping[str, Any], decision: Mapping[str, Any]) -> dict[str, str]:
    """Append the decision at both ledger levels: repository first, organization consuming it."""
    transition_id = TRANSITION_CLASS + ":" + hashlib.sha256(
        str(packet.get("packet_id")).encode()).hexdigest()[:24]
    predecessor = "sha256:" + str(decision.get("governance_request_sha256"))
    successor = sha(dict(decision))
    evidence = {"request_packet_id": packet.get("packet_id"),
                "origin_organization": decision.get("origin_organization"),
                "decision": dict(decision)}
    completed = subprocess.run(
        [sys.executable, str(ROOT / ".stegverse/transition-ledger/emit.py"),
         "--transition-id", transition_id, "--transition-class", TRANSITION_CLASS,
         "--predecessor-state-sha256", predecessor, "--successor-state-sha256", successor,
         "--evidence-json", json.dumps(evidence, sort_keys=True), "--authority-effect", "NONE"],
        cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise SystemExit("governance-decision-repository-receipt-failed:"
                         + (completed.stderr or completed.stdout).strip()[-300:])
    repository_receipt = json.loads(completed.stdout.strip().splitlines()[-1])
    organization_ledger = _module("aggregate_repo_transition",
                                  "resident-runtime/aggregate_repo_transition.py")
    organization_receipt = organization_ledger.aggregate_transition(
        repository_receipt, org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=predecessor, successor_org_state_sha256=successor,
        boundary_evidence={"service_id": SERVICE_ID, "transition_class": TRANSITION_CLASS,
                           "disposition": decision.get("disposition"),
                           "request_packet_id": packet.get("packet_id")},
        authority_effect="NONE")
    return {"repository_receipt_sha256": repository_receipt["receipt_sha256"],
            "organization_receipt_sha256": organization_receipt["receipt_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    decision = decide(packet)
    receipts = record(packet, decision)
    result = {**decision, **receipts, "records_authority": "ORGANIZATION_RECORDS_ONLY"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
