"""A branch fan must fail closed rather than execute only its first branch.

The SDK journey generalizes to N parallel round trips, each with its own LLM and
its own four endpoint receipts. This owner executes the request-level operation
only. Without a guard it would run branch one and return a result that looks
complete while 4(N-1) receipts were never produced - a false success, which is
the one outcome the receipt-before-claim invariant cannot tolerate.

The guard is inert on a single round trip, so it is safe whether or not the SDK
change has landed.
"""
from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workers import manifest_state_transition_intr_ingress as mod  # noqa: E402

PREDICATE = "MANIFEST_SELECTED_STEGBROWSER_BRANCH_FAN_EXECUTION_SUPPORTED"


def custody_rows():
    """Custody is a real Master Records call; the guard's decision is what is under test."""
    counter = {"n": 0}

    def fake(**kwargs):
        counter["n"] += 1
        digest = str(counter["n"]) * 64
        return {
            "receipt": {"transition_id": kwargs["transition_id"],
                        "transition_outcome": kwargs["outcome"]},
            "evidence": dict(kwargs.get("evidence") or {}),
            "custody": {
                "state": "RECORDED",
                "organization_receipt": {"receipt_sha256": digest,
                                         "evidence": dict(kwargs.get("evidence") or {})},
            },
        }

    return fake


def execute(validated_request, tmp_path):
    with patch.object(mod, "_custody_transition", side_effect=custody_rows()):
        return mod._execute_stegbrowser_llm(tmp_path, validated_request)


def validated(branch_count=None, **graph_extra):
    graph = {
        "profile": "llm.v1",
        "request": {
            "secure_url": "https://huggingface.co/spaces/example/free-ai-chat",
            "browser_actions": [{"op": "read_text", "selector": ".bubble"}],
        },
    }
    if branch_count is not None:
        graph["branch_count"] = branch_count
    graph.update(graph_extra)
    return {
        "canonical_task_id": "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-AUTHENTIC-RUNTIME-001",
        "request_sha256": "f" * 64,
        "route_id": "stegverse.route.stegbrowser.v1",
        "state_graph": graph,
    }


@pytest.mark.parametrize("count", [2, 3, 7])
def test_a_fan_fails_closed_before_ingress_is_admitted(tmp_path, count):
    result = execute(validated(branch_count=count), tmp_path)
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == PREDICATE
    assert result["terminal"] is False, "the manifest is retryable after the owner is repaired"
    assert result["organization_records_before_master_records"] is True
    assert result["authority_effect"] == "NONE_RETURN_ASSEMBLY_ONLY"

    closures = result["transition_closures"]
    assert len(closures) == 1, "no branch may be executed before the fan is supported"
    evidence = closures[0]["evidence"]
    assert evidence.get("branch_count") == count
    assert evidence.get("required_endpoint_receipts") == 4 * count
    assert evidence.get("failed_predicate") == PREDICATE
    assert str(evidence.get("required_evidence_or_repair", "")).strip()
    assert str(evidence.get("retry_condition", "")).strip()


def test_the_guard_is_inert_on_a_single_round_trip(tmp_path):
    """branch_count 1, or absent entirely, is the existing single-worker path."""
    for graph_kwargs in ({"branch_count": 1}, {}):
        result = execute(validated(**graph_kwargs), tmp_path)
        assert result["failed_predicate"] != PREDICATE, (
            "the fan guard must not fire on a single round trip"
        )


def test_a_malformed_branch_count_is_treated_as_a_single_round_trip(tmp_path):
    for bad in ("three", 0, -1, None, [2]):
        result = execute(validated(branch_count=bad), tmp_path)
        assert result["failed_predicate"] != PREDICATE
