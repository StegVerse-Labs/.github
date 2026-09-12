from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "scripts/refresh_and_dispatch_resident_requests.py"
EXPECTED_HEAD = "4f2c20af71a6e3e56573b4bfde9fa950d67ac8ce"
TARGET_SHA = "aef6b6f5dc99d2a531718ca475d20858ae8e68a6"


def load_bridge():
    spec = importlib.util.spec_from_file_location("stegbrowser_consumption_bridge", BRIDGE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fake_refresh(source_root: Path, runtime_root: Path):
    return {
        "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
        "source_git_head": EXPECTED_HEAD,
        "mutable_runtime_state_preserved": True,
        "network_fetch_performed": False,
        "credential_read_or_acquired": False,
    }


def consumption_receipt(outcome: str = "STAGED"):
    value = {
        "schema": "stegverse.stegbrowser-tvc-source-promotion-request-consumption/v1",
        "state": "ATTEMPT_RECORDED",
        "outcome": outcome,
        "task_id": "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001",
        "exact_sha": TARGET_SHA,
        "credential_material_present": False,
        "network_source_fetch_performed": False,
    }
    if outcome == "HANDOFF_READY":
        value["pending_reason"] = "PRIVATE_SOURCE_REQUEST_SLOT_OCCUPIED_BY_OTHER_TASK"
    return value


def dispatch_receipt(result=None):
    row = {
        "consumer": "stegbrowser_tvc_source_promotion",
        "consumer_ref": "control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py",
        "state": result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT",
        "returncode": 0,
        "result": result,
        "attempted": True,
    }
    return {
        "state": "DISPATCH_COMPLETE",
        "selection_scope": "EXACT_SELECTOR",
        "selected_consumers": ["stegbrowser_tvc_source_promotion"],
        "consumer_count": 1,
        "outcomes": [row],
    }


def prepare(tmp_path: Path):
    bridge = load_bridge()
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    source.mkdir()
    dispatcher = runtime / bridge.DISPATCHER_REL
    dispatcher.parent.mkdir(parents=True)
    dispatcher.write_text("# materialized dispatcher\n")
    return bridge, source, runtime


def run_with_consumption(tmp_path: Path, monkeypatch, outcome: str):
    bridge, source, runtime = prepare(tmp_path)
    monkeypatch.setattr(bridge, "refresh", fake_refresh)

    def runner(command, **_kwargs):
        assert command[-2:] == ["--only-consumer", "stegbrowser_tvc_source_promotion"]
        current = consumption_receipt(outcome)
        dispatch_path = runtime / bridge.DISPATCH_RECEIPT_REL
        dispatch_path.parent.mkdir(parents=True, exist_ok=True)
        dispatch_path.write_text(json.dumps(dispatch_receipt(current)))
        consumption_path = runtime / bridge.STEG_BROWSER_TVC_CONSUMPTION_REL
        consumption_path.parent.mkdir(parents=True, exist_ok=True)
        consumption_path.write_text(json.dumps(current))
        return SimpleNamespace(returncode=0)

    result = bridge.refresh_and_dispatch(
        source,
        runtime,
        target_consumer="stegbrowser_tvc_source_promotion",
        runner=runner,
        env={},
    )
    return bridge, runtime, result


def test_stegbrowser_complete_requires_and_binds_dedicated_consumption_receipt(tmp_path: Path, monkeypatch):
    bridge, runtime, result = run_with_consumption(tmp_path, monkeypatch, "STAGED")

    assert result["state"] == "REFRESH_AND_DISPATCH_COMPLETE"
    assert result["refresh_receipt"]["source_git_head"] == EXPECTED_HEAD
    assert result["exact_consumer_selection_observed"] is True
    assert result["target_consumption_evidence_required"] is True
    assert result["target_consumption_receipt_observed"] is True
    assert result["target_consumption_matches_current_dispatch_result"] is True
    assert result["exact_target_consumption_evidence_observed"] is True
    assert len(result["target_consumption_receipt_sha256"]) == 64
    assert result["target_consumption_receipt"]["task_id"] == "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
    assert result["target_consumption_receipt"]["exact_sha"] == TARGET_SHA

    persisted = json.loads((runtime / bridge.RECEIPT_REL).read_text())
    assert persisted["refresh_receipt"]["source_git_head"] == EXPECTED_HEAD
    assert persisted["dispatch_receipt"]["selected_consumers"] == ["stegbrowser_tvc_source_promotion"]
    assert persisted["target_consumption_matches_current_dispatch_result"] is True
    assert persisted["target_consumption_receipt_sha256"] == result["target_consumption_receipt_sha256"]


def test_stegbrowser_dispatch_fails_closed_when_dedicated_consumption_receipt_missing(tmp_path: Path, monkeypatch):
    bridge, source, runtime = prepare(tmp_path)
    monkeypatch.setattr(bridge, "refresh", fake_refresh)

    def runner(_command, **_kwargs):
        dispatch_path = runtime / bridge.DISPATCH_RECEIPT_REL
        dispatch_path.parent.mkdir(parents=True, exist_ok=True)
        dispatch_path.write_text(json.dumps(dispatch_receipt(consumption_receipt())))
        return SimpleNamespace(returncode=0)

    result = bridge.refresh_and_dispatch(
        source,
        runtime,
        target_consumer="stegbrowser_tvc_source_promotion",
        runner=runner,
        env={},
    )

    assert result["state"] == "REFRESH_COMPLETE_DISPATCH_INCOMPLETE"
    assert result["exact_consumer_selection_observed"] is True
    assert result["target_consumption_evidence_required"] is True
    assert result["target_consumption_receipt_observed"] is False
    assert result["target_consumption_matches_current_dispatch_result"] is False
    assert result["exact_target_consumption_evidence_observed"] is False
    assert result["target_consumption_receipt_sha256"] is None


def test_stegbrowser_handoff_ready_does_not_count_as_complete_consumption(tmp_path: Path, monkeypatch):
    _bridge, _runtime, result = run_with_consumption(tmp_path, monkeypatch, "HANDOFF_READY")

    assert result["state"] == "REFRESH_COMPLETE_DISPATCH_INCOMPLETE"
    assert result["target_consumption_receipt_observed"] is True
    assert result["target_consumption_matches_current_dispatch_result"] is True
    assert result["exact_target_consumption_evidence_observed"] is False
    assert result["target_consumption_receipt"]["outcome"] == "HANDOFF_READY"
    assert result["target_consumption_receipt"]["pending_reason"] == "PRIVATE_SOURCE_REQUEST_SLOT_OCCUPIED_BY_OTHER_TASK"


def test_stegbrowser_stale_prior_receipt_cannot_satisfy_current_dispatch(tmp_path: Path, monkeypatch):
    bridge, source, runtime = prepare(tmp_path)
    monkeypatch.setattr(bridge, "refresh", fake_refresh)
    stale = consumption_receipt("STAGED")
    stale["request_id"] = "prior-dispatch"
    consumption_path = runtime / bridge.STEG_BROWSER_TVC_CONSUMPTION_REL
    consumption_path.parent.mkdir(parents=True, exist_ok=True)
    consumption_path.write_text(json.dumps(stale))

    def runner(_command, **_kwargs):
        current = consumption_receipt("STAGED")
        current["request_id"] = "current-dispatch"
        dispatch_path = runtime / bridge.DISPATCH_RECEIPT_REL
        dispatch_path.parent.mkdir(parents=True, exist_ok=True)
        dispatch_path.write_text(json.dumps(dispatch_receipt(current)))
        return SimpleNamespace(returncode=0)

    result = bridge.refresh_and_dispatch(
        source,
        runtime,
        target_consumer="stegbrowser_tvc_source_promotion",
        runner=runner,
        env={},
    )

    assert result["state"] == "REFRESH_COMPLETE_DISPATCH_INCOMPLETE"
    assert result["target_consumption_receipt_observed"] is True
    assert result["target_consumption_matches_current_dispatch_result"] is False
    assert result["exact_target_consumption_evidence_observed"] is False
    assert result["target_consumption_receipt"]["request_id"] == "prior-dispatch"
    assert result["dispatch_receipt"]["outcomes"][0]["result"]["request_id"] == "current-dispatch"
