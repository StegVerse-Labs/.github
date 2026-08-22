#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime import CarrierHeartbeatRuntime  # noqa: E402

EXPECTED_TASK = "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009"
REQUIRED_CAPS = {"heartbeat_runtime_observation", "bounded_repository_mutation", "independent_oscillator_live_proof"}
CANONICAL_RUNTIME_REFS = [
    "heartbeat_runtime/independent_oscillator.py",
    "heartbeat_runtime/oscillator_producer.py",
    "heartbeat_runtime/engine_v13.py",
    "docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md",
]


def verify_live_proof(result: dict[str, Any], carrier: dict[str, Any], observation: dict[str, Any]) -> None:
    """Verify the canonical persisted independent-oscillator evidence shape."""
    oscillator = carrier.get("oscillator") or {}
    obs_carrier = observation.get("carrier") or {}

    assert result.get("progression_dependency") == "OSCILLATOR_ONLY"
    assert result.get("oscillator_period_ms") == 10
    assert result.get("observation_is_causal") is False

    assert carrier.get("frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
    assert carrier.get("authority_effect") == "NONE"
    assert oscillator.get("mechanism") == "INDEPENDENT_PHASE_OSCILLATOR"
    assert oscillator.get("period_ns") == 10_000_000
    assert oscillator.get("phase_travel_time_ms") == 10
    assert oscillator.get("reference_increment_interval_ms") == 10
    assert oscillator.get("reference_frequency_hz") == 100
    assert oscillator.get("progression_dependency") == "OSCILLATOR_ONLY"
    assert oscillator.get("downstream_gating") is False
    assert oscillator.get("observation_is_causal") is False
    assert oscillator.get("snapshot_is_observation_only") is True
    assert oscillator.get("sampled_reference_epoch") == carrier.get("epoch")

    assert obs_carrier.get("frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
    assert obs_carrier.get("phase_travel_time_ms") == 10
    assert obs_carrier.get("observation_is_causal") is False
    assert obs_carrier.get("authority_effect") == "NONE"


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if task.get("task_id") != EXPECTED_TASK:
        return 3
    required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if required != REQUIRED_CAPS:
        return 4
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = (task.get("assignment_timer") or {}).get("fencing_token")
    if fence is None:
        fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not isinstance(fence, int):
        return 5
    sequence = int(timing.get("transition_sequence", 0)) + 1

    try:
        result = CarrierHeartbeatRuntime(ROOT).cycle(write=True)
        carrier = json.loads((ROOT / "control" / "heartbeat-carrier-runtime-state.json").read_text(encoding="utf-8"))
        observation = json.loads((ROOT / "control" / "heartbeat-carrier-observation.json").read_text(encoding="utf-8"))
        verify_live_proof(result, carrier, observation)
    except Exception as exc:
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "INDEPENDENT_HEARTBEAT_LIVE_PROOF_BLOCKED",
            "transition_sequence": sequence,
            "expected_next_transition": "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED",
            "expected_next_earliest_epoch": invocation.get("heartbeat_epoch"),
            "expected_next_latest_epoch": None,
            "checkpoint_ref": "control/heartbeat-carrier-runtime-state.json",
            "evidence_refs": CANONICAL_RUNTIME_REFS,
            "blocker": {
                "dependency_class": "INTERNAL_CAPABILITY",
                "problem_statement": str(exc),
                "solution_required": True,
                "may_remain_blocked": False,
                "next_solution_action": "RECHECK_CORRECTED_SOVEREIGN_HEARTBEAT_RUNTIME",
                "machine_observable_release_condition": "one corrected v13 sampler execution persists canonical nested oscillator-only carrier and observation state",
                "github_token_required": False,
                "third_party_blocker": False,
            },
            "cost_observation": {"hb_transition_count": 0, "compute_units": 1, "external_cost_usd": 0, "task_class": "independent_heartbeat_live_proof"},
        }
        json.dump(response, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED",
        "transition_sequence": sequence,
        "expected_next_transition": "NONE_TERMINAL",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": "control/heartbeat-carrier-runtime-state.json",
        "evidence_refs": [
            "control/heartbeat-carrier-runtime-state.json",
            "control/heartbeat-carrier-observation.json",
            *CANONICAL_RUNTIME_REFS[:3],
        ],
        "blocker": None,
        "cost_observation": {"hb_transition_count": int(result.get("elapsed_heartbeat_references", 0)), "compute_units": 1, "external_cost_usd": 0, "task_class": "independent_heartbeat_live_proof"},
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
