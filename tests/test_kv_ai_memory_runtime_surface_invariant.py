from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_canonical_task_prohibits_connected_device_runtime_gate():
    record = load_json("data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json")
    policy = record["runtime_requirements"]["runtime_surface_policy"]
    assert policy["current_device_label_informational_only"] is True
    assert policy["device_confirmation_required"] is False
    assert policy["device_discovery_required"] is False
    assert policy["device_presence_probe_required"] is False
    assert policy["remote_connected_device_required"] is False
    assert policy["remote_desktop_commander_required"] is False
    assert policy["second_user_operated_device_required"] is False
    assert policy["absence_of_connected_device_is_blocker"] is False
    assert policy["device_identity_mints_authority"] is False


def test_executable_handoff_and_registry_preserve_same_invariant():
    handoff = load_json("handoffs/SV-KV-AI-PERSISTENCE-001.json")
    policy = handoff["execution"]["runtime_surface_policy"]
    assert all(policy[key] is False for key in (
        "device_confirmation_required",
        "device_discovery_required",
        "device_presence_probe_required",
        "remote_connected_device_required",
        "remote_desktop_commander_required",
        "second_user_operated_device_required",
        "absence_of_connected_device_is_blocker",
        "device_identity_mints_authority",
    ))
    assert policy["current_device_label_informational_only"] is True

    registry = load_json("control/worker-registry.d/kv-ai-memory-resident-001.json")
    admission = registry["tasks"][0]["admission"]
    for key in (
        "device_confirmation_required",
        "device_discovery_required",
        "device_presence_probe_required",
        "remote_connected_device_required",
        "remote_desktop_commander_required",
        "second_user_operated_device_required",
        "absence_of_connected_device_is_blocker",
    ):
        assert admission[key] is False


def test_resident_request_does_not_wait_for_device_presence():
    request = load_json("control/resident-execution-request.d/kv-ai-memory-resident-001.json")
    for key in (
        "second_machine_required",
        "device_confirmation_required",
        "device_discovery_required",
        "device_presence_probe_required",
        "remote_connected_device_required",
        "remote_desktop_commander_required",
        "absence_of_connected_device_is_blocker",
    ):
        assert request[key] is False


