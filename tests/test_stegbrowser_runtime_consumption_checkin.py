import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"


def run_checkin():
    payload = {
        "task_id": TASK_ID,
        "caller_surface": CALLER_SURFACE,
        "checkin_context": {
            "repository": "StegVerse-Labs/.github",
            "branch": "stegbrowser-runtime-consumption-checkin-001",
            "first_unresolved_predicate": "TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED",
        },
    }
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_stegbrowser_runtime_consumption_exact_registry_checkin_is_continue():
    out = run_checkin()
    assert out["schema"] == "stegverse.task-registry-checkin-disposition/v1"
    assert out["task_id"] == TASK_ID
    assert out["caller_surface"] == CALLER_SURFACE
    assert out["registry_identity_source"] == "CANONICAL_TASK_REGISTRY"
    assert out["authority_effect"] == "NONE"
    assert out["selected_execution_substrate"] == "STEG-BROWSER-RETAINED-RESIDENT-NODE"
    assert out["disposition"] == "CONTINUE", json.dumps(out, sort_keys=True)
    assert out["session_action"] == "CONTINUE_CURRENT_TASK"
    assert out["hard_collision_task_ids"] == []
