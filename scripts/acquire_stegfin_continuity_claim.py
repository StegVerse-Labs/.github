#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterator

TASK_ID = "STEGFIN-CONTINUITY-CARRIER-007"
GOAL_ID = "STEGFIN-BASE-ROUNDTRIP-001"
COLLISION_SCOPE = "stegfin:base-validation-entry:0xA503DCe5471492bbA2D06e9f78F4d9D6Bcc852aA:12.50-USDC-WETH"
CONFLICT_TASKS = {"STEGFIN-LIVE-ENTRY-003", "STEGFIN-LIVE-PRETRADE-005"}
DEFAULT_HEARTBEAT_STALE_AFTER_SECONDS = 60


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def load_required_coordination(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"authoritative heartbeat coordination state unavailable: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"authoritative heartbeat coordination state malformed: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"authoritative heartbeat coordination state must be an object: {path}")
    epoch = value.get("epoch")
    subsignals = value.get("subsignals")
    worker_coordination = subsignals.get("worker_coordination") if isinstance(subsignals, dict) else None
    leases = worker_coordination.get("active_leases") if isinstance(worker_coordination, dict) else None
    if not isinstance(epoch, int) or epoch < 0:
        raise RuntimeError("authoritative heartbeat coordination state missing valid epoch")
    if not isinstance(leases, list):
        raise RuntimeError("authoritative heartbeat coordination state missing active_leases")
    for index, lease in enumerate(leases):
        if not isinstance(lease, dict):
            raise RuntimeError(f"authoritative heartbeat coordination lease {index} is malformed")
        fence = lease.get("fencing_token")
        if fence is not None and (not isinstance(fence, int) or fence < 0):
            raise RuntimeError(f"authoritative heartbeat coordination lease {index} has invalid fencing_token")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


@contextmanager
def exclusive_claim_lock(state_root: Path) -> Iterator[None]:
    lock_dir = state_root / "claims" / f".{TASK_ID}.acquire.lock"
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_dir.mkdir()
    except FileExistsError as exc:
        raise RuntimeError("continuity claim denied: claim acquisition already in progress") from exc
    try:
        yield
    finally:
        try:
            lock_dir.rmdir()
        except FileNotFoundError:
            pass


def heartbeat_staleness(
    state: dict[str, Any],
    *,
    now: datetime,
    stale_after_seconds: int,
) -> tuple[bool, int, datetime | None]:
    if stale_after_seconds < 1:
        raise RuntimeError("heartbeat stale threshold must be positive")
    last_cycle = parse_utc(state.get("last_cycle_at"))
    if last_cycle is None:
        # Absence of a liveness timestamp never creates permission to ignore a
        # resident collision. It simply disables the stale-lease override and
        # preserves the pre-existing fail-closed collision semantics.
        return False, 0, None
    age_seconds = max(0, int((now - last_cycle).total_seconds()))
    return age_seconds >= stale_after_seconds, age_seconds, last_cycle


def heartbeat_conflict(
    state: dict[str, Any],
    *,
    now: datetime,
    stale_after_seconds: int,
) -> tuple[bool, int, bool, int, bool]:
    leases = state["subsignals"]["worker_coordination"]["active_leases"]
    stale, age_seconds, last_cycle = heartbeat_staleness(
        state,
        now=now,
        stale_after_seconds=stale_after_seconds,
    )
    max_fence = 0
    resident_conflict = False
    for lease in leases:
        fence = lease.get("fencing_token")
        if isinstance(fence, int):
            max_fence = max(max_fence, fence)
        if lease.get("task_id") in CONFLICT_TASKS and lease.get("task_state") not in {"COMPLETE", "SUPERSEDED", "RELEASED"}:
            resident_conflict = True
    # A stale resident heartbeat may lose collision authority, but this
    # observation never grants execution authority. The new continuity claim
    # still fences strictly above every observed resident fence.
    return resident_conflict and not stale, max_fence, stale, age_seconds, last_cycle is not None


def record_stale_heartbeat_reclamation(
    *,
    heartbeat: dict[str, Any],
    state_root: Path,
    observed_at: datetime,
    age_seconds: int,
    stale_after_seconds: int,
    max_observed_fence: int,
) -> dict[str, Any]:
    leases = heartbeat["subsignals"]["worker_coordination"]["active_leases"]
    material = {
        "schema": "stegverse.stale-heartbeat-reclamation.v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "collision_scope": COLLISION_SCOPE,
        "observed_heartbeat_epoch": heartbeat["epoch"],
        "observed_last_cycle_at": heartbeat.get("last_cycle_at"),
        "observed_at_utc": observed_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "heartbeat_age_seconds": age_seconds,
        "stale_after_seconds": stale_after_seconds,
        "stale": True,
        "observed_active_leases": leases,
        "max_observed_fencing_token": max_observed_fence,
        "resident_lease_collision_effect": "NONBLOCKING_WHILE_HEARTBEAT_STALE",
        "authority_effect": "REVOKE_STALE_COLLISION_ONLY_NO_EXECUTION_AUTHORITY_GRANTED",
        "new_execution_authority_granted": False,
        "master_records_notification_required": True,
        "master_records_destination": "master-records/orchestration",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
    }
    material["receipt_sha256"] = digest(material)
    output = state_root / "receipts" / "stale-heartbeat" / f"{TASK_ID}-HB{heartbeat['epoch']}.json"
    atomic_write(output, material)
    return material


