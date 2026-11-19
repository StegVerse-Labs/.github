"""Exercise query CLI against canonical string and mapping references."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/query_canonical_tasks.py"


class CanonicalTaskQueryTests(unittest.TestCase):
    def query(self, *args):
        registry = {
            "generation": 326,
            "tasks": [
                {"task_id": "MIXED", "coordination_state": "ACTIVE",
                 "dependencies": ["STRING-DEP", {"dependency_id": "MAP-DEP", "ref": "PinnedRef"}],
                 "blockers": ["STRING-BLOCK", {"blocker_id": "MAP-BLOCK", "reason": "NeedReceipt"}]},
                {"task_id": "CLOSED", "coordination_state": "CLOSED",
                 "dependencies": ["STRING-DEP"], "blockers": []},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            before = json.dumps(registry).encode()
            path.write_bytes(before)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--registry", str(path), *args],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(path.read_bytes(), before)
        return json.loads(result.stdout)

    def test_string_dependency_and_blocker_search(self):
        for term in ("string-dep", "STRING-BLOCK"):
            with self.subTest(term=term):
                result = self.query(term)
                self.assertEqual([x["task_id"] for x in result["tasks"]], ["MIXED"])

    def test_mapping_fields_and_and_matching(self):
        self.assertEqual(self.query("pinnedref", "needreceipt")["count"], 1)
        self.assertEqual(self.query("pinnedref", "missing")["count"], 0)

    def test_original_reference_shapes_and_nonclaim_preserved(self):
        result = self.query("mixed")
        row = result["tasks"][0]
        self.assertEqual(row["dependencies"], ["STRING-DEP", {"dependency_id": "MAP-DEP", "ref": "PinnedRef"}])
        self.assertEqual(row["blockers"], ["STRING-BLOCK", {"blocker_id": "MAP-BLOCK", "reason": "NeedReceipt"}])
        self.assertEqual(result["nonclaim"], "QUERY_RESULT_DOES_NOT_GRANT_CLAIM_OR_EXECUTION_AUTHORITY")

    def test_closed_filter_and_include_closed(self):
        self.assertEqual(self.query("string-dep")["count"], 1)
        self.assertEqual(self.query("--include-closed", "string-dep")["count"], 2)

    def test_state_filter(self):
        result = self.query("--include-closed", "--state", "CLOSED", "string-dep")
        self.assertEqual([x["task_id"] for x in result["tasks"]], ["CLOSED"])


if __name__ == "__main__":
    unittest.main()
