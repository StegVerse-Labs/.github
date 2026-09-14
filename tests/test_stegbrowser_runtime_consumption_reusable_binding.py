import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"
HISTORICAL_TASK = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
COSV = "40000100100000"
RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("stegbrowser_runtime_consumption_reusable", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reusable_binding_targets_active_remediation_without_reopening_historical_goal():
    shard = json.loads((ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json").read_text())
    request = json.loads((ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json").read_text())
    active = json.loads((ROOT / "data/canonical-task-records" / f"{TASK}.json").read_text())
    historical = json.loads((ROOT / "data/canonical-task-records" / f"{HISTORICAL_TASK}.json").read_text())
    runner = RUNNER.read_text()

    assert shard["active_tracking_task_id"] == TASK
    assert shard["operation_lineage_task_id"] == HISTORICAL_TASK
    assert request["task_id"] == TASK
    assert request["operation_lineage_task_id"] == HISTORICAL_TASK
    assert request["cosv_task_vector"] == COSV
    assert request["reusable_task_binding"]["selected_execution_substrate"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert request["reusable_task_binding"]["manual_device_prerequisite"] is False
    assert request["reusable_task_binding"]["historical_task_reactivation_required"] is False
    assert active["execution_substrate_resolution"]["selected_substrate_id"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert active["coordination_state"] == "ACTIVE"
    assert historical["coordination_state"] == "RETIRED"
    assert 'TASK_ID = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"' in runner
    assert 'OPERATION_LINEAGE_TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"' in runner
    assert "SovereignLocalEventRuntimeAdapter" in runner
    assert "install_and_run_canonical_work_event_bootstrap.py" in runner
    assert "stage_runtime_ingress_projection" in runner
    assert 'projected_record["coordination_state"] = "PROPOSED"' in runner
    assert "AUTHENTIC_INTR_INGRESS_OBSERVED" in runner
    assert "CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED" in runner
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
    assert runtime_record["runtime_ingress_projection"]["operation_lineage_task_id"] == HISTORICAL_TASK
    assert projection["authority_effect"] == "NONE_RUNTIME_PROJECTION_ONLY"


def test_bootstrap_evidence_retention_is_exact_and_non_authorizing(tmp_path):
    module = load_runner()
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
