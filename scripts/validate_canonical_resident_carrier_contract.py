#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "control/canonical-resident-carrier-contract.json"
DISPATCHER = ROOT / "scripts/dispatch_resident_execution_requests.py"
RUNTIME_SEPARATION = ROOT / "control/runtime-separation-contract.json"


def validate(root: Path = ROOT) -> dict:
    contract = json.loads((root / CONTRACT.relative_to(ROOT)).read_text(encoding="utf-8"))
    separation = json.loads((root / RUNTIME_SEPARATION.relative_to(ROOT)).read_text(encoding="utf-8"))
    dispatcher = (root / DISPATCHER.relative_to(ROOT)).read_text(encoding="utf-8")

    assert contract["schema"] == "stegverse.canonical-resident-carrier-contract/v1"
    assert contract["credential_authority"] == "TV/TVC"
    assert contract["github_token_runtime_authority"] == "NONE"
    assert contract["second_user_operated_machine_required"] is False

    hb = contract["heartbeat"]
    assert hb["mechanism"] == "INDEPENDENT_PHASE_OSCILLATOR"
    assert hb["progression_dependency"] == "OSCILLATOR_ONLY"
    assert hb["reference_frequency_hz"] == 100
    assert hb["reference_increment_interval_ms"] == 10
    assert hb["grants_execution_authority"] is False
    assert hb["grants_admission_authority"] is False
    assert hb["grants_claim_or_fence_authority"] is False

    worker = contract["worker_runtime"]
    assert worker["implementation_ref"] == "heartbeat_runtime/worker_runtime.py"
    assert worker["class"] == "WorkerCoordinator"
    assert worker["second_scheduler_allowed"] is False
    assert worker["second_worker_runtime_allowed"] is False
    assert worker["request_dispatch_grants_authority"] is False

    assert separation["carrier_oscillator"]["progression_dependency"] == "OSCILLATOR_ONLY"
    assert separation["authority"]["heartbeat_grants_execution_authority"] is False
    assert separation["authority"]["credential_authority"] == "TV/TVC"

    expected = {
        "stegverse001_bounded_autonomy": "scripts/consume_stegverse001_bounded_autonomy_request.py",
        "sv002_org_runtime_activation": "scripts/consume_sv002_org_runtime_activation_request.py",
        "sv011_phase5": "scripts/consume_sv011_phase5_resident_execution_request.py",
    }
    by_selector = {row["selector"]: row["consumer_ref"] for row in contract["consumers"]}
    assert by_selector == expected
    assert any(row.get("predecessor_selector") == "sv011_phase5_source_materialization" for row in contract["consumers"])

    for selector, consumer in expected.items():
        assert f'(\"{selector}\", \"{consumer}\")' in dispatcher
    assert '(\"sv011_phase5_source_materialization\", \"scripts/consume_sv011_phase5_source_materialization_request.py\")' in dispatcher

    return {
        "schema": "stegverse.canonical-resident-carrier-validation/v1",
        "state": "PASS",
        "consumer_count": len(expected),
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "worker_runtime": "WorkerCoordinator",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_VALIDATION_ONLY",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
