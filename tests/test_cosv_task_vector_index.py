from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "control" / "task-vector-index.json"
FRAGMENTS = ROOT / "control" / "worker-registry.d"
GLOBAL_REGISTRY = ROOT / "control" / "worker-registry.json"
ORGANIZATION_REGISTRY = ROOT / "control" / "organization-task-registry.json"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class COSVTaskVectorIndexTests(unittest.TestCase):
    def load_index(self) -> dict:
        return json.loads(INDEX.read_text(encoding="utf-8"))

    def vectorized_registry_tasks(self) -> dict[str, tuple[dict, Path]]:
        found: dict[str, tuple[dict, Path]] = {}
        paths = [GLOBAL_REGISTRY, ORGANIZATION_REGISTRY, *sorted(FRAGMENTS.glob("*.json"))]
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for task in payload.get("tasks", []):
                if task.get("source_state_vector_ref"):
                    task_id = task["task_id"]
                    self.assertNotIn(task_id, found, f"duplicate vectorized task {task_id}")
                    found[task_id] = (task, path)
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
        self.assertEqual(set(ids), set(registry))

        coverage = index["coverage"]
        self.assertEqual(coverage["indexed_vectorized_tasks"], len(rows))
        self.assertEqual(
            coverage["local_cosv_record_tasks"] + coverage["external_owner_projection_tasks"],
            len(rows),
        )

    def test_index_vectors_match_machine_sources(self) -> None:
        index = self.load_index()
        registry = self.vectorized_registry_tasks()
        for row in index["tasks"]:
            task, path = registry[row["task_id"]]
            self.assertEqual(row["registry_ref"], path.relative_to(ROOT).as_posix())
            self.assertEqual(row["source_state_vector_ref"], task["source_state_vector_ref"])
            self.assertRegex(row["vector"], r"^[0-9]{14}$")
            self.assertEqual(row["vector_state"], "EMITTED")
            self.assertEqual(row["authority_effect"], "NONE")

            ref = row["source_state_vector_ref"]
            if ref.startswith("control/task-vectors/"):
                record = json.loads((ROOT / ref).read_text(encoding="utf-8"))
                self.assertTrue(cosv.validate_record(record))
                self.assertEqual(record["profile"], "task.v1")
                self.assertEqual(record["vector"], row["vector"])
                self.assertEqual(record["exact_metrics"]["symbol_order"], "LRUIVGOCMTBEAP")
                if row["task_id"] == "SHWP-DURABLE-RUNTIME-ACTIVATION":
                    self.assertEqual(record["vector"], "60000000101000")
                    self.assertEqual(record["exact_metrics"]["lifecycle"], "BLOCKED")
                    self.assertEqual(record["exact_metrics"]["blocker_count"], 1)
            else:
                embedded = task["machine_readable_state"]["cosv"]
                self.assertEqual(embedded["profile"], "task.v1")
                self.assertEqual(embedded["notation"], "L R U I V G O C M T B E A P")
                self.assertEqual(embedded["width"], 14)
                self.assertEqual(embedded["vector"], row["vector"])
                self.assertEqual(embedded["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
