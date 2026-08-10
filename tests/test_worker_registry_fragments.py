from __future__ import annotations

import json
from pathlib import Path

import pytest

from heartbeat_runtime.engine_v9 import HeartbeatRuntime


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fragment() -> dict:
    return {
        "schema": "stegverse.worker-registry-fragment/v0.1",
        "fragment_id": "TEST-001",
        "tasks": [
            {
                "task_id": "TEST-001",
                "goal_id": "TEST-GOAL",
                "state": "HANDOFF_READY",
                "handoff_ref": "handoffs/TEST-001.json",
            }
        ],
        "workers": [
            {
                "worker_id": "test-worker",
                "adapter_ref": "process:test-v1",
                "status": "AVAILABLE",
                "capabilities": ["runtime_observation"],
            }
        ],
        "authority_effect": "NONE_REGISTRATION_ONLY",
        "github_token_required": False,
    }


def test_registry_fragment_is_append_only_and_idempotent(tmp_path: Path) -> None:
    write(tmp_path / "handoffs" / "TEST-001.json", {"schema": "stegverse.executable-handoff/v0.1"})
    write(tmp_path / "control" / "worker-registry.d" / "test.json", fragment())
    registry = {"schema": "stegverse.heartbeat-worker-registry/v0.1", "generation": 7, "tasks": [], "workers": []}
    runtime = HeartbeatRuntime(tmp_path)

    applied = runtime._apply_registry_fragments(registry)
    assert applied == ["control/worker-registry.d/test.json"]
    assert registry["generation"] == 8
    assert [item["task_id"] for item in registry["tasks"]] == ["TEST-001"]
    assert [item["worker_id"] for item in registry["workers"]] == ["test-worker"]

    registry["tasks"][0]["state"] = "ACTIVE"
    registry["workers"][0]["status"] = "BUSY"
    assert runtime._apply_registry_fragments(registry) == []
    assert registry["generation"] == 8
    assert registry["tasks"][0]["state"] == "ACTIVE"
    assert registry["workers"][0]["status"] == "BUSY"


def test_registry_fragment_fails_closed_on_authority_or_token_requirement(tmp_path: Path) -> None:
    write(tmp_path / "handoffs" / "TEST-001.json", {"schema": "stegverse.executable-handoff/v0.1"})
    value = fragment()
    value["github_token_required"] = True
    write(tmp_path / "control" / "worker-registry.d" / "test.json", value)
    runtime = HeartbeatRuntime(tmp_path)
    with pytest.raises(RuntimeError, match="GitHub token"):
        runtime._apply_registry_fragments({"generation": 0, "tasks": [], "workers": []})

    value = fragment()
    value["authority_effect"] = "GRANT"
    write(tmp_path / "control" / "worker-registry.d" / "test.json", value)
    with pytest.raises(RuntimeError, match="may not grant authority"):
        runtime._apply_registry_fragments({"generation": 0, "tasks": [], "workers": []})
