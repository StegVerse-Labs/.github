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
