"""Regression: scripts/query_canonical_tasks.py reads plain-string dependency and blocker entries.

schemas/canonical-task-record.schema.json requires object entries, but registry rows at generation 321 hold
bare strings; the query used to raise AttributeError on them. A string entry is read as its ref.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "query_canonical_tasks.py"

AGGREGATE = {
    "schema": "stegverse.canonical-task-registry/v1",
    "generation": 1,
    "tasks": [
        {
            "task_id": "TASK-STRING-ENTRIES-001",
            "coordination_state": "ACTIVE",
            "goal": "string entries",
            "dependencies": ["TASK-UPSTREAM-STRING-DEP-001"],
            "blockers": ["owner custody receipt pending"],
        },
        {
            "task_id": "TASK-OBJECT-ENTRIES-001",
            "coordination_state": "ACTIVE",
            "goal": "object entries",
            "dependencies": [{"dependency_id": "DEP-OBJ-1", "kind": "TASK", "state": "UNRESOLVED",
                              "ref": "TASK-UPSTREAM-OBJECT-DEP-001"}],
            "blockers": [{"blocker_id": "BLK-OBJ-1", "dependency_id": "DEP-OBJ-1", "reason": "object blocker"}],
        },
    ],
}


class QueryCanonicalTasksStringEntriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = Path(self.tmp.name) / "registry.json"
        self.registry.write_text(json.dumps(AGGREGATE), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def query(self, *terms):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--registry", str(self.registry), *terms],
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return [t["task_id"] for t in json.loads(proc.stdout)["tasks"]]

    def test_any_term_does_not_crash(self):
        self.assertEqual(self.query("entries"), ["TASK-STRING-ENTRIES-001", "TASK-OBJECT-ENTRIES-001"])

    def test_string_dependency_matches_as_ref(self):
        self.assertEqual(self.query("upstream-string-dep"), ["TASK-STRING-ENTRIES-001"])

    def test_string_blocker_matches_as_ref(self):
        self.assertEqual(self.query("custody receipt"), ["TASK-STRING-ENTRIES-001"])

    def test_object_entries_still_match(self):
        self.assertEqual(self.query("upstream-object-dep"), ["TASK-OBJECT-ENTRIES-001"])
        self.assertEqual(self.query("blk-obj-1"), ["TASK-OBJECT-ENTRIES-001"])


if __name__ == "__main__":
    unittest.main()
