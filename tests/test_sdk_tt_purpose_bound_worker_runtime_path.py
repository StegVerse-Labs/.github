from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
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


def test_workercoordinator_initializes_manifest_request_state_before_assignment_record_use():
    runtime = (ROOT / "heartbeat_runtime/worker_runtime_legacy.py").read_text(encoding="utf-8")
    function_start = runtime.index("    def _activate_from_trigger(")
    function_end = runtime.index("\n    def ", function_start + 10)
    body = runtime[function_start:function_end]

    assignment = 'manifest_runtime_request_present = manifest_runtime_request_path.is_file()'
    guarded_use = 'if manifest_runtime_request_present:'
    custody_call = 'assignment_custody = self._custody_assignment_transition('

    assert assignment in body
    assert guarded_use in body
    assert custody_call in body
    assert body.index(assignment) < body.index(guarded_use) < body.index(custody_call)


def test_manifest_bound_test1_retains_and_forwards_exact_claim_fence_predecessor():
    runtime = (ROOT / "heartbeat_runtime/worker_runtime_legacy.py").read_text(encoding="utf-8")
    worker = (ROOT / "workers/stegagents_governed_runtime_worker.py").read_text(encoding="utf-8")

    assert 'if task_id == "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001":' in runtime
    assert 'task["claim_fence_master_records_transition"] = dict(assignment_custody)' in runtime

    manifest_start = worker.index("def build_manifest_bound_purpose_request(")
    manifest_end = worker.index("\ndef _required_capability(", manifest_start)
    manifest_body = worker[manifest_start:manifest_end]
    assert '_closed_transition(' in manifest_body
    assert '"WORKERCOORDINATOR_CLAIM_FENCE_BOUND"' in manifest_body
    assert '"graph_predecessor_master_records_transition": predecessor' in manifest_body


def test_manifest_bound_test1_predecessor_is_exact_master_records_closure():
    m = load_worker()
    task = {
        "task_id": m.PURPOSE_TASK_ID,
        "claim_id": "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001-G42",
        "worker_id": m.WORKER_ID,
        "worker_instance_id": "worker-instance:test1",
        "heartbeat_timing": {"fencing_token": 42},
        "claim_fence_master_records_transition": {
            "transition_id": "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": "a" * 64,
            "reconstructed_receipt_sha256": "a" * 64,
            "master_record_ref": "master-record:state-transition:sha256:" + "a" * 64,
        },
    }
    handoff = json.loads(PURPOSE_HANDOFF.read_text(encoding="utf-8"))
    contract = handoff["purpose_bound_worker_request"]
    runtime_request = {
        "state_graph": {"request": contract},
        "canonical_manifest_sha256": "b" * 64,
        "graph_id": "graph:test1",
        "processing_capability": "governance",
        "route_id": "route:test1",
        "request_sha256": "c" * 64,
    }
    request = m.build_manifest_bound_purpose_request(task, runtime_request)
    predecessor = request["graph_predecessor_master_records_transition"]
    assert predecessor["transition_id"] == "WORKERCOORDINATOR_CLAIM_FENCE_BOUND"
    assert predecessor["state"] == "RECORDED"
    assert predecessor["reconstruction_status"] == "PASS"
    assert predecessor["required_evidence_validation_status"] == "PASS"
    assert predecessor["receipt_sha256"] == predecessor["reconstructed_receipt_sha256"] == "a" * 64

def test_workercoordinator_does_not_project_purpose_task_active_before_governed_activation():
    runtime = (ROOT / "heartbeat_runtime/worker_runtime_legacy.py").read_text(encoding="utf-8")
    function_start = runtime.index("    def _activate_from_trigger(")
    function_end = runtime.index("\n    def ", function_start + 10)
    body = runtime[function_start:function_end]

    custody_call = 'assignment_custody = self._custody_assignment_transition('
    purpose_branch = 'if task_id == "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001":'
    provisional = '"state": "ACTIVE",'
    terminal_projection = '"state": "COMPLETED",'
    purpose_branch_end = '        if self._atomic_constitutive_activation_required(handoff):'

    purpose_start = body.index(purpose_branch, body.index(custody_call))
    purpose_end = body.index(purpose_branch_end, purpose_start)
    purpose_body = body[purpose_start:purpose_end]

    assert body.index(custody_call) < purpose_start
    assert provisional in purpose_body
    assert terminal_projection in purpose_body
    assert 'task_active_projected_before_governed_activation=False' in purpose_body
    assert 'task.update({\n                "state": "ACTIVE",' not in purpose_body



