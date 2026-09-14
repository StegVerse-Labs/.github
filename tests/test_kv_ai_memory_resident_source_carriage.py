from __future__ import annotations

"""Regression coverage for KV AI memory source carriage into resident runtime roots."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("install_sovereign_heartbeat_service", "scripts/install_sovereign_heartbeat_service.py")
refresher = load("refresh_sovereign_worker_runtime_source", "scripts/refresh_sovereign_worker_runtime_source.py")
portable = load("refresh_and_dispatch_resident_requests", "scripts/refresh_and_dispatch_resident_requests.py")
consumer = load("consume_kv_ai_memory_resident_request", "scripts/consume_kv_ai_memory_resident_request.py")
event_bootstrap = load("kv_ai_memory_intr_event_bootstrap", "workers/kv_ai_memory_intr_event_bootstrap.py")

REQUIRED = {
    "scripts/consume_kv_ai_memory_resident_request.py",
    "scripts/prepare_kv_ai_memory_intr_runtime_source.py",
    "scripts/install_kv_ai_memory_universal_intr_route.py",
    "scripts/submit_kv_ai_memory_packet_local.py",
}


def test_normal_runtime_materializer_carries_kv_ai_memory_execution_source():
    copied = set(installer.COPY_FILES)
    assert REQUIRED <= copied
    assert "workers" in installer.COPY_DIRS


def test_local_worker_source_refresh_carries_kv_ai_memory_execution_source():
    copied = {path.as_posix() for path in refresher.STATIC_FILES}
    assert REQUIRED <= copied
    assert Path("workers") in refresher.STATIC_DIRS


def test_resident_native_event_bootstrap_is_carried_wholesale():
    assert (ROOT / "workers/kv_ai_memory_intr_event_bootstrap.py").is_file()
    assert "workers" in installer.COPY_DIRS
    assert Path("workers") in refresher.STATIC_DIRS


def test_materializer_requires_kv_ai_memory_execution_source_after_copy():
    source = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
    for rel in REQUIRED:
        assert f'target_root / "{rel.split("/")[0]}" / "{rel.split("/")[1]}"' in source


def test_portable_targeted_dispatch_admits_kv_ai_memory():
    assert "kv_ai_memory" in portable.ALLOWED_TARGET_CONSUMERS


def test_generic_kv_ai_memory_consumer_bridges_to_autonomous_personal_kv_staging():
    source = (ROOT / "scripts/consume_kv_ai_memory_resident_request.py").read_text(encoding="utf-8")
    assert hasattr(consumer, "attempt_personal_kv_private_staging")
    assert "stage_from_personal_kv" in source
    assert "private_staging_attempt" in source
    assert "packet_provider_inputs_ready" in source
    assert "STEGVERSE_KV_SOURCE_ROOT" in source
    assert "STEGVERSE_KV_ROOT" in source
    assert "STEGVERSE_KV_AI_CONTEXT_REQUEST_PATH" in source
    assert "private_content_exported_to_repository" in source


def test_portable_dispatch_forwards_nonsecret_universal_intr_endpoint():
    endpoint = "http://127.0.0.1:7777/intr/materialization"
    safe = portable.clean_exec_env({
        "PATH": "/usr/bin",
        "HOME": "/home/stegverse",
        "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": endpoint,
    })
    assert safe["STEGVERSE_UNIVERSAL_INTR_INGRESS_URL"] == endpoint
    assert safe["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] == "NONE"
    assert safe["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] == "TV/TVC"


def test_native_worker_service_carries_nonsecret_universal_intr_endpoint():
    endpoint = "http://127.0.0.1:7777/intr/materialization"
    assert "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL" in installer.WORKER_SAFE_LOCAL_BINDINGS
    rendered = installer.materialize_service(
        ROOT,
        system="linux",
        env={
            "HOME": "/home/stegverse",
            "XDG_CONFIG_HOME": "/tmp/stegverse-kv-ai-memory-test-config",
            "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": endpoint,
        },
    )
    assert "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL" in rendered["safe_local_worker_bindings"]


def test_event_bootstrap_reports_personal_kv_root_not_ready_without_inventing_inputs(tmp_path):
    result = event_bootstrap.run_cycle(
        ROOT,
        tmp_path / "runtime",
        env={"HOME": str(tmp_path), "PATH": "/usr/bin"},
    )
    assert result["state"] == "PERSONAL_KV_ROOT_NOT_READY"
    assert result["shared_listener_started"] is False
    assert result["runtime_execution_attempted"] is False
    assert result["private_input_bytes_read_by_bootstrap"] is False
    assert result["private_staging_result"]["authority_effect"] == "NONE_WAIT_STATE"


def test_real_personal_kv_root_without_ai_memory_files_is_named_wait_state(tmp_path):
    kv_root = tmp_path / "personal-kv"
    kv_root.mkdir()
    result = event_bootstrap.run_cycle(
        ROOT,
        tmp_path / "runtime",
        env={
            "HOME": str(tmp_path),
            "PATH": "/usr/bin",
            "STEGVERSE_KV_ROOT": str(kv_root),
        },
    )
    assert result["state"] == "PERSONAL_KV_AI_MEMORY_INPUTS_NOT_FOUND"
    staging = result["private_staging_result"]
    assert sorted(staging["missing_inputs"]) == ["context_entries", "context_request", "provider_request_input"]
    assert staging["expected_relative_root"] == "_System/AI/Memory/Inputs"
    assert staging["private_content_exported_to_repository"] is False
    assert result["shared_listener_started"] is False


def test_existing_real_local_input_files_advance_to_private_staging(tmp_path):
    kv_root = tmp_path / "personal-kv"
    inputs = kv_root / "_System/AI/Memory/Inputs"
    inputs.mkdir(parents=True)
    for name, value in {
        "context-request.json": {"real": "request"},
        "context-entries.json": [{"real": "entry"}],
        "provider-request-input.json": {"real": "provider-input"},
    }.items():
        (inputs / name).write_text(json.dumps(value), encoding="utf-8")
    kv_source = tmp_path / "kv-source"
    stager = kv_source / "scripts/stage_kv_ai_memory_resident_inputs.py"
    stager.parent.mkdir(parents=True)
    stager.write_text("# local validated stager placeholder for runner interception\n", encoding="utf-8")

    def fake_runner(command, **_kwargs):
        assert "stage_kv_ai_memory_resident_inputs.py" in str(command[1])
        assert str(inputs / "context-request.json") in command
        assert str(inputs / "context-entries.json") in command
        assert str(inputs / "provider-request-input.json") in command
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "state": "PRIVATE_INPUTS_STAGED_AWAITING_INTR_ADMISSION",
                "packet_id": "PKT-REAL-LOCAL",
                "selected_item_count": 2,
                "memory_packet_admission_present": False,
            }) + "\n",
            stderr="",
        )

    result = event_bootstrap.stage_from_personal_kv(
        ROOT,
        tmp_path / "runtime",
        runner=fake_runner,
        env={
            "HOME": str(tmp_path),
            "PATH": "/usr/bin",
            "STEGVERSE_KV_ROOT": str(kv_root),
            "STEGVERSE_KV_SOURCE_ROOT": str(kv_source),
        },
    )
    assert result["state"] == "PERSONAL_KV_PRIVATE_INPUTS_STAGED"
    assert result["packet_id"] == "PKT-REAL-LOCAL"
    assert result["selected_item_count"] == 2
    assert result["memory_packet_admission_present"] is False
    assert result["private_content_exported_to_repository"] is False


def test_event_bootstrap_rejects_hosted_execution(tmp_path):
    with pytest.raises(RuntimeError, match="hosted environment"):
        event_bootstrap.run_cycle(
            ROOT,
            tmp_path / "runtime",
            env={"HOME": str(tmp_path), "PATH": "/usr/bin", "CI": "true"},
        )


def test_event_bootstrap_reuses_shared_listener_implementation():
    source = (ROOT / "workers/kv_ai_memory_intr_event_bootstrap.py").read_text(encoding="utf-8")
    assert 'importlib.import_module("workers.universal_intr_profiled_ingress")' in source
    assert 'shared.Server(("127.0.0.1", 0), runtime, 1)' in source
    assert '"second_listener_implementation_created": False' in source


def test_script_is_thin_wrapper_over_resident_native_bootstrap():
    source = (ROOT / "scripts/run_kv_ai_memory_intr_event_bootstrap.py").read_text(encoding="utf-8")
    assert "from workers.kv_ai_memory_intr_event_bootstrap import ROOT, run_cycle" in source
