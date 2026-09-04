#!/usr/bin/env python3
"""Fail-closed source validation for canonical-work runtime integration."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "control" / "canonical-work-runtime-profile.json"
CARRIER = ROOT / "control" / "canonical-resident-carrier-contract.json"
POLICY = ROOT / "data" / "task-coordination-policy.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
WORKERS = ROOT / "control" / "worker-registry.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL_CLOSED: {reason}")


def main() -> int:
    profile = load(PROFILE)
    carrier = load(CARRIER)
    policy = load(POLICY)
    registry = load(REGISTRY)
    workers = load(WORKERS)

    require(profile.get("schema") == "stegverse.canonical-work-runtime-profile/v1", "profile schema")
    hb = profile.get("heartbeat", {})
    canonical_hb = carrier.get("heartbeat", {})
    for key in ("protocol_anchor", "mechanism", "reference_frequency_hz", "reference_increment_interval_ms", "progression_dependency"):
        require(hb.get(key) == canonical_hb.get(key), f"heartbeat drift:{key}")
    require(hb.get("protocol_anchor") == "HB32", "HB32 required")
    require(hb.get("mechanism") == "INDEPENDENT_PHASE_OSCILLATOR", "independent oscillator required")
    require(hb.get("progression_dependency") == "OSCILLATOR_ONLY", "OSCILLATOR_ONLY required")
    for key in ("carrier_grants_admission_authority", "carrier_grants_execution_authority", "carrier_grants_claim_or_fence_authority", "carrier_grants_transition_authority"):
        require(hb.get(key) is False, f"{key} must be false")

    runtime = profile.get("worker_runtime", {})
    require(runtime.get("single_scheduler_required") is True, "single scheduler required")
    require(runtime.get("second_scheduler_allowed") is False, "second scheduler forbidden")
    require(runtime.get("second_worker_runtime_allowed") is False, "second WorkerCoordinator forbidden")
    require(runtime.get("claim_fence_projection_only_in_task_registry") is True, "claim/fence must remain projection-only")

    truth = policy.get("canonical_truth", {})
    require(truth.get("execution_claim_and_fence") == "WORKERCOORDINATOR", "WorkerCoordinator authority drift")
    require(truth.get("observed_reality_and_reconstruction") == "MASTER_RECORDS", "Master Records authority drift")
    require(truth.get("governed_ingress_egress") == "INTERLOCK_INTR", "Interlock/InTr authority drift")
    require(registry.get("authoritative_roles", {}).get("execution_claim_and_fence") == "control/worker-registry.json / WorkerCoordinator", "registry claim authority drift")
    require(workers.get("schema") == "stegverse.heartbeat-worker-registry/v0.1", "worker registry schema drift")

    print("PASS: canonical work runtime source profile respects HB32 independent oscillator and authority separation")
    print("NONCLAIM: source validation does not prove authentic resident execution, ingress, claim/fence, Master Records reconciliation, or egress")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