def acquire_claim(
    *,
    carrier_id: str,
    heartbeat_state: Path,
    state_root: Path,
    ttl_seconds: int,
    heartbeat_stale_after_seconds: int = DEFAULT_HEARTBEAT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    if not carrier_id.strip():
        raise RuntimeError("carrier id required")
    if ttl_seconds < 60 or ttl_seconds > 1800:
        raise RuntimeError("continuity claim TTL must be 60..1800 seconds")
    if heartbeat_stale_after_seconds < 1 or heartbeat_stale_after_seconds > 3600:
        raise RuntimeError("heartbeat stale threshold must be 1..3600 seconds")

    with exclusive_claim_lock(state_root):
        heartbeat = load_required_coordination(heartbeat_state)
        now = datetime.now(timezone.utc)
        conflict, heartbeat_max_fence, heartbeat_stale, heartbeat_age_seconds, liveness_known = heartbeat_conflict(
            heartbeat,
            now=now,
            stale_after_seconds=heartbeat_stale_after_seconds,
        )
        if conflict:
            raise RuntimeError("continuity claim denied: fresh resident StegFin worker already owns the validation lineage")

        stale_receipt = None
        if heartbeat_stale:
            stale_receipt = record_stale_heartbeat_reclamation(
                heartbeat=heartbeat,
                state_root=state_root,
                observed_at=now,
                age_seconds=heartbeat_age_seconds,
                stale_after_seconds=heartbeat_stale_after_seconds,
                max_observed_fence=heartbeat_max_fence,
            )

        state_file = state_root / "claims" / f"{TASK_ID}.json"
        current = load(state_file)
        current_expiry = parse_utc(current.get("expires_at_utc"))
        if current.get("state") == "ACTIVE" and current_expiry is not None and current_expiry > now:
            raise RuntimeError("continuity claim denied: active continuity claim already exists")

        previous_fence = current.get("fencing_token") if isinstance(current.get("fencing_token"), int) else 0
        fence = max(previous_fence, heartbeat_max_fence) + 1
        issued = now.replace(microsecond=0)
        expires = issued + timedelta(seconds=ttl_seconds)
        material = {
            "schema": "stegverse.continuity-claim.v1",
            "task_id": TASK_ID,
            "goal_id": GOAL_ID,
            "collision_scope": COLLISION_SCOPE,
            "claim_id": f"CONT-{TASK_ID}-G{fence}",
            "fencing_token": fence,
            "carrier_id": carrier_id,
            "state": "ACTIVE",
            "issued_at_utc": issued.isoformat().replace("+00:00", "Z"),
            "expires_at_utc": expires.isoformat().replace("+00:00", "Z"),
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_allowed": False,
            "github_token_required": False,
            "wallet_signing_authority": "USER_ONLY",
            "broadcast_authority": "USER_ONLY",
            "resident_conflict_checked": True,
            "resident_heartbeat_liveness_known": liveness_known,
            "resident_heartbeat_stale": heartbeat_stale,
            "resident_heartbeat_age_seconds": heartbeat_age_seconds if liveness_known else None,
            "resident_heartbeat_stale_after_seconds": heartbeat_stale_after_seconds,
            "heartbeat_state_epoch_observed": heartbeat["epoch"],
            "stale_heartbeat_reclamation_receipt_sha256": stale_receipt.get("receipt_sha256") if stale_receipt else None,
            "master_records_notification_required": bool(stale_receipt),
        }
        material["receipt_sha256"] = digest(material)
        atomic_write(state_file, material)
        return material


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire a collision-safe StegFin continuity claim")
    parser.add_argument("--carrier-id", required=True)
    parser.add_argument("--heartbeat-state", type=Path, default=Path("control/heartbeat-state.json"))
    parser.add_argument("--state-root", type=Path, default=Path.home() / ".stegverse" / "continuity")
    parser.add_argument("--ttl-seconds", type=int, default=900)
    parser.add_argument("--heartbeat-stale-after-seconds", type=int, default=DEFAULT_HEARTBEAT_STALE_AFTER_SECONDS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        material = acquire_claim(
            carrier_id=args.carrier_id,
            heartbeat_state=args.heartbeat_state,
            state_root=args.state_root,
            ttl_seconds=args.ttl_seconds,
            heartbeat_stale_after_seconds=args.heartbeat_stale_after_seconds,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    state_file = args.state_root / "claims" / f"{TASK_ID}.json"
    output = args.output or state_file
    if output != state_file:
        atomic_write(output, material)
    print(json.dumps(material, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
