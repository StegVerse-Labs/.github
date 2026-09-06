import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "canonical-task-record.schema.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
ACTIVE_POLICY = ROOT / "control" / "active-worker-state-policy.json"
TASK_POLICY = ROOT / "data" / "task-coordination-policy.json"
WORKER_PROJECTION = ROOT / "scripts" / "project_worker_claim_into_canonical_task.py"
INGRESS_PROJECTION = ROOT / "scripts" / "apply_admitted_canonical_work_projection.py"
README = ROOT / "README.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_blocked_is_not_a_canonical_task_coordination_state():
    schema = load(SCHEMA)
    states = schema["properties"]["coordination_state"]["enum"]
    assert "BLOCKED" not in states
    assert "IN_PROGRESS" in states


def test_active_worker_policy_keeps_constraints_separate_from_operational_state():
    policy = load(ACTIVE_POLICY)
    assert policy["forbidden_unresolved_state"] == "BLOCKED"
    assert policy["active_worker_requirements"]["constraint_metadata_separate_from_operational_state"] is True
    assert policy["active_worker_requirements"]["next_executable_action_required"] is True


def test_current_registry_contains_no_blocked_task_state_or_transition():
    registry = load(REGISTRY)
    for task in registry.get("tasks", []):
        assert task.get("coordination_state") != "BLOCKED"
        assert "BLOCKED" not in task.get("allowed_next_transitions", [])


def test_transition_producers_do_not_emit_blocked_task_state():
    worker_projection = WORKER_PROJECTION.read_text(encoding="utf-8")
    ingress_projection = INGRESS_PROJECTION.read_text(encoding="utf-8")
    assert '"BLOCKED"' not in worker_projection
    assert '"BLOCKED"' not in ingress_projection
    assert '["IN_PROGRESS", "COMPLETION_CLAIMED", "TRANSFERRED"]' in worker_projection
    assert '["CLAIMABLE", "RECONCILIATION_REQUIRED"]' in ingress_projection


def test_task_policy_selects_admissible_work_and_preserves_active_solution_semantics():
    policy = load(TASK_POLICY)
    invariants = set(policy["invariants"])
    assert "UNRESOLVED_CONSTRAINTS_ARE_METADATA_NOT_OPERATIONAL_STOP_STATES" in invariants
    assert "ACTIVE_WORK_CONTINUES_ATTEMPTING_SOLUTION_WITHIN_AUTHORITY_CEILING" in invariants
    sequence = policy["new_session_entry_contract"]["sequence"]
    assert "SELECT_HIGHEST_PRIORITY_ADMISSIBLE_NON_DUPLICATE_NON_COLLIDING_TASK" in sequence
    assert "SELECT_HIGHEST_PRIORITY_UNBLOCKED_NON_DUPLICATE_NON_COLLIDING_TASK" not in sequence


def test_readme_documents_active_solution_semantics():
    text = README.read_text(encoding="utf-8")
    assert "Problems and constraints are metadata, not an operational stopping state." in text
    assert "highest-priority admissible nonduplicate task" in text
