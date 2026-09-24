"""Source-only regression for component-011's existing portable initiation entry.

Fake runner/refresh deliberately exercise no sovereign execution or authority.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts import dispatch_resident_execution_requests as dispatcher
from scripts import refresh_and_dispatch_resident_requests as portable
from scripts import refresh_sovereign_worker_runtime_source as source_refresh

SELECTOR = "ungoverned_ai_defensive_envelope"
REQUEST_REL = Path("control/resident-execution-request.d/ungoverned-ai-defensive-envelope-001.json")
CONSUMER_REL = Path("scripts/consume_ungoverned_ai_defensive_envelope_request.py")


def test_component011_exact_selector_has_one_existing_producer_and_materializes():
    assert SELECTOR in portable.ALLOWED_TARGET_CONSUMERS
    assert dict(dispatcher.CONSUMERS)[SELECTOR] == CONSUMER_REL.as_posix()
    assert REQUEST_REL.parent in source_refresh.CONTROL_DIRS
    assert CONSUMER_REL in source_refresh.STATIC_FILES
    assert portable.TARGET_CONSUMER != SELECTOR  # preserve historical default
    request = json.loads((portable.REPO_ROOT / REQUEST_REL).read_text(encoding="utf-8"))
    assert request["state"] == "REQUESTED"
    assert request["request_id"] == "RESIDENT-EXEC-UNGOVERNED-AI-DEFENSIVE-ENVELOPE-001"
    assert request["task_id"] == "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"


def test_component011_portable_refresh_forwards_exact_selector_without_claiming_execution():
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        source, runtime = base / "source", base / "runtime"
        source.mkdir()
        runtime.mkdir()
        calls = []

        def fake_refresh(actual_source, actual_runtime):
            assert (actual_source, actual_runtime) == (source, runtime)
            (runtime / portable.DISPATCHER_REL).parent.mkdir(parents=True)
            (runtime / portable.DISPATCHER_REL).write_text("# existing dispatcher fixture\n")
            return {
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
                "mutable_runtime_state_preserved": True,
            }

        def fake_runner(command, **kwargs):
            calls.append((command, kwargs))
            assert command[-2:] == ["--only-consumer", SELECTOR]
            assert "--goal-task-id" not in command
            assert kwargs["env"]["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] == "NONE"
            assert "GITHUB_TOKEN" not in kwargs["env"]
            receipt = {
                "schema": "stegverse.resident-request-dispatch/v1",
                "state": "DISPATCH_COMPLETE",
                "selection_scope": "EXACT_SELECTOR",
                "selected_consumers": [SELECTOR],
                "consumer_count": 1,
                "outcomes": [{
                    "consumer": SELECTOR,
                    "attempted": True,
                    "returncode": 0,
                    "state": "ATTEMPT_RECORDED",
                }],
            }
            location = runtime / portable.DISPATCH_RECEIPT_REL
            location.parent.mkdir(parents=True, exist_ok=True)
            location.write_text(json.dumps(receipt) + "\n")
            return SimpleNamespace(returncode=0, stdout=json.dumps(receipt), stderr="")

        with patch.object(portable, "refresh", side_effect=fake_refresh):
            outcome = portable.refresh_and_dispatch(
                source, runtime, target_consumer=SELECTOR,
                runner=fake_runner, env={"PATH": "/bin", "STEGVERSE_TVC_ROOT": "/local/tvc"},
            )
        assert len(calls) == 1
        assert outcome["state"] == "REFRESH_AND_DISPATCH_COMPLETE"
        assert outcome["exact_consumer_selection_observed"] is True
        assert outcome["target_consumer"] == SELECTOR
        assert outcome["bridge_grants_execution_authority"] is False
        assert outcome["bridge_mints_claim_or_fence"] is False
        assert outcome["target_consumption_evidence_required"] is False
        assert outcome["dispatch_receipt"]["outcomes"][0]["state"] == "ATTEMPT_RECORDED"


def test_unknown_selector_fails_before_source_refresh():
    with tempfile.TemporaryDirectory() as temp:
        with patch.object(portable, "refresh") as refresh:
            with pytest.raises(RuntimeError, match="unsupported portable resident consumer"):
                portable.refresh_and_dispatch(
                    Path(temp) / "source", Path(temp) / "runtime",
                    target_consumer="unregistered_component011_selector",
                    env={"PATH": "/bin"},
                )
            refresh.assert_not_called()


@pytest.mark.parametrize("unsafe_env", [
    {"GITHUB_ACTIONS": "true"},
    {"CI": "true"},
    {"GITHUB_TOKEN": "not-forwarded"},
    {"OPENAI_API_KEY": "not-forwarded"},
])
def test_hosted_and_credential_inputs_fail_before_refresh_or_dispatch(unsafe_env):
    with tempfile.TemporaryDirectory() as temp:
        with patch.object(portable, "refresh") as refresh:
            with pytest.raises(RuntimeError, match="hosted environment|credential-bearing environment"):
                portable.refresh_and_dispatch(
                    Path(temp) / "source", Path(temp) / "runtime",
                    target_consumer=SELECTOR,
                    env={"PATH": "/bin", **unsafe_env},
                )
            refresh.assert_not_called()
