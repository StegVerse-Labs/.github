from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_de006_observability_consumer_uses_canonical_shared_projector() -> None:
    profile = json.loads(
        (ROOT / "control/runtime-observability-consumers/decision-envelope-de006.json").read_text(encoding="utf-8")
    )
    assert profile["schema"] == "stegverse.hb-runtime-resident-observability.consumer/v1"
    assert profile["canonical_module"] == "heartbeat_runtime/runtime_presence_projection.py"
    assert profile["shared_contract"] == "management/HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT.json"
    assert profile["authority_effect"] == "NONE_OBSERVATION_ONLY"
    assert profile["propagation_state"] == {
        "completed_destinations": 0,
        "required_destinations": 4,
        "propagation_complete": False,
    }
    assert profile["predicates"] == {
        "resident_request_consumption": "consumption",
        "resident_targeted_execution": "execution",
        "ecosystem_chat_parent_activation": "parent_activation",
    }


def test_de006_wrapper_does_not_define_a_new_runtime_or_authority() -> None:
    text = (ROOT / "scripts/project_de006_runtime_observability.py").read_text(encoding="utf-8")
    assert "from heartbeat_runtime.runtime_presence_projection import project" in text
    assert "NONE_OBSERVATION_ONLY" in text
    assert "WorkerCoordinator(" not in text
    assert "HeartbeatRuntime(" not in text


def test_de006_consumer_records_authentic_ios_runtime_without_parent_promotion() -> None:
    profile = json.loads(
        (ROOT / "control/runtime-observability-consumers/decision-envelope-de006.json").read_text(encoding="utf-8")
    )
    evidence = profile["external_observed_runtime_evidence"]["stegos_ios_device_local_inference"]
    assert profile["generic_runtime_evidence_absent"] is False
    assert profile["second_user_operated_machine_required"] is False
    assert evidence["state"] == "OBSERVED_AUTHENTIC_DEVICE_LOCAL"
    assert evidence["terminal_state"] == "COMPLETED"
    assert evidence["reconstruction_state"] == "PASS"
    assert evidence["same_execution"] is True
    assert evidence["credential_authority"] == "TV/TVC"
    assert evidence["credential_requirement"] == "NONE"
    assert evidence["external_non_stegverse_machine_used"] is False
    assert evidence["global_workercoordinator_authority"] is False
    assert evidence["parent_predicate_effect"] == "NONE_UNTIL_EXACT_PARENT_ADMISSION_OR_REEXECUTION"
