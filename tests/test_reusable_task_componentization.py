import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "evaluate_reusable_task_componentization.py"
spec = importlib.util.spec_from_file_location("componentize", MODULE_PATH)
componentize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(componentize)


def test_low_signal_keeps_composed():
    result = componentize.evaluate({"task_id": "T", "signals": {"multiple_round_trips": True}})
    assert result["score"] == 2
    assert result["componentization_required"] is False
    assert result["decision"].startswith("KEEP_COMPOSED")


def test_reuse_search_threshold():
    result = componentize.evaluate({
        "task_id": "T",
        "signals": {"repeated_subflow": True, "multiple_round_trips": True},
    })
    assert result["score"] == 6
    assert result["must_search_existing_components"] is True
    assert result["componentization_required"] is False


def test_componentization_required_before_scope_growth_stop():
    result = componentize.evaluate({
        "task_id": "T",
        "signals": {
            "repeated_subflow": True,
            "multiple_authority_crossings": True,
            "multiple_round_trips": True,
        },
    })
    assert result["score"] == 9
    assert result["componentization_required"] is True
    assert result["must_stop_scope_growth"] is False


def test_high_ambiguity_stops_task_specific_scope_growth():
    result = componentize.evaluate({
        "task_id": "T",
        "signals": {
            "task_specific_adapter_duplicates_generic_work": True,
            "independent_reusability": True,
            "optional_subflow_present": True,
            "independent_evidence_predicate": True,
        },
    })
    assert result["score"] == 15
    assert result["must_stop_scope_growth"] is True
    assert result["authority_effect"] == "NONE_COORDINATION_ONLY"


def test_unknown_signal_fails_closed():
    try:
        componentize.evaluate({"task_id": "T", "signals": {"invented_signal": True}})
    except ValueError as exc:
        assert "unknown signals" in str(exc)
    else:
        raise AssertionError("unknown signal must fail closed")
