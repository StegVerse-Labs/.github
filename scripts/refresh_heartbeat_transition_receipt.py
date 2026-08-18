#!/usr/bin/env python3
"""Recompute heartbeat transition release predicates without advancing the carrier.

This verifier is deliberately fail-closed.  A release refresh must prove the
immutable HB29 bytes, the cutover/carrier lineage, the current carrier/control-
plane alignment, and worker observation.  Merely seeing epoch/generation fields
with plausible values is not sufficient.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRANSITION_REL = Path("receipts/heartbeat-transition-continuity/latest.json")
LEGACY_REL = Path("control/heartbeat-state.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CUTOVER_REL = Path("receipts/heartbeat-schema-cutover/HB29.json")
WORKER_REL = Path("control/worker-runtime-state.json")
CONTROL_REL = Path("control/worker-control-plane-coordination.json")
CARRIER_SCHEMA = "stegverse.heartbeat-carrier-runtime-state/v1"
CONTROL_SCHEMA = "stegverse.worker-control-plane-coordination/v1"
CUTOVER_SCHEMA = "stegverse.heartbeat-schema-cutover-receipt/v1"


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


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(raw)


def active_leases(control_plane: dict[str, Any]) -> list[dict[str, Any]]:
    rows = ((control_plane.get("worker_coordination") or {}).get("active_leases") or [])
    return [row for row in rows if isinstance(row, dict)]


def no_duplicate_claim_or_fence(control_plane: dict[str, Any]) -> bool:
    rows = active_leases(control_plane)
    claims = [row.get("claim_id") for row in rows if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in rows if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in rows if row.get("worker_instance_id")]
    return (
        len(claims) == len(set(claims))
        and len(fences) == len(set(fences))
        and len(instances) == len(set(instances))
    )


def _reference_frame(epoch: int) -> str:
    return f"heartbeat_epoch:{epoch}"


def refresh(root: Path) -> dict[str, Any]:
    root = root.resolve()
    transition_path = root / TRANSITION_REL
    legacy_path = root / LEGACY_REL
    carrier_path = root / CARRIER_REL
    cutover_path = root / CUTOVER_REL

    transition = load(transition_path)
    legacy_raw = legacy_path.read_bytes()
    legacy = json.loads(legacy_raw.decode("utf-8"))
    if not isinstance(legacy, dict):
        raise RuntimeError("legacy heartbeat must be a JSON object")
    carrier = load(carrier_path)
    cutover = load(cutover_path)
    worker = load(root / WORKER_REL) if (root / WORKER_REL).is_file() else {}
    control = load(root / CONTROL_REL) if (root / CONTROL_REL).is_file() else {}

    target_epoch = transition.get("carrier_epoch_after")
    target_generation = transition.get("carrier_generation_after")
    carrier_epoch = carrier.get("epoch")
    carrier_generation = carrier.get("generation")
    worker_epoch = worker.get("last_observed_carrier_epoch")
    worker_generation = worker.get("last_observed_carrier_generation")
    legacy_sha = sha256_bytes(legacy_raw)

    target_valid = (
        isinstance(target_epoch, int)
        and target_epoch >= 30
        and isinstance(target_generation, int)
        and target_generation >= 30
    )
    carrier_valid = (
        carrier.get("schema") == CARRIER_SCHEMA
        and isinstance(carrier_epoch, int)
        and isinstance(carrier_generation, int)
        and target_valid
        and carrier_epoch >= target_epoch
        and carrier_generation >= target_generation
        and carrier.get("reference_frame") == _reference_frame(carrier_epoch)
        and carrier.get("authority_effect") == "NONE"
    )

    expected_legacy_sha = transition.get("legacy_state_sha256")
    carrier_cutover = carrier.get("legacy_cutover") or {}
    legacy_binding_ok = (
        legacy.get("schema") == "stegverse.org-heartbeat-state/v1"
        and int(legacy.get("epoch", -1)) == 29
        and int(legacy.get("generation", -1)) == 29
        and isinstance(expected_legacy_sha, str)
        and legacy_sha == expected_legacy_sha
        and carrier_cutover.get("legacy_state_sha256") == legacy_sha
        and carrier_cutover.get("legacy_epoch") == 29
        and carrier_cutover.get("legacy_generation") == 29
        and carrier_cutover.get("source_ref") == str(LEGACY_REL)
        and carrier_cutover.get("closed") is True
    )

    cutover_binding_ok = (
        cutover.get("schema") == CUTOVER_SCHEMA
        and cutover.get("state") == "CLOSED_MIGRATED"
        and cutover.get("legacy_epoch") == 29
        and cutover.get("legacy_state_ref") == str(LEGACY_REL)
        and cutover.get("legacy_state_sha256") == legacy_sha
        and cutover.get("legacy_state_mutated") is False
        and cutover.get("new_carrier_schema") == CARRIER_SCHEMA
        and cutover.get("new_carrier_state_ref") == str(CARRIER_REL)
        and cutover.get("first_new_epoch") == 30
        and isinstance(cutover.get("observed_new_epoch"), int)
        and cutover.get("observed_new_epoch") >= 30
    )

    # While the carrier is still the first materialized successor, prove the
    # exact canonical carrier object bound into the cutover receipt.  Once a
    # later carrier epoch legitimately exists, lineage is instead proven by the
    # immutable legacy binding retained inside the current carrier plus the
    # closed cutover receipt.
    initial_carrier_digest_ok = True
    if carrier_valid and carrier_epoch == target_epoch == cutover.get("observed_new_epoch"):
        expected_carrier_digest = cutover.get("new_carrier_state_sha256")
        initial_carrier_digest_ok = (
            isinstance(expected_carrier_digest, str)
            and canonical_sha256(carrier) == expected_carrier_digest
        )

    observed_reference = control.get("observed_reference") or {}
    control_aligned = (
        control.get("schema") == CONTROL_SCHEMA
        and carrier_valid
        and observed_reference.get("carrier_generation") == carrier_generation
        and observed_reference.get("reference_frame") == carrier.get("reference_frame")
        and observed_reference.get("heartbeat_is_authority") is False
    )

    worker_observed = (
        target_valid
        and isinstance(worker_epoch, int)
        and isinstance(worker_generation, int)
        and worker_epoch >= target_epoch
        and worker_generation >= target_generation
    )

    reconstruction_ok = (
        target_valid
        and carrier_valid
        and legacy_binding_ok
        and cutover_binding_ok
        and initial_carrier_digest_ok
        and transition.get("legacy_state_ref") == str(LEGACY_REL)
        and transition.get("carrier_state_ref") == str(CARRIER_REL)
    )

    predicates = {
        "legacy_hb29_unchanged": legacy_binding_ok,
        "carrier_epoch_at_least_30": carrier_valid,
        "carrier_generation_non_regressing": carrier_valid,
        "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": worker_observed,
        "worker_control_plane_observed": control_aligned,
        "no_duplicate_claim_or_fence": bool(control) and no_duplicate_claim_or_fence(control),
        "state_reconstruction_pass": reconstruction_ok,
    }
    transition["predicates"] = predicates
    transition["all_carrier_transition_predicates_pass"] = all(
        predicates[name]
        for name in (
            "legacy_hb29_unchanged",
            "carrier_epoch_at_least_30",
            "carrier_generation_non_regressing",
            "worker_control_plane_observed",
            "no_duplicate_claim_or_fence",
            "state_reconstruction_pass",
        )
    )
    transition["all_release_predicates_pass"] = all(predicates.values())
    if transition["all_release_predicates_pass"]:
        transition["release_state"] = "RELEASE_COMPLETE"
    elif transition["all_carrier_transition_predicates_pass"]:
        transition["release_state"] = "WORKER_CHECKPOINT_PENDING"
    else:
        transition["release_state"] = "FAIL_CLOSED_INTEGRITY"
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
