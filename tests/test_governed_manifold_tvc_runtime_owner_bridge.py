from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "consume_governed_multilane_manifold_activation_request.py"
CONTROL = ROOT / "control" / "resident-execution-request.d" / "consume-governed-multilane-manifold-activation.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("path", [SCRIPT, CONTROL])
def test_tvc_runtime_owner_bridge_is_present_in_both_consumers(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert "execute_existing_tvc_runtime_owner_path" in source
    assert "tvc.primary_runtime_binder.preflight" in source
    assert "tvc.primary_runtime_binder.activate" in source
    assert "observe_tvc_runtime_boundary.py" in source
    assert "TVC-PROVIDER-OPERATION-BROKER-003" in source
    assert "TVC-CAPABILITY-RUNTIME-002" in source


def test_bridge_fails_closed_without_tvtvc_activation_declaration(monkeypatch, tmp_path: Path) -> None:
    module = _load(SCRIPT)
    for name in module.HOSTED_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY", raising=False)
    monkeypatch.delenv("STEGVERSE_TVC_ROOT", raising=False)
    monkeypatch.delenv("STEGVERSE_REPO_ROOTS_JSON", raising=False)

    result = module.execute_existing_tvc_runtime_owner_path(tmp_path)
    assert result["state"] == "BLOCKED_TV_TVC_RUNTIME_ACTIVATION_DECLARATION_REQUIRED"
    assert result["authority_effect"] == "NONE_FAIL_CLOSED"


def test_bridge_rejects_hosted_execution_before_owner_dispatch(monkeypatch, tmp_path: Path) -> None:
    module = _load(SCRIPT)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY", "TV/TVC")

    result = module.execute_existing_tvc_runtime_owner_path(tmp_path)
    assert result["state"] == "BLOCKED_HOSTED_SURFACE_REJECTED"
    assert "GITHUB_ACTIONS" in result["hosted"]
