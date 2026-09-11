import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"


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
