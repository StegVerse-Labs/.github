#!/usr/bin/env python3
"""Recompute heartbeat carrier and downstream runtime-goal predicates.

Heartbeat progression is oscillator-only. WorkerCoordinator/G18 state is downstream
consumer/runtime-goal evidence and must never gate carrier existence or carrier
release. A task-capable WorkerCoordinator cycle remains mandatory for the G18
runtime goal, but is reported separately from carrier release.
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
WORKER_EVENTS_REL = Path("events/worker-runtime.jsonl")
CARRIER_SCHEMA = "stegverse.heartbeat-carrier-runtime-state/v1"
CONTROL_SCHEMA = "stegverse.worker-control-plane-coordination/v1"
CUTOVER_SCHEMA = "stegverse.heartbeat-schema-cutover-receipt/v1"
TASK_CAPABLE_MODE = "TASK_CAPABLE_WORKER_COORDINATOR"
OBSERVATION_ONLY_EVENT = "worker_carrier_reference_observed"


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
    return len(claims) == len(set(claims)) and len(fences) == len(set(fences)) and len(instances) == len(set(instances))


def _reference_frame(epoch: int) -> str:
    return f"heartbeat_epoch:{epoch}"


def task_capable_worker_cycle_observed(root: Path, worker: dict[str, Any], target_epoch: int) -> bool:
    """Require evidence from the real WorkerCoordinator, not the observer shim.

    Canonical WorkerCoordinator events use ``epoch``. ``carrier_epoch`` is
    accepted only for compatibility with older/specialized event producers.
    """
    if worker.get("observation_mode") == TASK_CAPABLE_MODE:
        return True
    events_path = root / WORKER_EVENTS_REL
    if not events_path.is_file():
        return False
    try:
        with events_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                epoch = event.get("epoch")
                if not isinstance(epoch, int):
                    epoch = event.get("carrier_epoch")
                event_type = event.get("event_type")
                if isinstance(epoch, int) and epoch >= target_epoch and isinstance(event_type, str) and event_type and event_type != OBSERVATION_ONLY_EVENT:
                    return True
    except OSError:
        return False
    return False


def _oscillator_predicates(carrier: dict[str, Any]) -> tuple[bool, bool]:
    oscillator = carrier.get("oscillator") or {}
    period_ok = (
        carrier.get("frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
        and oscillator.get("mechanism") == "INDEPENDENT_PHASE_OSCILLATOR"
        and oscillator.get("period_ns") == 10_000_000
        and oscillator.get("phase_travel_time_ms") == 10
        and oscillator.get("reference_increment_interval_ms") == 10
        and oscillator.get("reference_frequency_hz") == 100
    )
    derived_ok = (
        period_ok
        and oscillator.get("progression_dependency") == "OSCILLATOR_ONLY"
        and oscillator.get("downstream_gating") is False
        and oscillator.get("observation_is_causal") is False
        and oscillator.get("snapshot_is_observation_only") is True
        and oscillator.get("sampled_reference_epoch") == carrier.get("epoch")
    )
    return period_ok, derived_ok


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

    target_valid = isinstance(target_epoch, int) and target_epoch >= 30 and isinstance(target_generation, int) and target_generation >= 30
    carrier_non_regressing = (
        carrier.get("schema") == CARRIER_SCHEMA
        and isinstance(carrier_epoch, int)
        and isinstance(carrier_generation, int)
        and target_valid
        and carrier_epoch >= target_epoch
        and carrier_generation >= target_generation
        and carrier.get("reference_frame") == _reference_frame(carrier_epoch)
        and carrier.get("authority_effect") == "NONE"
    )
    oscillator_period_ok, oscillator_derived_ok = _oscillator_predicates(carrier)

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

    initial_carrier_digest_ok = True
    if carrier_non_regressing and carrier_epoch == target_epoch == cutover.get("observed_new_epoch"):
        expected_carrier_digest = cutover.get("new_carrier_state_sha256")
        initial_carrier_digest_ok = isinstance(expected_carrier_digest, str) and canonical_sha256(carrier) == expected_carrier_digest

    reconstruction_ok = (
        target_valid
        and carrier_non_regressing
        and legacy_binding_ok
        and cutover_binding_ok
        and initial_carrier_digest_ok
        and transition.get("legacy_state_ref") == str(LEGACY_REL)
        and transition.get("carrier_state_ref") == str(CARRIER_REL)
    )

    observed_reference = control.get("observed_reference") or {}
    control_aligned = (
        control.get("schema") == CONTROL_SCHEMA
        and observed_reference.get("heartbeat_is_authority") is False
        and isinstance(observed_reference.get("carrier_generation"), int)
    )
    worker_observed = (
        target_valid
        and isinstance(worker_epoch, int)
        and isinstance(worker_generation, int)
        and worker_epoch >= target_epoch
        and worker_generation >= target_generation
    )
    worker_task_capable = worker_observed and isinstance(target_epoch, int) and task_capable_worker_cycle_observed(root, worker, target_epoch)
    no_duplicates = bool(control) and no_duplicate_claim_or_fence(control)

    predicates = {
        "legacy_hb29_unchanged": legacy_binding_ok,
        "oscillator_period_exactly_10ms": oscillator_period_ok,
        "carrier_epoch_non_regressing": carrier_non_regressing,
        "carrier_reference_derived_from_oscillator": oscillator_derived_ok,
        "state_reconstruction_pass": reconstruction_ok,
        "worker_runtime_checkpoint_observed_reference_when_worker_runs": worker_observed,
        "worker_task_capable_cycle_observed": worker_task_capable,
        "worker_control_plane_observed_when_control_plane_runs": control_aligned,
        "no_duplicate_claim_or_fence": no_duplicates,
        "carrier_epoch_at_least_30": carrier_non_regressing,
        "carrier_generation_non_regressing": carrier_non_regressing,
        "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": worker_observed,
        "worker_control_plane_observed": control_aligned,
    }
    transition["predicates"] = predicates
    transition["worker_runtime_observation_mode"] = worker.get("observation_mode")

    carrier_names = (
        "legacy_hb29_unchanged",
        "oscillator_period_exactly_10ms",
        "carrier_epoch_non_regressing",
        "carrier_reference_derived_from_oscillator",
        "state_reconstruction_pass",
    )
    consumer_names = (
        "worker_runtime_checkpoint_observed_reference_when_worker_runs",
        "worker_control_plane_observed_when_control_plane_runs",
        "no_duplicate_claim_or_fence",
    )
    transition["all_carrier_transition_predicates_pass"] = all(predicates[name] for name in carrier_names)
    transition["all_consumer_observation_predicates_pass"] = all(predicates[name] for name in consumer_names)
    transition["all_runtime_goal_predicates_pass"] = transition["all_carrier_transition_predicates_pass"] and transition["all_consumer_observation_predicates_pass"] and worker_task_capable

    transition["all_release_predicates_pass"] = transition["all_carrier_transition_predicates_pass"]
    transition["release_state"] = "RELEASE_COMPLETE" if transition["all_carrier_transition_predicates_pass"] else "FAIL_CLOSED_CARRIER_INTEGRITY"

    if transition["all_runtime_goal_predicates_pass"]:
        transition["runtime_goal_release_state"] = "RELEASE_COMPLETE"
    elif transition["all_carrier_transition_predicates_pass"] and worker_observed:
        transition["runtime_goal_release_state"] = "WORKER_TASK_CAPABLE_CYCLE_PENDING"
    elif transition["all_carrier_transition_predicates_pass"]:
        transition["runtime_goal_release_state"] = "WORKER_CHECKPOINT_PENDING"
    else:
        transition["runtime_goal_release_state"] = "CARRIER_INTEGRITY_PENDING"

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
