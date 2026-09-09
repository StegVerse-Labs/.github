from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "dispatch_gadi_resident_execution.py"
spec = importlib.util.spec_from_file_location("dispatch_gadi", PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_preflight_block_prevents_consumer(tmp_path):
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "control/resident-execution-request.d").mkdir(parents=True)
    (tmp_path / module.PREFLIGHT).write_text("# preflight\n")
    (tmp_path / module.CONSUMER).write_text("# consumer\n")
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=2, stdout='{"state":"BLOCKED_FAIL_CLOSED","ready":false,"blocker_count":1}\n')
    result = module.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "PREFLIGHT_BLOCKED_FAIL_CLOSED"
    assert result["consumer_attempted"] is False
    assert len(calls) == 1


def test_ready_preflight_allows_consumer(tmp_path):
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "control/resident-execution-request.d").mkdir(parents=True)
    (tmp_path / module.PREFLIGHT).write_text("# preflight\n")
    (tmp_path / module.CONSUMER).write_text("# consumer\n")
    outputs = [
        SimpleNamespace(returncode=0, stdout='{"state":"READY_FOR_RESIDENT_CONSUMPTION","ready":true,"blocker_count":0}\n'),
        SimpleNamespace(returncode=0, stdout='{"state":"AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"}\n'),
    ]
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        return outputs.pop(0)
    result = module.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    assert result["consumer_attempted"] is True
    assert result["activation_claimed"] is False
    assert len(calls) == 2


def test_ready_state_with_nonzero_blockers_still_fails_closed(tmp_path):
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "control/resident-execution-request.d").mkdir(parents=True)
    (tmp_path / module.PREFLIGHT).write_text("# preflight\n")
    (tmp_path / module.CONSUMER).write_text("# consumer\n")
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stdout='{"state":"READY_FOR_RESIDENT_CONSUMPTION","ready":true,"blocker_count":1}\n')
    result = module.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "PREFLIGHT_BLOCKED_FAIL_CLOSED"
    assert result["consumer_attempted"] is False
