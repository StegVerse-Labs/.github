"""The InTr owner executes every branch of a journey fan, or fails closed saying which.

A v2 journey fans to N parallel round trips, each with its own LLM and its own
four endpoint receipts. The StegBrowser owner executes exactly one round trip,
and v1 describes exactly that, so this owner translates the fan into N v1
operations rather than moving browser semantics into the control plane.

That translation is also the fix for a real seam break: the SDK began emitting a
v2 journey while the browser owner accepted v1 only, so a single-worker manifest
would have failed at the owner with a schema error. Both repositories' suites
stayed green because neither covers the seam between them. The shape assertions
below are that missing coverage, stated as this repo's contract with the owner.

Non-authorizing: no browser runs here and no receipt is minted. The custody
client and the browser owner are both patched; what is under test is which
transitions this owner emits and in what order.
"""
from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workers import manifest_state_transition_intr_ingress as mod  # noqa: E402

JOURNEY_V1 = "stegverse.packet-carried-endpoint-receipt-journey/v1"
JOURNEY_V2 = "stegverse.packet-carried-endpoint-receipt-journey/v2"
DIGEST = {k: f"sha256:{c * 64}" for k, c in
          {"a": "a", "ar": "b", "c": "c", "cr": "d", "e": "e", "er": "f"}.items()}


def branch(bid, out, ret, **extra):
    row = {
        "branch_id": bid,
        "ephemeral_endpoint": f"stegbrowser:ephemeral:{bid}",
        "outbound_manifest_sha256": out,
        "return_manifest_sha256": ret,
        "prompt": f"Return the exact marker TEST6_{bid.upper()}.",
        "response_marker": f"TEST6_{bid.upper()}",
        "provider": "credential-free-huggingface-space",
        "model": "Qwen3",
        "secure_url": "https://huggingface.co/spaces/example/free-ai-chat",
        "browser_actions": [{"op": "read_text", "selector": ".bubble"}],
    }
    row.update(extra)
    return row


def graph(branches=None, *, journey_id="test6-fan"):
    request = {
        "schema": "stegbrowser.llm-profile-request.v1",
        "profile": "llm.v1",
        "prompt": "Return the exact marker.",
        "response_marker": "TEST_DEFAULT",
        "secure_url": "https://huggingface.co/spaces/example/free-ai-chat",
        "browser_actions": [{"op": "read_text", "selector": ".bubble"}],
        "journey": {
            "schema": JOURNEY_V2 if branches else JOURNEY_V1,
            "journey_id": journey_id,
            "origin_endpoint": "stegverse:test6-origin",
        },
    }
    row = {"profile": "llm.v1", "request": request}
    if branches:
        row["branches"] = branches
        row["branch_count"] = len(branches)
    return row


def validated(graph_row):
    return {
        "canonical_task_id": "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-AUTHENTIC-RUNTIME-001",
        "request_sha256": "f" * 64,
        "route_id": "stegverse.route.stegbrowser.v1",
        "state_graph": graph_row,
    }


def custody_rows():
    counter = {"n": 0}

    def fake(**kwargs):
        counter["n"] += 1
        digest = f"{counter['n']:064d}"
        return {
            "receipt": {"transition_id": kwargs["transition_id"],
                        "transition_outcome": kwargs["outcome"],
                        "sequence": kwargs["sequence"]},
            "evidence": dict(kwargs.get("evidence") or {}),
            "prior": kwargs.get("prior"),
            "custody": {"state": "RECORDED",
                        "organization_receipt": {"receipt_sha256": digest}},
        }

    return fake


def browser_result(receipts=4):
    return {
        "schema": "stegbrowser.llm-manifested-browser-execution.v1",
        "result": {"response_text": "TEST6"},
        "endpoint_receipts": [{"leg": 1, "direction": "EGRESS"}] * receipts,
    }


def execute(graph_row, *, side_effect=None, receipts=4, tmp_path=None):
    leases = []

    def fake_browser(op, lease):
        leases.append(lease)
        if side_effect is not None:
            outcome = side_effect(op, lease)
            if isinstance(outcome, Exception):
                raise outcome
        return browser_result(receipts)

    with patch.object(mod, "_custody_transition", side_effect=custody_rows()), \
         patch.object(mod, "_repo_root", return_value=Path("/tmp/stegbrowser")), \
         patch.dict(sys.modules, {
             "src": type(sys)("src"),
             "src.stegbrowser": type(sys)("src.stegbrowser"),
             "src.stegbrowser.llm_browser_execution": type(sys)("m"),
         }):
        sys.modules["src.stegbrowser.llm_browser_execution"].execute_manifested_llm_browser_operation = fake_browser
        result = mod._execute_stegbrowser_llm(tmp_path or Path("/tmp"), validated(graph_row))
    return result, leases


# --- the translation: a fan becomes N single round trips -------------------

def test_a_fan_becomes_one_v1_round_trip_per_branch():
    ops = mod._branch_operations(graph([
        branch("a", DIGEST["a"], DIGEST["ar"]),
        branch("c", DIGEST["c"], DIGEST["cr"]),
        branch("e", DIGEST["e"], DIGEST["er"]),
    ]))
    assert len(ops) == 3
    assert [o["journey"]["journey_id"] for o in ops] == [
        "test6-fan:a", "test6-fan:c", "test6-fan:e"
    ]
    assert [o["journey"]["ephemeral_endpoint"] for o in ops] == [
        "stegbrowser:ephemeral:a", "stegbrowser:ephemeral:c", "stegbrowser:ephemeral:e"
    ]
    assert [o["response_marker"] for o in ops] == ["TEST6_A", "TEST6_C", "TEST6_E"]


