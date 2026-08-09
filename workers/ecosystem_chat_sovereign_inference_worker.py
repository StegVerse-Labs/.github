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
LOCAL_MODEL_PROOF_CANDIDATES = [
    Path("/var/lib/stegverse/models/sovereign_local_model_proof.generated.json"),
    Path.home() / ".stegverse" / "models" / "sovereign_local_model_proof.generated.json",
    ROOT / "runtime" / "sovereign" / "sovereign_local_model_proof.generated.json",
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


def load_first_json(paths: list[Path]) -> tuple[Path | None, dict | None]:
    for path in paths:
        if not path.exists():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(value, dict):
            return path, value
    return None, None


def reference_model_proof_verified(proof: dict | None) -> bool:
    if not isinstance(proof, dict):
        return False
    predicates = proof.get("predicates") or {}
    return (
        proof.get("schema") == "stegverse.sovereign-local-model-proof/v1"
        and proof.get("state") == "VERIFIED_REFERENCE_MODEL_RUNTIME"
        and proof.get("authority_effect") == "NONE"
        and proof.get("qualifies_as_large_production_llm") is False
        and predicates.get("real_model_process_observed") is True
        and predicates.get("private_endpoint_only") is True
        and predicates.get("real_inference_response_observed") is True
        and predicates.get("measured_usage_persistable") is True
        and predicates.get("local_training_observed") is True
        and predicates.get("third_party_inference_required") is False
        and predicates.get("model_output_grants_authority") is False
    )


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

    evidence_path, evidence = load_first_json(CANDIDATE_EVIDENCE)
    model_proof_path, model_proof = load_first_json(LOCAL_MODEL_PROOF_CANDIDATES)
    reference_ready = reference_model_proof_verified(model_proof)

    passed = bool(evidence) and all(evidence.get(k) is True for k in REQUIRED_TRUE) and evidence.get("third_party_inference_required") is False
    missing = REQUIRED_TRUE if evidence is None else [k for k in REQUIRED_TRUE if evidence.get(k) is not True]
    if evidence is not None and evidence.get("third_party_inference_required") is not False:
        missing.append("third_party_inference_required=false")

    if passed:
        state = "COMPLETED"
        transition = "ECOSYSTEM_CHAT_SOVEREIGN_INFERENCE_VERIFIED"
        next_transition = None
        next_action = None
        blocker = None
    elif reference_ready:
        state = "ACTIVE"
        transition = "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED"
        next_transition = "LLM_ADAPTER_LOCAL_MODEL_BINDING_EXECUTION"
        next_action = (
            "Bind the verified private local model runtime to StegVerseLocalHTTPProviderClient, execute the governed "
            "E1-to-worker-to-E2 request, persist measured usage, and submit same-execution provider-usage and transition "
            "evidence to Master Records. The reference model proves the local execution path but is not a production-scale LLM."
        )
        blocker = None
    else:
        state = "BLOCKED"
        transition = "SOVEREIGN_LOCAL_MODEL_RUNTIME_NOT_YET_VERIFIED"
        next_transition = "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED"
        next_action = (
            "Execute StegVerse-002/micro-node-runtime#22 tools/verify_sovereign_model_runtime.py on the sovereign carrier. "
            "The in-repository stegverse-reference-lm-v1 is the guaranteed zero-external-dependency path; optional llama.cpp/Ollama "
            "models may improve capability but their absence is not a blocker."
        )
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "The sovereign carrier has not yet emitted an admitted local-model runtime proof from the implemented StegVerse reference model path.",
            "solution_required": True,
            "may_remain_blocked": True,
            "workaround_candidates": [
                "Execute the in-repository stegverse-reference-lm-v1 verifier on the sovereign node.",
                "If a qualifying local llama.cpp/GGUF runtime is already installed, execute it privately and preserve the same proof contract.",
                "If a qualifying Ollama model is already installed, execute it privately and preserve the same proof contract."
            ],
            "next_solution_action": next_action,
        }

    receipt = {
        "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.3",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "local_model_proof_path": str(model_proof_path) if model_proof_path else None,
        "reference_model_runtime_verified": reference_ready,
        "reference_model_is_production_scale_llm": False,
        "missing_predicates": missing,
        "next_authorized_action": next_action,
        "third_party_inference_required": False,
        "github_models_required": False,
        "render_required": False,
        "cloudflare_required": False,
        "third_party_dependency_is_blocker": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "authority_effect": "none_beyond_admitted_receipt_namespace",
        "completed": passed,
    }
    atomic_write(RECEIPT_ROOT / f"{EXPECTED_TASK}.json", receipt)
    evidence_refs = [
        "StegVerse-org/LLM-adapter#18",
        "StegVerse-Labs/.github#60",
        "StegVerse-002/micro-node-runtime#22",
        f"receipts/ecosystem-chat-sovereign-inference/{EXPECTED_TASK}.json",
        "control/blocker-resolution-policy.json",
    ]
    if model_proof_path:
        evidence_refs.append(str(model_proof_path))
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 2 if reference_ready and not passed else (3 if passed else 1),
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": f"receipts/ecosystem-chat-sovereign-inference/{EXPECTED_TASK}.json",
        "evidence_refs": evidence_refs,
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "ecosystem_chat_sovereign_inference"},
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