def test_purpose_bound_worker_cost_basis_resolves_existing_expiry_gate():
    from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator
    from scripts.run_worker_runtime import load_adapters

    purpose = json.loads(PURPOSE_FRAGMENT.read_text(encoding="utf-8"))
    task = purpose["tasks"][0]
    cost_path = ROOT / task["cost_basis_ref"]
    assert cost_path.is_file()

    cost = json.loads(cost_path.read_text(encoding="utf-8"))
    handoff = json.loads(PURPOSE_HANDOFF.read_text(encoding="utf-8"))
    assert cost["schema"] == "stegverse.worker-runtime-cost-basis/v0.1"
    assert cost["task_class"] == "stegagents_governed_runtime"
    assert cost["hb_estimate"]["expiry_candidate_beats"] == handoff["execution"]["runtime_window_beats"] == 4096
    assert cost["hb_estimate"]["confidence"] != "NONE"

    runtime = WorkerCoordinator(ROOT, adapters=load_adapters(ROOT))
    budget, basis = runtime._expiry_budget(task)
    assert budget == 4096
    assert basis == "TASK_CLASS_COST_BASIS"

def test_purpose_post_claim_issues_fresh_tvc_warrant_through_existing_service():
    m = load_worker()
    claim_id = "SHWP-SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001-G42"
    task = {
        "task_id": m.PURPOSE_TASK_ID,
        "claim_id": claim_id,
        "claim_fence_master_records_transition": {
            "transition_id": "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": "a" * 64,
            "reconstructed_receipt_sha256": "a" * 64,
        },
    }
    commit_sha = "b" * 40
    calls = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        agents = root / "StegAgents"
        agents.mkdir()
        request_root = root / "requests"
        receipt_root = root / "receipts"

        def runner(command, **kwargs):
            calls.append(command)
            if command[0] == "git":
                return subprocess.CompletedProcess(command, 0, stdout=commit_sha + "\n", stderr="")
            assert command == ["systemctl", "start", m.TVC_WARRANT_SERVICE_TEMPLATE.format(instance=claim_id)]
            request = json.loads((request_root / f"{claim_id}.json").read_text(encoding="utf-8"))
            assert request["task_id"] == m.PURPOSE_TASK_ID
            assert request["commit_sha"] == commit_sha
            warrant = {
                "warrant_id": f"tvc:{claim_id}",
                "issuer": "tv.warrant.resident",
                "issued_at": "2026-09-21T00:00:00Z",
                "expires_at": "2026-09-21T00:15:00Z",
                "policy": {"bundle_sha256": "c" * 64},
                "claims": {"repo": m.STEGAGENTS_REPO, "commit_sha": commit_sha, "task_id": m.PURPOSE_TASK_ID},
                "scope": {"action": "run_agent", "module": m.STEGAGENTS_REPO},
                "signature": {"alg": "ed25519", "public_key_id": "tv.warrant.resident.ed25519.001", "sig_b64": "sig"},
            }
            receipt_root.mkdir(parents=True, exist_ok=True)
            (receipt_root / f"{claim_id}.json").write_text(json.dumps({
                "schema": "stegverse.tvc.execution-warrant-issuance/v1",
                "state": "ISSUED",
                "credential_authority": "TV/TVC",
                "issuer_pubkey_b64": "pubkey",
                "policy_bundle_sha256": "c" * 64,
                "max_ttl_seconds": 900,
                "warrant": warrant,
                "private_key_exposed": False,
                "private_key_persisted": False,
            }), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        env = m._fresh_tvc_warrant_env(
            task=task,
            agents_root=agents,
            runner=runner,
            request_root=request_root,
            receipt_root=receipt_root,
        )

    assert calls[0][:3] == ["git", "-C", str(agents)]
    assert calls[1][0:2] == ["systemctl", "start"]
    assert json.loads(env["STEGVERSE_WARRANT_JSON"])["claims"]["commit_sha"] == commit_sha
    assert env["TV_POLICY_BUNDLE_SHA256"] == "c" * 64
    assert env["TV_WARRANT_ISSUER_PUBKEY_B64"] == "pubkey"
    assert env["TV_WARRANT_MAX_TTL_SECONDS"] == "900"


def test_purpose_post_claim_warrant_bridge_requires_closed_claim_fence():
    m = load_worker()
    task = {"task_id": m.PURPOSE_TASK_ID, "claim_id": "claim", "claim_fence_master_records_transition": {}}
    with tempfile.TemporaryDirectory() as td:
        try:
            m._fresh_tvc_warrant_env(
                task=task,
                agents_root=Path(td),
                runner=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("runner must not execute")),
                request_root=Path(td) / "requests",
                receipt_root=Path(td) / "receipts",
            )
        except RuntimeError as exc:
            assert "WORKERCOORDINATOR_CLAIM_FENCE_BOUND transition" in str(exc)
        else:
            raise AssertionError("TVC issuance ran without closed claim/fence")
