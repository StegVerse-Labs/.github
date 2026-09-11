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


def materialized_tools(root: Path) -> None:
    for rel in (module.RESOLVER, module.MATERIALIZER, module.PREFLIGHT, module.CONSUMER):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# stub\n", encoding="utf-8")


def resolver_success() -> SimpleNamespace:
    return SimpleNamespace(
        returncode=0,
        stdout='{"state":"SOURCE_RESOLUTION_COMPLETE","blockers":[]}\n',
    )


def materializer_success() -> SimpleNamespace:
    return SimpleNamespace(
        returncode=0,
        stdout='{"state":"MATERIALIZED_READY_FOR_PREFLIGHT","ready":true,"blockers":[]}\n',
    )


def test_preflight_block_prevents_consumer(tmp_path):
    materialized_tools(tmp_path)
    outputs = [
        resolver_success(),
        materializer_success(),
        SimpleNamespace(
            returncode=2,
            stdout='{"state":"BLOCKED_FAIL_CLOSED","ready":false,"blocker_count":1}\n',
        ),
    ]
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return outputs.pop(0)

    result = module.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "PREFLIGHT_BLOCKED_FAIL_CLOSED"
    assert result["preflight_attempted"] is True
    assert result["consumer_attempted"] is False
    assert len(calls) == 3


def test_ready_preflight_allows_consumer(tmp_path):
    materialized_tools(tmp_path)
    outputs = [
        resolver_success(),
        materializer_success(),
        SimpleNamespace(
            returncode=0,
            stdout='{"state":"READY_FOR_RESIDENT_CONSUMPTION","ready":true,"blocker_count":0}\n',
        ),
        SimpleNamespace(
            returncode=0,
            stdout='{"state":"AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"}\n',
        ),
    ]
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        return outputs.pop(0)

    result = module.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    assert result["consumer_attempted"] is True
    assert result["activation_claimed"] is False
    assert len(calls) == 4
    assert module.RESOLVER.name in calls[0][1]
    assert module.MATERIALIZER.name in calls[1][1]
    assert module.PREFLIGHT.name in calls[2][1]
    assert module.CONSUMER.name in calls[3][1]


def test_ready_state_with_nonzero_blockers_still_fails_closed(tmp_path):
    materialized_tools(tmp_path)
    outputs = [
        resolver_success(),
        materializer_success(),
        SimpleNamespace(
            returncode=0,
            stdout='{"state":"READY_FOR_RESIDENT_CONSUMPTION","ready":true,"blocker_count":1}\n',
        ),
    ]

    def runner(command, **kwargs):
        return outputs.pop(0)

    result = module.dispatch(tmp_path, tmp_path, runner=runner)
    assert result["state"] == "PREFLIGHT_BLOCKED_FAIL_CLOSED"
    assert result["preflight_attempted"] is True
    assert result["consumer_attempted"] is False
