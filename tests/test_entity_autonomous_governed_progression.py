import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "entity_transition_ownership",
    ROOT / "scripts" / "evaluate_entity_transition_ownership.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_current_iphone_machine_transition_does_not_require_human_queue():
    result = mod.evaluate({
        "transition_id": "SV001-NEXT-MACHINE-TRANSITION",
        "authority_class": "MACHINE_GOVERNED",
        "execution_surface": "CURRENT_USER_IPHONE",
    })
    assert result["human_interaction_required"] is False
    assert result["route"] == "ENTITY_MACHINE_GOVERNANCE_LOOP"
    assert result["current_governance_required"] is True
    assert result["authority_inferred"] is False
    assert result["authority_reused"] is False


def test_user_only_transition_routes_to_human_queue():
    result = mod.evaluate({
        "transition_id": "WALLET-SIGN",
        "authority_class": "USER_ONLY",
        "execution_surface": "CURRENT_USER_IPHONE",
    })
    assert result["human_interaction_required"] is True
    assert result["route"] == "CURRENT_USER_IOS_INTERACTION_QUEUE"


def test_machine_transition_cannot_be_promoted_to_manual_approval():
    try:
        mod.evaluate({
            "transition_id": "MACHINE-TASK",
            "authority_class": "MACHINE_GOVERNED",
            "human_approval_required": True,
        })
    except SystemExit as exc:
        assert "may not be promoted to human approval" in str(exc)
    else:
        raise AssertionError("expected fail-closed classification")


def test_missing_authority_class_fails_closed_instead_of_inferring():
    try:
        mod.evaluate({"transition_id": "UNKNOWN"})
    except SystemExit as exc:
        assert "do not infer authority" in str(exc)
    else:
        raise AssertionError("expected fail-closed classification")
