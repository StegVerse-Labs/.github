#!/usr/bin/env python3
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"


def load_module():
    spec = importlib.util.spec_from_file_location("canonical_work_resident_consumer", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def seed_preserved_source_state(mod, source: Path) -> None:
    source_registry = source / "data/canonical-task-registry.json"
    source_registry.parent.mkdir(parents=True, exist_ok=True)
    source_registry.write_text(json.dumps({"generation": 15}) + "\n", encoding="utf-8")
    for rel in mod.PRESERVE_IF_PRESENT:
        if rel == Path("data/canonical-task-registry.json"):
            continue
        path = source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")


class CanonicalWorkResidentRegistryPreservationTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_existing_runtime_registry_is_preserved(self):
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as runtime_dir:
            source = Path(source_dir)
            runtime = Path(runtime_dir)
            for rel in self.mod.MATERIALIZE:
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("source\n", encoding="utf-8")
            seed_preserved_source_state(self.mod, source)
            source_registry = source / "data/canonical-task-registry.json"
            runtime_registry = runtime / "data/canonical-task-registry.json"
            runtime_registry.parent.mkdir(parents=True, exist_ok=True)
            runtime_registry.write_text(json.dumps({"generation": 99, "runtime_projection": True}) + "\n", encoding="utf-8")

            before = runtime_registry.read_bytes()
            rows = self.mod.materialize(source, runtime)
            after = runtime_registry.read_bytes()

            self.assertEqual(after, before)
            row = next(row for row in rows if row["path"] == "data/canonical-task-registry.json")
            self.assertTrue(row["preserved_existing_runtime_projection"])
            self.assertFalse(row["exact_copy"])
            self.assertNotEqual(row["sha256"], row["source_sha256"])

    def test_missing_runtime_registry_is_seeded_from_source(self):
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as runtime_dir:
            source = Path(source_dir)
            runtime = Path(runtime_dir)
            for rel in self.mod.MATERIALIZE:
                path = source / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("source\n", encoding="utf-8")
            seed_preserved_source_state(self.mod, source)
            source_registry = source / "data/canonical-task-registry.json"

            rows = self.mod.materialize(source, runtime)
            runtime_registry = runtime / "data/canonical-task-registry.json"

            self.assertEqual(runtime_registry.read_bytes(), source_registry.read_bytes())
            row = next(row for row in rows if row["path"] == "data/canonical-task-registry.json")
            self.assertFalse(row["preserved_existing_runtime_projection"])
            self.assertTrue(row["exact_copy"])


    def test_current_goal_can_be_projected_into_preserved_stale_registry(self):
        task_id = "HYGIENE-CAUSAL-ROOTS-001"
        task = {
            "schema": "stegverse.canonical-task-record/v1",
            "task_id": task_id,
            "correlation_id": task_id,
            "root_correlation_id": task_id,
            "coordination_state": "PROPOSED",
        }
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as runtime_dir:
            source = Path(source_dir)
            runtime = Path(runtime_dir)
            source_registry = source / "data/canonical-task-registry.json"
            source_registry.parent.mkdir(parents=True, exist_ok=True)
            source_registry.write_text(json.dumps({"generation": 22, "tasks": [task]}) + "\n", encoding="utf-8")
            runtime_registry = runtime / "data/canonical-task-registry.json"
            runtime_registry.parent.mkdir(parents=True, exist_ok=True)
            runtime_registry.write_text(json.dumps({"generation": 21, "tasks": []}) + "\n", encoding="utf-8")
            runtime_entrypoint = runtime / self.mod.TARGET_ENTRYPOINT
            runtime_entrypoint.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / self.mod.TARGET_ENTRYPOINT, runtime_entrypoint)

            identity = self.mod.ensure_task_identity_materialized(source, runtime, task_id)
            projection = self.mod.refresh_current_goal_registry_projection(runtime, task_id)
            refreshed = json.loads(runtime_registry.read_text(encoding="utf-8"))

            self.assertEqual(identity["state"], "SOURCE_TASK_SHARD_MATERIALIZED")
            self.assertEqual(identity["source_kind"], "MONOLITHIC_SOURCE_REGISTRY")
            self.assertEqual(projection["state"], "EXACT_SHARD_PROJECTED_INTO_MONOLITHIC_RUNTIME_REGISTRY")
            self.assertEqual([row["task_id"] for row in refreshed["tasks"]], [task_id])
            self.assertEqual(refreshed["generation"], 22)
            self.assertEqual(projection["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
