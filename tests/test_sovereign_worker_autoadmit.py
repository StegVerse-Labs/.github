from __future__ import annotations

import json
from pathlib import Path

from heartbeat_runtime.sovereign_autoadmit import auto_admit_declared_workers


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_autoadmit_adds_task_and_worker_without_github_activation(tmp_path):
    write(tmp_path / "control" / "worker-registry.json", {"schema": "stegverse.heartbeat-worker-registry/v0.1", "generation": 1, "tasks": [], "workers": []})
    write(tmp_path / "handoffs" / "task.json", {"schema": "stegverse.executable-handoff/v0.1"})
    write(
        tmp_path / "control" / "sovereign-worker-autoadmit.json",
        {
            "schema": "stegverse.sovereign-worker-autoadmit/v0.1",
            "generation": 1,
            "workers": [{
                "task_id": "T1",
                "goal_id": "G1",
                "handoff_ref": "handoffs/task.json",
                "worker_id": "w1",
                "adapter_ref": "process:w1",
                "capability_profile_ref": "profile",
                "capabilities": ["runtime_observation"],
                "authority_source": "handoffs/task.json#authority",
                "cost_basis_ref": None,
                "evidence_refs": [],
                "enabled": True,
                "third_party_activation_required": False,
                "github_activation_required": False,
            }],
        },
    )
    assert auto_admit_declared_workers(tmp_path) == ["T1"]
    registry = json.loads((tmp_path / "control" / "worker-registry.json").read_text())
    task = registry["tasks"][0]
    worker = registry["workers"][0]
    assert task["state"] == "HANDOFF_READY"
    assert task["executor_binding"] == "AUTHORIZED"
    assert worker["status"] == "AVAILABLE"
    assert worker["adapter_ref"] == "process:w1"
    assert registry["generation"] == 2


def test_autoadmit_is_idempotent(tmp_path):
    write(tmp_path / "control" / "worker-registry.json", {"schema": "stegverse.heartbeat-worker-registry/v0.1", "generation": 1, "tasks": [], "workers": []})
    write(tmp_path / "handoffs" / "task.json", {"schema": "stegverse.executable-handoff/v0.1"})
    declaration = {
        "schema": "stegverse.sovereign-worker-autoadmit/v0.1",
        "generation": 1,
        "workers": [{
            "task_id": "T1", "goal_id": "G1", "handoff_ref": "handoffs/task.json",
            "worker_id": "w1", "adapter_ref": "process:w1", "capabilities": [],
            "enabled": True, "third_party_activation_required": False, "github_activation_required": False,
        }],
    }
    write(tmp_path / "control" / "sovereign-worker-autoadmit.json", declaration)
    auto_admit_declared_workers(tmp_path)
    assert auto_admit_declared_workers(tmp_path) == []
    registry = json.loads((tmp_path / "control" / "worker-registry.json").read_text())
    assert len(registry["tasks"]) == 1
    assert len(registry["workers"]) == 1


def test_autoadmit_rejects_hosted_activation_requirement(tmp_path):
    write(tmp_path / "control" / "worker-registry.json", {"generation": 1, "tasks": [], "workers": []})
    write(tmp_path / "handoffs" / "task.json", {})
    write(tmp_path / "control" / "sovereign-worker-autoadmit.json", {
        "schema": "stegverse.sovereign-worker-autoadmit/v0.1",
        "workers": [{
            "task_id": "T1", "worker_id": "w1", "handoff_ref": "handoffs/task.json", "adapter_ref": "process:w1",
            "enabled": True, "third_party_activation_required": False, "github_activation_required": True,
        }],
    })
    try:
        auto_admit_declared_workers(tmp_path)
    except RuntimeError as exc:
        assert "hosted activation plane" in str(exc)
    else:
        raise AssertionError("hosted activation requirement must fail closed")
