#!/usr/bin/env python3
"""Refresh the mutable heartbeat transition observation without coupling workers to heartbeat.

Heartbeat progression is oscillator-only at 10 ms / 100 Hz. WorkerCoordinator, task,
claim, fence, lease, G18, route, credential, and control-plane state are downstream
observations only and never participate in heartbeat progression or release predicates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from heartbeat_runtime.task_capable_observation import task_capable_worker_cycle_observed

ROOT = Path(__file__).resolve().parents[1]
TRANSITION_REL = Path("receipts/heartbeat-transition-continuity/latest.json")
LEGACY_REL = Path("control/heartbeat-state.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CUTOVER_REL = Path("receipts/heartbeat-schema-cutover/HB29.json")
WORKER_REL = Path("control/worker-runtime-state.json")
CONTROL_REL = Path("control/worker-control-plane-coordination.json")
CARRIER_SCHEMA = "stegverse.heartbeat-carrier-runtime-state/v1"
CUTOVER_SCHEMA = "stegverse.heartbeat-schema-cutover-receipt/v1"
CONTROL_SCHEMA = "stegverse.worker-control-plane-coordination/v1"
OSCILLATOR_RULE = "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
HISTORICAL_RULE = "GATE_PASSBAND_DERIVED"
HISTORICAL_MAX_EPOCH = 31


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


def _reference_frame(epoch: int) -> str:
    return f"heartbeat_epoch:{epoch}"


def _oscillator_predicates(carrier: dict[str, Any]) -> tuple[bool, bool]:
    oscillator = carrier.get("oscillator") or {}
    period_ok = (
        carrier.get("frequency_rule") == OSCILLATOR_RULE
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


def _historical_observation(carrier: dict[str, Any]) -> bool:
    epoch = carrier.get("epoch")
    return (
        carrier.get("frequency_rule") == HISTORICAL_RULE
        and isinstance(epoch, int)
        and epoch <= HISTORICAL_MAX_EPOCH
    )


def _downstream_runtime_observation(worker: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    observed_reference = control.get("observed_reference") or {}
    return {
        "causal_to_heartbeat": False,
        "heartbeat_progression_dependency": "NONE",
        "worker_observation_mode": worker.get("observation_mode"),
        "worker_last_observed_carrier_epoch": worker.get("last_observed_carrier_epoch"),
        "worker_last_observed_carrier_generation": worker.get("last_observed_carrier_generation"),
        "control_plane_schema_valid": control.get("schema") == CONTROL_SCHEMA,
        "control_plane_heartbeat_is_authority": observed_reference.get("heartbeat_is_authority"),
        "authority_effect": "NONE",
    }


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
    legacy_sha = sha256_bytes(legacy_raw)

    target_valid = (
        isinstance(target_epoch, int)
        and target_epoch >= 30
        and isinstance(target_generation, int)
        and target_generation >= 30
    )
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
    historical_observation = _historical_observation(carrier)

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

    predicates = {
        "legacy_hb29_unchanged": legacy_binding_ok,
        "carrier_epoch_non_regressing": carrier_non_regressing,
        "state_reconstruction_pass": reconstruction_ok,
        "oscillator_period_exactly_10ms": oscillator_period_ok,
        "carrier_reference_derived_from_oscillator": oscillator_derived_ok,
        "historical_pre_correction_snapshot_only": historical_observation,
        "worker_or_task_state_gates_progression": False,
        "observation_is_causal": False,
    }

    oscillator_live_observation = oscillator_period_ok and oscillator_derived_ok
    carrier_integrity = legacy_binding_ok and carrier_non_regressing and reconstruction_ok

    transition["continuity_model"] = "OSCILLATOR_REFERENCE_CONTINUITY"
    transition["heartbeat_progression_dependency"] = "OSCILLATOR_ONLY"
    transition["phase_travel_time_ms"] = 10
    transition["reference_frequency_hz"] = 100
    transition["worker_checkpoint_required"] = False
    transition["worker_checkpoint_is_heartbeat_predicate"] = False
    transition["predicates"] = predicates
    transition["all_carrier_transition_predicates_pass"] = carrier_integrity
    transition["all_release_predicates_pass"] = oscillator_live_observation and carrier_integrity
    transition["release_state"] = (
        "OSCILLATOR_OBSERVATION_VERIFIED"
        if transition["all_release_predicates_pass"]
        else "OSCILLATOR_LIVE_OBSERVATION_PENDING"
    )
    transition["historical_semantics"] = {
        "preserved_receipt_ref": "receipts/heartbeat-transition-continuity/HB31-pre-oscillator-semantic-reconciliation.json",
        "historical_worker_checkpoint_gating_superseded": True,
        "historical_gate_passband_frequency_semantics_superseded": True,
        "historical_snapshot_rewrite_performed": False,
    }
    transition["downstream_runtime_observation"] = _downstream_runtime_observation(worker, control)
    transition.pop("all_consumer_observation_predicates_pass", None)
    transition.pop("all_runtime_goal_predicates_pass", None)
    transition.pop("runtime_goal_release_state", None)
    transition.pop("worker_runtime_observation_mode", None)

    atomic_write(transition_path, transition)
    return transition


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = refresh(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
