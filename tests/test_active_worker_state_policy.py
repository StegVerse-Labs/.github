import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "active_worker_validator", ROOT / "tools" / "validate_active_worker_states.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

POLICY = {
    "forbidden_unresolved_state": "BLOCKED"
}


def test_rejects_blocked_unbound_unresolved_task():
    registry = {"tasks": [{
        "task_id": "T1",
        "state": "BLOCKED",
        "executor_binding": "UNBOUND",
        "handoff_ref": "handoffs/T1.json"
    }]}
    errors = MOD.validate(registry, POLICY)
    assert any("operational state BLOCKED" in e for e in errors)
    assert any("no bound executor" in e for e in errors)


def test_accepts_active_bound_claimed_task_with_next_transition():
    registry = {"tasks": [{
        "task_id": "T2",
        "state": "ACTIVE",
        "executor_binding": "BOUND",
        "claim_id": "CLAIM-T2-G1",
        "handoff_ref": "handoffs/T2.json",
        "heartbeat_timing": {"expected_next_transition": "SOLUTION_EXECUTION"}
    }]}
    assert MOD.validate(registry, POLICY) == []


def test_terminal_task_does_not_require_executor():
    registry = {"tasks": [{
        "task_id": "T3",
        "state": "COMPLETED",
        "executor_binding": "UNBOUND"
    }]}
    assert MOD.validate(registry, POLICY) == []
