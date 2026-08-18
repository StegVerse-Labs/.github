#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "control" / "heartbeat-documentation-semantics-audit.json"
HANDOFF = ROOT / "docs" / "HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md"
RUNTIME_CONTRACT = ROOT / "control" / "runtime-separation-contract.json"
CONTINUITY_CONTRACT = ROOT / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    handoff = HANDOFF.read_text(encoding="utf-8")
    runtime = json.loads(RUNTIME_CONTRACT.read_text(encoding="utf-8"))
    continuity = json.loads(CONTINUITY_CONTRACT.read_text(encoding="utf-8"))

    require(audit.get("schema") == "stegverse.heartbeat-documentation-semantics-audit/v3", "audit schema mismatch", errors)
    require(audit.get("credential_authority") == "TV/TVC", "credential authority must be TV/TVC", errors)
    require(audit.get("github_token_runtime_authority") is False, "GitHub-token runtime authority must be false", errors)

    inv = audit.get("canonical_invariants") or {}
    for key in (
        "heartbeat_application_payload",
        "heartbeat_dispatches_tasks",
        "heartbeat_issues_claims_or_fences",
        "heartbeat_routes_communications",
        "heartbeat_grants_authority",
        "heartbeat_is_master_records_transport",
        "worker_or_task_gating",
        "admission_gating",
        "claim_or_fence_gating",
        "route_or_credential_gating",
        "observation_is_causal",
    ):
        require(inv.get(key) is False, f"{key} must be false", errors)

    require(inv.get("heartbeat_role") == "CARRIER_SYNCHRONIZATION_SIGNAL", "heartbeat role mismatch", errors)
    require(inv.get("carrier_progression_dependency") == "OSCILLATOR_ONLY", "heartbeat progression must depend only on oscillator", errors)
    require(inv.get("phase_travel_time_ms") == 10, "heartbeat phase travel time must be 10 ms", errors)
    require(inv.get("reference_increment_interval_ms") == 10, "heartbeat reference interval must be 10 ms", errors)
    require(inv.get("reference_frequency_hz") == 100, "heartbeat reference frequency must be 100 Hz", errors)
    require(inv.get("carrier_frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL", "carrier frequency rule mismatch", errors)
    require(inv.get("persisted_state_is_sample_only") is True, "persisted heartbeat state must be a sample only", errors)

    osc = runtime.get("carrier_oscillator") or {}
    require(runtime.get("schema") == "stegverse.heartbeat-runtime-separation-contract/v2", "runtime contract schema mismatch", errors)
    require(osc.get("phase_travel_time_ms") == 10, "runtime oscillator phase travel mismatch", errors)
    require(osc.get("progression_dependency") == "OSCILLATOR_ONLY", "runtime progression dependency mismatch", errors)
    require(osc.get("worker_or_task_gating") is False, "worker/task may not gate heartbeat", errors)
    require(osc.get("observation_is_causal") is False, "observation may not cause heartbeat", errors)

    cont_osc = continuity.get("oscillator") or {}
    require(continuity.get("continuity_model") == "INDEPENDENT_OSCILLATOR_CONTINUITY", "continuity model mismatch", errors)
    require(cont_osc.get("phase_travel_time_ms") == 10, "continuity oscillator phase travel mismatch", errors)
    require(cont_osc.get("progression_dependency") == "OSCILLATOR_ONLY", "continuity progression dependency mismatch", errors)
    require(cont_osc.get("worker_or_task_gating") is False, "continuity worker/task gating must be false", errors)

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
        "10 ms",
        "OSCILLATOR_ONLY",
        "observation does not cause",
        "manifest packet + expiration wrapper + data packet",
        "Master Records is the End-Of-Life state/destination for every Transition Table element",
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
    )
    for phrase in required_handoff_phrases:
        require(phrase in handoff, f"canonical handoff missing phrase: {phrase}", errors)

    require(audit.get("runtime_refactor_owner") == "StegVerse-Labs/.github#122", "runtime refactor owner must remain #122", errors)
    require(audit.get("historical_evidence_rewrite_allowed") is False, "historical evidence rewrite must remain false", errors)

    if errors:
        for error in errors:
            print(f"HEARTBEAT_CARRIER_CONTRACT_INVALID:{error}")
        return 1

    print(
        "HEARTBEAT_CARRIER_CONTRACT_PASS "
        "heartbeat=independent_10ms_oscillator observation=noncausal "
        "communication=manifest+expiration+data eol=master_records credential_authority=TV/TVC"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
