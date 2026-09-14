import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGOS-AI-PREEXECUTION-RUNTIME-PROOF-001"
RT_ID = "RT-STEGOS-AI-PREEXECUTION-RUNTIME-PROOF-001"
COSV = "40000100100000"


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_task_registry_shard_binds_ephemeral_stegos_and_authority_boundaries():
    task = load(f"data/canonical-task-records/{TASK_ID}.json")
    assert task["task_id"] == TASK_ID
    assert task["coordination_state"] == "ACTIVE"
    assert task["checkout_state"] == "CHECKED_OUT"
    assert task["cosv_task_vector"] == COSV
    resolution = task["execution_substrate_resolution"]
    assert resolution["selected_substrate_id"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert resolution["external_device_required"] is False
    assert resolution["second_user_operated_device_allowed"] is False
    authority = task["authority_model"]
    assert authority["workercoordinator_remains_claim_fence_authority"] is True
    assert authority["interlock_intr_remains_transition_authority"] is True
    assert authority["tvc_remains_credential_provider_release_authority"] is True
    assert authority["model_output_grants_execution_authority"] is False
    assert authority["github_runtime_authority"] == "NONE"


def test_reusable_definition_reuses_existing_runtime_and_stops_at_authentic_ai_boundary():
    reusable = load(f"source-bundles/reusable-task-registry.d/{RT_ID}.json")
    assert reusable["reusable_task_id"] == RT_ID
    assert reusable["runner_templates"] == ["scripts/run_stegos_ai_preexecution_runtime_proof_reusable.py"]
    assert reusable["authority_effect"] == "NONE_ORCHESTRATION_ONLY"
    text = reusable["reuse_instructions"]
    for marker in (
        "SovereignLocalEventRuntimeAdapter",
        "Canonical Work",
        "WorkerCoordinator",
        "Interlock/InTr",
        "runtime-local PROPOSED",
        "authentic-AI evidence boundary",
    ):
        assert marker in text


def test_component_profile_uses_reusable_component_owners_without_duplicate_authority():
    profile = load(f"data/goal-task-component-profiles/{TASK_ID}.json")
    ids = [row["component_id"] for row in profile["selected_components"]]
    assert ids == [
        "RTC-MANIFEST-001",
        "RTC-GOVERNED-PROCESSING-002",
        "RTC-INTERLOCK-INTR-TRANSPORT-008",
        "REUSABLE-EPHEMERAL-CONSTRUCT",
        "RTC-FARSIDE-FINAL-009",
        "RTC-EVIDENCE-CUSTODY-004",
    ]
    invariants = profile["invariants"]
    assert invariants["duplicate_runtime_allowed"] is False
    assert invariants["duplicate_scheduler_allowed"] is False
    assert invariants["duplicate_workercoordinator_allowed"] is False
    assert invariants["duplicate_credential_path_allowed"] is False
    assert invariants["model_output_authority"] == "NONE"
    assert invariants["credential_authority"] == "TV/TVC"


def test_cosv_and_resident_request_bind_reusable_runner():
    vector = load(f"control/task-vectors/{TASK_ID}.json")
    request = load("control/resident-execution-request.d/canonical-work-stegos-ai-preexecution-runtime-proof-001.json")
    assert vector["vector"] == COSV
    assert vector["exact_metrics"]["lifecycle"] == "CHECKED_OUT"
    assert vector["authority_effect"] == "NONE"
    assert request["task_id"] == TASK_ID
    assert request["cosv_task_vector"] == COSV
    assert request["reusable_task_binding"]["reusable_task_id"] == RT_ID
    assert request["reusable_task_binding"]["runner"] == "scripts/run_stegos_ai_preexecution_runtime_proof_reusable.py"
    assert request["reusable_task_binding"]["selected_execution_substrate"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert request["credential_authority"] == "TV/TVC"
    assert request["github_token_runtime_authority"] == "NONE"
    assert request["second_machine_required"] is False
    assert request["request_granted_authority"] is False


def test_runner_contains_only_existing_runtime_path_and_explicit_nonclaim():
    text = (ROOT / "scripts/run_stegos_ai_preexecution_runtime_proof_reusable.py").read_text(encoding="utf-8")
    for marker in (
        "SovereignLocalEventRuntimeAdapter",
        "RuntimeClass.EVENT_EPHEMERAL",
        "install_and_run_canonical_work_event_bootstrap.py",
        "canonical_work_intr_admission_evidence_not_observed",
        "tests/test_ai_preexecution_governance.py",
        "tests/test_ai_preexecution_network_runtime.py",
        '"authentic_external_ai_originated_proposal_observed": False',
        '"model_output_authority": "NONE"',
        '"github_runtime_authority": "NONE"',
    ):
        assert marker in text
