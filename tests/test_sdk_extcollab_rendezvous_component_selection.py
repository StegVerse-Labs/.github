import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004"
RESEAL = "sdk_workspace_external_collab_client_secret_reseal"
LISTENER = "sdk_workspace_external_collab_consent_listener"


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_goal_selects_existing_resident_rendezvous_only_for_resident_delivery_round_trips():
    profile = load_json(f"data/goal-task-transport-profiles/{TASK_ID}.json")
    requirement = profile["transport_requirements"]["resident_rendezvous"]

    assert requirement["required"] is True
    assert requirement["component"] == "RTC-RESIDENT-RENDEZVOUS-010"
    assert requirement["required_for_round_trips"] == [
        "resident_client_secret_reseal",
        "resident_consent_listener",
    ]
    assert requirement["target_node_role"] == "ROUTING_ONLY_NOT_USER_VERIFICATION"
    assert "RTC-RESIDENT-RENDEZVOUS-010" in profile["selected_components"]


def test_existing_lower_level_dispatcher_already_owns_exact_external_collab_consumers():
    text = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
    assert RESEAL in text
    assert LISTENER in text


def test_rendezvous_registration_gap_remains_exact_and_does_not_create_duplicate_transport():
    component = load_json("data/reusable-task-components/RTC-RESIDENT-RENDEZVOUS-010.json")
    registered = set(component["registered_consumers"])

    assert component["canonical_implementation"] == "scripts/consume_resident_rendezvous.py"
    assert component["authority_effect"] == "NONE"
    # Until the reusable component extension lands, these exact selectors remain
    # the source gap. This test prevents a task-specific alternate rendezvous path
    # from being mistaken for the canonical component.
    assert RESEAL not in registered
    assert LISTENER not in registered
