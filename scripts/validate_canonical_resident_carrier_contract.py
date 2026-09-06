#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "control/canonical-resident-carrier-contract.json"
DISPATCHER = ROOT / "scripts/dispatch_resident_execution_requests.py"
RUNTIME_SEPARATION = ROOT / "control/runtime-separation-contract.json"
PROGRESSION = ROOT / "control/entity-autonomous-governed-progression-contract.json"
PROGRESSION_COORDINATION = ROOT / "control/cross-task-coordination.d/entity-autonomous-governed-progression-runtime-adoption.json"
TASK_POLICY = ROOT / "data/task-coordination-policy.json"
README = ROOT / "README.md"


def validate(root: Path = ROOT) -> dict:
    contract = json.loads((root / CONTRACT.relative_to(ROOT)).read_text(encoding="utf-8"))
    separation = json.loads((root / RUNTIME_SEPARATION.relative_to(ROOT)).read_text(encoding="utf-8"))
    progression_contract = json.loads((root / PROGRESSION.relative_to(ROOT)).read_text(encoding="utf-8"))
    progression_coordination = json.loads((root / PROGRESSION_COORDINATION.relative_to(ROOT)).read_text(encoding="utf-8"))
    task_policy = json.loads((root / TASK_POLICY.relative_to(ROOT)).read_text(encoding="utf-8"))
    dispatcher = (root / DISPATCHER.relative_to(ROOT)).read_text(encoding="utf-8")
    readme = (root / README.relative_to(ROOT)).read_text(encoding="utf-8")

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

    progression = contract["entity_progression"]
    assert progression["contract_ref"] == "control/entity-autonomous-governed-progression-contract.json"
    assert progression["coordination_task_id"] == "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
    assert progression["coordination_fragment_ref"] == "control/cross-task-coordination.d/entity-autonomous-governed-progression-runtime-adoption.json"
    assert progression["runtime_adoption_predicate_id"] == "PRED-ENTITY-AUTONOMOUS-PROGRESSION-RUNTIME-ADOPTED"
    assert progression["canonical_work_policy_ref"] == "data/task-coordination-policy.json"
    assert progression["default_for_machine_owned_transitions"] == "MACHINE_GOVERNED_AUTONOMOUS"
    assert progression["human_approval_default"] is False
    assert progression["every_state_change_requires_current_governance"] is True
    assert progression["authority_is_inferred"] is False
    assert progression["authority_is_reused"] is False
    assert progression["prior_receipt_authorizes_next_transition"] is False
    assert progression["human_interaction_queue_scope"] == "TRUE_HUMAN_DEVICE_MUTATIONS_ONLY"
    assert progression["runtime_adoption_claimed"] is False

    assert progression_contract["transition_rule"]["every_state_change_requires_current_governance"] is True
    assert progression_contract["transition_rule"]["authority_is_inferred"] is False
    assert progression_contract["transition_rule"]["authority_is_reused"] is False
    assert progression_contract["transition_rule"]["human_approval_default"] is False
    assert progression_contract["human_interaction_queue_must_not_schedule_machine_runtime"] is True

    assert progression_coordination["schema"] == "stegverse.cross-task-coordination-fragment/v1"
    assert progression_coordination["fragment_id"] == "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
    assert progression_coordination["authority_effect"] == "NONE_COORDINATION_ONLY"
    task = progression_coordination["tasks"][0]
    assert task["task_id"] == progression["coordination_task_id"]
    assert task["autonomous_augmentation"] is True
    assert task["readme_impact_required"] is True
    assert task["readme_impact"]["readme_updated_in_change_set"] is True
    assert task["readme_impact"]["readme_path"] == "StegVerse-Labs/.github/README.md"
    predicate = next(row for row in progression_coordination["predicates"] if row["predicate_id"] == progression["runtime_adoption_predicate_id"])
    assert predicate["state"] == "UNSATISFIED"

    assert task_policy["canonical_truth"]["work_intent_and_coordination"] == "CANONICAL_TASK_REGISTRY"
    assert task_policy["canonical_truth"]["execution_claim_and_fence"] == "WORKERCOORDINATOR"
    assert task_policy["canonical_truth"]["observed_reality_and_reconstruction"] == "MASTER_RECORDS"
    assert task_policy["canonical_truth"]["governed_ingress_egress"] == "INTERLOCK_INTR"
    assert "SELECT_HIGHEST_PRIORITY_ADMISSIBLE_NON_DUPLICATE_NON_COLLIDING_TASK" in task_policy["new_session_entry_contract"]["sequence"]

    assert "## Autonomous Governed Entity Progression" in readme
    assert "without inserting a human approval checkpoint between ordinary machine-owned cycles" in readme

    expected = {
        "stegverse001_bounded_autonomy": "scripts/consume_stegverse001_bounded_autonomy_request.py",
        "sv002_org_runtime_activation": "scripts/consume_sv002_org_runtime_activation_request.py",
        "sv011_phase5": "scripts/consume_sv011_phase5_resident_execution_request.py",
    }
    by_selector = {row["selector"]: row["consumer_ref"] for row in contract["consumers"]}
    assert by_selector == expected
    for row in contract["consumers"]:
        assert row["progression_mode"] == "MACHINE_GOVERNED_AUTONOMOUS"
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
        "entity_progression_mode": "MACHINE_GOVERNED_AUTONOMOUS",
        "runtime_adoption_predicate": progression["runtime_adoption_predicate_id"],
        "runtime_adoption_claimed": False,
        "readme_impact_complete": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_VALIDATION_ONLY",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
