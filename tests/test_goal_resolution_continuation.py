from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/evaluate_goal_resolution_continuation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("evaluate_goal_resolution_continuation", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _contract():
    return {
        "credential_authority": "TV/TVC",
        "goal_resolution_continuation": {
            "default_report_interval_iterations": 5,
        },
    }


def test_machine_owned_iterations_continue_without_user_reentry():
    mod = _load_module()
    result = mod.evaluate(
        {
            "goal_id": "GOAL-1",
            "iteration": 1,
            "returned_tasks": [
                {
                    "task_id": "TASK-1",
                    "cosv_task_vector": "50000000100000",
                    "state": "HANDOFF_READY",
                    "authority_class": "MACHINE_GOVERNED",
                    "handoff": "docs/TASK_1_MIRROR_HANDOFF.md",
                }
            ],
        },
        _contract(),
    )
    assert result["disposition"] == "CONTINUE_AUTONOMOUSLY"
    assert result["surface_response"] is False
    assert result["continue_machine_work"] is True
    assert result["automatic_reingestion"] is True


def test_fifth_iteration_reports_but_does_not_stop_machine_work():
    mod = _load_module()
    result = mod.evaluate(
        {
            "goal_id": "GOAL-1",
            "iteration": 5,
            "returned_tasks": [
                {
                    "task_id": "TASK-1",
                    "cosv_task_vector": "50000000100000",
                    "state": "ACTIVE",
                }
            ],
        },
        _contract(),
    )
    assert result["disposition"] == "REPORT_AND_CONTINUE"
    assert result["surface_response"] is True
    assert result["continue_machine_work"] is True
    assert result["periodic_report_stops_machine_work"] is False


def test_human_authority_boundary_surfaces_immediately():
    mod = _load_module()
    result = mod.evaluate(
        {
            "goal_id": "GOAL-1",
            "iteration": 2,
            "returned_tasks": [
                {
                    "task_id": "TASK-LEGAL",
                    "cosv_task_vector": "50000000100000",
                    "state": "ACTIVE",
                    "authority_class": "LEGAL_PERSON_SIGNATURE",
                }
            ],
        },
        _contract(),
    )
    assert result["disposition"] == "HUMAN_REVIEW_REQUIRED"
    assert result["surface_response"] is True
    assert result["continue_machine_work"] is False
    assert result["human_review_task_ids"] == ["TASK-LEGAL"]


def test_goal_completion_surfaces_immediately():
    mod = _load_module()
    result = mod.evaluate(
        {
            "goal_id": "GOAL-1",
            "iteration": 3,
            "goal_state": "COMPLETE",
            "returned_tasks": [],
        },
        _contract(),
    )
    assert result["disposition"] == "GOAL_COMPLETE"
    assert result["surface_response"] is True
    assert result["continue_machine_work"] is False


def test_duplicate_multiline_task_returns_collapse_by_task_id():
    mod = _load_module()
    result = mod.evaluate(
        {
            "goal_id": "GOAL-1",
            "iteration": 1,
            "returned_tasks": [
                {
                    "task_id": "TASK-1",
                    "cosv_task_vector": "50000000100000",
                    "state": "ACTIVE",
                    "dependencies": ["DEP-A"],
                },
                {
                    "task_id": "TASK-1",
                    "cosv_task_vector": "50000000100000",
                    "state": "HANDOFF_READY",
                    "dependencies": ["DEP-B"],
                    "handoff": "docs/TASK_1_MIRROR_HANDOFF.md",
                },
            ],
        },
        _contract(),
    )
    assert result["returned_task_count"] == 1
    assert result["deduplicated_task_ids"] == ["TASK-1"]
    assert result["continuation_pointers"][0]["handoff"] == "docs/TASK_1_MIRROR_HANDOFF.md"


def test_malformed_cosv_vector_fails_closed():
    mod = _load_module()
    try:
        mod.evaluate(
            {
                "goal_id": "GOAL-1",
                "iteration": 1,
                "returned_tasks": [
                    {
                        "task_id": "TASK-1",
                        "cosv_task_vector": "5000000010600",
                    }
                ],
            },
            _contract(),
        )
    except ValueError as exc:
        assert "expected 14 digits" in str(exc)
    else:
        raise AssertionError("malformed COSV vector must fail closed")