def test_every_translated_operation_satisfies_the_owner_journey_contract():
    """This is the seam that broke: the owner accepts v1 and predecessor-linked only."""
    ops = mod._branch_operations(graph([
        branch("a", DIGEST["a"], DIGEST["ar"]),
        branch("c", DIGEST["c"], DIGEST["cr"]),
    ]))
    for op in ops:
        assert op["schema"] == "stegbrowser.llm-profile-request.v1"
        assert op["profile"] == "llm.v1"
        journey = op["journey"]
        assert journey["schema"] == JOURNEY_V1, "the browser owner accepts v1 only"
        assert isinstance(journey["ephemeral_endpoint"], str), "v1 endpoint is scalar"
        assert "branches" not in journey
        assert journey["return_predecessor_manifest_sha256"] == journey["outbound_manifest_sha256"]
        for field in ("prompt", "response_marker", "secure_url", "browser_actions"):
            assert op[field], f"{field} must survive translation"


def test_a_graph_without_branches_is_the_single_round_trip():
    """A graph built before the journey generalized still executes."""
    ops = mod._branch_operations(graph())
    assert len(ops) == 1
    assert ops[0]["journey"]["journey_id"] == "test6-fan"


# --- execution --------------------------------------------------------------

def test_every_branch_executes_with_its_own_lease_and_receipts():
    rows = [branch("a", DIGEST["a"], DIGEST["ar"]),
            branch("c", DIGEST["c"], DIGEST["cr"]),
            branch("e", DIGEST["e"], DIGEST["er"])]
    result, leases = execute(graph(rows))
    assert result["disposition"] == "ALLOW"
    assert result["branch_count"] == 3
    assert result["endpoint_receipt_count"] == 12, "four endpoint receipts per branch"
    assert [b["branch_id"] for b in result["branch_executions"]] == ["a", "c", "e"]
    assert len(result["transition_closures"]) == 9, "ingress/interaction/egress per branch"
    assert len({lease["lease_id"] for lease in leases}) == 3, "no branch reuses another's lease"


def test_custody_sequence_is_continuous_and_predecessor_linked_across_branches():
    rows = [branch("a", DIGEST["a"], DIGEST["ar"]), branch("c", DIGEST["c"], DIGEST["cr"])]
    result, _ = execute(graph(rows))
    closures = result["transition_closures"]
    assert [c["receipt"]["sequence"] for c in closures] == [1, 2, 3, 4, 5, 6]
    assert closures[0]["prior"] is None
    for earlier, later in zip(closures, closures[1:]):
        assert later["prior"] == earlier["custody"]["organization_receipt"]["receipt_sha256"]


def test_a_single_branch_keeps_the_existing_result_shape():
    result, _ = execute(graph([branch("a", DIGEST["a"], DIGEST["ar"])]))
    assert result["disposition"] == "ALLOW"
    assert result["browser_execution"] is not None, "existing consumers read this"
    assert result["branch_count"] == 1
    assert len(result["transition_closures"]) == 3


# --- a partial fan is never a success ---------------------------------------

def test_a_failing_branch_fails_closed_and_keeps_earlier_branches_receipts():
    rows = [branch("a", DIGEST["a"], DIGEST["ar"]),
            branch("c", DIGEST["c"], DIGEST["cr"]),
            branch("e", DIGEST["e"], DIGEST["er"])]

    def fail_second(op, lease):
        if op["journey"]["journey_id"].endswith(":c"):
            return RuntimeError("navigation timeout")
        return None

    result, _ = execute(graph(rows), side_effect=fail_second)
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["terminal"] is False
    assert result["failed_predicate"] == "MANIFEST_SELECTED_STEGBROWSER_BROWSER_OPERATION_COMPLETED"
    failure = result["failure"]
    assert failure["branch_id"] == "c"
    assert failure["branch_index"] == 2
    assert failure["branch_count"] == 3
    assert failure["branches_completed"] == 1, "branch a completed and is recorded"
    assert failure["error_type"] == "RuntimeError"
    # a's three closures, then c's ingress and its failure: nothing for e.
    assert len(result["transition_closures"]) == 5
    assert result["organization_records_before_master_records"] is True


def test_a_short_endpoint_receipt_count_is_not_a_complete_packet():
    rows = [branch("a", DIGEST["a"], DIGEST["ar"]), branch("c", DIGEST["c"], DIGEST["cr"])]
    result, _ = execute(graph(rows), receipts=3)
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == "BRANCH_FAN_ENDPOINT_RECEIPTS_COMPLETE"
    assert result["failure"]["required_endpoint_receipts"] == 8
    assert result["failure"]["observed_endpoint_receipts"] == 6


def test_an_unbound_source_root_still_fails_closed_before_any_branch():
    rows = [branch("a", DIGEST["a"], DIGEST["ar"]), branch("c", DIGEST["c"], DIGEST["cr"])]
    with patch.object(mod, "_custody_transition", side_effect=custody_rows()), \
         patch.object(mod, "_repo_root", return_value=None):
        result = mod._execute_stegbrowser_llm(Path("/tmp"), validated(graph(rows)))
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == "STEGBROWSER_SOURCE_ROOT_BOUND"
    assert result["failure"]["branch_count"] == 2
    assert len(result["transition_closures"]) == 1


def test_execution_grants_no_authority():
    result, _ = execute(graph([branch("a", DIGEST["a"], DIGEST["ar"])]))
    assert result["authority_effect"] == "NONE_RETURN_ASSEMBLY_ONLY"
    assert result["organization_records_before_master_records"] is True
