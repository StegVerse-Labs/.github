import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
HISTORICAL_TASK = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py"
LEGACY_RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.legacy.py"
REUSABLE_TASK = ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json"


def load_legacy_runner():
    spec = importlib.util.spec_from_file_location("stegbrowser_runtime_consumption_legacy", LEGACY_RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reusable_binding_targets_active_remediation_without_reopening_historical_goal():
    shard = json.loads(REUSABLE_TASK.read_text())
    request = json.loads((ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json").read_text())
    active = json.loads((ROOT / "data/canonical-task-records" / f"{TASK}.json").read_text())
    historical = json.loads((ROOT / "data/canonical-task-records" / f"{HISTORICAL_TASK}.json").read_text())
    runner = RUNNER.read_text()

    assert shard["active_tracking_task_id"] == TASK
    assert shard["operation_lineage_task_id"] == HISTORICAL_TASK
    assert request["task_id"] == TASK
    assert request["operation_lineage_task_id"] == HISTORICAL_TASK
    assert request["cosv_task_vector"] == COSV
    binding = request["reusable_task_binding"]
    assert binding["selected_execution_substrate"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert binding["manual_device_prerequisite"] is False
    assert binding["historical_task_reactivation_required"] is False
    assert binding["node_interlock_binding_required_before_lease"] is True
    assert binding["path_parameters"]["node_genesis_receipt"] == "STEGVERSE_NODE_GENESIS_RECEIPT"
    assert active["execution_substrate_resolution"]["selected_substrate_id"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert active["coordination_state"] == "ACTIVE"
    assert historical["coordination_state"] == "RETIRED"
    assert 'TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"' in runner
    assert 'OPERATION_LINEAGE_TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"' in runner
    assert "stage_runtime_ingress_projection" in runner
    assert 'projected_record["coordination_state"] = "PROPOSED"' in runner
    assert 'result.get("state") != INGRESS_APPEND_PREDICATE' in runner
    assert "workercoordinator_claim_fence_observed" in runner
    assert "node_interlock_lease_runtime_correlation_verified" in runner
    assert "GITHUB_TOKEN" not in runner


def test_runner_accepts_only_the_ingress_append_predicate():
    """#3012 K2: the ingress state is the A4 append predicate, not a passive observation."""
    runner = RUNNER.read_text()
    assert 'INGRESS_APPEND_PREDICATE = "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:INTERLOCK_INTR_INGRESS"' in runner
    assert 'result.get("state") != INGRESS_APPEND_PREDICATE' in runner
    assert 'mod.fail("organization_local_intr_ingress_not_observed")' in runner
    assert "AUTHENTIC_INTR_INGRESS_OBSERVED" not in runner


def test_reusable_contract_records_implemented_node_interlock_binding_pending_validation():
    shard = json.loads(REUSABLE_TASK.read_text())
    trace = shard["implementation_trace"]
    contract = shard["node_interlock_binding_contract"]
    legacy = LEGACY_RUNNER.read_text()

    assert shard["source_conformance_state"] == "NODE_INTERLOCK_BINDING_SOURCE_IMPLEMENTED_VALIDATION_PENDING"
    assert trace["manifest_binding"] == "IMPLEMENTED"
    assert trace["registered_stegverse_node_binding"] == "IMPLEMENTED_VIA_REQUIRED_NODE_GENESIS_RECEIPT"
    assert trace["interlock_binding_from_node"] == "IMPLEMENTED_FROM_VALIDATED_RECEIPT_1"
    assert trace["event_ephemeral_stegos_materialization"] == "IMPLEMENTED"
    assert trace["execution_time_runtime_identity"].startswith("IMPLEMENTED_AND_BOUND_BACK")
    assert contract["validator"].endswith("validate_node_genesis_receipt")
    assert contract["a4_exact_correlation_required"] is True
    assert contract["fail_closed_on_missing_or_mismatch"] is True
    assert "STEGVERSE_NODE_BOUND_TO_INVOCATION" in shard["completion_predicates"]
    assert "INTERLOCK_BOUND_TO_NODE_AND_MANIFEST" in shard["completion_predicates"]
    assert "INVOCATION_SCOPED_LEASE_ESTABLISHED" in shard["completion_predicates"]
    assert "EVENT_EPHEMERAL_STEGOS_RUNTIME_MATERIALIZED" in shard["completion_predicates"]
    assert "EXECUTION_TIME_RUNTIME_IDENTITY_BOUND" in shard["completion_predicates"]

    assert "validate_node_genesis_receipt" in legacy
    assert 'p.get("node_genesis_receipt")' in legacy
    assert '"manifest_sha256": manifest_sha256' in legacy
    assert '"node_id": node_id' in legacy
    assert '"interlock_id": interlock_id' in legacy
    assert '"registration_receipt_sha256": registration_receipt_sha256' in legacy
    assert "binding_sha256" in legacy
    assert "LeaseRequest(" in legacy
    assert "RuntimeClass.EVENT_EPHEMERAL" in legacy
    assert "RendezvousRequirement.NOT_REQUIRED" in legacy
    assert "SovereignLocalEventRuntimeAdapter" in legacy
    assert "adapter.provision(request)" in legacy
    assert "adapter.materialize(compute" in legacy
    assert 'runtime.get("lease_id") != lease_id' in legacy
    assert '"runtime_id": runtime_id' in legacy
    assert "NODE_RUNTIME_BINDING_RECEIPT" in legacy


def test_runtime_ingress_projection_preserves_canonical_active_state(tmp_path):
    module = load_legacy_runner()
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    record = {
        "schema": "stegverse.canonical-task-record/v1",
        "task_id": TASK,
        "correlation_id": TASK,
        "coordination_state": "ACTIVE",
        "checkout_state": "CHECKED_OUT",
        "allowed_next_transitions": ["INGRESS_ADMITTED"],
        "worker_claim": {
            "authority": "WORKERCOORDINATOR",
            "claim_ref": None,
            "fence_ref": None,
            "projection_only": True,
        },
    }
    source_record = source / "data/canonical-task-records" / f"{TASK}.json"
    source_registry = source / "data/canonical-task-registry.json"
    source_record.parent.mkdir(parents=True, exist_ok=True)
    source_record.write_text(json.dumps(record), encoding="utf-8")
    source_registry.write_text(json.dumps({"schema": "stegverse.canonical-task-registry/v1", "tasks": [record]}), encoding="utf-8")

    projection = module.stage_runtime_ingress_projection(source, runtime, record)

    canonical_after = json.loads(source_record.read_text())
    runtime_record = json.loads((runtime / "data/canonical-task-records" / f"{TASK}.json").read_text())
    runtime_registry = json.loads((runtime / "data/canonical-task-registry.json").read_text())
    projected_row = next(row for row in runtime_registry["tasks"] if row["task_id"] == TASK)

    assert canonical_after["coordination_state"] == "ACTIVE"
    assert runtime_record["coordination_state"] == "PROPOSED"
    assert projected_row["coordination_state"] == "PROPOSED"
    assert runtime_record["runtime_ingress_projection"]["source_mutated"] is False
    assert runtime_record["runtime_ingress_projection"]["claim_or_fence_minted"] is False
    assert runtime_record["runtime_ingress_projection"]["operation_lineage_task_id"] == HISTORICAL_TASK
    assert projection["authority_effect"] == "NONE_RUNTIME_PROJECTION_ONLY"


def test_node_runtime_binding_retention_is_exact(tmp_path):
    module = load_legacy_runner()
    ephemeral = tmp_path / "ephemeral"
    resident = tmp_path / "resident"
    value = {
        "schema": "stegverse.stegbrowser-node-interlock-runtime-binding/v1",
        "state": "NODE_INTERLOCK_LEASE_RUNTIME_BOUND",
        "node_id": "SV-NODE-test",
        "interlock_id": "SV-IL-test",
        "lease_id": "STEGBROWSER-test",
        "runtime_id": "LOCAL-EVENT-test",
    }
    module.retain_node_runtime_binding(ephemeral, resident, value)
    assert (ephemeral / module.NODE_RUNTIME_BINDING_RECEIPT).read_bytes() == (resident / module.NODE_RUNTIME_BINDING_RECEIPT).read_bytes()


def test_bootstrap_evidence_retention_is_exact_and_non_authorizing(tmp_path):
    module = load_legacy_runner()
    ephemeral = tmp_path / "ephemeral"
    resident = tmp_path / "resident"
    bootstrap = ephemeral / module.BOOTSTRAP_RECEIPT_REL
    bootstrap.parent.mkdir(parents=True, exist_ok=True)
    bootstrap.write_bytes((json.dumps({"state": "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED", "task_id": TASK}) + "\n").encode())

    custody = module.retain_bootstrap_evidence(ephemeral, resident, bootstrap)

    assert (resident / module.BOOTSTRAP_RECEIPT_REL).read_bytes() == bootstrap.read_bytes()
    assert custody["state"] == "AUTHENTIC_INTR_INGRESS_EVIDENCE_RETAINED_IN_EXISTING_RESIDENT_RUNTIME"
    assert custody["task_id"] == TASK
    assert custody["operation_lineage_task_id"] == HISTORICAL_TASK
    assert custody["claim_or_fence_minted"] is False
    assert custody["github_token_runtime_authority"] == "NONE"


def test_pre_verification_boundary_is_typed_fail_closed_not_an_ingress_claim(tmp_path):
    """#3012: the boundary is written before ingress readback, so it must not claim ingress."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_transition_disposition import non_allow_missing

    module = load_legacy_runner()
    boundary = module.remediation_boundary(tmp_path, {"node_id": "SV-NODE-test"}, {"source_mutated": False}, {"claim_or_fence_minted": False})

    assert boundary["disposition"] == "FAIL_CLOSED"
    assert boundary["state"] == "FAIL_CLOSED"
    assert boundary["failed_predicate"] == "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:INTERLOCK_INTR_INGRESS"
    assert boundary["consequence_committed"] is False
    assert "verified_organization_receipt" in boundary["satisfying_edge"]
    assert "ORGANIZATION_LEDGER_LOCK" in boundary["satisfying_edge"]
    assert boundary["retry_entrypoint"] == "scripts/run_stegbrowser_runtime_consumption_reusable.py"
    assert non_allow_missing(boundary) == []
    assert boundary["workercoordinator_claim_fence_observed"] is False
    assert boundary["completion_evidence_observed"] is False
    assert boundary["next_required_predicate"] == "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:WORKERCOORDINATOR_CLAIM_FENCE"
    assert boundary["authority_effect"] == "NONE_BOUNDARY_EVIDENCE_ONLY"
    text = json.dumps(boundary)
    assert "AUTHENTIC_INTR_INGRESS_OBSERVED" not in text
    assert "CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED" not in text
    assert "AUTHENTIC_INTR_INGRESS_OBSERVED" not in LEGACY_RUNNER.read_text()


def test_runner_retires_pre_verification_disposition_only_after_ingress_readback():
    runner = RUNNER.read_text()
    guard = 'projection.get("workercoordinator_claim_fence_observed") is True and projection.get("authentic_intr_ingress_observed") is True'
    assert guard in runner
    assert 'if boundary.get("failed_predicate") == INGRESS_APPEND_PREDICATE:' in runner
    assert '"authority_effect": "NONE_HISTORY_ONLY"' in runner
    assert runner.index(guard) < runner.index('boundary["state"] = INGRESS_APPEND_PREDICATE')
    # The readback that sets the projection flags rejects any other worker state.
    assert runner.index('result.get("state") != INGRESS_APPEND_PREDICATE') < runner.index('"authentic_intr_ingress_observed":True')
