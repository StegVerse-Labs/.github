from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/stegagents_governed_runtime_worker.py"
OWNER_FRAGMENT = ROOT / "control/worker-registry.d/stegagents-governed-runtime-001.json"
PURPOSE_FRAGMENT = ROOT / "control/worker-registry.d/sdk-tt-purpose-bound-worker-runtime-proof-001.json"
ADAPTER = ROOT / "control/process-worker-adapters.d/stegagents-governed-runtime-001.json"
PURPOSE_HANDOFF = ROOT / "handoffs/SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001.json"


def load_worker():
    spec = importlib.util.spec_from_file_location("stegagents_governed_runtime_worker", WORKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def purpose_invocation(fence: int = 42) -> dict:
    handoff = json.loads(PURPOSE_HANDOFF.read_text(encoding="utf-8"))
    claim = f"SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001-G{fence}"
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001",
            "state": "ACTIVE",
            "claim_id": claim,
            "worker_id": "stegagents-governed-runtime-worker",
            "worker_instance_id": "worker-instance:purpose-bound-test",
            "heartbeat_timing": {"fencing_token": fence},
        },
        "scope": {"claim_id": claim, "fencing_token": fence},
        "handoff": handoff,
    }


def test_successor_uses_existing_worker_and_process_adapter_only():
    owner = json.loads(OWNER_FRAGMENT.read_text(encoding="utf-8"))
    purpose = json.loads(PURPOSE_FRAGMENT.read_text(encoding="utf-8"))
    adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))

    assert purpose["workers"] == []
    assert len(owner["workers"]) == 1
    existing = owner["workers"][0]
    process = adapter["adapters"][0]

    assert existing["worker_id"] == "stegagents-governed-runtime-worker"
    assert existing["adapter_ref"] == process["adapter_ref"] == "process:stegagents-governed-runtime-v1"
    assert process["command"] == ["python", "workers/stegagents_governed_runtime_worker.py"]
    assert "stegagents_purpose_bound_worker_lifecycle" in existing["capabilities"]
    assert "stegagents_purpose_bound_worker_lifecycle" in process["capabilities"]


def test_shared_worker_dispatches_successor_without_changing_owner_identity():
    m = load_worker()
    inv = purpose_invocation()
    task = m.validate_invocation(inv)
    assert task["task_id"] == m.PURPOSE_TASK_ID
    assert task["worker_id"] == m.WORKER_ID
    assert m.OWNER_TASK_ID == "STEGAGENTS-GOVERNED-RUNTIME-001"
    assert m.TASK_ID == m.OWNER_TASK_ID
    assert m._profile(m.OWNER_TASK_ID)["runtime_module"] == "src.governed_coderepair_runtime"
    assert m._profile(m.PURPOSE_TASK_ID)["runtime_module"] == "src.purpose_bound_worker_runtime"


def test_exact_purpose_capability_lifetime_tuple_is_carried_from_handoff():
    m = load_worker()
    inv = purpose_invocation()
    task = m.validate_invocation(inv)
    request = m.build_request(task, inv["handoff"])

    contract = inv["handoff"]["purpose_bound_worker_request"]
    candidate = contract["transition_cell"]["candidate"]
    carried = request["purpose_bound_worker_request"]["transition_cell"]["candidate"]

    assert request["schema"] == "stegverse.stegagents-purpose-bound-worker-request/v1"
    assert request["task_id"] == m.PURPOSE_TASK_ID
    assert request["cosv_task_vector"] == m.PURPOSE_COSV
    assert request["purpose_bound_worker_request"] == contract
    assert carried["purpose"] == candidate["purpose"]
    assert carried["required_capability"] == candidate["required_capability"] == "text.integrity_summary"
    assert carried["max_lifetime_seconds"] == candidate["max_lifetime_seconds"] == 30
    policy = carried["lifetime_policy"]
    assert policy["mode"] == "DERIVED_COST_TASK_DELAY_BUDGET"
    assert policy["profile"] == "DEMONSTRATION"
    assert policy["production_recompute_required"] is True
    assert policy["decomposition_target"] == "RECORDS_ENABLED_PACKET"
    assert sum(policy["time_budget_seconds"].values()) == carried["max_lifetime_seconds"]
    assert inv["handoff"]["execution"]["lifetime_semantics"]["demo_value_is_production_default"] is False
    assert inv["handoff"]["execution"]["lifetime_semantics"]["extension_requires_new_governed_recalculation"] is True
    assert request["worker_claim"]["worker_instance_id"] == "worker-instance:purpose-bound-test"


