from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "execute_device_kv_skap_roundtrip_event.py"
SPEC = importlib.util.spec_from_file_location("device_kv_skap_event_execution", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_safe_env_forwards_only_nonsecret_roundtrip_bindings(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    stegos = tmp_path / "stegos"
    sidecar = tmp_path / "gateway.json"
    tvc = tmp_path / "tvc.json"
    output = tmp_path / "out.json"
    env = mod._safe_env(
        {
            "PATH": "/usr/bin",
            "HOME": "/tmp/home",
            "GITHUB_TOKEN": "must-not-pass",
            "TVC_TOKEN": "must-not-pass",
            "OPENAI_API_KEY": "must-not-pass",
        },
        runtime=runtime,
        stegos=stegos,
        sidecar=sidecar,
        tvc_receipt=tvc,
        output=output,
    )
    assert env["STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT"] == str(runtime)
    assert env["STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR"] == str(sidecar)
    assert env["STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT"] == str(tvc)
    assert env["STEGVERSE_STEGOS_ROOT"] == str(stegos)
    assert env["STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT"] == str(output)
    assert env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] == "TV/TVC"
    assert env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] == "NONE"
    assert "GITHUB_TOKEN" not in env
    assert "TVC_TOKEN" not in env
    assert "OPENAI_API_KEY" not in env


def test_safe_env_rejects_hosted_execution(tmp_path: Path) -> None:
    with pytest.raises(mod.RoundtripEventExecutionError, match="hosted_runtime_forbidden"):
        mod._safe_env(
            {"PATH": "/usr/bin", "GITHUB_ACTIONS": "true"},
            runtime=tmp_path / "runtime",
            stegos=tmp_path / "stegos",
            sidecar=tmp_path / "gateway.json",
            tvc_receipt=tmp_path / "tvc.json",
            output=tmp_path / "out.json",
        )


def test_event_executor_binds_canonical_task_and_cosv() -> None:
    assert mod.TASK_ID == "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
    assert mod.COSV_VECTOR == "50000000102000"
    assert mod.RUNNER_REL.as_posix() == "scripts/run_worker_runtime.py"
