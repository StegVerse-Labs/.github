from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-STEGNUTRITION-CONTINUATION-001"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def invocation() -> dict:
    handoff = load("handoffs/SHWP-STEGNUTRITION-CONTINUATION-001.json")
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 30,
        "task": {
            "task_id": TASK_ID,
            "claim_id": "CLAIM-STEGNUTRITION-TEST-G30",
            "worker_id": "stegnutrition-machine-continuation-worker",
            "worker_instance_id": "stegnutrition-machine-continuation-worker-HB30-G30",
            "heartbeat_timing": {"fencing_token": 30},
        },
        "handoff": handoff,
    }


def test_registry_fragment_has_unique_capability_and_no_token_requirement() -> None:
    fragment = load("control/worker-registry.d/stegnutrition-continuation-001.json")
    assert fragment["github_token_required"] is False
    task = fragment["tasks"][0]
    worker = fragment["workers"][0]
    assert task["task_id"] == TASK_ID
    assert task["state"] == "HANDOFF_READY"
    assert worker["adapter_ref"] == "process:stegnutrition-machine-continuation-v1"
    assert "stegnutrition_machine_continuation" in worker["capabilities"]


def test_process_adapter_allows_only_local_root_environment() -> None:
    adapters = load("control/process-worker-adapters.json")["adapters"]
    row = next(item for item in adapters if item["adapter_ref"] == "process:stegnutrition-machine-continuation-v1")
    assert row["command"] == ["python", "workers/stegnutrition_continuation_worker.py"]
    assert row["env_allowlist"] == ["STEGVERSE_STEGNUTRITION_ROOT"]
    notes = " ".join(row["notes"]).lower()
    assert "no github token" in notes
    assert "remote source checkout" in notes


def test_capability_profile_does_not_grant_general_code_or_github_authority() -> None:
    profiles = load("control/worker-capability-profiles.json")["profiles"]
    row = next(item for item in profiles if item["profile_id"] == "sovereign-runtime-worker-v1")
    assert "stegnutrition_machine_continuation" in row["allowed_capabilities"]
    assert "github_repository_write" not in row["allowed_capabilities"]
    assert "code_and_schema_implementation" not in row["allowed_capabilities"]


def test_worker_fails_closed_without_local_stegnutrition_materialization(tmp_path: Path) -> None:
    receipt = ROOT / "receipts/stegnutrition-continuation" / f"{TASK_ID}.json"
    if receipt.exists():
        receipt.unlink()
    env = os.environ.copy()
    env.pop("STEGVERSE_STEGNUTRITION_ROOT", None)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    proc = subprocess.run(
        [sys.executable, "workers/stegnutrition_continuation_worker.py"],
        cwd=ROOT,
        input=json.dumps(invocation()),
        text=True,
        capture_output=True,
        env=env,
        timeout=20,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["state"] == "BLOCKED"
    assert response["transition_id"] == "STEGNUTRITION_LOCAL_MATERIALIZATION_REQUIRED"
    assert response["blocker"]["solution_required"] is True
    assert "GitHub token" in response["blocker"]["workaround_candidates"][0]
    stored = json.loads(receipt.read_text(encoding="utf-8"))
    assert stored["github_token_required"] is False
    assert stored["github_repository_fetch_performed"] is False
    receipt.unlink()
