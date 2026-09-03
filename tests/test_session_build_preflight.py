import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "session_build_preflight.py"

class SessionBuildPreflightTests(unittest.TestCase):
    def fake_root(self, decision, **extra):
        tmp = tempfile.TemporaryDirectory()
        scripts = Path(tmp.name) / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        payload = {
            "authority_effect": "NONE_INDEX_RESOLUTION_ONLY",
            "decision": decision,
            "generic_blocker_permitted": False,
            "machine_continuation_required": decision == "CONTINUE_MACHINE_EXECUTION",
            "indexed_truth_usable": decision != "EXACT_BLOCKER_ONLY",
            "existing_capability_found": decision in {
                "CONTINUE_MACHINE_EXECUTION", "REUSE_OR_EXTEND_EXISTING", "EXACT_BLOCKER_ONLY"
            },
        }
        payload.update(extra)
        (scripts / "preflight.py").write_text(
            "import json\nprint(json.dumps(" + repr(payload) + "))\n",
            encoding="utf-8",
        )
        return tmp

    def run_entry(self, root, goal="test goal"):
        return subprocess.run(
            [
                sys.executable,
                str(ENTRY),
                "--goal", goal,
                "--stegindex-root", root,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_reuse_prevents_new_task_creation(self):
        with self.fake_root("REUSE_OR_EXTEND_EXISTING") as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "REUSE_EXISTING_CAPABILITY")
        self.assertFalse(result["task_creation_permitted"])

    def test_machine_continuation_prevents_new_task_creation(self):
        with self.fake_root("CONTINUE_MACHINE_EXECUTION") as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "CONTINUE_THROUGH_CANONICAL_OWNER")
        self.assertFalse(result["task_creation_permitted"])

    def test_exact_dependency_prevents_new_task_creation(self):
        with self.fake_root(
            "EXACT_BLOCKER_ONLY",
            exact_dependency="indexed_truth_reconciled",
            indexed_truth_usable=False,
        ) as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "STOP_AT_EXACT_DEPENDENCY")
        self.assertFalse(result["task_creation_permitted"])

    def test_no_match_is_only_state_that_permits_new_work(self):
        with self.fake_root("NO_EXISTING_CAPABILITY_MATCH") as tmp:
            proc = self.run_entry(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["disposition"], "NEW_WORK_MAY_BE_CONSIDERED")
        self.assertTrue(result["task_creation_permitted"])

if __name__ == "__main__":
    unittest.main()
