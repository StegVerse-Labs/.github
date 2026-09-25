"""Exact-goal routing must not strand household admission behind unrelated MIR work."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py"
TASK = "ERL-HOUSEHOLD-ECONOMIC-CONDITIONS-SITE-001"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("household_priority_consumer", WRAPPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_household_request_first_without_mir_preemption(monkeypatch, capsys, tmp_path):
    module = load_wrapper()
    original = module.mod.REQUEST_SPECS
    assert sum(item.get("task_id") == TASK for item in original) == 1
    visited = []

    def fake_consume(source, runtime, *, goal_task_id):
        visited.extend(item["task_id"] for item in module.mod.REQUEST_SPECS)
        assert goal_task_id == TASK
        return {"state": "ATTEMPT_RECORDED", "outcomes": []}

    def forbidden_mir(*args):
        raise AssertionError("unrelated MIR request must not preempt exact household target")

    monkeypatch.setattr(module.mod, "consume_all", fake_consume)
    monkeypatch.setattr(module, "_consume_mir_duplicate_first", forbidden_mir)
    monkeypatch.setattr(sys, "argv", ["consumer", "--source-root", str(tmp_path),
                                     "--runtime-root", str(tmp_path), "--goal-task-id", TASK])
    assert module.main() == 0
    result = json.loads(capsys.readouterr().out.strip())
    assert visited[0] == TASK
    assert result["exact_household_request_prioritized"] is True
    assert result["mir_roundtrip_egress_authenticity"]["state"] == "NOT_SELECTED_EXACT_HOUSEHOLD_TARGET"
    assert result["claim_or_fence_minted_by_wrapper"] is False


def test_other_goals_preserve_mir_first(monkeypatch, capsys, tmp_path):
    module = load_wrapper()
    sequence = []
    monkeypatch.setattr(module, "_consume_mir_duplicate_first",
                        lambda *args: (sequence.append("mir") or {"state": "COMPLETED"}))
    monkeypatch.setattr(module.mod, "consume_all",
                        lambda *args, **kwargs: (sequence.append("legacy") or {"state": "ATTEMPT_RECORDED"}))
    monkeypatch.setattr(sys, "argv", ["consumer", "--source-root", str(tmp_path),
                                     "--runtime-root", str(tmp_path), "--goal-task-id", "ANOTHER-GOAL"])
    assert module.main() == 0
    result = json.loads(capsys.readouterr().out.strip())
    assert sequence == ["mir", "legacy"]
    assert result["exact_household_request_prioritized"] is False
    assert result["mir_visited_before_legacy_request_set"] is True
