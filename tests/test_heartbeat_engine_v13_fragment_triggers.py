from __future__ import annotations

import json
from pathlib import Path

from heartbeat_runtime.engine_v13 import HeartbeatRuntime


def test_fragment_only_handoff_ready_task_emits_assignment_trigger(tmp_path: Path) -> None:
    handoff = tmp_path / "handoffs" / "fragment-task.json"
    handoff.parent.mkdir(parents=True, exist_ok=True)
    handoff.write_text("{}\n", encoding="utf-8")

    fragment_dir = tmp_path / "control" / "worker-registry.d"
    fragment_dir.mkdir(parents=True, exist_ok=True)
    fragment = {
        "schema": "stegverse.worker-registry-fragment/v0.1",
        "fragment_id": "TEST-FRAGMENT",
        "tasks": [
            {
                "task_id": "FRAGMENT-ONLY-TASK",
                "goal_id": "FRAGMENT-ONLY-GOAL",
                "handoff_ref": "handoffs/fragment-task.json",
                "state": "HANDOFF_READY",
                "executor_binding": "AUTHORIZED",
                "worker_id": None,
                "worker_instance_id": None,
                "claim_id": None,
                "cost_basis_ref": None,
            }
        ],
        "workers": [
            {
                "worker_id": "fragment-worker",
                "adapter_ref": "process:fragment-worker-v1",
                "status": "AVAILABLE",
                "capabilities": ["fragment_test"],
            }
        ],
        "authority_effect": "NONE_REGISTRATION_ONLY",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
    }
    (fragment_dir / "fragment.json").write_text(json.dumps(fragment), encoding="utf-8")

    runtime = HeartbeatRuntime(tmp_path)
    registry = {
        "schema": "stegverse.heartbeat-worker-registry/v0.1",
        "generation": 1,
        "tasks": [],
        "workers": [],
    }

    triggers = runtime._assignment_triggers(registry, 32)

    assert [item["task_id"] for item in triggers] == ["FRAGMENT-ONLY-TASK"]
    assert triggers[0]["carrier_epoch"] == 32
    assert triggers[0]["authority_effect"] == "NONE"
    assert triggers[0]["execution_authority"] is False
    assert registry["tasks"][0]["task_id"] == "FRAGMENT-ONLY-TASK"
    assert registry["workers"][0]["worker_id"] == "fragment-worker"
    assert registry["generation"] == 2
