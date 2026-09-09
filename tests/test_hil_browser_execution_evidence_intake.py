from copy import deepcopy
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hil_browser_intake", ROOT / "scripts" / "intake_hil_browser_execution_evidence.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def request():
    return MOD.load_json(ROOT / "control" / "resident-execution-request.d" / "hil-sovereign-receiver-001.json")


def evidence():
    return {
        "schema": "stegos.hil_browser_receiver_activation_result/v1",
        "state": "BROWSER_HIL_LOCAL_READY_OBSERVED",
        "resident_request_id": MOD.REQUEST_ID,
        "resident_request_sha256": MOD.REQUEST_SHA256,
        "task_id": MOD.TASK_ID,
        "node_id": "stegnode-web-test",
        "browser_context_id": "ctx_0123456789abcdef0123456789abcdef",
        "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25",
        "fencing_token": 25,
        "continuation_reused_existing_checkout": False,
        "second_claim_minted": False,
        "transition": MOD.TRANSITION,
        "execution_entry_sha256": "a" * 64,
        "journal_replay_state": "PASS",
        "journal_replay_tail_sha256": "b" * 64,
        "browser_receiver_execution_observed": True,
        "installed_native_app_required": False,
        "request_consumption_claimed": False,
        "authority_effect": "NONE_COMPONENT_EVIDENCE_ONLY",
    }


def test_exact_browser_evidence_builds_consumption_receipt_without_widening_authority():
    receipt = MOD.build_consumption_receipt(request(), evidence())
    assert receipt["state"] == "COMPLETED"
    assert receipt["request_id"] == MOD.REQUEST_ID
    assert receipt["request_sha256"] == MOD.REQUEST_SHA256
    assert receipt["runtime_execution_attempted"] is True
    assert receipt["runtime_execution_surface"] == "CURRENT_USER_IPHONE_BROWSER"
    assert receipt["terminal_hil_transition_observed"] is True
    assert receipt["terminal_hil_transition"] == MOD.TRANSITION
    assert receipt["broader_hil_lifecycle_complete"] is False
    assert receipt["retry_allowed"] is False
    assert receipt["github_token_runtime_authority"] == "NONE"
    assert receipt["heartbeat_grants_execution_authority"] is False
    assert receipt["credential_authority"] == "TV/TVC"
    assert receipt["second_machine_required"] is False
    assert receipt["screenshot_substitution_allowed"] is False
    assert receipt["component_claimed_request_consumption"] is False


@pytest.mark.parametrize("field,value", [
    ("resident_request_id", "wrong"),
    ("resident_request_sha256", "0" * 64),
    ("state", "READY"),
    ("transition", "OTHER"),
    ("journal_replay_state", "FAIL"),
    ("second_claim_minted", True),
    ("request_consumption_claimed", True),
    ("browser_receiver_execution_observed", False),
    ("installed_native_app_required", True),
    ("authority_effect", "OTHER"),
])
def test_browser_evidence_fails_closed_on_binding_or_component_drift(field, value):
    item = evidence()
    item[field] = value
    with pytest.raises(RuntimeError):
        MOD.build_consumption_receipt(request(), item)


def test_claim_and_fence_must_match_and_be_above_g24():
    item = evidence()
    item["claim_id"] = "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G26"
    with pytest.raises(RuntimeError):
        MOD.build_consumption_receipt(request(), item)
    item = evidence()
    item["claim_id"] = "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G24"
    item["fencing_token"] = 24
    with pytest.raises(RuntimeError):
        MOD.build_consumption_receipt(request(), item)


def test_request_object_must_remain_exact_stable_hash():
    req = deepcopy(request())
    req["note"] += " changed"
    with pytest.raises(RuntimeError):
        MOD.build_consumption_receipt(req, evidence())


def test_browser_context_and_journal_hashes_are_required():
    item = evidence()
    item["browser_context_id"] = "ctx_bad"
    with pytest.raises(RuntimeError):
        MOD.build_consumption_receipt(request(), item)
    item = evidence()
    item["execution_entry_sha256"] = "short"
    with pytest.raises(RuntimeError):
        MOD.build_consumption_receipt(request(), item)
