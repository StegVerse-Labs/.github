import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "control" / "resident-execution-request.d" / "governed-multilane-manifold-activation-001.json"


def test_complete_all_declared_children_policy_is_explicit() -> None:
    request = json.loads(REQUEST.read_text())
    policy = request["lineage_policy"]
    assert policy["complete_all_declared_subordinates"] is True
    assert policy["do_not_prune_incomplete_tasks_for_expected_future_consolidation"] is True


def test_execution_sequence_forbids_speculative_retirement() -> None:
    request = json.loads(REQUEST.read_text())
    sequence = "\n".join(request["execution_sequence"])
    prohibited = "\n".join(request["prohibited"])
    assert "finish every declared subordinate" in sequence
    assert "do not retire, skip, or prune" in sequence
    assert "retiring or pruning an incomplete declared subordinate" in prohibited
