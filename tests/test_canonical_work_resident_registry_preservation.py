#!/usr/bin/env python3
import importlib.util
import json
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
            source_registry = source / "data/canonical-task-registry.json"
            source_registry.parent.mkdir(parents=True, exist_ok=True)
            source_registry.write_text(json.dumps({"generation": 15}) + "\n", encoding="utf-8")
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
            source_registry = source / "data/canonical-task-registry.json"
            source_registry.parent.mkdir(parents=True, exist_ok=True)
            source_registry.write_text(json.dumps({"generation": 15}) + "\n", encoding="utf-8")

            rows = self.mod.materialize(source, runtime)
            runtime_registry = runtime / "data/canonical-task-registry.json"

            self.assertEqual(runtime_registry.read_bytes(), source_registry.read_bytes())
            row = next(row for row in rows if row["path"] == "data/canonical-task-registry.json")
            self.assertFalse(row["preserved_existing_runtime_projection"])
            self.assertTrue(row["exact_copy"])


if __name__ == "__main__":
    unittest.main()
