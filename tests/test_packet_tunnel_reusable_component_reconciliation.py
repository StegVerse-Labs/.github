import json
from pathlib import Path

from scripts.evaluate_reusable_task_componentization import evaluate

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "data/canonical-task-records/STEGOS-DEVICE-CONTINUITY-PACKET-TUNNEL-RUNTIME-001.json"
PROFILE = ROOT / "data/goal-task-component-profiles/STEGOS-DEVICE-CONTINUITY-PACKET-TUNNEL-RUNTIME-001.json"
HANDOFF = ROOT / "docs/STEGOS_DEVICE_CONTINUITY_PACKET_TUNNEL_COMPONENT_MODEL_MIRROR_HANDOFF.md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_goal_identity_and_runtime_predicates_are_preserved():
    task = load(TASK)
    profile = load(PROFILE)
    assert task["task_id"] == "STEGOS-DEVICE-CONTINUITY-PACKET-TUNNEL-RUNTIME-001"
    assert task["coordination_state"] == "IN_PROGRESS"
    assert profile["goal_identity_preserved"] is True
    assert profile["new_goal_task_required"] is False
    assert task["expected_evidence_predicates"] == profile["goal_specific_completion_predicates_preserved"]
    assert task["remaining_evidence_predicates"] == profile["remaining_predicates"]


def test_host_activation_source_is_resolved_but_runtime_is_not_upgraded():
    task = load(TASK)
    deps = {item["dependency_id"]: item for item in task["dependencies"]}
    assert deps["DEP-PACKET-TUNNEL-HOST-ACTIVATION-SOURCE"]["state"] == "RESOLVED"
    assert deps["DEP-PACKET-TUNNEL-GOVERNED-RUNTIME-OBSERVATION"]["state"] == "UNRESOLVED"
    assert task["completion"]["claimed"] is False
    assert task["completion"]["validated"] is False
    assert task["runtime_resolution"] is None


def test_decomposition_score_requires_componentization_before_more_bespoke_scope():
    signals = {
        "repeated_subflow": True,
        "multiple_authority_crossings": True,
        "multiple_round_trips": False,
        "cross_repository_or_org_spread": False,
        "task_specific_adapter_duplicates_generic_work": False,
        "handoff_sequence_growth": True,
        "failure_path_branching": False,
        "independent_reusability": True,
        "optional_subflow_present": True,
        "independent_evidence_predicate": True,
    }
    result = evaluate({
        "task_id": "STEGOS-DEVICE-CONTINUITY-PACKET-TUNNEL-RUNTIME-001",
        "cosv_task_vector": None,
        "signals": signals,
    })
    assert result["score"] == 19
    assert result["must_stop_scope_growth"] is True
    assert result["decision"] == "STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION"


def test_profile_reuses_existing_owners_and_does_not_force_maximal_transport_chain():
    profile = load(PROFILE)
    ids = [item["component_id"] for item in profile["selected_components"]]
    assert ids == ["RTC-INTERLOCK-INTR-TRANSPORT-008", "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001"]
    assert profile["new_reusable_component_required"] is False
    assert "RTC-PUBLISHER-005" in profile["not_selected"]
    assert "RTC-SDK-RETURN-006" in profile["not_selected"]
    assert "RTC-FARSIDE-FINAL-009" in profile["not_selected"]


def test_authority_separation_and_no_device_verification():
    profile = load(PROFILE)
    invariants = profile["authority_invariants"]
    assert invariants["task_registry"] == "COORDINATION_ONLY"
    assert invariants["worker_claim_fence"] == "WorkerCoordinator"
    assert invariants["user_verification"] == "KV/SKAP Vault"
    assert invariants["governed_transition"] == "Interlock/InTr"
    assert invariants["observed_reality_custody_reconstruction"] == "Master Records"
    assert "NOT_USER_VERIFIER" in invariants["stegos_device_role"]


def test_component_handoff_preserves_runtime_truth_boundary():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "Runtime truth handoff" in text
    assert "PACKET_TUNNEL" not in text or "AUTHENTIC_PACKET_TUNNEL_ACTIVATION_OBSERVED" in text
    assert "No second user-operated device" in text
    assert "No device verification" in text
