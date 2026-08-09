#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-DURABLE-RUNTIME-ACTIVATION"
RECEIPT_ROOT = (ROOT / "receipts" / "sovereign-runtime-activation").resolve()
CANDIDATE_EVIDENCE = [
    Path("/var/lib/stegverse/heartbeat/activation.latest.json"),
    Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json",
    ROOT / "runtime" / "sovereign" / "activation.latest.json",
]
REQUIRED_PREDICATES = [
    "runtime_materialized",
    "native_service_active",
    "continuous_runtime_live",
    "heartbeat_epoch_advanced",
    "worker_coordination_checkpoint_observed",
    "controlled_restart_observed",
    "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
]


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 4
    execution = handoff.get("execution") or {}
    required_caps = set(execution.get("required_capabilities") or [])
    for cap in ("runtime_observation", "continuous_process_execution", "durable_state_reconstruction", "bounded_repository_mutation"):
        if cap not in required_caps:
            return 5
    if "receipts/sovereign-runtime-activation/**" not in set(execution.get("allowed_paths") or []):
        return 6

    evidence_path = next((p for p in CANDIDATE_EVIDENCE if p.exists()), None)
    evidence = None
    if evidence_path is not None:
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except Exception:
            evidence = None

    passed = bool(evidence) and all(evidence.get(name) is True for name in REQUIRED_PREDICATES)
    missing = REQUIRED_PREDICATES if evidence is None else [name for name in REQUIRED_PREDICATES if evidence.get(name) is not True]
    transition = "SOVEREIGN_RUNTIME_VERIFIED" if passed else "SOVEREIGN_RUNTIME_SOLUTION_REQUIRED"
    blocker = None if passed else {
        "dependency_class": "PHYSICAL_RESOURCE",
        "problem_statement": "No StegVerse-owned/federated node has yet emitted evidence satisfying the sovereign runtime activation predicates.",
        "solution_required": True,
        "may_remain_blocked": True,
        "workaround_candidates": [
            "Install and start the canonical heartbeat service on any eligible StegVerse-owned/federated Linux node using scripts/install_sovereign_heartbeat_service.py.",
            "Materialize the sovereign runtime capsule on an alternate eligible StegVerse node and migrate the canonical durable state before service start.",
            "Use an existing StegVerse-002 micro-node as the carrier if it satisfies the same local-storage, restart, reconstruction, and no-split-brain predicates."
        ],
        "next_solution_action": "Select an eligible StegVerse-owned/federated node and execute the native service installation/activation path; do not wait for a hosted provider."
    }
    receipt = {
        "schema": "stegverse.sovereign-runtime-worker-receipt/v0.2",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "required_predicates": REQUIRED_PREDICATES,
        "missing_predicates": missing,
        "third_party_runtime_required": False,
        "third_party_dependency_is_blocker": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "authority_effect": "none_beyond_admitted_receipt_namespace",
        "completed": passed,
    }
    receipt_path = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if passed else "BLOCKED",
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if passed else "SOVEREIGN_RUNTIME_SOLUTION_EXECUTION",
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
        "evidence_refs": [f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json", "StegVerse-Labs/.github#12", "StegVerse-Labs/.github#59", "control/blocker-resolution-policy.json"],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "sovereign_runtime_activation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
