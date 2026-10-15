"""Verify canonical registration discovery links without third-party dependencies."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/TASK_REGISTRATION_GUIDE.md"
ENTRYPOINTS = [
    ROOT / "README.md",
    ROOT / "scripts/query_canonical_tasks.py",
    ROOT / "scripts/run_task_registry_canonical_work_cycle.py",
    ROOT / "docs/WORKER_TASK_ADMISSION_PACKET_MIRROR_HANDOFF.md",
]

class RegistrationDiscoveryTests(unittest.TestCase):
    def test_guide_and_links(self):
        self.assertTrue(GUIDE.is_file())
        for path in ENTRYPOINTS:
            with self.subTest(path=str(path)):
                self.assertIn("TASK_REGISTRATION_GUIDE.md", path.read_text(encoding="utf-8"))

    def test_authority_separation(self):
        body = GUIDE.read_text(encoding="utf-8")
        for marker in (
            "data/canonical-task-registry.json",
            "scripts/evaluate_task_registry_collision_checkin.py",
            "worker_task_admission.py",
            "ALLOW | DENY | FAIL_CLOSED",
            "disclosure",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, body)

if __name__ == "__main__":
    unittest.main()