def test_purpose_result_requires_ordered_retirement_and_records_only_closeout():
    m = load_worker()
    profile = m._profile(m.PURPOSE_TASK_ID)
    result = {
        "state": "GOVERNED_PURPOSE_BOUND_WORKER_RETURNED",
        "execution_authority": False,
        "self_authorization_allowed": False,
        "provider_operation_required": False,
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "records_only": True,
        "worker_live_after_close": False,
        "continued_authority_after_retirement": False,
        "governance": {
            "chain_verified": True,
            "transaction_identity_continuous": True,
            "master_records_custody_status": "RECORDED",
            "external_side_effect": False,
        },
        "master_records_replay": {
            "operation_transition_custody_status": "RECORDED",
            "operation_receipt_ids": ["RP1"],
            "deterministic_disposition_match": True,
            "consequence_reexecuted": False,
        },
        "master_records_reconstruction": {
            "operation_transition_custody_status": "RECORDED",
            "operation_receipt_ids": ["OR1"],
        },
        "purpose_bound_worker_result": {
            "callable_retained": False,
            "executor_reference_retained": False,
            "lifecycle_receipts": [
                {"phase": "MATERIALIZED"},
                {"phase": "INVOCATION_STARTED"},
                {"phase": "TASK_COMPLETED"},
                {"phase": "RETIRED"},
            ],
        },
    }
    m._validate_result(profile, result)

    bad = json.loads(json.dumps(result))
    bad["purpose_bound_worker_result"]["lifecycle_receipts"][3]["phase"] = "TASK_COMPLETED"
    try:
        m._validate_result(profile, bad)
    except RuntimeError as exc:
        assert "lifecycle order" in str(exc)
    else:
        raise AssertionError("invalid lifecycle order accepted")

    bad = json.loads(json.dumps(result))
    bad["purpose_bound_worker_result"]["callable_retained"] = True
    try:
        m._validate_result(profile, bad)
    except RuntimeError as exc:
        assert "callable" in str(exc)
    else:
        raise AssertionError("records-only packet retaining callable accepted")


def test_successor_handoff_preserves_authority_boundaries():
    handoff = json.loads(PURPOSE_HANDOFF.read_text(encoding="utf-8"))
    authority = handoff["authority"]
    activation = handoff["activation"]
    assert authority["credential_authority"] == "TV/TVC"
    assert authority["github_token_production_authority"] == "NONE"
    assert authority["heartbeat_grants_execution_authority"] is False
    assert authority["request_grants_execution_authority"] is False
    assert authority["second_machine_required"] is False
    assert activation["targeted_execution"]["entrypoint"] == "scripts/run_worker_runtime.py"
    assert activation["targeted_execution"]["heartbeat_grants_execution_authority"] is False


def test_purpose_bound_targeted_runtime_reuses_shared_worker_without_runtime_owner_completion_gate() -> None:
    handoff = json.loads((ROOT / "handoffs/SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001.json").read_text(encoding="utf-8"))
    fragment = json.loads((ROOT / "control/worker-registry.d/sdk-tt-purpose-bound-worker-runtime-proof-001.json").read_text(encoding="utf-8"))
    assert handoff["task"]["dependencies"] == []
    assert handoff["task"]["runtime_predecessor_reconstruction_required"] is False
    assert handoff["task"]["runtime_capability_provider_task_id"] == "STEGAGENTS-GOVERNED-RUNTIME-001"
    assert handoff["activation"]["targeted_execution"]["requires_existing_separated_carrier_reference"] is False
    assert fragment["workers"] == []
    assert fragment["shared_worker_provider_fragment_refs"] == [
        "control/worker-registry.d/stegagents-governed-runtime-001.json"
    ]


def test_four_case_graph_is_wired_through_existing_workercoordinator_and_worker():
    runtime = (ROOT / "heartbeat_runtime/worker_runtime_legacy.py").read_text()
    worker = (ROOT / "workers/stegagents_governed_runtime_worker.py").read_text()
    handoff = json.loads((ROOT / "handoffs/SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001.json").read_text())

    assert "purpose_bound_state_graph_claim_bundle" in runtime
    assert "claim_authority" in runtime and "WORKERCOORDINATOR" in runtime
    assert "CASE_1" in runtime and "CASE_2" in runtime and "CASE_3" in runtime
    assert "TASK4_A" in runtime and "TASK4_B" in runtime and "TASK4_C" in runtime
    assert "claim_fence_master_records_transition" in runtime

    assert "build_state_graph_request" in worker
    assert "src.purpose_bound_worker_state_graph" in worker
    assert "WORKERCOORDINATOR_CLAIM_FENCE_BOUND" in worker
    assert "PURPOSE_BOUND_WORKER_TASK4_THREE_WAY_JOIN" in worker
    assert handoff["state_dependent_graph"]["enabled"] is True
    assert len(handoff["state_dependent_graph"]["single_worker_requests"]) == 3
    assert len(handoff["state_dependent_graph"]["task4_worker_requests"]) == 3
    assert handoff["state_dependent_graph"]["task4"]["worker_count"] == 3
