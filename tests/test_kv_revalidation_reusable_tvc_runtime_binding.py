import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "KV-CONNECTION-REVALIDATION-WORKER-001"
COSV = "50000000102000"
RT_ID = "RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001"
RUNNER = "scripts/run_tvc_runtime_boundary_reusable.py"
MANIFEST = "manifests/reusable-task-invocations/KV-CONNECTION-REVALIDATION-WORKER-001.TVC-CAPABILITY-RUNTIME-002.json"
REQUEST = "control/resident-execution-request.d/canonical-work-kv-connection-revalidation-tvc-runtime-001.json"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_registry_uses_local_admitted_runner():
    shard = load("source-bundles/reusable-task-registry.d/RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001.json")
    assert shard["reusable_task_id"] == RT_ID
    assert shard["runner_templates"] == [RUNNER]
    assert "RT-TVC-PRIMARY-RUNTIME-BINDING-001" in shard["composes"]
    assert (ROOT / RUNNER).is_file()


def test_manifest_and_request_bind_exact_goal_cosv_once():
    manifest = load(MANIFEST)
    request = load(REQUEST)
    assert manifest["task_id"] == TASK_ID
    assert manifest["cosv_task_vector"] == COSV
    assert manifest["reusable_task_id"] == RT_ID
    assert manifest["automation_plan"]["declared_runner_refs"] == [RUNNER]
    assert manifest["runner_plan"]["materialization_refs"] == [RUNNER]
    assert request["task_id"] == TASK_ID
    assert request["cosv_task_vector"] == COSV
    binding = request["reusable_task_binding"]
    assert binding["reusable_task_id"] == RT_ID
    assert binding["runner"] == RUNNER
    assert binding["manifest_ref"] == MANIFEST
    assert binding["manifest_hash"] == manifest["manifest_hash"]
    assert binding["manual_device_prerequisite"] is False
    assert binding["persistent_runner_required"] is False
    assert binding["second_scheduler_required"] is False
    assert request["google_consent_allowed"] is False
    assert request["provider_connect_verify_allowed"] is False
    assert request["kv2_materialization_allowed"] is False


def test_existing_kv_process_adapter_remains_unchanged_and_enabled():
    adapters = load("control/process-worker-adapters.d/kv-connection-revalidation-worker-001.json")
    adapter = adapters["adapters"][0]
    assert adapter["adapter_ref"] == "process:kv-connection-revalidation-v1"
    assert adapter["enabled"] is True
    assert "runtime_observation" in adapter["capabilities"]
    assert "bounded_process_execution" in adapter["capabilities"]
    assert "private_kv_state_reconciliation" in adapter["capabilities"]


def test_runner_reuses_released_same_service_activation_delivery():
    source = (ROOT / RUNNER).read_text(encoding="utf-8")
    assert "install_tvc_primary_runtime_service.py" in source
    assert '"--activate"' in source
    assert '[sys.executable, str(dispatcher), "tvc.primary_runtime_binder.activate"]' not in source


def test_neutral_runner_does_not_mint_tvc_activation_authority_or_preflight():
    source = (ROOT / RUNNER).read_text(encoding="utf-8")
    assert "STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY" not in source
    assert "tvc.primary_runtime_binder.preflight" not in source
    assert "install_tvc_primary_runtime_service.py" in source
    assert '"--activate"' in source
