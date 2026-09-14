from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import consume_kv_ai_memory_resident_request as consumer
from scripts import dispatch_resident_execution_requests as dispatcher
from workers import kv_ai_memory_resident_worker as worker

ROOT = Path(__file__).resolve().parents[1]


def invocation():
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": "SV-KV-AI-PERSISTENCE-001",
            "state": "ACTIVE",
            "claim_id": "SV-KV-AI-PERSISTENCE-001-G1",
            "heartbeat_timing": {"fencing_token": 1},
        },
        "scope": {
            "claim_id": "SV-KV-AI-PERSISTENCE-001-G1",
            "fencing_token": 1,
            "bound_state_enabled": True,
        },
    }


def materialized_payload():
    return {
        "schema": "stegverse.llm-adapter.kv-memory-provider-request-materialization/v1",
        "state": "PROVIDER_REQUEST_MATERIALIZED",
        "provider_request": {"provider": "fixture", "model": "fixture", "messages": []},
        "provider_request_hash": "a" * 64,
        "memory_packet_id": "packet-1",
        "memory_packet_sha256": "b" * 64,
        "memory_packet_intr_receipt_hash": "sha256:" + "c" * 64,
        "provider_ingress_admission_observed": False,
        "provider_execution_observed": False,
        "provider_egress_admission_observed": False,
        "kv_writeback_observed": False,
        "credential_material_present": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_MATERIALIZATION_ONLY",
    }


def setup_roots(tmp_path: Path, monkeypatch):
    state = tmp_path / "state"
    llm = tmp_path / "llm"
    script = llm / "scripts/materialize_kv_memory_provider_request.py"
    script.parent.mkdir(parents=True)
    script.write_text("# fixture\n", encoding="utf-8")
    monkeypatch.setenv("STEGVERSE_BOUND_STATE_ROOT", str(state))
    monkeypatch.setenv("STEGVERSE_LLM_ADAPTER_ROOT", str(llm))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return state, llm


def stage_consumer_inputs(home: Path, *, admission: bool = False) -> Path:
    root = home / consumer.BOUND_STATE_REL
    inputs = root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "context-packet.json").write_text("{}\n", encoding="utf-8")
    (inputs / "provider-request-input.json").write_text("{}\n", encoding="utf-8")
    if admission:
        (inputs / "memory-packet-admission.json").write_text("{}\n", encoding="utf-8")
    return root


def test_worker_waits_without_private_bound_state_inputs(tmp_path, monkeypatch):
    setup_roots(tmp_path, monkeypatch)
    result = worker.run(invocation())
    assert result["state"] == "HANDOFF_READY"
    assert result["transition_id"] == "KV_AI_MEMORY_RESIDENT_INPUT_NOT_READY"
    assert result["authority_effect"] == "NONE_BOUND_STATE_MATERIALIZATION_ONLY"


