from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SHWP-HIL-SOVEREIGN-RECEIVER-001.json"
DOC = ROOT / "docs" / "HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md"


def test_hil_universal_intr_transport_precedes_receiver_ready_and_g18() -> None:
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    activation = handoff["activation"]
    event = activation["transport_event_materialization"]

    assert event["schema"] == "stegverse.universal-intr-transport/v1"
    assert event["event_triggered"] is True
    assert event["always_on_receiver_required"] is False
    assert event["second_user_device_required"] is False
    assert event["receiver_unavailable_disposition"] == "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION"
    assert event["g18_completion_required"] is False
    assert event["g18_claim_or_fence_consumed"] is False
    assert event["receiver_ready_is_precondition_to_submit"] is False
    assert event["receiver_ready_is_downstream_observation"] is True
    assert event["request_grants_authority"] is False
    assert event["authority_effect"] == "NONE_TRANSPORT_ONLY"

    targeted = activation["targeted_execution"]
    assert targeted["g18_bootstrap_allowed"] is False
    assert targeted["heartbeat_grants_execution_authority"] is False
    assert targeted["credential_authority"] == "TV/TVC"
    assert handoff["task"]["dependencies"] == []

    text = DOC.read_text(encoding="utf-8")
    for marker in (
        "canonical Universal InTr activation-order reconciliation",
        "event_triggered=true",
        "always_on_receiver_required=false",
        "G18 completion required for HIL Submit: false",
        "G18 claim/fence consumed by HIL: false",
        "receiver-side receipt/custody lineage is emitted",
        "TVC independently admits and receipts its boundary",
    ):
        assert marker in text, marker

    forbidden_prerequisite = """G18 complete
-> resident HIL receiver already running
-> receiver READY
-> participant may Submit"""
    assert forbidden_prerequisite in text
    assert "not** a valid prerequisite chain" in text


def test_hil_handoff_binds_merged_universal_intr_source_chain() -> None:
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    refs = "\n".join(handoff["task"]["source_refs"])
    assert "StegVerse-Labs/Site@1cb2b9b950674400c5e5aa341b8b6efba5cbeb47" in refs
    assert "StegVerse-org/LLM-adapter@ad1a7c3f8bb727d1007f254930d9a77df0bfa94f" in refs
    assert "StegVerse-Labs/TVC@31a4ea2fcc42b807ec24ae2612df4e60d38a73eb" in refs
    assert "StegVerse-Labs/StegOS/stegos/universal_intr_transport.py" in refs

    next_action = handoff["completion"]["next_authorized_action"]
    assert "Do not wait for G18 completion" in next_action
    assert "continuously READY receiver" in next_action
    assert handoff["block"]["recheck_trigger"] == "each admitted HIL Universal InTr transport event"
