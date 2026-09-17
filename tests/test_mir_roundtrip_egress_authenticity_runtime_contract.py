import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001"
COSV = "50000000100000"


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_cosv_pointer_and_resident_request_are_exact():
    vector = load(f"control/task-vectors/{TASK}.json")
    index = load(f"control/task-vector-index.d/{TASK}.json")
    request = load("control/resident-execution-request.d/mir-roundtrip-egress-authenticity-001.json")
    assert vector["vector"] == COSV
    assert index["task_id"] == TASK
    assert index["vector"] == COSV
    assert index["source_state_vector_ref"] == f"control/task-vectors/{TASK}.json"
    assert request["state"] == "REQUESTED"
    assert request["task_id"] == TASK
    assert request["cosv_task_vector"] == COSV
    assert request["generic_sv002_route_reproof_required"] is False
    assert request["manual_device_prerequisite"] is False
    assert request["second_machine_required"] is False
    assert request["github_token_runtime_authority"] == "NONE"


def test_workercoordinator_binding_reuses_existing_authority_plane():
    fragment = load("control/worker-registry.d/mir-roundtrip-egress-authenticity-001.json")
    adapter = load("control/process-worker-adapters.d/mir-roundtrip-egress-authenticity-001.json")
    task = fragment["tasks"][0]
    worker = fragment["workers"][0]
    proc = adapter["adapters"][0]
    assert task["task_id"] == TASK
    assert task["state"] == "HANDOFF_READY"
    assert task["admission"]["fresh_fence_required"] is True
    assert task["admission"]["heartbeat_grants_execution_authority"] is False
    assert worker["capabilities"] == ["mir_roundtrip_egress_authenticity"]
    assert proc["capabilities"] == worker["capabilities"]
    assert proc["command"] == ["python", "workers/mir_roundtrip_egress_authenticity_worker.py"]
    assert "STEGVERSE_NODE_GENESIS_RECEIPT" in proc["env_allowlist"]
    assert fragment["github_token_required"] is False


def test_worker_is_duplicate_first_and_runtime_evidence_bounded():
    source = (ROOT / "workers/mir_roundtrip_egress_authenticity_worker.py").read_text(encoding="utf-8")
    required = (
        "DUPLICATE_PROVEN_SV002_ROUTE_FIRST_THEN_APPLY_MIR_SPECIFIC_REQUIREMENTS",
        "run_mir_profile_transition",
        "SovereignLocalEventRuntimeAdapter",
        "validate_node_genesis_receipt",
        "reusable_task_master_records_roundtrip.py",
        "MIR_MIRROR_ONE_WAY_TRANSITION_OBSERVED",
        "MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME",
        '"successful_data_transport_round_trip_identified": False',
        '"authentic_external_mir_endpoint_claimed": False',
    )
    for token in required:
        assert token in source
    forbidden = (
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "SECOND_RUNTIME_PLANE",
        "USER_DEVICE_PREREQUISITE",
    )
    for token in forbidden:
        assert token not in source
