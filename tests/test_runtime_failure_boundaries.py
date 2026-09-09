import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "runtime_failure_boundaries.py"


def load_module():
    spec = importlib.util.spec_from_file_location("runtime_failure_boundaries", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_ten_runtime_loop_boundaries_have_stable_codes_and_non_authority():
    module = load_module()
    assert [row["index"] for row in module.STAGES] == list(range(1, 11))
    assert len({row["stage"] for row in module.STAGES}) == 10
    assert len({row["code"] for row in module.STAGES}) == 10
    for row in module.STAGES:
        response = module.failure_response(
            task_id="TEST-TASK",
            lane="Test",
            stage_index=row["index"],
            raw_state="INJECTED_FAILURE",
        )
        assert response["failure_code"] == row["code"]
        assert response["failure_stage"] == row["stage"]
        assert response["heartbeat_grants_authority"] is False
        assert response["authority_effect"] == "NONE_DIAGNOSTIC_ONLY"


def test_existing_global_resume_labels_map_to_precise_loop_boundaries():
    module = load_module()
    expected = {
        "AUTHENTIC_REQUEST_CONSUMPTION": 3,
        "SUBJECT_BOUND_RESIDENT_REQUEST_EXECUTION": 3,
        "AUTHENTIC_MATERIALIZATION_CONSUMPTION": 3,
        "RESIDENT_PROCESS_AND_REQUEST_CONSUMPTION": 3,
        "CANONICALWORK_INGRESS_ADMITTED": 3,
        "WORKERCOORDINATOR_CLAIM_FENCE": 4,
        "PER_CHILD_CLAIM_FENCE_AND_FORMALISM_EXECUTION": 4,
        "CURRENT_DEVICE_CONTINUATION": 5,
        "ESRL_LEASE_OPEN": 6,
        "PROVIDER_RUNTIME_CONSUMPTION": 6,
        "SDK_FIRST_ROUND_RESIDENT_ANALYSIS": 7,
        "EXACT_PARENT_SDK_EXECUTION": 7,
        "CANONICAL_ADAPTER_EXECUTION": 7,
        "AUTHENTIC_DEVICE_KV_PARENT": 7,
        "SUBJECT_BOUND_GLM_EXECUTION": 7,
        "SUBJECT_BOUND_PHASE5_EXECUTION": 7,
        "AUTHENTIC_BROWSER_INVOCATION": 7,
        "EXACT_PARENT_REBINDING_REEXECUTION": 7,
    }
    for resume_stage, stage_index in expected.items():
        annotated = module.annotate_lane_outcome({
            "lane": resume_stage,
            "task_id": "TEST-" + resume_stage,
            "resume_stage": resume_stage,
            "state": "INJECTED_UNRESOLVED",
        })
        assert annotated["first_failure_stage_index"] == stage_index
        assert annotated["first_failure_code"] == module.BY_INDEX[stage_index]["code"]
        assert sum(1 for row in annotated["boundary_trace"] if row["failed"]) == 1


def test_explicit_stage_observations_stop_at_first_real_failure_not_projected_resume():
    module = load_module()
    annotated = module.annotate_lane_outcome({
        "lane": "Injected",
        "task_id": "TEST-EXPLICIT",
        "resume_stage": "SUBJECT_BOUND_GLM_EXECUTION",
        "state": "COMPONENT_PENDING",
        "stage_observations": {
            "RUNTIME_PROFILE_RESOLUTION": {"state": "PASSED"},
            "PERSISTENT_NODE_CONTINUITY": {"state": "PASSED"},
            "EPHEMERAL_REQUEST_CONSUMPTION": {"state": "PASSED"},
            "WORKERCOORDINATOR_CLAIM_FENCE": {"state": "PASSED"},
            "EPHEMERAL_INTERLOCK_INTR_ADMISSION": {
                "state": "FAILED",
                "reason": "injected InTr refusal",
                "evidence_ref": "receipt://intr-refusal",
            },
            "EPHEMERAL_TRANSPORT_PROVIDER_LEASE": {"state": "NOT_REACHED"},
            "COMPONENT_EXECUTION": {"state": "NOT_REACHED"},
        },
    })
    assert annotated["first_failure_stage_index"] == 5
    assert annotated["first_failure_code"] == "RUNTIME_STAGE_05_INTR_ADMISSION_NOT_OBSERVED"
    assert annotated["first_failure"]["reason"] == "injected InTr refusal"
    assert annotated["first_failure"]["evidence_ref"] == "receipt://intr-refusal"


def test_terminal_success_has_no_failure_response():
    module = load_module()
    annotated = module.annotate_lane_outcome({
        "lane": "Completed",
        "task_id": "TEST-COMPLETED",
        "resume_stage": "AUTHENTIC_BROWSER_INVOCATION",
        "state": "COMPLETED",
    })
    assert annotated["first_failure"] is None
    assert annotated["first_failure_stage_index"] is None
    assert annotated["first_failure_code"] is None
    assert not any(row["failed"] for row in annotated["boundary_trace"])


def test_failure_summary_counts_exact_first_boundaries():
    module = load_module()
    outcomes = [
        module.annotate_lane_outcome({"lane": "A", "task_id": "A", "resume_stage": "AUTHENTIC_REQUEST_CONSUMPTION", "state": "PENDING"}),
        module.annotate_lane_outcome({"lane": "B", "task_id": "B", "resume_stage": "AUTHENTIC_REQUEST_CONSUMPTION", "state": "PENDING"}),
        module.annotate_lane_outcome({"lane": "C", "task_id": "C", "resume_stage": "WORKERCOORDINATOR_CLAIM_FENCE", "state": "PENDING"}),
        module.annotate_lane_outcome({"lane": "D", "task_id": "D", "resume_stage": "AUTHENTIC_BROWSER_INVOCATION", "state": "COMPLETED"}),
    ]
    summary = module.summarize_failure_boundaries(outcomes)
    assert summary["failed_lane_count"] == 3
    assert summary["failure_stage_counts"] == {
        "3:EPHEMERAL_REQUEST_CONSUMPTION": 2,
        "4:WORKERCOORDINATOR_CLAIM_FENCE": 1,
    }
    assert summary["failure_code_counts"]["RUNTIME_STAGE_03_REQUEST_NOT_CONSUMED"] == 2
    assert summary["failure_code_counts"]["RUNTIME_STAGE_04_CLAIM_FENCE_NOT_OBSERVED"] == 1
