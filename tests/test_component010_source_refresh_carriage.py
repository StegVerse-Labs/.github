from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_component010_source_refresh_contains_existing_gate_files():
    source = (ROOT / 'scripts/refresh_sovereign_worker_runtime_source.py').read_text()
    for name in (
        'scripts/evaluate_task_registry_ai_session_checkin.py',
        'scripts/evaluate_task_registry_collision_checkin.py',
        'scripts/task_registry_checkin_event_history.py',
        'scripts/validate_task_registration_substrate_resolution.py',
        'data/task-registry-ai-ingress-policy.json',
        'data/task-registry-general-checkin-caller-policy.json',
    ):
        assert 'Path("' + name + '")' in source
