from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "control" / "task-vector-index.json"
INDEX_SHARDS = ROOT / "control" / "task-vector-index.d"
FRAGMENTS = ROOT / "control" / "worker-registry.d"
GLOBAL_REGISTRY = ROOT / "control" / "worker-registry.json"
ORGANIZATION_REGISTRY = ROOT / "control" / "organization-task-registry.json"
CANONICAL_REGISTRY = ROOT / "data" / "canonical-task-registry.json"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class COSVTaskVectorIndexTests(unittest.TestCase):
    def load_index(self) -> dict:
        return json.loads(INDEX.read_text(encoding="utf-8"))

    def load_effective_index_rows(self) -> dict[str, tuple[dict, Path]]:
        found: dict[str, tuple[dict, Path]] = {}
        for row in self.load_index()["tasks"]:
            task_id = row["task_id"]
            self.assertNotIn(task_id, found, f"duplicate aggregate index task {task_id}")
            found[task_id] = (row, INDEX)

        if INDEX_SHARDS.exists():
            for path in sorted(INDEX_SHARDS.glob("*.json")):
                row = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(row.get("schema"), "stegverse.cosv-task-vector-index-entry/v1")
                task_id = row["task_id"]
                if task_id in found:
                    aggregate, _ = found[task_id]
                    for key in ("source_state_vector_ref", "vector", "vector_state", "authority_effect"):
                        self.assertEqual(row.get(key), aggregate.get(key), f"index shard disagrees for {task_id}:{key}")
                # Shards may relocate registry ownership while preserving the exact
                # source vector and non-authorizing semantics of an aggregate row.
                found[task_id] = (row, path)
        return found

    def vectorized_registry_tasks(self) -> dict[str, tuple[dict, Path]]:
        found: dict[str, tuple[dict, Path]] = {}
        paths = [GLOBAL_REGISTRY, ORGANIZATION_REGISTRY, *sorted(FRAGMENTS.glob("*.json"))]
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for task in payload.get("tasks", []):
                if task.get("source_state_vector_ref"):
                    task_id = task["task_id"]
                    self.assertNotIn(task_id, found, f"duplicate vectorized worker/organization task {task_id}")
                    found[task_id] = (task, path)

        canonical = json.loads(CANONICAL_REGISTRY.read_text(encoding="utf-8"))
        for task in canonical.get("tasks", []):
            task_id = task.get("task_id")
            if task_id in found or not task.get("source_state_vector_ref"):
                continue
            found[task_id] = (task, CANONICAL_REGISTRY)
        return found

    def test_index_is_complete_for_vectorized_registry_tasks(self) -> None:
        index = self.load_index()
        self.assertEqual(index["profile"], "task.v1")
        self.assertEqual(index["notation"], "L R U I V G O C M T B E A P")
        self.assertEqual(index["width"], 14)
        self.assertEqual(index["authority_effect"], "NONE")

        rows = index["tasks"]
        ids = [row["task_id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))
        registry = self.vectorized_registry_tasks()
        effective = self.load_effective_index_rows()
        self.assertTrue(set(registry).issubset(set(effective)))
        for row in rows:
            ref = row.get("source_state_vector_ref")
            self.assertIsInstance(ref, str, row["task_id"])
            if ref.startswith("control/task-vectors/"):
                self.assertTrue((ROOT / ref).is_file(), f"aggregate index source missing for {row['task_id']}: {ref}")

        coverage = index["coverage"]
        self.assertEqual(coverage["indexed_vectorized_tasks"], len(rows))
        self.assertEqual(
            coverage["local_cosv_record_tasks"] + coverage["external_owner_projection_tasks"],
            len(rows),
        )

    def test_index_vectors_match_machine_sources(self) -> None:
        registry = self.vectorized_registry_tasks()
        effective = self.load_effective_index_rows()
        for task_id, (task, registry_path) in registry.items():
            row, index_path = effective[task_id]
            if index_path == INDEX:
                self.assertEqual(row["registry_ref"], registry_path.relative_to(ROOT).as_posix(), task_id)
            else:
                self.assertEqual(index_path.parent, INDEX_SHARDS)
                canonical_ref = row["registry_ref"]
                canonical_path = ROOT / canonical_ref
                self.assertTrue(canonical_path.is_file(), f"index shard registry_ref missing for {task_id}")
                canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
                if canonical.get("task_id") != task_id:
                    matches = [entry for entry in canonical.get("tasks", []) if entry.get("task_id") == task_id]
                    self.assertEqual(len(matches), 1, f"index shard registry_ref does not resolve {task_id}")
                self.assertEqual(canonical_ref, registry_path.relative_to(ROOT).as_posix(), task_id)

            self.assertEqual(row["source_state_vector_ref"], task["source_state_vector_ref"], task_id)
            self.assertRegex(row["vector"], r"^[0-9]{14}$", task_id)
            self.assertEqual(row["vector_state"], "EMITTED", task_id)
            self.assertEqual(row["authority_effect"], "NONE", task_id)

            embedded = task.get("machine_readable_state", {}).get("cosv")
            if isinstance(embedded, dict):
                self.assertEqual(embedded["profile"], "task.v1", task_id)
                self.assertEqual(embedded["notation"], "L R U I V G O C M T B E A P", task_id)
                self.assertEqual(embedded["width"], 14, task_id)
                self.assertEqual(embedded["vector"], row["vector"], task_id)
                self.assertEqual(embedded["authority_effect"], "NONE", task_id)

            ref = row["source_state_vector_ref"]
            if ref.startswith("control/task-vectors/"):
                record = json.loads((ROOT / ref).read_text(encoding="utf-8"))
                self.assertTrue(cosv.validate_record(record), task_id)
                self.assertEqual(record["profile"], "task.v1", task_id)
                self.assertEqual(record["vector"], row["vector"], task_id)
                self.assertEqual(record["exact_metrics"]["symbol_order"], "LRUIVGOCMTBEAP", task_id)
                if task_id == "SHWP-DURABLE-RUNTIME-ACTIVATION":
                    self.assertEqual(record["vector"], "60000000101000")
                    self.assertEqual(record["exact_metrics"]["lifecycle"], "BLOCKED")
                    self.assertEqual(record["exact_metrics"]["blocker_count"], 1)
            else:
                self.assertIsInstance(embedded, dict, task_id)


if __name__ == "__main__":
    unittest.main()
