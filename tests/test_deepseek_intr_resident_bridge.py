from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "deepseek_consumer",
    ROOT / "control/resident-execution-request.d/consume-deepseek-intr-runtime.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def request():
    return json.loads((ROOT / mod.REQUEST_REL).read_text())


def bridge(state="BLOCKED"):
    return {
        "schema": "stegverse.resident-refresh-targeted-execution/v2",
        "mode": mod.TARGET_MODE,
        "task_id": mod.TARGET_TASK,
        "runtime_execution_attempted": True,
        "network_fetch_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        "execution_result": {"state": state},
    }


def test_request_is_non_authorizing_and_single_machine():
    value = request()
    mod.validate_request(value)
    assert value["request_granted_authority"] is False
    assert value["heartbeat_grants_execution_authority"] is False
    assert value["provider_credential_material_allowed"] is False
    assert value["second_machine_required"] is False
    assert value["master_records_custody_required_for_egress"] is True
    assert value["same_execution_required"] is True


def test_consumer_invokes_existing_targeted_runner_and_strips_secrets():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source"; source.mkdir()
        runtime = root / "runtime"
        request_path = runtime / mod.REQUEST_REL
        request_path.parent.mkdir(parents=True)
        request_path.write_text(json.dumps(request()) + "\n")
        entry = runtime / mod.TARGET_ENTRYPOINT
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("# existing bridge\n")
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(returncode=0, stdout=json.dumps(bridge()) + "\n", stderr="")
        result = mod.consume(
            source,
            runtime,
            runner=runner,
            env={
                "PATH": "/bin",
                "HOME": "/home/sv",
                "STEGVERSE_LLM_ADAPTER_ROOT": "/srv/llm-adapter",
                "STEGVERSE_TVC_ROOT": "/srv/tvc",
                "STEGVERSE_STEGCORE_SOURCE_ROOT": "/srv/stegcore",
                "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": "/srv/master-records",
                "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET": "/run/stegverse/vault-broker.sock",
                "GITHUB_TOKEN": "forbidden",
                "DEEPSEEK_API_KEY": "forbidden",
                "STEGVERSE_MASTER_RECORDS_TOKEN": "forbidden",
            },
        )
        assert result["state"] == "ATTEMPT_RECORDED"
        assert len(calls) == 1
        command, kwargs = calls[0]
        assert command[-2:] == ["--task-id", mod.TARGET_TASK]
        forwarded = kwargs["env"]
        assert forwarded["STEGVERSE_LLM_ADAPTER_ROOT"] == "/srv/llm-adapter"
        assert forwarded["STEGVERSE_TVC_ROOT"] == "/srv/tvc"
        assert forwarded["STEGVERSE_STEGCORE_SOURCE_ROOT"] == "/srv/stegcore"
        assert forwarded["STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"] == "/srv/master-records"
        assert forwarded["STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET"] == "/run/stegverse/vault-broker.sock"
        assert "GITHUB_TOKEN" not in forwarded
        assert "DEEPSEEK_API_KEY" not in forwarded
        assert "STEGVERSE_MASTER_RECORDS_TOKEN" not in forwarded


def test_completed_worker_result_becomes_terminal_consumption():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source"; source.mkdir()
        runtime = root / "runtime"
        request_path = runtime / mod.REQUEST_REL
        request_path.parent.mkdir(parents=True)
        request_path.write_text(json.dumps(request()) + "\n")
        entry = runtime / mod.TARGET_ENTRYPOINT
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("# bridge\n")
        result = mod.consume(
            source,
            runtime,
            runner=lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(bridge("COMPLETED")) + "\n", stderr=""),
            env={"PATH": "/bin", "HOME": "/home/sv"},
        )
        assert result["state"] == "COMPLETED"
        assert result["terminal"] is True
        assert result["runtime_execution_attempted"] is True


def test_dispatcher_and_worker_registration_are_single_path():
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    assert '("deepseek_intr_runtime", "control/resident-execution-request.d/consume-deepseek-intr-runtime.py")' in dispatcher
    assert "scripts/consume_deepseek_intr_runtime_request.py" not in dispatcher
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/deepseek-intr-runtime-001.json").read_text())
    assert adapter["adapters"][0]["command"] == ["python", "workers/deepseek_intr_runtime_worker.py"]
    registry = json.loads((ROOT / "control/worker-registry.d/deepseek-intr-runtime-001.json").read_text())
    assert registry["tasks"][0]["task_id"] == mod.TARGET_TASK
    assert registry["tasks"][0]["executor_binding"] == "AUTHORIZED"
    assert registry["tasks"][0]["admission"]["fresh_fence_required"] is True


def test_worker_source_requires_exact_runtime_boundaries():
    worker = (ROOT / "workers/deepseek_intr_runtime_worker.py").read_text()
    assert "evaluate_interlock" in worker
    assert "tvc_issue_deepseek_intr_lease" in worker
    assert "execute_governed_deepseek_via_tvc_runtime" in worker
    assert "admit_deepseek_tvc_runtime_egress" in worker
    assert "MASTER_RECORDS_CUSTODY_NOT_RECORDED" in worker
    assert '"credential_material_present": False' in worker
    assert '"second_machine_required": False' in worker
