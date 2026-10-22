from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_registry_collision_checkin as gate  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "task-registry-collision-checkin.yml"
HYGIENE = ROOT / "control" / "workflow-surface-registry.json"


def task(task_id, components, state="ACTIVE", checkout="CHECKED_OUT", **extra):
    row = {"task_id": task_id, "coordination_state": state, "checkout_state": checkout,
           "parent_task_id": None, "root_correlation_id": task_id,
           "targets": {"repositories": ["StegVerse-Labs/.github"], "components": components}}
    row.update(extra)
    return row


BASE_TASKS = [
    task("H48-OWNER-001", ["collision-owner-component"]),
    task("H48-PRE-EXISTING-001", ["collision-owner-component"], checkout="AVAILABLE"),
    task("H48-ISOLATED-001", ["isolated-component"]),
]


def tree(path: Path, tasks, generation=1) -> Path:
    (path / "data" / "canonical-task-records").mkdir(parents=True)
    (path / "scripts").symlink_to(ROOT / "scripts")
    shutil.copy(ROOT / gate.INVARIANTS_PATH, path / gate.INVARIANTS_PATH)
    (path / gate.REGISTRY_PATH).write_text(
        json.dumps({"generation": generation, "tasks": tasks}, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def base(tmp_path):
    return tree(tmp_path / "base", copy.deepcopy(BASE_TASKS))


def head_with(tmp_path, tasks):
    return tree(tmp_path / "head", tasks, generation=2)


def by_task(result):
    return {r["task_id"]: r for r in result["results"]}


def test_pr_without_task_changes_is_not_applicable(tmp_path, base):
    result = gate.check(base, head_with(tmp_path, copy.deepcopy(BASE_TASKS)))
    assert result["disposition"] == gate.ALLOW
    assert result["applicability"] == "NOT_APPLICABLE"


def test_new_task_colliding_with_checked_out_owner_fails_closed_with_six_fields(tmp_path, base):
    tasks = copy.deepcopy(BASE_TASKS) + [task("H48-NEW-COLLIDER-001", ["collision-owner-component"])]
    result = gate.check(base, head_with(tmp_path, tasks))
    assert result["disposition"] == gate.FAIL_CLOSED
    row = by_task(result)["H48-NEW-COLLIDER-001"]
    assert row["head_disposition"] == "STOP_COLLISION"
    assert row["base_disposition"] is None
    assert row["failure_code"] == "REGISTRY_COLLISION_CHECKIN_STOP_COLLISION"
    assert all(row[field] for field in gate.SIX_FIELDS)
    assert "H48-OWNER-001" in row["evidence"]["hard_collision_task_ids"]


def test_changed_isolated_task_that_continues_is_allowed(tmp_path, base):
    tasks = copy.deepcopy(BASE_TASKS)
    tasks[2]["notes"] = "re-scoped"
    result = gate.check(base, head_with(tmp_path, tasks))
    assert result["disposition"] == gate.ALLOW
    assert by_task(result)["H48-ISOLATED-001"]["reason"] == "CONTINUE"


def test_pre_existing_collision_is_reported_not_charged_unless_strict(tmp_path, base):
    tasks = copy.deepcopy(BASE_TASKS)
    tasks[1]["notes"] = "touched"
    head = head_with(tmp_path, tasks)
    result = gate.check(base, head)
    row = by_task(result)["H48-PRE-EXISTING-001"]
    assert row["base_disposition"] == row["head_disposition"] == "STOP_COLLISION"
    assert row["reason"] == "PRE_EXISTING_AT_BASE"
    assert result["disposition"] == gate.ALLOW
    assert gate.check(base, head, strict=True)["disposition"] == gate.FAIL_CLOSED


def test_scope_widening_into_a_collision_fails_closed(tmp_path, base):
    tasks = copy.deepcopy(BASE_TASKS)
    tasks[2]["targets"]["components"].append("collision-owner-component")
    result = gate.check(base, head_with(tmp_path, tasks))
    row = by_task(result)["H48-ISOLATED-001"]
    assert (row["base_disposition"], row["head_disposition"]) == ("CONTINUE", "STOP_COLLISION")
    assert result["disposition"] == gate.FAIL_CLOSED


def test_task_retired_by_the_pr_is_terminal_not_a_failure(tmp_path, base):
    tasks = copy.deepcopy(BASE_TASKS)
    tasks[1]["coordination_state"] = "RETIRED"
    result = gate.check(base, head_with(tmp_path, tasks))
    assert by_task(result)["H48-PRE-EXISTING-001"]["reason"] == "TERMINAL_AT_HEAD"
    assert result["disposition"] == gate.ALLOW


def test_evaluator_refusal_is_never_a_pass(tmp_path, base):
    tasks = copy.deepcopy(BASE_TASKS)
    tasks[2]["user_action_surfaces"] = "not-an-array"
    result = gate.check(base, head_with(tmp_path, tasks))
    row = by_task(result)["H48-ISOLATED-001"]
    assert row["failure_code"] == "REGISTRY_COLLISION_CHECKIN_REFUSED"
    assert result["disposition"] == gate.FAIL_CLOSED


def test_gate_appends_no_checkin_event_and_restores_environment(tmp_path, base, monkeypatch):
    monkeypatch.delenv("STEGVERSE_TASK_REGISTRY_EVENT_LEDGER", raising=False)
    tasks = copy.deepcopy(BASE_TASKS) + [task("H48-NEW-COLLIDER-001", ["collision-owner-component"])]
    head = head_with(tmp_path, tasks)
    gate.check(base, head)
    assert "STEGVERSE_TASK_REGISTRY_EVENT_LEDGER" not in os.environ
    assert not any(tmp_path.rglob("*.jsonl"))


def test_caller_surface_is_declared_in_policy():
    policy = json.loads((ROOT / "data" / "task-registry-general-checkin-caller-policy.json").read_text())
    surface = policy["admitted_production_caller_surfaces"][gate.CALLER_SURFACE]
    assert surface["path"] == "scripts/check_registry_collision_checkin.py"
    assert surface["transition_predicate"] is False
    assert surface["event_ledger_append"] is False


def test_workflow_binding_is_pull_request_only_tokenless_and_registered():
    text = WORKFLOW.read_text(encoding="utf-8")
    trigger = text.split("on:", 1)[1].split("permissions:", 1)[0]
    assert "pull_request:" in trigger and "push:" not in trigger
    for path in ("'data/canonical-task-registry.json'", "'data/canonical-task-records/**'",
                 "'scripts/evaluate_task_registry_collision_checkin.py'",
                 "'scripts/check_registry_collision_checkin.py'"):
        assert path in trigger
    assert "permissions: {}" in text
    assert "uses:" not in text and "secrets." not in text
    assert 'test -z "${GITHUB_TOKEN:-}"' in text
    assert "python scripts/check_registry_collision_checkin.py" in text
    assert '--base-root "$base_root" --head-root "$head_root"' in text
    assert "--strict" not in text
    registry = json.loads(HYGIENE.read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in registry["surfaces"]}
    assert ".github/workflows/task-registry-collision-checkin.yml" in paths
