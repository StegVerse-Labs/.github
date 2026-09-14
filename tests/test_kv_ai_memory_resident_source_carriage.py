from __future__ import annotations

"""Regression coverage for KV AI memory source carriage into resident runtime roots."""

import importlib.util
from pathlib import Path

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
event_bootstrap = load("run_kv_ai_memory_intr_event_bootstrap", "scripts/run_kv_ai_memory_intr_event_bootstrap.py")

REQUIRED = {
    "scripts/consume_kv_ai_memory_resident_request.py",
    "scripts/prepare_kv_ai_memory_intr_runtime_source.py",
    "scripts/install_kv_ai_memory_universal_intr_route.py",
    "scripts/submit_kv_ai_memory_packet_local.py",
}


def test_normal_runtime_materializer_carries_kv_ai_memory_execution_source():
    copied = set(installer.COPY_FILES)
    assert REQUIRED <= copied


def test_local_worker_source_refresh_carries_kv_ai_memory_execution_source():
    copied = {path.as_posix() for path in refresher.STATIC_FILES}
    assert REQUIRED <= copied


def test_materializer_requires_kv_ai_memory_execution_source_after_copy():
    required_source = {
        "scripts/consume_kv_ai_memory_resident_request.py",
        "scripts/prepare_kv_ai_memory_intr_runtime_source.py",
        "scripts/install_kv_ai_memory_universal_intr_route.py",
        "scripts/submit_kv_ai_memory_packet_local.py",
    }
    source = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
    for rel in required_source:
        assert f'target_root / "{rel.split("/")[0]}" / "{rel.split("/")[1]}"' in source


def test_portable_targeted_dispatch_admits_kv_ai_memory():
    assert "kv_ai_memory" in portable.ALLOWED_TARGET_CONSUMERS


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


def test_event_bootstrap_waits_without_starting_listener_when_private_inputs_missing(tmp_path):
    result = event_bootstrap.run_cycle(
        ROOT,
        tmp_path / "runtime",
        env={"HOME": str(tmp_path), "PATH": "/usr/bin"},
    )
    assert result["state"] == "BOUND_STATE_INPUT_NOT_READY"
    assert result["shared_listener_started"] is False
    assert result["runtime_execution_attempted"] is False
    assert result["private_input_bytes_read_by_bootstrap"] is False


def test_event_bootstrap_rejects_hosted_execution(tmp_path):
    with pytest.raises(RuntimeError, match="hosted environment"):
        event_bootstrap.run_cycle(
            ROOT,
            tmp_path / "runtime",
            env={"HOME": str(tmp_path), "PATH": "/usr/bin", "CI": "true"},
        )


def test_event_bootstrap_reuses_shared_listener_implementation():
    source = (ROOT / "scripts/run_kv_ai_memory_intr_event_bootstrap.py").read_text(encoding="utf-8")
    assert 'importlib.import_module("workers.universal_intr_profiled_ingress")' in source
    assert 'shared.Server(("127.0.0.1", 0), runtime, 1)' in source
    assert '"second_listener_implementation_created": False' in source
