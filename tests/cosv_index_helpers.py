from __future__ import annotations

import json
from pathlib import Path


def load_effective_index(root: Path) -> dict[str, dict]:
    """Return canonical aggregate COSV rows plus non-duplicating index shards."""
    aggregate = json.loads((root / "control/task-vector-index.json").read_text(encoding="utf-8"))
    rows = {row["task_id"]: row for row in aggregate["tasks"]}
    shard_root = root / "control/task-vector-index.d"
    if shard_root.exists():
        for path in sorted(shard_root.glob("*.json")):
            row = json.loads(path.read_text(encoding="utf-8"))
            if row.get("schema") != "stegverse.cosv-task-vector-index-entry/v1":
                continue
            task_id = row["task_id"]
            if task_id in rows:
                for key in ("source_state_vector_ref", "vector", "vector_state", "authority_effect"):
                    assert row.get(key) == rows[task_id].get(key), f"index shard disagrees for {task_id}:{key}"
            else:
                rows[task_id] = row
    return rows


def indexed_worker_ids(root: Path) -> set[str]:
    worker_ids: set[str] = set()
    paths = [root / "control/worker-registry.json", *sorted((root / "control/worker-registry.d").glob("*.json"))]
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for task in payload.get("tasks", []):
            task_id = task.get("task_id")
            if isinstance(task_id, str) and task_id:
                worker_ids.add(task_id)
    return set(load_effective_index(root)).intersection(worker_ids)
