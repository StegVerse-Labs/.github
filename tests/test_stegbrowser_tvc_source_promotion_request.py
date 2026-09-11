from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py"
REQUEST = ROOT / "control/resident-execution-request.d/stegbrowser-tvc-source-promotion-001.json"
REFRESH_DISPATCH = ROOT / "scripts/refresh_and_dispatch_resident_requests.py"
TARGET_SHA = "aef6b6f5dc99d2a531718ca475d20858ae8e68a6"

spec = importlib.util.spec_from_file_location("stegbrowser_tvc_source_promotion", CONSUMER)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def load_refresh_dispatch():
    spec = importlib.util.spec_from_file_location("stegbrowser_refresh_dispatch", REFRESH_DISPATCH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_request_is_exact_parent_task_and_immutable_tvc_pin():
    value = json.loads(REQUEST.read_text())
    mod.validate_request(value)
    assert value["task_id"] == "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
    assert value["source_repository"] == "StegVerse-Labs/TVC"
    assert value["reference_mode"] == "IMMUTABLE_COMMIT"
    assert value["exact_sha"] == TARGET_SHA
    assert value["materialization_id"] == "stegbrowser-tvc-runtime-aef6b6f5"
    assert value["github_token_required"] is False
    assert value["network_source_fetch_allowed"] is False
    assert value["second_machine_required"] is False


def test_consumer_stages_exact_private_source_request(tmp_path: Path):
    runtime = tmp_path / "runtime"
    source = tmp_path / "source"
    (runtime / REQUEST.parent.relative_to(ROOT)).mkdir(parents=True)
    (source / REQUEST.parent.relative_to(ROOT)).mkdir(parents=True)
    request = json.loads(REQUEST.read_text())
    request_path = runtime / REQUEST.relative_to(ROOT)
    request_path.write_text(json.dumps(request))

    result = mod.consume(source, runtime)
    assert result["state"] == "ATTEMPT_RECORDED"
    assert result["outcome"] == "STAGED"
    staged = json.loads((runtime / "tvc-handoff/private-source-request.json").read_text())
    assert staged == {
        "caller_repository": "StegVerse-Labs/.github",
        "source_repository": "StegVerse-Labs/TVC",
        "consumer_task": "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001",
        "reference_mode": "IMMUTABLE_COMMIT",
        "exact_ref": "commit:" + TARGET_SHA,
        "exact_sha": TARGET_SHA,
        "materialization_id": "stegbrowser-tvc-runtime-aef6b6f5",
        "ttl_seconds": 900,
    }


def test_consumer_does_not_overwrite_other_private_source_task(tmp_path: Path):
    runtime = tmp_path / "runtime"
    source = tmp_path / "source"
    request_path = runtime / REQUEST.relative_to(ROOT)
    request_path.parent.mkdir(parents=True)
    request_path.write_text(REQUEST.read_text())
    slot = runtime / "tvc-handoff/private-source-request.json"
    slot.parent.mkdir(parents=True)
    other = {
        "caller_repository": "StegVerse-Labs/TVC",
        "source_repository": "StegVerse-Labs/.github",
        "consumer_task": "SHWP-SV002-ORG-RUNTIME-ACTIVATION-001",
        "reference_mode": "IMMUTABLE_COMMIT",
        "exact_ref": "commit:" + "1" * 40,
        "exact_sha": "1" * 40,
        "materialization_id": "other",
        "ttl_seconds": 900,
    }
    slot.write_text(json.dumps(other))

    result = mod.consume(source, runtime)
    assert result["state"] == "ATTEMPT_RECORDED"
    assert result["outcome"] == "HANDOFF_READY"
    assert result["pending_reason"] == "PRIVATE_SOURCE_REQUEST_SLOT_OCCUPIED_BY_OTHER_TASK"
    assert json.loads(slot.read_text()) == other


def test_dispatcher_registers_materialized_consumer():
    source = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text()
    assert '("stegbrowser_tvc_source_promotion", "control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py")' in source
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    assert 'Path("control/resident-execution-request.d")' in refresh


def test_portable_refresh_dispatch_allows_exact_stegbrowser_promotion_selector():
    source = REFRESH_DISPATCH.read_text()
    assert '"stegbrowser_tvc_source_promotion"' in source
    assert 'parser.add_argument("--only-consumer", choices=ALLOWED_TARGET_CONSUMERS' in source


def test_portable_dispatch_preserves_exact_source_git_head_and_selection(tmp_path: Path, monkeypatch):
    bridge = load_refresh_dispatch()
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    source.mkdir()
    dispatcher = runtime / bridge.DISPATCHER_REL
    dispatcher.parent.mkdir(parents=True)
    dispatcher.write_text("# materialized dispatcher\n")
    expected_head = "4f2c20af71a6e3e56573b4bfde9fa950d67ac8ce"

    def fake_refresh(source_root: Path, runtime_root: Path):
        assert source_root == source.resolve()
        assert runtime_root == runtime.resolve()
        return {
            "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
            "source_git_head": expected_head,
            "mutable_runtime_state_preserved": True,
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
        }

    def fake_runner(command, **_kwargs):
        assert command[-2:] == ["--only-consumer", "stegbrowser_tvc_source_promotion"]
        receipt = {
            "state": "DISPATCH_COMPLETE",
            "selection_scope": "EXACT_SELECTOR",
            "selected_consumers": ["stegbrowser_tvc_source_promotion"],
            "consumer_count": 1,
        }
        path = runtime / bridge.DISPATCH_RECEIPT_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(bridge, "refresh", fake_refresh)
    result = bridge.refresh_and_dispatch(
        source,
        runtime,
        target_consumer="stegbrowser_tvc_source_promotion",
        runner=fake_runner,
        env={},
    )

    assert result["state"] == "REFRESH_AND_DISPATCH_COMPLETE"
    assert result["target_consumer"] == "stegbrowser_tvc_source_promotion"
    assert result["exact_consumer_selection_observed"] is True
    assert result["refresh_receipt"]["source_git_head"] == expected_head
    persisted = json.loads((runtime / bridge.RECEIPT_REL).read_text())
    assert persisted["refresh_receipt"]["source_git_head"] == expected_head
    assert persisted["dispatch_receipt"]["selected_consumers"] == ["stegbrowser_tvc_source_promotion"]
