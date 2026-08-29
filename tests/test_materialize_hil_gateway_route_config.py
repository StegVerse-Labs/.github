from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "materialize_hil_gateway_route_config",
    ROOT / "scripts/materialize_hil_gateway_route_config.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_materializes_non_authorizing_shared_gateway_route(tmp_path, monkeypatch):
    home = tmp_path / "home"
    runtime = tmp_path / "runtime"
    home.mkdir()
    runtime.mkdir()
    marker = home / ".stegverse/node.json"
    marker.parent.mkdir(parents=True)
    marker.write_text(json.dumps({
        "declared": True,
        "node_id": "NODE-HIL-TEST",
        "credential_authority": "TV/TVC"
    }), encoding="utf-8")
    monkeypatch.setattr(mod, "NODE_MARKERS", (marker,))
    target = tmp_path / "hil-route.json"
    result = mod.materialize({
        "STEGVERSE_HEARTBEAT_ROOT": str(runtime),
        "STEGVERSE_HIL_RECEIVER_PORT": "8765"
    }, target)
    cfg = result["config"]
    assert cfg["loopback_url"] == "http://127.0.0.1:8765"
    assert cfg["public_tls_terminated_by"] == "STEGVERSE_SHARED_SERVICE_GATEWAY"
    assert cfg["event_triggered"] is True
    assert cfg["always_on_receiver_required"] is False
    assert cfg["second_user_device_required"] is False
    assert cfg["g18_completion_required"] is False
    assert cfg["credential_authority"] == "TV/TVC"
    assert cfg["github_token_runtime_authority"] == "NONE"
    assert cfg["execution_authority"] == "NONE"


def test_missing_runtime_is_predicate_pending(tmp_path, monkeypatch):
    marker = tmp_path / "node.json"
    marker.write_text(json.dumps({
        "declared": True,
        "node_id": "NODE-HIL-TEST",
        "credential_authority": "TV/TVC"
    }), encoding="utf-8")
    monkeypatch.setattr(mod, "NODE_MARKERS", (marker,))
    try:
        mod.materialize({}, tmp_path / "route.json")
    except mod.PredicatePending as exc:
        assert "runtime root" in str(exc)
    else:
        raise AssertionError("missing runtime must remain predicate pending")
