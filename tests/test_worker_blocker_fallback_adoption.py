import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkerBlockerFallbackAdoptionTests(unittest.TestCase):
    def test_adoption_inventory(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_worker_blocker_fallback_adoption.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("WORKER_BLOCKER_FALLBACK_ADOPTION_PASS", proc.stdout)

if __name__ == "__main__":
    unittest.main()
