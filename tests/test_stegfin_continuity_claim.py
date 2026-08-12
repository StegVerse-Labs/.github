from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "acquire_stegfin_continuity_claim.py"


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_claim_denied_when_resident_stegfin_lease_active(tmp_path: Path) -> None:
    heartbeat = tmp_path / "heartbeat.json"
    write(heartbeat, {
        "epoch": 29,
        "subsignals": {"worker_coordination": {"active_leases": [{
            "task_id": "STEGFIN-LIVE-PRETRADE-005",
            "task_state": "ACTIVE",
            "fencing_token": 31,
        }]}}
    })
    completed = subprocess.run([
        sys.executable, str(SCRIPT),
        "--carrier-id", "test-carrier",
        "--heartbeat-state", str(heartbeat),
        "--state-root", str(tmp_path / "state"),
    ], capture_output=True, text=True, check=False)
    assert completed.returncode != 0
    assert "resident StegFin worker already owns" in (completed.stderr + completed.stdout)


def test_claim_uses_fence_above_observed_resident_state(tmp_path: Path) -> None:
    heartbeat = tmp_path / "heartbeat.json"
    write(heartbeat, {
        "epoch": 29,
        "subsignals": {"worker_coordination": {"active_leases": [{
            "task_id": "OTHER-TASK",
            "task_state": "ACTIVE",
            "fencing_token": 44,
        }]}}
    })
    output = tmp_path / "claim.json"
    completed = subprocess.run([
        sys.executable, str(SCRIPT),
        "--carrier-id", "test-carrier",
        "--heartbeat-state", str(heartbeat),
        "--state-root", str(tmp_path / "state"),
        "--output", str(output),
    ], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    claim = json.loads(output.read_text(encoding="utf-8"))
    assert claim["fencing_token"] == 45
    assert claim["credential_authority"] == "TV/TVC"
    assert claim["non_tv_tvc_secret_or_token_allowed"] is False
    assert claim["wallet_signing_authority"] == "USER_ONLY"
    assert claim["broadcast_authority"] == "USER_ONLY"
