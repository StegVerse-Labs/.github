#!/usr/bin/env python3
"""Compatibility command that samples the independent heartbeat oscillator.

This command does not advance, authorize, schedule, or gate the heartbeat.
The heartbeat progresses independently at a 10 ms phase-travel/reference
interval. This command merely persists the oscillator-derived reference visible
at sampling time and records downstream observation status separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.engine_v12 import HeartbeatRuntime  # noqa: E402
from heartbeat_runtime.independent_oscillator import FREQUENCY_RULE, OSCILLATOR_PERIOD_MS  # noqa: E402

LEGACY_REL = Path("control/heartbeat-state.json")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
CONTROL_PLANE_REL = Path("control/worker-control-plane-coordination.json")
WORKER_STATE_REL = Path("control/worker-runtime-state.json")
DEFAULT_RECEIPT_REL = Path("receipts/heartbeat-transition-continuity/latest.json")
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def active_leases(control_plane: dict[str, Any]) -> list[dict[str, Any]]:
    coordination = control_plane.get("worker_coordination") or {}
    rows = coordination.get("active_leases") or []
    return [row for row in rows if isinstance(row, dict)]


def no_duplicate_claim_or_fence(control_plane: dict[str, Any]) -> bool:
    rows = active_leases(control_plane)
    claims = [row.get("claim_id") for row in rows if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in rows if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in rows if row.get("worker_instance_id")]
    return len(claims) == len(set(claims)) and len(fences) == len(set(fences)) and len(instances) == len(set(instances))


def sample(root: Path, receipt_path: Path, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    receipt_path = receipt_path.expanduser().resolve()
    legacy_path = root / LEGACY_REL
    carrier_path = root / CARRIER_REL
    control_plane_path = root / CONTROL_PLANE_REL
    worker_state_path = root / WORKER_STATE_REL

    receipt: dict[str, Any] = {
        "schema": "stegverse.heartbeat-state-transition-receipt/v2",
        "contract_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "oscillator_period_ms": OSCILLATOR_PERIOD_MS,
        "frequency_rule": FREQUENCY_RULE,
        "progression_dependency": "OSCILLATOR_ONLY",
        "observation_is_causal": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_forwarded": False,
        "state": "FAIL_CLOSED",
        "release_state": "FAIL_CLOSED",
    }

    if hosted_environment(env):
        receipt["reason"] = "THIRD_PARTY_HOST_IS_NOT_PRIMARY_SOVEREIGN_CARRIER_EVIDENCE"
        atomic_write(receipt_path, receipt)
        return receipt
    if not legacy_path.is_file():
        receipt["reason"] = "LEGACY_HB29_PROVENANCE_MISSING"
        atomic_write(receipt_path, receipt)
        return receipt

    legacy_before = legacy_path.read_bytes()
    before_epoch = 29
    before_generation = 29
    if carrier_path.is_file():
        prior = load_json(carrier_path)
        before_epoch = int(prior.get("epoch", 29))
        before_generation = int(prior.get("generation", before_epoch))

    result = HeartbeatRuntime(root).cycle(write=True)
    if not carrier_path.is_file():
        receipt["reason"] = "OSCILLATOR_SAMPLE_NOT_YET_PAST_FIRST_10MS_REFERENCE"
        receipt["sample_result"] = result
        atomic_write(receipt_path, receipt)
        return receipt

    carrier = load_json(carrier_path)
    control_plane = load_json(control_plane_path) if control_plane_path.is_file() else {}
    worker_state = load_json(worker_state_path) if worker_state_path.is_file() else {}
    after_epoch = int(carrier.get("epoch", -1))
    after_generation = int(carrier.get("generation", -1))
    oscillator = carrier.get("oscillator") or {}
    legacy_after = legacy_path.read_bytes()

    carrier_predicates = {
        "legacy_hb29_unchanged": legacy_after == legacy_before and int(json.loads(legacy_after.decode("utf-8")).get("epoch", -1)) == 29,
        "oscillator_period_exactly_10ms": oscillator.get("period_ns") == 10_000_000 and oscillator.get("phase_travel_time_ms") == 10,
        "carrier_epoch_non_regressing": after_epoch >= before_epoch,
        "carrier_generation_non_regressing": after_generation >= before_generation,
        "carrier_reference_derived_from_oscillator": carrier.get("frequency_rule") == FREQUENCY_RULE and oscillator.get("progression_dependency") == "OSCILLATOR_ONLY" and oscillator.get("observation_is_causal") is False,
        "state_reconstruction_pass": carrier.get("reference_frame") == f"heartbeat_epoch:{after_epoch}" and oscillator.get("sampled_reference_epoch") == after_epoch,
    }
    observed_epoch = worker_state.get("last_observed_carrier_epoch")
    consumer_observation = {
        "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": isinstance(observed_epoch, int) and observed_epoch >= after_epoch,
        "worker_control_plane_observed": control_plane.get("schema") == "stegverse.worker-control-plane-coordination/v1",
        "no_duplicate_claim_or_fence": bool(control_plane) and no_duplicate_claim_or_fence(control_plane),
    }

    receipt.update({
        "legacy_state_sha256": sha256_bytes(legacy_before),
        "carrier_epoch_before_observation": before_epoch,
        "carrier_generation_before_observation": before_generation,
        "carrier_epoch_after": after_epoch,
        "carrier_generation_after": after_generation,
        "elapsed_heartbeat_references_since_prior_observation": max(0, after_epoch - before_epoch),
        "predicates": {**carrier_predicates, **consumer_observation},
        "carrier_predicates": carrier_predicates,
        "consumer_observation_predicates": consumer_observation,
        "all_carrier_transition_predicates_pass": all(carrier_predicates.values()),
        "all_release_predicates_pass": all(carrier_predicates.values()),
        "consumer_observation_complete": all(consumer_observation.values()),
        "state": "CARRIER_TRANSITION_COMPLETE" if all(carrier_predicates.values()) else "REVIEW_REQUIRED",
        "release_state": "RELEASE_COMPLETE" if all(carrier_predicates.values()) else "REVIEW_REQUIRED",
        "reason": "OSCILLATOR_REFERENCE_SAMPLED_AND_VERIFIED" if all(carrier_predicates.values()) else "OSCILLATOR_SAMPLE_INVARIANTS_INCOMPLETE",
        "heartbeat_progression_waited_for_worker": False,
        "heartbeat_progression_waited_for_task": False,
        "heartbeat_progression_waited_for_admission": False,
    })
    atomic_write(receipt_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt-path", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    receipt_path = (args.receipt_path or (root / DEFAULT_RECEIPT_REL)).expanduser().resolve()
    result = sample(root, receipt_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") == "CARRIER_TRANSITION_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
