#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime import CarrierHeartbeatRuntime  # noqa: E402

EXPECTED_TASK = "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009"
REQUIRED_CAPS = {"heartbeat_runtime_observation", "bounded_repository_mutation", "independent_oscillator_live_proof"}


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
    fence = ((task.get("assignment_timer") or {}).get("fencing_token"))
    if fence is None:
        fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not isinstance(fence, int):
        return 5
    sequence = int(timing.get("transition_sequence", 0)) + 1

    try:
        result = CarrierHeartbeatRuntime(ROOT).cycle(write=True)
        carrier = json.loads((ROOT / "control" / "heartbeat-carrier-runtime-state.json").read_text(encoding="utf-8"))
        observation = json.loads((ROOT / "control" / "heartbeat-carrier-observation.json").read_text(encoding="utf-8"))
        assert result.get("progression_dependency") == "OSCILLATOR_ONLY"
        assert result.get("oscillator_period_ms") == 10
        assert result.get("observation_is_causal") is False
        assert carrier.get("progression_dependency") == "OSCILLATOR_ONLY"
        assert carrier.get("phase_travel_time_ms") == 10
        assert carrier.get("snapshot_is_observation_only") is True
        assert carrier.get("frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
        obs_carrier = observation.get("carrier") or {}
        assert obs_carrier.get("phase_travel_time_ms") == 10
        assert obs_carrier.get("observation_is_causal") is False
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
            "evidence_refs": ["heartbeat_runtime/independent_oscillator.py", "heartbeat_runtime/engine_v12.py", "docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md"],
            "blocker": {"dependency_class": "INTERNAL_CAPABILITY", "problem_statement": str(exc), "solution_required": True, "may_remain_blocked": False, "next_solution_action": "RECHECK_CORRECTED_SOVEREIGN_HEARTBEAT_RUNTIME", "machine_observable_release_condition": "one corrected sampler execution persists oscillator-only carrier and observation state", "github_token_required": False, "third_party_blocker": False},
            "cost_observation": {"hb_transition_count": 0, "compute_units": 1, "external_cost_usd": 0, "task_class": "independent_heartbeat_live_proof"}
        }
        json.dump(response, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED",
        "transition_sequence": sequence,
        "expected_next_transition": "NONE_TERMINAL",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": "control/heartbeat-carrier-runtime-state.json",
        "evidence_refs": ["control/heartbeat-carrier-runtime-state.json", "control/heartbeat-carrier-observation.json", "heartbeat_runtime/independent_oscillator.py", "heartbeat_runtime/engine_v12.py"],
        "blocker": None,
        "cost_observation": {"hb_transition_count": int(result.get("elapsed_heartbeat_references", 0)), "compute_units": 1, "external_cost_usd": 0, "task_class": "independent_heartbeat_live_proof"}
    }
    json.dump(response, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
