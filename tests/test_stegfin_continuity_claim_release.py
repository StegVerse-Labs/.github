from __future__ import annotations

import json
from pathlib import Path

from workers.stegfin_continuity_carrier_worker_v2 import TASK_ID, release_owned_claim


def write_claim(home: Path, carrier: str, state: str = "ACTIVE") -> Path:
    path = home / ".stegverse" / "continuity" / "claims" / f"{TASK_ID}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema": "stegverse.continuity-claim.v1",
        "task_id": TASK_ID,
        "goal_id": "STEGFIN-BASE-ROUNDTRIP-001",
        "collision_scope": "stegfin:base-validation-entry:0xA503DCe5471492bbA2D06e9f78F4d9D6Bcc852aA:12.50-USDC-WETH",
        "claim_id": "CONT-STEGFIN-CONTINUITY-CARRIER-007-G21",
        "fencing_token": 21,
        "carrier_id": carrier,
        "state": state,
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_allowed": False,
        "github_token_required": False,
        "wallet_signing_authority": "USER_ONLY",
        "broadcast_authority": "USER_ONLY",
    }, indent=2) + "\n", encoding="utf-8")
    return path


def test_release_owned_claim_releases_same_worker(tmp_path: Path) -> None:
    path = write_claim(tmp_path, "worker-a")
    assert release_owned_claim("worker-a", "STEGFIN_CONTINUITY_RUNTIME_REQUIRED", home=tmp_path) is True
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["state"] == "RELEASED"
    assert value["release_reason"] == "STEGFIN_CONTINUITY_RUNTIME_REQUIRED"
    assert value["credential_authority"] == "TV/TVC"
    assert value["github_token_required"] is False
    assert value["wallet_signing_authority"] == "USER_ONLY"
    assert value["broadcast_authority"] == "USER_ONLY"
    assert value["receipt_sha256"].startswith("sha256:")


def test_release_owned_claim_refuses_other_worker(tmp_path: Path) -> None:
    path = write_claim(tmp_path, "worker-b")
    assert release_owned_claim("worker-a", "BLOCKED", home=tmp_path) is False
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["state"] == "ACTIVE"
    assert "released_at_utc" not in value


def test_release_owned_claim_is_idempotent_after_release(tmp_path: Path) -> None:
    path = write_claim(tmp_path, "worker-a")
    assert release_owned_claim("worker-a", "COMPLETE", home=tmp_path) is True
    first = json.loads(path.read_text(encoding="utf-8"))
    assert release_owned_claim("worker-a", "COMPLETE", home=tmp_path) is False
    second = json.loads(path.read_text(encoding="utf-8"))
    assert first == second
