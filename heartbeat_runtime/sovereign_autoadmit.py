from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "stegverse.sovereign-worker-autoadmit/v0.1"


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def auto_admit_declared_workers(root: Path) -> list[str]:
    root = root.resolve()
    declaration_path = root / "control" / "sovereign-worker-autoadmit.json"
    registry_path = root / "control" / "worker-registry.json"
    if not declaration_path.is_file() or not registry_path.is_file():
        return []

    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    if declaration.get("schema") != SCHEMA:
        raise RuntimeError("unsupported sovereign worker auto-admission schema")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    tasks = registry.setdefault("tasks", [])
    workers = registry.setdefault("workers", [])
    admitted: list[str] = []

    for entry in declaration.get("workers", []):
        if not entry.get("enabled"):
            continue
        if entry.get("third_party_activation_required") is not False or entry.get("github_activation_required") is not False:
            raise RuntimeError("sovereign auto-admission cannot require a hosted activation plane")

        task_id = str(entry.get("task_id") or "")
        worker_id = str(entry.get("worker_id") or "")
        handoff_ref = str(entry.get("handoff_ref") or "")
        adapter_ref = str(entry.get("adapter_ref") or "")
        if not all((task_id, worker_id, handoff_ref, adapter_ref)):
            raise RuntimeError("sovereign auto-admission entry is incomplete")
        if not (root / handoff_ref).is_file():
            raise RuntimeError(f"sovereign auto-admission handoff missing: {handoff_ref}")

        task = next((row for row in tasks if row.get("task_id") == task_id), None)
        if task is None:
            tasks.append({
                "archive_eligible": False,
                "archive_reason_codes": [],
                "authorized_policy_version": "shwp-single-hb-v0.4-sovereign-trading",
                "block_ref": f"{handoff_ref}#block",
                "claim_id": None,
                "cost_basis_ref": entry.get("cost_basis_ref"),
                "evidence_refs": list(entry.get("evidence_refs") or []),
                "executor_binding": "AUTHORIZED",
                "external_entity_job_ref": None,
                "goal_id": entry.get("goal_id") or task_id,
                "handoff_ref": handoff_ref,
                "heartbeat_timing": None,
                "last_checkpoint_ref": handoff_ref,
                "lease": None,
                "state": "HANDOFF_READY",
                "task_id": task_id,
                "worker_id": None,
                "worker_instance_id": None,
            })
            admitted.append(task_id)

        worker = next((row for row in workers if row.get("worker_id") == worker_id), None)
        if worker is None:
            workers.append({
                "adapter_ref": adapter_ref,
                "authority_source": entry.get("authority_source"),
                "capabilities": list(entry.get("capabilities") or []),
                "capability_profile_ref": entry.get("capability_profile_ref"),
                "executor_type": "repository_worker",
                "last_seen_at": None,
                "status": "AVAILABLE",
                "worker_id": worker_id,
            })
            if task_id not in admitted:
                admitted.append(task_id)

    if admitted:
        registry["generation"] = int(registry.get("generation", 0)) + 1
        _atomic_write(registry_path, registry)
    return admitted


__all__ = ["auto_admit_declared_workers"]
