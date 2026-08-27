#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from materialize_live_cosv_packet import materialize  # noqa: E402

EXPECTED_TASK = "COSV-LIVE-PACKET-AUTOMATION-006"
REQUIRED_CAPS = {"runtime_observation", "bounded_repository_mutation", "cosv_live_packet_materialization"}


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if task.get("task_id") != EXPECTED_TASK or not isinstance(epoch, int):
        return 3
    required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if required != REQUIRED_CAPS:
        return 4
    claim_id = task.get("claim_id")
    fence = ((task.get("assignment_timer") or {}).get("fencing_token"))
    timing = task.get("heartbeat_timing") or {}
    if fence is None:
        fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not isinstance(fence, int):
        return 5
    sequence = int(timing.get("transition_sequence", 0)) + 1

    try:
        result = materialize(ROOT)
    except Exception as exc:
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "COSV_LIVE_PACKET_MATERIALIZATION_BLOCKED",
            "transition_sequence": sequence,
            "expected_next_transition": "COSV_LIVE_PACKET_MATERIALIZED",
            "expected_next_earliest_epoch": epoch + 1,
            "expected_next_latest_epoch": epoch + 1,
            "checkpoint_ref": "receipts/cosv/live/latest-state.json",
            "evidence_refs": [
                "management/COSV_HEARTBEAT_STATE_PACKET_CONTRACT.json",
                "scripts/materialize_live_cosv_packet.py",
            ],
            "blocker": {
                "dependency_class": "INTERNAL_CAPABILITY",
                "problem_statement": str(exc),
                "solution_required": True,
                "may_remain_blocked": False,
                "next_solution_action": "RECHECK_CANONICAL_PROTOCOL_REFERENCE_AND_LOCAL_STATE_EVIDENCE",
                "machine_observable_release_condition": "materializer returns PACKET_MATERIALIZED or NO_NEW_REFERENCE without invariant failure",
                "github_token_required": False,
                "third_party_blocker": False,
            },
            "cost_observation": {
                "hb_transition_count": 1,
                "compute_units": 1,
                "external_cost_usd": 0,
                "task_class": "cosv_live_packet_automation",
            },
        }
        json.dump(response, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    packet_materialized = result.get("state") == "PACKET_MATERIALIZED"
    transition_id = "COSV_LIVE_PACKET_MATERIALIZED" if packet_materialized else "COSV_LIVE_PACKET_REFERENCE_CURRENT"
    evidence_refs = [
        "management/COSV_HEARTBEAT_STATE_PACKET_CONTRACT.json",
        "scripts/materialize_live_cosv_packet.py",
    ]
    for key in ("packet_ref", "validation_ref"):
        if result.get(key):
            evidence_refs.append(str(result[key]))

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "ACTIVE",
        "transition_id": transition_id,
        "transition_sequence": sequence,
        "expected_next_transition": "COSV_LIVE_PACKET_MATERIALIZED",
        "expected_next_earliest_epoch": epoch + 1,
        "expected_next_latest_epoch": epoch + 1,
        "checkpoint_ref": "receipts/cosv/live/latest-state.json",
        "evidence_refs": sorted(set(evidence_refs)),
        "blocker": None,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "cosv_live_packet_automation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
