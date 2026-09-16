from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_canonical_dispatcher_registers_mir_consumer():
    dispatcher = load(ROOT / "scripts/dispatch_resident_execution_requests.py", "mir_dispatcher")
    by_name = dict(dispatcher.CONSUMERS)
    assert by_name["mir_tvc_provider_roundtrip"] == "scripts/consume_mir_tvc_provider_roundtrip_request.py"


def test_mir_consumer_visits_existing_workercoordinator_entrypoint_without_authority_expansion(tmp_path):
    consumer = load(ROOT / "scripts/consume_mir_tvc_provider_roundtrip_request.py", "mir_consumer")
    runtime = tmp_path / "runtime"
    source = tmp_path / "source"
    runtime.mkdir(); source.mkdir()

    request_src = ROOT / consumer.REQUEST_REL
    request_dst = runtime / consumer.REQUEST_REL
    request_dst.parent.mkdir(parents=True, exist_ok=True)
    request_dst.write_text(request_src.read_text(encoding="utf-8"), encoding="utf-8")

    vector_src = ROOT / consumer.VECTOR_REL
    vector_dst = runtime / consumer.VECTOR_REL
    vector_dst.parent.mkdir(parents=True, exist_ok=True)
    vector_dst.write_text(vector_src.read_text(encoding="utf-8"), encoding="utf-8")

    entrypoint = runtime / consumer.TARGET_ENTRYPOINT
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("# placeholder\n", encoding="utf-8")

    observed = {}
    def runner(command, **kwargs):
        observed["command"] = command
        observed["env"] = kwargs["env"]
        payload = {
            "schema": "stegverse.resident-refresh-targeted-execution/v3",
            "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
            "task_id": consumer.TARGET_TASK,
            "runtime_execution_attempted": True,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        }
        return subprocess.CompletedProcess(command, 0, json.dumps(payload) + "\n", "")

    receipt = consumer.consume(
        source,
        runtime,
        runner=runner,
        env={
            "PATH": "/usr/bin",
            "STEGVERSE_TVC_ROOT": "/srv/stegverse/tvc",
            "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET": "/run/stegverse/vault-broker.sock",
            "GITHUB_TOKEN": "must-not-forward",
        },
    )
    assert receipt["state"] == "ATTEMPT_RECORDED"
    assert receipt["task_id"] == consumer.TARGET_TASK
    assert receipt["provider_request_id"] == "MIR-RUN2-EVENT-001"
    assert receipt["provider_operation"] == "SUBMIT_EVENT"
    assert receipt["runtime_execution_attempted"] is True
    assert receipt["request_granted_authority"] is False
    assert receipt["provider_credential_material_allowed"] is False
    assert receipt["heartbeat_grants_execution_authority"] is False
    assert receipt["github_token_runtime_authority"] == "NONE"
    assert receipt["second_machine_required"] is False
    assert "GITHUB_TOKEN" not in observed["env"]
    assert observed["env"]["STEGVERSE_TVC_ROOT"] == "/srv/stegverse/tvc"
    assert observed["env"]["STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET"] == "/run/stegverse/vault-broker.sock"
    assert observed["command"][-2:] == ["--task-id", consumer.TARGET_TASK]
    retained = json.loads((runtime / consumer.CONSUMPTION_REL).read_text(encoding="utf-8"))
    assert retained == receipt
