import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cycle",
    ROOT / "scripts" / "run_task_registry_canonical_work_cycle.py",
)
cycle = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cycle)

TASK_ID = "CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001"


def test_conversation_evidence_task_is_direct_workercoordinator_successor():
    rows = cycle.canonical_registry_rows()
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    record = cycle.registry_candidate_projection(matches[0])
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "CHECKED_OUT"
    assert "INGRESS_ADMITTED" not in record["allowed_next_transitions"]
    assert record["allowed_next_transitions"][0] == "WORKERCOORDINATOR_CLAIM_FENCE_BOUND"
    assert cycle.workercoordinator_target_candidate(record) is True
    assert cycle.delegation_mode(record) == "WORKERCOORDINATOR_TARGETED_STATE_TRANSITION"
