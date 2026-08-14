from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "acquire_stegfin_continuity_claim.py"


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def heartbeat(*, last_cycle_at: datetime, leases: list[dict], epoch: int = 29) -> dict:
    return {
        "epoch": epoch,
        "last_cycle_at": iso(last_cycle_at),
        "subsignals": {"worker_coordination": {"active_leases": leases}},
    }


def test_claim_denied_when_fresh_resident_stegfin_lease_active(tmp_path: Path) -> None:
    heartbeat_path = tmp_path / "heartbeat.json"
    write(heartbeat_path, heartbeat(
        last_cycle_at=datetime.now(timezone.utc),
        leases=[{
            "task_id": "STEGFIN-LIVE-PRETRADE-005",
            "task_state": "ACTIVE",
            "fencing_token": 31,
        }],
    ))
    completed = subprocess.run([
        sys.executable, str(SCRIPT),
        "--carrier-id", "test-carrier",
        "--heartbeat-state", str(heartbeat_path),
        "--state-root", str(tmp_path / "state"),
        "--heartbeat-stale-after-seconds", "60",
    ], capture_output=True, text=True, check=False)
    assert completed.returncode != 0
    assert "fresh resident StegFin worker already owns" in (completed.stderr + completed.stdout)


def test_stale_resident_stegfin_lease_is_preserved_but_not_a_collision_block(tmp_path: Path) -> None:
    heartbeat_path = tmp_path / "heartbeat.json"
    write(heartbeat_path, heartbeat(
        last_cycle_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        leases=[{
            "task_id": "STEGFIN-LIVE-PRETRADE-005",
            "task_state": "ACTIVE",
            "fencing_token": 31,
            "claim_id": "RESIDENT-G31",
            "worker_id": "resident-stegfin-worker",
        }],
    ))
    output = tmp_path / "claim.json"
    state_root = tmp_path / "state"
    completed = subprocess.run([
        sys.executable, str(SCRIPT),
        "--carrier-id", "test-carrier",
        "--heartbeat-state", str(heartbeat_path),
        "--state-root", str(state_root),
        "--heartbeat-stale-after-seconds", "60",
        "--output", str(output),
    ], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    claim = json.loads(output.read_text(encoding="utf-8"))
    assert claim["resident_heartbeat_liveness_known"] is True
    assert claim["resident_heartbeat_stale"] is True
    assert claim["fencing_token"] == 32
    assert claim["master_records_notification_required"] is True
    receipt = json.loads((state_root / "receipts" / "stale-heartbeat" / "STEGFIN-CONTINUITY-CARRIER-007-HB29.json").read_text(encoding="utf-8"))
    assert receipt["stale"] is True
    assert receipt["observed_active_leases"][0]["claim_id"] == "RESIDENT-G31"
    assert receipt["resident_lease_collision_effect"] == "NONBLOCKING_WHILE_HEARTBEAT_STALE"
    assert receipt["new_execution_authority_granted"] is False
    assert receipt["master_records_destination"] == "master-records/orchestration"


def test_claim_uses_fence_above_observed_resident_state(tmp_path: Path) -> None:
    heartbeat_path = tmp_path / "heartbeat.json"
    write(heartbeat_path, heartbeat(
        last_cycle_at=datetime.now(timezone.utc),
        leases=[{
            "task_id": "OTHER-TASK",
            "task_state": "ACTIVE",
            "fencing_token": 44,
        }],
    ))
    output = tmp_path / "claim.json"
    completed = subprocess.run([
        sys.executable, str(SCRIPT),
        "--carrier-id", "test-carrier",
        "--heartbeat-state", str(heartbeat_path),
        "--state-root", str(tmp_path / "state"),
        "--heartbeat-stale-after-seconds", "60",
        "--output", str(output),
    ], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    claim = json.loads(output.read_text(encoding="utf-8"))
    assert claim["fencing_token"] == 45
    assert claim["resident_heartbeat_liveness_known"] is True
    assert claim["resident_heartbeat_stale"] is False
    assert claim["credential_authority"] == "TV/TVC"
    assert claim["non_tv_tvc_secret_or_token_allowed"] is False
    assert claim["wallet_signing_authority"] == "USER_ONLY"
    assert claim["broadcast_authority"] == "USER_ONLY"


def test_missing_liveness_timestamp_never_creates_stale_override(tmp_path: Path) -> None:
    heartbeat_path = tmp_path / "heartbeat.json"
    write(heartbeat_path, {
        "epoch": 29,
        "subsignals": {"worker_coordination": {"active_leases": [{
            "task_id": "STEGFIN-LIVE-ENTRY-003",
            "task_state": "ACTIVE",
            "fencing_token": 31,
        }]}},
    })
    completed = subprocess.run([
        sys.executable, str(SCRIPT),
        "--carrier-id", "test-carrier",
        "--heartbeat-state", str(heartbeat_path),
        "--state-root", str(tmp_path / "state"),
    ], capture_output=True, text=True, check=False)
    assert completed.returncode != 0
    assert "fresh resident StegFin worker already owns" in (completed.stderr + completed.stdout)
