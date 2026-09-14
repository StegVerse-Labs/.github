import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"


def test_reusable_binding_preserves_selected_ephemeral_substrate_and_authority():
    shard = json.loads((ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json").read_text())
    request = json.loads((ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json").read_text())
    record = json.loads((ROOT / "data/canonical-task-records" / f"{TASK}.json").read_text())
    runner = (ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py").read_text()

    assert shard["reusable_task_id"] == "RT-STEGBROWSER-RUNTIME-CONSUMPTION-001"
    assert shard["runner_templates"] == ["scripts/run_stegbrowser_runtime_consumption_reusable.py"]
    assert request["task_id"] == TASK
    assert request["cosv_task_vector"] == COSV
    assert request["reusable_task_binding"]["selected_execution_substrate"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert request["reusable_task_binding"]["manual_device_prerequisite"] is False
    assert record["execution_substrate_resolution"]["selected_substrate_id"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert record["execution_substrate_resolution"]["external_device_required"] is False
    assert record["execution_substrate_resolution"]["second_user_operated_device_allowed"] is False

    assert "SovereignLocalEventRuntimeAdapter" in runner
    assert "consume-canonical-work-coordination-bootstrap.py" in runner
    assert "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY" in runner
    assert "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY" in runner
    assert "OWNER_INGRESS_READY_OBSERVED" in runner
    assert "stegbrowser-tvc-source-promotion-request-consumption.latest.json" in runner
    assert "GITHUB_TOKEN" not in runner