def test_handoff_and_readme_do_not_make_rdc_or_device_presence_a_gate():
    handoff = (ROOT / "docs/KV_AI_MEMORY_RESIDENT_EXECUTION_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "device discovery/presence/RDC gate: PROHIBITED" in handoff
    assert "Remote Desktop Commander requirement: NOT_APPLICABLE" in handoff
    assert "absence of connected-device result is blocker: false" in handoff

    # Repository-wide README already states current-device presence is not an authority
    # source and does not contain a KV-memory connected-device/RDC prerequisite.
    assert "Running on a user's iPhone does not by itself make a transition human-owned." in readme
    kv_section = readme.split("### Fenced Personal-KV AI memory resident execution", 1)[1].split("### Bounded StegSocials Universal InTr ingress", 1)[0]
    assert "Remote Desktop Commander" not in kv_section
    assert "connected device required" not in kv_section.lower()
    assert "second machine required" not in kv_section.lower()


def test_task_coordination_policy_must_be_resolved_before_runtime_state_mutation():
    """Prevent a repeat of treating a runtime evidence gap as a transfer/stop state."""
    policy = load_json("data/task-coordination-policy.json")

    assert policy["canonical_truth"]["work_intent_and_coordination"] == "CANONICAL_TASK_REGISTRY"
    assert policy["canonical_truth"]["observed_reality_and_reconstruction"] == "MASTER_RECORDS"
    assert policy["runtime_profile_discovery"]["task_requirements_field"] == "runtime_requirements"
    assert policy["runtime_profile_discovery"]["task_resolution_field"] == "runtime_resolution"
    assert policy["runtime_profile_discovery"]["generic_runtime_missing_claim_allowed_before_resolution"] is False
    assert policy["runtime_profile_discovery"]["workercoordinator_admission_still_required"] is True
    assert policy["runtime_profile_discovery"]["interlock_intr_transition_admission_still_required"] is True

    invariants = set(policy["invariants"])
    assert "RUNTIME_MISSING_MUST_RESOLVE_AGAINST_CANONICAL_RUNTIME_PROFILE_MAP_BEFORE_ESCALATION" in invariants
    assert "UNRESOLVED_CONSTRAINTS_ARE_METADATA_NOT_OPERATIONAL_STOP_STATES" in invariants
    assert "ACTIVE_WORK_CONTINUES_ATTEMPTING_SOLUTION_WITHIN_AUTHORITY_CEILING" in invariants
    assert "DUPLICATE_AND_ADJACENT_WORK_RESOLUTION_PRECEDES_EXECUTION_ADMISSION" in invariants
    assert "TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY" in invariants
    assert "HANDOFFS_ARE_PROJECTIONS_NOT_INDEPENDENT_TRUTH" in invariants

    continuation = policy["goal_resolution_continuation_contract"]["continuation_sequence"]
    assert continuation.index("DEDUPLICATE_EQUIVALENT_WORK") < continuation.index("SELECT_NEXT_ADMISSIBLE_NON_DUPLICATE_WORK")
    assert continuation.index("RESOLVE_REPOSITORY_RUNTIME_AUTHORITY_AND_EVIDENCE_COLLISIONS") < continuation.index("SELECT_NEXT_ADMISSIBLE_NON_DUPLICATE_WORK")
    assert policy["adjacent_task_derivation_contract"]["reuse_existing_equivalent_task_first"] is True
    assert policy["adjacent_task_derivation_contract"]["duplicate_task_creation_prohibited"] is True


def test_kv_runtime_evidence_gaps_remain_on_parent_task_until_authentic_completion():
    parent = load_json("data/canonical-task-records/SV-KV-AI-PERSISTENCE-001.json")
    successor = load_json("data/canonical-task-records/SV-KV-AI-RUNTIME-EVIDENCE-001.json")

    assert parent["coordination_state"] == "IN_PROGRESS"
    assert parent["completion"]["claimed"] is False
    assert parent["completion"]["validated"] is False
    assert "TRANSFERRED" not in parent.get("allowed_next_transitions", [])

    unresolved = {
        row["dependency_id"]: row
        for row in parent["dependencies"]
        if row.get("state") == "UNRESOLVED"
    }
    assert unresolved["DEP-LIVE-INTR-ADMISSION"]["kind"] == "RUNTIME_PREDICATE"
    assert unresolved["DEP-LIVE-WORKERCOORDINATOR-PROVIDERREQUEST"]["kind"] == "RUNTIME_PREDICATE"
    assert unresolved["DEP-LIVE-PROVIDER-MODEL-CHAIN"]["kind"] == "RUNTIME_PREDICATE"
    assert unresolved["DEP-LIVE-KV-WRITEBACK-READBACK"]["kind"] == "RUNTIME_PREDICATE"
    assert unresolved["DEP-MACHINE-KV-CROSS-PROVIDER-RECONSTRUCTION-EVIDENCE"]["kind"] == "EVIDENCE"
    assert unresolved["DEP-HB-KV-RECEIPT-OBSERVATION-EVIDENCE"]["kind"] == "EVIDENCE"

    expected = set(parent["expected_evidence_predicates"])
    assert "LIVE_MEMORY_PACKET_INTR_ADMISSION_RECEIPT_OBSERVED" in expected
    assert "LIVE_RESIDENT_PROVIDER_REQUEST_MATERIALIZATION_OBSERVED" in expected
    assert "LIVE_EXTERNAL_PROVIDER_INGRESS_RESPONSE_EGRESS_CHAIN_OBSERVED" in expected
    assert "LIVE_KV_WRITEBACK_READBACK_OBSERVED_BEFORE_ACTIVATION" in expected
    assert "MACHINE_KV_CROSS_PROVIDER_RECONSTRUCTION_OBSERVED" in expected
    assert "HB_OBSERVATION_BOUND_TO_VERIFIED_KV_RECEIPTS_WITHOUT_STATE_AUTHORITY" in expected

    assert "SV-KV-AI-RUNTIME-EVIDENCE-001" in parent.get("superseded_duplicate_task_refs", [])
    assert successor["coordination_state"] == "RETIRED"
    assert successor["retirement"]["canonical_continuation_task_id"] == "SV-KV-AI-PERSISTENCE-001"
    assert successor["authority_model"]["retired_duplicate_grants_authority"] is False
