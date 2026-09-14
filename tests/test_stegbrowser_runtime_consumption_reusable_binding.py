import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("stegbrowser_runtime_consumption_reusable", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reusable_binding_preserves_selected_ephemeral_substrate_and_authority():
    shard = json.loads((ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json").read_text())
    request = json.loads((ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json").read_text())
    record = json.loads((ROOT / "data/canonical-task-records" / f"{TASK}.json").read_text())
    runner = RUNNER.read_text()

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
    assert "stage_runtime_ingress_projection" in runner
    assert 'projected_record["coordination_state"] = "PROPOSED"' in runner
    assert "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY" in runner
    assert "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY" in runner
    assert "OWNER_INGRESS_READY_OBSERVED" in runner
    assert "stegbrowser-tvc-source-promotion-request-consumption.latest.json" in runner
    assert "GITHUB_TOKEN" not in runner


def test_runtime_ingress_projection_preserves_canonical_active_state(tmp_path):
    module = load_runner()
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
    assert projection["authority_effect"] == "NONE_RUNTIME_PROJECTION_ONLY"