def test_worker_materializes_only_inside_bound_state(tmp_path, monkeypatch):
    state, _ = setup_roots(tmp_path, monkeypatch)
    inputs = state / "inputs"
    inputs.mkdir(parents=True)
    for name in ("context-packet.json", "memory-packet-admission.json", "provider-request-input.json"):
        (inputs / name).write_text("{}\n", encoding="utf-8")

    def fake_runner(command, **kwargs):
        output = Path(command[command.index("--output") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(materialized_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="{}", stderr="")

    result = worker.run(invocation(), runner=fake_runner)
    assert result["state"] == "HANDOFF_READY"
    assert result["transition_id"] == "KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED"
    assert (state / "materialized/provider-request.json").is_file()
    receipt = json.loads((state / "receipts/provider-request-materialization.json").read_text())
    assert receipt["provider_ingress_admission_observed"] is False
    assert receipt["provider_execution_observed"] is False
    assert receipt["provider_egress_admission_observed"] is False
    assert receipt["kv_writeback_observed"] is False
    assert receipt["credential_material_present"] is False
    assert receipt["worker_claim_or_fence_minted"] is False


def test_consumer_does_not_attempt_worker_until_inputs_exist(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    request_target = runtime / consumer.REQUEST_REL
    request_target.parent.mkdir(parents=True)
    request_target.write_text((ROOT / consumer.REQUEST_REL).read_text(encoding="utf-8"), encoding="utf-8")
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("STEGVERSE_LLM_ADAPTER_ROOT", str(tmp_path / "llm"))

    def forbidden_runner(*args, **kwargs):
        raise AssertionError("runner must not be called before private inputs exist")

    result = consumer.consume(ROOT, runtime, runner=forbidden_runner, env={"HOME": str(home), "PATH": "/usr/bin", "STEGVERSE_LLM_ADAPTER_ROOT": str(tmp_path / "llm")})
    assert result["state"] == "BOUND_STATE_INPUT_NOT_READY"
    assert result["private_input_bytes_read"] is False
    assert result["runtime_execution_attempted"] is False


def test_consumer_waits_without_explicit_intr_ingress_when_packet_is_staged(tmp_path):
    runtime = tmp_path / "runtime"
    request_target = runtime / consumer.REQUEST_REL
    request_target.parent.mkdir(parents=True)
    request_target.write_text((ROOT / consumer.REQUEST_REL).read_text(encoding="utf-8"), encoding="utf-8")
    home = tmp_path / "home"
    stage_consumer_inputs(home)

    def forbidden_runner(*args, **kwargs):
        raise AssertionError("runner must not be called without explicit shared ingress")

    result = consumer.consume(ROOT, runtime, runner=forbidden_runner, env={"HOME": str(home), "PATH": "/usr/bin"})
    assert result["state"] == "BOUND_STATE_INPUT_NOT_READY"
    assert result["missing_input_refs"] == ["inputs/memory-packet-admission.json"]
    assert result["admission_attempt"]["state"] == "INGRESS_NOT_READY"
    assert result["admission_attempt"]["admission_attempted"] is False
    assert result["private_input_bytes_read"] is False


def test_admission_attempt_uses_canonical_source_preparer_and_accepts_only_submitter_evidence(tmp_path):
    home = tmp_path / "home"
    stage_root = stage_consumer_inputs(home)
    env = {
        "HOME": str(home),
        "PATH": "/usr/bin",
        "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "http://127.0.0.1:7777/intr/materialization",
    }
    calls = []

    def fake_runner(command, **kwargs):
        calls.append(command)
        if "prepare_kv_ai_memory_intr_runtime_source.py" in command[1]:
            out = {"state": "ROUTE_INSTALLED_LOCAL_SOURCE", "authority_effect": "NONE_SOURCE_PREPARATION_ONLY"}
            return SimpleNamespace(returncode=0, stdout=json.dumps(out) + "\n", stderr="")
        if "submit_kv_ai_memory_packet_local.py" in command[1]:
            admission = {
                "schema": "stegverse.kv.ai-memory-intr-admission/v1",
                "disposition": "ALLOW",
                "packet_id": "KVMEM-fixture",
                "packet_sha256": "a" * 64,
                "receipt_hash": "sha256:" + "b" * 64,
                "authority_effect": "NONE_ADMISSION_EVIDENCE_ONLY",
            }
            target = stage_root / consumer.ADMISSION_INPUT
            target.write_text(json.dumps(admission) + "\n", encoding="utf-8")
            out = {"state": "AUTHENTIC_INGRESS_ADMISSION_WRITTEN", "admission_written": True, "receipt_hash": admission["receipt_hash"]}
            return SimpleNamespace(returncode=0, stdout=json.dumps(out) + "\n", stderr="")
        raise AssertionError(command)

    result = consumer.attempt_memory_packet_admission(ROOT, runner=fake_runner, env=env)
    assert result["state"] == "AUTHENTIC_INGRESS_ADMISSION_WRITTEN"
    assert result["route_preparation_state"] == "ROUTE_INSTALLED_LOCAL_SOURCE"
    assert result["admission_attempted"] is True
    assert result["admission_written"] is True
    assert result["private_input_bytes_read_by_consumer"] is False
    assert len(calls) == 2
    assert "prepare_kv_ai_memory_intr_runtime_source.py" in calls[0][1]
    assert (stage_root / consumer.ADMISSION_INPUT).is_file()


def test_admission_attempt_fails_closed_on_invalid_preparation_result(tmp_path):
    home = tmp_path / "home"
    stage_consumer_inputs(home)
    env = {
        "HOME": str(home),
        "PATH": "/usr/bin",
        "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "http://127.0.0.1:7777/intr/materialization",
    }

    def fake_runner(command, **kwargs):
        if "prepare_kv_ai_memory_intr_runtime_source.py" in command[1]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"state": "UNEXPECTED"}) + "\n", stderr="")
        raise AssertionError("submitter must not run after invalid preparation result")

    result = consumer.attempt_memory_packet_admission(ROOT, runner=fake_runner, env=env)
    assert result["state"] == "ROUTE_PREPARATION_RESULT_INVALID"
    assert result["admission_attempted"] is False


def test_dispatcher_registers_wait_state_and_selector():
    by_name = dict(dispatcher.CONSUMERS)
    assert by_name["kv_ai_memory"] == "scripts/consume_kv_ai_memory_resident_request.py"
    assert dispatcher.select_consumers(("kv_ai_memory",)) == (("kv_ai_memory", "scripts/consume_kv_ai_memory_resident_request.py"),)


def test_registry_handoff_and_adapter_preserve_authority_boundaries():
    registry = json.loads((ROOT / "control/worker-registry.d/kv-ai-memory-resident-001.json").read_text())
    handoff = json.loads((ROOT / "handoffs/SV-KV-AI-PERSISTENCE-001.json").read_text())
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/kv-ai-memory-resident-001.json").read_text())
    request = json.loads((ROOT / "control/resident-execution-request.d/kv-ai-memory-resident-001.json").read_text())

    assert registry["tasks"][0]["state"] == "HANDOFF_READY"
    assert registry["credential_authority"] == "TV/TVC"
    assert registry["github_token_required"] is False
    assert handoff["authority"]["heartbeat_grants_execution_authority"] is False
    assert handoff["activation"]["private_state_policy"]["repository_private_content_allowed"] is False
    row = adapter["adapters"][0]
    assert row["type"] == "process_json_bound_state_v0.1"
    assert "STEGVERSE_LLM_ADAPTER_ROOT" in row["env_allowlist"]
    assert "GITHUB_TOKEN" not in row["env_allowlist"]
    assert request["private_content_in_request"] is False
    assert request["request_granted_authority"] is False
    assert request["provider_credential_material_allowed"] is False
