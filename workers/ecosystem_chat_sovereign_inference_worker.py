#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECEIPT_ROOT = (ROOT / "receipts" / "ecosystem-chat-sovereign-inference").resolve()
CANDIDATE_EVIDENCE = [
    Path("/var/lib/stegverse/ecosystem-chat/activation.latest.json"),
    Path.home() / ".stegverse" / "ecosystem-chat" / "activation.latest.json",
    ROOT / "runtime" / "sovereign" / "ecosystem-chat-activation.latest.json",
]
REQUIRED_TRUE = [
    "real_model_process_observed",
    "private_endpoint_only",
    "ephemeral_e1_e2_execution_observed",
    "measured_usage_persisted",
    "provider_usage_reconstruction_pass",
    "transition_reconstruction_pass",
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
    for cap in ("runtime_observation", "durable_state_reconstruction", "bounded_repository_mutation"):
        if cap not in required_caps:
            return 5
    if "receipts/ecosystem-chat-sovereign-inference/**" not in set(execution.get("allowed_paths") or []):
        return 6

    evidence_path = next((p for p in CANDIDATE_EVIDENCE if p.exists()), None)
    evidence = None
    if evidence_path:
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except Exception:
            evidence = None
    passed = bool(evidence) and all(evidence.get(k) is True for k in REQUIRED_TRUE) and evidence.get("third_party_inference_required") is False
    missing = REQUIRED_TRUE if evidence is None else [k for k in REQUIRED_TRUE if evidence.get(k) is not True]
    if evidence is not None and evidence.get("third_party_inference_required") is not False:
        missing.append("third_party_inference_required=false")
    transition = "ECOSYSTEM_CHAT_SOVEREIGN_INFERENCE_VERIFIED" if passed else "SOVEREIGN_INFERENCE_SOLUTION_REQUIRED"
    blocker = None if passed else {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": "No admitted StegVerse-local inference execution has yet satisfied the real-model, private-endpoint, E1-to-E2, measured-usage, and reconstruction predicates.",
        "solution_required": True,
        "may_remain_blocked": True,
        "workaround_candidates": [
            "Start an eligible local model runtime on the sovereign carrier and bind the LLM adapter to loopback/private transport.",
            "Use another StegVerse-owned/federated node with a compatible local model process and preserve the same E1-to-E2 and Master Records reconstruction contract.",
            "If the selected local model cannot run on available hardware, select a smaller compatible local model rather than falling back to a hosted inference dependency."
        ],
        "next_solution_action": "Select an executable StegVerse-local model/runtime combination and activate it; model/provider unavailability requires an alternate local solution, not waiting on a third party."
    }
    receipt = {
        "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.2",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "missing_predicates": missing,
        "third_party_inference_required": False,
        "github_models_required": False,
        "render_required": False,
        "cloudflare_required": False,
        "third_party_dependency_is_blocker": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "authority_effect": "none_beyond_admitted_receipt_namespace",
        "completed": passed
    }
    atomic_write(RECEIPT_ROOT / f"{EXPECTED_TASK}.json", receipt)
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if passed else "BLOCKED",
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if passed else "SOVEREIGN_INFERENCE_SOLUTION_EXECUTION",
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": f"receipts/ecosystem-chat-sovereign-inference/{EXPECTED_TASK}.json",
        "evidence_refs": ["StegVerse-org/LLM-adapter#18", "StegVerse-Labs/.github#60", f"receipts/ecosystem-chat-sovereign-inference/{EXPECTED_TASK}.json", "control/blocker-resolution-policy.json"],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "ecosystem_chat_sovereign_inference"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
