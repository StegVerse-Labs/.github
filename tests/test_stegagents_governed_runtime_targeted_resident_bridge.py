import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEGAGENTS-GOVERNED-RUNTIME-001"
COSV = "71000000101001"


def test_targeted_request_is_non_authorizing_and_exactly_bound():
    request = json.loads((ROOT / "control/resident-execution-request.d/stegagents-governed-runtime-targeted-001.json").read_text())
    assert request["task_id"] == TASK
    assert request["cosv_task_vector"] == COSV
    assert request["mode"] == "TARGETED_INDEPENDENT_TASK_CONTROL"
    assert request["entrypoint"] == "scripts/refresh_and_execute_resident_task.py"
    assert request["argv"] == ["--task-id", TASK, "--cosv-task-vector", COSV]
    assert request["request_granted_authority"] is False
    assert request["provider_credential_material_allowed"] is False
    assert request["github_token_runtime_authority"] == "NONE"
    assert request["credential_authority"] == "TV/TVC"


def test_existing_dispatcher_and_source_refresh_carry_targeted_bridge():
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    refresh_base = (ROOT / "scripts/refresh_sovereign_worker_runtime_source_base.py").read_text()
    consumer = (ROOT / "scripts/consume_stegagents_governed_runtime_targeted_request.py").read_text()
    assert '("stegagents_governed_runtime_targeted", "scripts/consume_stegagents_governed_runtime_targeted_request.py")' in dispatcher
    assert 'Path("scripts/consume_stegagents_governed_runtime_targeted_request.py")' in refresh
    assert 'Path("scripts/consume_stegagents_governed_runtime_targeted_request.py")' in refresh_base
    assert 'refresh_and_execute_resident_task.py' in consumer
    assert '--cosv-task-vector' in consumer
    assert 'STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY' in consumer
    assert 'STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY' in consumer
    assert 'OPENAI_API_KEY' in consumer
