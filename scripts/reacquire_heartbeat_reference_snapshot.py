#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.reference_snapshot import evaluate_required_states, reacquire_reference_snapshot

DEFAULT_POLICY = Path("control/heartbeat-reference-snapshot-policy.json")
DEFAULT_LATEST = Path("control/heartbeat-reference-snapshot.json")
DEFAULT_HISTORY = Path("receipts/heartbeat-reference-snapshots")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        name = stream.name
    os.replace(name, path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reacquire a non-authorizing heartbeat reference snapshot under GATE_PASSBAND_DERIVED monitoring semantics.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--latest", type=Path, default=DEFAULT_LATEST)
    parser.add_argument("--history-dir", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--observed-at", default=None, help="Explicit observation timestamp for deterministic validation.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    policy_path = args.policy if args.policy.is_absolute() else root / args.policy
    latest_path = args.latest if args.latest.is_absolute() else root / args.latest
    history_dir = args.history_dir if args.history_dir.is_absolute() else root / args.history_dir

    policy = load_json(policy_path)
    carrier_ref = policy.get("carrier_state_ref")
    if not isinstance(carrier_ref, str) or not carrier_ref:
        raise SystemExit("snapshot policy carrier_state_ref is required")
    carrier = load_json(root / carrier_ref)
    previous = load_json(latest_path) if latest_path.is_file() else None
    required_states = evaluate_required_states(root, policy)
    snapshot, decision = reacquire_reference_snapshot(
        policy=policy,
        carrier=carrier,
        required_states=required_states,
        previous=previous,
        acquired_at=args.observed_at or utc_now(),
    )

    result: dict[str, Any] = {
        "schema": "stegverse.heartbeat-reference-snapshot-reacquisition-result/v1",
        "monitor_id": policy.get("monitor_id"),
        "goal_id": policy.get("goal_id"),
        "reacquisition_rule": policy.get("reacquisition_rule"),
        "reacquired": snapshot is not None,
        "decision": decision,
        "carrier_epoch_observed": carrier.get("epoch"),
        "carrier_generation_observed": carrier.get("generation"),
        "carrier_progression_effect": "NONE",
        "execution_authority": False,
        "claim_or_fence_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
    }

    if snapshot is not None:
        safe_id = snapshot["snapshot_id"].replace(":", "-")
        history_path = history_dir / f"{safe_id}.json"
        result["snapshot_id"] = snapshot["snapshot_id"]
        result["snapshot_sha256"] = snapshot["snapshot_sha256"]
        result["snapshot_latest_ref"] = str(latest_path.relative_to(root)) if latest_path.is_relative_to(root) else str(latest_path)
        result["snapshot_history_ref"] = str(history_path.relative_to(root)) if history_path.is_relative_to(root) else str(history_path)
        result["gate"] = snapshot["gate"]
        if not args.dry_run:
            if history_path.exists():
                existing = load_json(history_path)
                if existing.get("snapshot_sha256") != snapshot.get("snapshot_sha256"):
                    raise RuntimeError("snapshot history identity collision")
            else:
                atomic_write(history_path, snapshot)
            atomic_write(latest_path, snapshot)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
