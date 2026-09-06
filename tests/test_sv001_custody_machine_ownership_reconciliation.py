import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "entity_transition_ownership",
    ROOT / "scripts" / "evaluate_entity_transition_ownership.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_sv001_master_records_custody_routes_to_machine_governance():
    result = mod.evaluate({
        "transition_id": "SV001_MASTER_RECORDS_CUSTODY_AND_RECONSTRUCTION",
        "authority_class": "MACHINE_GOVERNED",
        "execution_surface": "CURRENT_USER_IPHONE",
        "human_approval_required": False,
    })
    assert result["human_interaction_required"] is False
    assert result["route"] == "ENTITY_MACHINE_GOVERNANCE_LOOP"
    assert result["current_governance_required"] is True
    assert result["authority_inferred"] is False
    assert result["authority_reused"] is False


def test_human_queue_no_longer_contains_sv001_custody_action():
    queue = json.loads((ROOT / "control/current-user-ios-interaction-queue.json").read_text())
    assert queue["active_action_id"] is None
    assert queue["candidate_actions"] == []
    exclusions = {row["transition_id"]: row for row in queue["machine_owned_exclusions"]}
    row = exclusions["SV001_MASTER_RECORDS_CUSTODY_AND_RECONSTRUCTION"]
    assert row["authority_class"] == "MACHINE_GOVERNED"
    assert row["human_interaction_required"] is False
    assert row["queue_blocks_transition"] is False


def test_old_user_admission_is_superseded():
    override = json.loads((
        ROOT / "handoffs/SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001.interaction-admission.json"
    ).read_text())
    assert override["state"] == "SUPERSEDED_MACHINE_OWNED_TRANSITION"
    assert override["active_action_id"] is None
    assert override["human_interaction_required"] is False
    assert override["machine_transition"]["route"] == "ENTITY_MACHINE_GOVERNANCE_LOOP"
    assert override["machine_transition"]["current_governance_required"] is True


def test_readme_documents_material_sv001_authority_semantics():
    readme = (ROOT / "README.md").read_text()
    assert "SV001 Master Records custody/reconstruction is explicitly classified" in readme
    assert "former `IPHONE-MR-SV001-CUSTODY-001` human-action admission is superseded" in readme
    assert "neither authorizes nor proves custody" in readme
