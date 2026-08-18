#!/usr/bin/env python3
"""Recompute heartbeat transition release predicates without advancing the carrier."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRANSITION_REL = Path("receipts/heartbeat-transition-continuity/latest.json")
LEGACY_REL = Path("control/heartbeat-state.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
WORKER_REL = Path("control/worker-runtime-state.json")
CONTROL_REL = Path("control/worker-control-plane-coordination.json")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def active_leases(control_plane: dict[str, Any]) -> list[dict[str, Any]]:
    rows = ((control_plane.get("worker_coordination") or {}).get("active_leases") or [])
    return [row for row in rows if isinstance(row, dict)]


def no_duplicate_claim_or_fence(control_plane: dict[str, Any]) -> bool:
    rows = active_leases(control_plane)
    claims = [row.get("claim_id") for row in rows if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in rows if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in rows if row.get("worker_instance_id")]
    return len(claims) == len(set(claims)) and len(fences) == len(set(fences)) and len(instances) == len(set(instances))


def refresh(root: Path) -> dict[str, Any]:
    root = root.resolve()
    transition_path = root / TRANSITION_REL
    transition = load(transition_path)
    legacy = load(root / LEGACY_REL)
    carrier = load(root / CARRIER_REL)
    worker = load(root / WORKER_REL) if (root / WORKER_REL).is_file() else {}
    control = load(root / CONTROL_REL) if (root / CONTROL_REL).is_file() else {}

    target = transition.get("carrier_epoch_after")
    carrier_epoch = carrier.get("epoch")
    worker_epoch = worker.get("last_observed_carrier_epoch")
    target_valid = isinstance(target, int) and target >= 30
    worker_observed = isinstance(worker_epoch, int) and target_valid and worker_epoch >= target
    predicates = {
        "legacy_hb29_unchanged": int(legacy.get("epoch", -1)) == 29 and int(legacy.get("generation", -1)) == 29,
        "carrier_epoch_at_least_30": target_valid and isinstance(carrier_epoch, int) and carrier_epoch >= target,
        "carrier_generation_non_regressing": isinstance(carrier.get("generation"), int) and carrier.get("generation") >= int(transition.get("carrier_generation_before", 29)),
        "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": worker_observed,
        "worker_control_plane_observed": control.get("schema") == "stegverse.worker-control-plane-coordination/v1",
        "no_duplicate_claim_or_fence": bool(control) and no_duplicate_claim_or_fence(control),
        "state_reconstruction_pass": target_valid and worker_observed and int(legacy.get("epoch", -1)) == 29 and isinstance(carrier_epoch, int) and carrier_epoch >= target,
    }
    transition["predicates"] = predicates
    transition["all_carrier_transition_predicates_pass"] = all(
        predicates[name] for name in (
            "legacy_hb29_unchanged",
            "carrier_epoch_at_least_30",
            "carrier_generation_non_regressing",
            "worker_control_plane_observed",
            "no_duplicate_claim_or_fence",
        )
    )
    transition["all_release_predicates_pass"] = all(predicates.values())
    transition["release_state"] = "RELEASE_COMPLETE" if transition["all_release_predicates_pass"] else "WORKER_CHECKPOINT_PENDING"
    atomic_write(transition_path, transition)
    return transition


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = refresh(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("all_release_predicates_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
