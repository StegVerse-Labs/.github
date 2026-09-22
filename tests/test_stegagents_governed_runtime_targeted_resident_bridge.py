import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEGAGENTS-GOVERNED-RUNTIME-001"
COSV = "71000000101001"
PURPOSE_TASK = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"
PURPOSE_COSV = "71000000111111"
SELECTOR = "stegagents_governed_runtime_targeted"
GOVERNANCE_ENV = (
    "STEGVERSE_WARRANT_JSON",
    "TV_POLICY_BUNDLE_SHA256",
    "TV_WARRANT_ISSUER_PUBKEY_B64",
    "TV_WARRANT_MAX_TTL_SECONDS",
)
MASTER_RECORDS_ENV = (
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ENDPOINT",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
    "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
    "MASTER_RECORDS_DB",
    "MASTER_RECORDS_RECEIPT_KEY",
    "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
)


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


def test_existing_dispatcher_source_refresh_and_portable_bridge_carry_targeted_selector():
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    refresh_base = (ROOT / "scripts/refresh_sovereign_worker_runtime_source_base.py").read_text()
    portable = (ROOT / "scripts/refresh_and_dispatch_resident_requests.py").read_text()
    consumer = (ROOT / "scripts/consume_stegagents_governed_runtime_targeted_request.py").read_text()
    assert f'("{SELECTOR}", "scripts/consume_stegagents_governed_runtime_targeted_request.py")' in dispatcher
    assert 'Path("scripts/consume_stegagents_governed_runtime_targeted_request.py")' in refresh
    assert 'Path("scripts/consume_stegagents_governed_runtime_targeted_request.py")' in refresh_base
    assert f'"{SELECTOR}"' in portable
    assert 'choices=ALLOWED_TARGET_CONSUMERS' in portable
    assert 'refresh_and_execute_resident_task.py' in consumer
    assert '--cosv-task-vector' in consumer
    assert 'STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY' in consumer
    assert 'STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY' in consumer
    assert 'OPENAI_API_KEY' in consumer


def test_governance_warrant_inputs_are_carried_end_to_end_without_becoming_provider_credentials():
    portable = (ROOT / "scripts/refresh_and_dispatch_resident_requests.py").read_text()
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    consumer = (ROOT / "scripts/consume_stegagents_governed_runtime_targeted_request.py").read_text()
    targeted = (ROOT / "scripts/refresh_and_execute_resident_task.py").read_text()
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/stegagents-governed-runtime-001.json").read_text())
    worker = (ROOT / "workers/stegagents_governed_runtime_worker.py").read_text()
    env_allowlist = adapter["adapters"][0]["env_allowlist"]
    for name in GOVERNANCE_ENV:
        assert name in portable
        assert name in dispatcher
        assert name in consumer
        assert name in targeted
        assert name in env_allowlist
    for name in MASTER_RECORDS_ENV:
        assert name in consumer
        assert name in targeted
        assert name in env_allowlist
    assert 'warrant_policy_binding' in worker
    assert 'warrant_verified' in worker
    assert 'policy_bundle_verified' in worker
    assert 'provider credential material exposed to StegAgents' in worker


def test_purpose_bound_graph_request_reuses_same_targeted_resident_consumer():
    request = json.loads((ROOT / "control/resident-execution-request.d/sdk-tt-purpose-bound-worker-runtime-proof-001.json").read_text())
    assert request["task_id"] == PURPOSE_TASK
    assert request["cosv_task_vector"] == PURPOSE_COSV
    assert request["mode"] == "TARGETED_INDEPENDENT_TASK_CONTROL"
    assert request["argv"] == ["--task-id", PURPOSE_TASK, "--cosv-task-vector", PURPOSE_COSV]
    assert request["request_granted_authority"] is False
    assert request["heartbeat_grants_execution_authority"] is False
    assert request["second_machine_required"] is False
    consumer = (ROOT / "scripts/consume_stegagents_governed_runtime_targeted_request.py").read_text()
    assert "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001" in consumer
    assert "71000000111111" in consumer
    assert "PURPOSE_REQUEST_REL" in consumer


def test_targeted_consumer_preserves_master_records_custody_transport_inputs():
    import importlib.util
    module_path = ROOT / "scripts/consume_stegagents_governed_runtime_targeted_request.py"
    spec = importlib.util.spec_from_file_location("targeted_consumer", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = {
        "PATH": "/bin",
        "HOME": "/home/stegverse",
        "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": "/srv/master-records/orchestration",
        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/srv/master-records/orchestration",
        "STEGVERSE_MASTER_RECORDS_ENDPOINT": "http://127.0.0.1:8765",
        "STEGVERSE_MASTER_RECORDS_TOKEN": "mr-token",
        "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS": "12",
        "MASTER_RECORDS_DB": "/srv/stegverse/master-records.sqlite",
        "MASTER_RECORDS_RECEIPT_KEY": "receipt-key",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
        "GITHUB_TOKEN": "must-not-survive",
        "OPENAI_API_KEY": "must-not-survive",
    }
    env = module.clean_env(source)
    for name in MASTER_RECORDS_ENV:
        assert env[name] == source[name]
    assert "GITHUB_TOKEN" not in env
    assert "OPENAI_API_KEY" not in env
    assert env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] == "TV/TVC"
    assert env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] == "NONE"
