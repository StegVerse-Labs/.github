from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SourceRefreshCarriageTest(unittest.TestCase):
    def test_existing_gate_files(self):
        source = (ROOT / 'scripts/refresh_sovereign_worker_runtime_source.py').read_text()
        for name in (
            'scripts/evaluate_task_registry_ai_session_checkin.py',
            'scripts/evaluate_task_registry_collision_checkin.py',
            'scripts/task_registry_checkin_event_history.py',
            'scripts/validate_task_registration_substrate_resolution.py',
            'data/task-registry-ai-ingress-policy.json',
            'data/task-registry-general-checkin-caller-policy.json',
        ):
            self.assertTrue('Path("' + name + '")' in source)
