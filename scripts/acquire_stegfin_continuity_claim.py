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


def heartbeat_conflict(state: dict[str, Any]) -> tuple[bool, int]:
    leases = state["subsignals"]["worker_coordination"]["active_leases"]
    max_fence = 0
    for lease in leases:
        fence = lease.get("fencing_token")
        if isinstance(fence, int):
            max_fence = max(max_fence, fence)
        if lease.get("task_id") in CONFLICT_TASKS and lease.get("task_state") not in {"COMPLETE", "SUPERSEDED", "RELEASED"}:
            return True, max_fence
    return False, max_fence


def acquire_claim(
    *,
    carrier_id: str,
    heartbeat_state: Path,
    state_root: Path,
    ttl_seconds: int,
) -> dict[str, Any]:
    if not carrier_id.strip():
        raise RuntimeError("carrier id required")
    if ttl_seconds < 60 or ttl_seconds > 1800:
        raise RuntimeError("continuity claim TTL must be 60..1800 seconds")

    with exclusive_claim_lock(state_root):
        heartbeat = load_required_coordination(heartbeat_state)
        conflict, heartbeat_max_fence = heartbeat_conflict(heartbeat)
        if conflict:
            raise RuntimeError("continuity claim denied: resident StegFin worker already owns the validation lineage")

        state_file = state_root / "claims" / f"{TASK_ID}.json"
        current = load(state_file)
        now = datetime.now(timezone.utc)
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
            "heartbeat_state_epoch_observed": heartbeat["epoch"],
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        material = acquire_claim(
            carrier_id=args.carrier_id,
            heartbeat_state=args.heartbeat_state,
            state_root=args.state_root,
            ttl_seconds=args.ttl_seconds,
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
