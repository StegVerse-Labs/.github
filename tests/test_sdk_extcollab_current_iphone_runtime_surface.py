import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004"


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_sdk_extcollab_binds_to_established_node_not_physical_device():
    record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
    vector = load_json(f"control/task-vectors/{TASK_ID}.json")
    invariant = load_json("data/task-registry-global-invariants.json")
    correction = load_json(
        "receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-"
        "NODE-KV-CONTINUITY-CORRECTION-20260913.json"
    )

    binding = record["runtime_surface_binding"]
    requirements = record["runtime_requirements"]
    global_inv = invariant["invariants"]

    assert global_inv["stegos_device_role"] == "INTERCHANGEABLE_TRANSPORT_NODE"
    assert global_inv["physical_device_identity_gate"] == "NONE_PROHIBITED"
    assert global_inv["user_verification_authority"] == "KV/SKAP Vault"

    assert binding["eligible_execution_surface"] == "ANY_SUPPORTED_STEGOS_CAPABLE_DEVICE"
    assert binding["established_node_required"] is True
    assert binding["specific_physical_device_required"] is False
    assert binding["specific_iphone_required"] is False
    assert binding["physical_device_identity_gate"] is False
    assert binding["remote_device_connector_applicable"] is False
    assert binding["node_may_be_established_or_recovered_on_any_eligible_device"] is True
    assert binding["device_identity_is_execution_metadata_only"] is True

    assert requirements["eligible_execution_surface"] == "ANY_SUPPORTED_STEGOS_CAPABLE_DEVICE"
    assert requirements["established_node_required"] is True
    assert requirements["specific_physical_device_required"] is False
    assert requirements["specific_iphone_required"] is False
    assert requirements["physical_device_identity_gate"] is False
    assert requirements["user_verification_source"] == "KV/SKAP Vault"

    assert record["runtime_resolution"] == "TASK_BOUND_ESTABLISHED_NODE_EXECUTION_EVIDENCE_NOT_OBSERVED"
    assert "ONE_CURRENT_DEVICE_END_TO_END_PROVEN" not in record["remaining_predicates"]
    assert "ESTABLISHED_NODE_END_TO_END_PROVEN" in record["remaining_predicates"]

    metrics = vector["exact_metrics"]
    assert metrics["eligible_execution_surface"] == "ANY_SUPPORTED_STEGOS_CAPABLE_DEVICE"
    assert metrics["established_node_required"] is True
    assert metrics["specific_iphone_required"] is False
    assert metrics["physical_device_identity_gate"] is False
    assert metrics["runtime_resolution"] == "TASK_BOUND_ESTABLISHED_NODE_EXECUTION_EVIDENCE_NOT_OBSERVED"
    assert "one_current_device_end_to_end_proven" not in metrics
    assert metrics["established_node_end_to_end_proven"] is False

    assert correction["execution_model"]["established_node_required"] is True
    assert correction["execution_model"]["specific_iphone_required"] is False
    assert correction["continuity_model"]["user_verification_authority"] == "KV/SKAP Vault"
    assert correction["predicate_reconciliation"]["replacement"] == "ESTABLISHED_NODE_END_TO_END_PROVEN"


def test_prior_current_iphone_correction_is_historical_not_goal_binding():
    prior = load_json(
        "receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-"
        "RUNTIME-SURFACE-CORRECTION-20260913.json"
    )
    record = load_json(f"data/canonical-task-records/{TASK_ID}.json")

    # Preserve the prior correction as provenance: it correctly removed the remote
    # connector gate, but its CURRENT_USER_IPHONE surface is no longer the Goal gate.
    assert prior["supersedes_as_current_gate"]["classification"] == "NOT_APPLICABLE"
    assert prior["canonical_execution_surface"]["surface"] == "CURRENT_USER_IPHONE"
    assert record["runtime_surface_binding"]["specific_iphone_required"] is False
    assert record["runtime_surface_binding"]["device_identity_is_execution_metadata_only"] is True


def test_node_kv_correction_does_not_upgrade_runtime_evidence():
    record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
    correction = load_json(
        "receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-"
        "NODE-KV-CONTINUITY-CORRECTION-20260913.json"
    )

    assert record["completion"]["claimed"] is False
    assert record["completion"]["validated"] is False
    assert correction["runtime_truth"]["this_task_workercoordinator_checkout_observed"] is False
    assert correction["runtime_truth"]["this_task_intr_admission_observed"] is False
    assert correction["runtime_truth"]["this_task_established_node_execution_observed"] is False
    assert correction["runtime_truth"]["applicable_kv_skap_continuity_binding_observed"] is False
    assert correction["runtime_truth"]["completion_claimed"] is False
