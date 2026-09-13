import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004"


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_sdk_extcollab_does_not_gate_on_remote_connected_device():
    record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
    vector = load_json(f"control/task-vectors/{TASK_ID}.json")
    correction = load_json(
        "receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-"
        "RUNTIME-SURFACE-CORRECTION-20260913.json"
    )

    binding = record["runtime_surface_binding"]
    requirements = record["runtime_requirements"]

    assert binding["selected_execution_surface"] == "CURRENT_USER_IPHONE"
    assert binding["remote_device_connector_applicable"] is False
    assert binding["connected_resident_device_required"] is False
    assert binding["second_user_operated_device_required"] is False
    assert binding["always_on_external_host_required"] is False

    assert requirements["selected_execution_surface"] == "CURRENT_USER_IPHONE"
    assert requirements["remote_device_connector_required"] is False
    assert requirements["connected_resident_device_required"] is False
    assert requirements["second_user_operated_device_required"] is False
    assert requirements["always_on_external_host_required"] is False

    assert record["runtime_resolution"] == "TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_NOT_OBSERVED"
    assert "authorized_remote_device_count" not in record["latest_runtime_observation"]
    assert "RECONNECTION" not in record["latest_runtime_observation"]["disposition"]

    metrics = vector["exact_metrics"]
    assert metrics["selected_execution_surface"] == "CURRENT_USER_IPHONE"
    assert metrics["remote_device_connector_applicable"] is False
    assert metrics["connected_resident_device_required"] is False
    assert metrics["runtime_resolution"] == "TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_NOT_OBSERVED"
    assert "authorized_remote_device_count" not in metrics

    assert correction["supersedes_as_current_gate"]["classification"] == "NOT_APPLICABLE"
    assert correction["canonical_execution_surface"]["surface"] == "CURRENT_USER_IPHONE"
    assert correction["canonical_execution_surface"]["remote_device_connector_required"] is False


def test_runtime_surface_correction_does_not_upgrade_execution_evidence():
    record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
    correction = load_json(
        "receipts/preflight/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004-"
        "RUNTIME-SURFACE-CORRECTION-20260913.json"
    )

    assert record["completion"]["claimed"] is False
    assert record["completion"]["validated"] is False
    assert correction["runtime_truth"]["this_task_workercoordinator_checkout_observed"] is False
    assert correction["runtime_truth"]["this_task_intr_admission_observed"] is False
    assert correction["runtime_truth"]["this_task_native_stegos_execution_observed"] is False
    assert correction["runtime_truth"]["completion_claimed"] is False
