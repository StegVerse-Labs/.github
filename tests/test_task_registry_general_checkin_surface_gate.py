from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
POLICY = ROOT / "data" / "task-registry-general-checkin-caller-policy.json"
AI_GATE = ROOT / "scripts" / "evaluate_task_registry_ai_session_checkin.py"
BOOTSTRAP = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"
TASK_ID = "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"


def run_eval(payload: dict, strip_pytest: bool = False):
    env = os.environ.copy()
    if strip_pytest:
        env.pop("PYTEST_CURRENT_TEST", None)
    return subprocess.run([sys.executable, str(EVALUATOR)], cwd=str(ROOT), input=json.dumps(payload), text=True, capture_output=True, env=env, check=False)


def test_policy_surface_set_and_nonclaims():
    policy = json.loads(POLICY.read_text())
    assert set(policy["admitted_production_caller_surfaces"]) == {"AI_SESSION_GATE", "INTERNAL_CANONICAL_WORK_BOOTSTRAP"}
    assert policy["missing_or_unknown_surface"] == "FAIL_CLOSED"
    assert policy["declaration_is_authentic_origin_attestation"] is False
    assert policy["runtime_external_ai_reachability_proven_absent"] is False


def test_missing_surface_fails_closed_outside_pytest():
    proc = run_eval({"task_id": TASK_ID}, strip_pytest=True)
    assert proc.returncode != 0
    assert "caller_surface required" in proc.stderr


def test_unknown_surface_fails_closed():
    proc = run_eval({"task_id": TASK_ID, "caller_surface": "UNCLASSIFIED_DIRECT"}, strip_pytest=True)
    assert proc.returncode != 0
    assert "caller_surface not admitted" in proc.stderr


def test_internal_surface_is_preserved_without_attestation_claim():
    proc = run_eval({"task_id": TASK_ID, "caller_surface": "INTERNAL_CANONICAL_WORK_BOOTSTRAP"}, strip_pytest=True)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["caller_surface"] == "INTERNAL_CANONICAL_WORK_BOOTSTRAP"
    assert payload["caller_surface_attestation_proven"] is False
    assert payload["authority_effect"] == "NONE"


def test_production_callers_bind_expected_surfaces():
    assert 'CALLER_SURFACE = "AI_SESSION_GATE"' in AI_GATE.read_text()
    assert 'request["caller_surface"] = CALLER_SURFACE' in AI_GATE.read_text()
    assert 'CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"' in BOOTSTRAP.read_text()
    assert '"caller_surface": CALLER_SURFACE' in BOOTSTRAP.read_text()
