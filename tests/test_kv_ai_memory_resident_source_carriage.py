from __future__ import annotations

"""Regression coverage for KV AI memory source carriage into resident runtime roots."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("install_sovereign_heartbeat_service", "scripts/install_sovereign_heartbeat_service.py")
refresher = load("refresh_sovereign_worker_runtime_source", "scripts/refresh_sovereign_worker_runtime_source.py")

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
