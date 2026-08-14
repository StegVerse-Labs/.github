#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "control" / "heartbeat-documentation-semantics-audit.json"
HANDOFF = ROOT / "docs" / "HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    handoff = HANDOFF.read_text(encoding="utf-8")

    require(audit.get("schema") == "stegverse.heartbeat-documentation-semantics-audit/v2", "audit schema mismatch", errors)
    require(audit.get("credential_authority") == "TV/TVC", "credential authority must be TV/TVC", errors)
    require(audit.get("github_token_runtime_authority") is False, "GitHub-token runtime authority must be false", errors)

    inv = audit.get("canonical_invariants") or {}
    expected_false = (
        "heartbeat_application_payload",
        "heartbeat_dispatches_tasks",
        "heartbeat_issues_claims_or_fences",
        "heartbeat_routes_communications",
        "heartbeat_grants_authority",
        "heartbeat_is_master_records_transport",
        "fixed_universal_frequency",
    )
    for key in expected_false:
        require(inv.get(key) is False, f"{key} must be false", errors)

    require(inv.get("heartbeat_role") == "CARRIER_SYNCHRONIZATION_SIGNAL", "heartbeat role mismatch", errors)
    require(inv.get("carrier_frequency_rule") == "GATE_PASSBAND_DERIVED", "carrier frequency must be gate/passband derived", errors)
    require(
        inv.get("communication_object") == ["manifest_packet", "expiration_wrapper", "data_packet"],
        "communication object must be manifest+expiration+data",
        errors,
    )
    require(
        set(inv.get("terminal_triggers") or []) == {"ENDPOINT_OBJECTIVE_COMPLETE", "EXPIRED"},
        "terminal triggers must be completion|expiration",
        errors,
    )
    require(inv.get("terminal_object") == "MASTER_RECORDS_PACKET", "terminal object mismatch", errors)
    require(inv.get("transition_table_end_of_life") == "MASTER_RECORDS", "Transition Table EOL must be Master Records", errors)

    required_handoff_phrases = (
        "carrier/synchronization signal",
        "manifest packet + expiration wrapper + data packet",
        "Master Records is the End-Of-Life state/destination for every Transition Table element",
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
        "stegverse:capability:heartbeat-carrier:v1",
        "stegverse:capability:worker-control-plane:v1",
        "stegverse:capability:manifest-communication:v1",
        "stegverse:capability:master-records-terminal-custody:v1",
    )
    for phrase in required_handoff_phrases:
        require(phrase in handoff, f"canonical handoff missing phrase: {phrase}", errors)

    # The audit must keep runtime mutation outside this documentation contract.
    require(audit.get("runtime_refactor_owner") == "StegVerse-Labs/.github#122", "runtime refactor owner must remain #122", errors)
    require(audit.get("historical_evidence_rewrite_allowed") is False, "historical evidence rewrite must remain false", errors)

    if errors:
        for error in errors:
            print(f"HEARTBEAT_CARRIER_CONTRACT_INVALID:{error}")
        return 1

    print(
        "HEARTBEAT_CARRIER_CONTRACT_PASS "
        "heartbeat=carrier_only communication=manifest+expiration+data "
        "eol=master_records frequency=gate_derived credential_authority=TV/TVC"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
