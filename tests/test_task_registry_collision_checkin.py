import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
BOOTSTRAP = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"


def run(task_id):
    p = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps({"task_id":task_id}), text=True, capture_output=True, check=True)
    return json.loads(p.stdout)


def test_unregistered_stops_before_mutation():
    out = run("THIS-TASK-DOES-NOT-EXIST")
    assert out["disposition"] == "STOP_NOT_REGISTERED"
    assert out["session_action"] == "END_OR_REGISTER_BEFORE_MUTATION"
    assert out["authority_effect"] == "NONE"


def test_checked_out_task_returns_collision_context():
    out = run("STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001")
    assert out["task_id"] == "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
    assert out["disposition"] in {"STOP_COLLISION", "COORDINATE_CONVERGENCE", "CONTINUE"}
    assert "collision_candidates" in out
    assert out["authority_effect"] == "NONE"


def test_retired_task_returns_stop_disposition():
    out = run("STEGCORE-UNKNOWN-PROBE-SEMANTICS-001")
    assert out["disposition"] in {"STOP_INACTIVE", "STOP_SUPERSEDED"}
    assert out["session_action"].startswith("END_SESSION")


def test_canonical_work_bootstrap_requires_registry_preflight_before_route_mutation():
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert 'COLLISION_EVALUATOR_REL = Path("scripts/evaluate_task_registry_collision_checkin.py")' in text
    assert "checkin = collision_preflight(args.task_id)" in text
    checkin_pos = text.index("checkin = collision_preflight(args.task_id)")
    installer_pos = text.index("run([sys.executable, installer])")
    assert checkin_pos < installer_pos
    assert 'if disposition != "CONTINUE":' in text
    assert 'raise RuntimeError("TASK_REGISTRY_CHECKIN:"' in text
    assert 'result.get("authority_effect") != "NONE"' in text
