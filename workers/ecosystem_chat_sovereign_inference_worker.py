#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECEIPT_ROOT = (ROOT / "receipts" / "ecosystem-chat-sovereign-inference").resolve()
LOCAL_PROOF_RECEIPT = RECEIPT_ROOT / "sovereign_local_model_proof.generated.json"
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
CANDIDATE_EVIDENCE = [
    Path("/var/lib/stegverse/ecosystem-chat/activation.latest.json"),
    Path.home() / ".stegverse" / "ecosystem-chat" / "activation.latest.json",
    ROOT / "runtime" / "sovereign" / "ecosystem-chat-activation.latest.json",
]
LOCAL_MODEL_PROOF_CANDIDATES = [
    Path("/var/lib/stegverse/models/sovereign_local_model_proof.generated.json"),
    Path.home() / ".stegverse" / "models" / "sovereign_local_model_proof.generated.json",
    ROOT / "runtime" / "sovereign" / "sovereign_local_model_proof.generated.json",
    LOCAL_PROOF_RECEIPT,
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


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment() -> bool:
    return any(truthy(os.environ.get(name)) for name in THIRD_PARTY_ENV_VARS)


def local_runtime_roots() -> list[Path]:
    roots: list[Path] = []
    override = os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT")
    if override:
        roots.append(Path(override).expanduser().resolve())
    roots.extend(
        [
            ROOT / "workloads" / "micro-node-runtime",
            Path.home() / ".stegverse" / "workloads" / "micro-node-runtime",
            Path("/var/lib/stegverse/workloads/micro-node-runtime"),
        ]
    )
    return roots


def find_micro_node_root() -> Path | None:
    required = (
        Path("tools/verify_sovereign_model_runtime.py"),
        Path("tools/run_sovereign_model.py"),
        Path("micro_node/local_model_runtime.py"),
        Path("models/stegverse_reference_language_model.v1.json"),
        Path("models/stegverse_reference_corpus.v1.txt"),
    )
    for root in local_runtime_roots():
        if all((root / relative).is_file() for relative in required):
            return root.resolve()
    return None


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


def run_reference_model_verifier(root: Path) -> dict:
    verifier = root / "tools" / "verify_sovereign_model_runtime.py"
    if not verifier.is_file():
        return {
            "attempted": False,
            "state": "BLOCKED",
            "reason": "CANONICAL_LOCAL_MODEL_VERIFIER_NOT_INSTALLED",
            "runtime_root": str(root),
        }
    process = subprocess.run(
        [sys.executable, str(verifier)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        env={**os.environ, "PYTHONPATH": str(root)},
    )
    proof: dict | None = None
    if process.returncode == 0:
        try:
            candidate = json.loads(process.stdout)
        except Exception:
            candidate = None
        if isinstance(candidate, dict):
            proof = candidate
    verified = reference_model_proof_verified(proof)
    if verified and proof is not None:
        atomic_write(LOCAL_PROOF_RECEIPT, proof)
    return {
        "attempted": True,
        "state": "COMPLETE" if verified else "FAILED",
        "reason": "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED" if verified else "LOCAL_MODEL_RUNTIME_PROOF_FAILED",
        "returncode": process.returncode,
        "runtime_root": str(root),
        "proof_path": str(LOCAL_PROOF_RECEIPT) if verified else None,
        "proof": proof if verified else None,
        "stdout_tail": process.stdout[-1000:] if not verified else None,
        "stderr_tail": process.stderr[-1000:] if process.stderr else None,
        "github_token_required": False,
        "third_party_execution_platform_required": False,
    }


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
    runtime_root = find_micro_node_root()
    launch_result: dict | None = None

    if not reference_ready and not third_party_hosted_environment() and runtime_root is not None:
        launch_result = run_reference_model_verifier(runtime_root)
        candidate = launch_result.get("proof") if isinstance(launch_result, dict) else None
        if reference_model_proof_verified(candidate):
            model_proof = candidate
            model_proof_path = LOCAL_PROOF_RECEIPT
            reference_ready = True

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
        next_transition = "TVC_LOCAL_MODEL_ROUTE_ADMISSION"
        next_action = (
            "Submit the verified node-local runtime proof to TVC sovereign-local route evaluation, require ROUTE_ADMITTED with "
            "credential_requirement=NONE, then consume exactly that private endpoint through StegVerseLocalHTTPProviderClient, "
            "execute governed E1-to-worker-to-E2, persist measured usage, and obtain same-execution Master Records reconstruction."
        )
        blocker = None
    elif third_party_hosted_environment():
        state = "BLOCKED"
        transition = "SOVEREIGN_LOCAL_MODEL_RUNTIME_AWAITS_STEGVERSE_CARRIER"
        next_transition = "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED"
        next_action = (
            "Execute the already-installed heartbeat worker on the StegVerse-owned/federated carrier. Hosted runners are validation-only "
            "and may not launch or authorize production local-model execution."
        )
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "Current invocation is on a hosted validation surface; production model launch is reserved to the StegVerse carrier.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": next_action,
            "machine_observable_release_condition": "the same heartbeat worker executes on the StegVerse carrier and emits SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED",
            "github_token_required": False,
            "third_party_blocker": False,
        }
    elif runtime_root is None:
        state = "BLOCKED"
        transition = "SOVEREIGN_LOCAL_MODEL_CAPSULE_NOT_MATERIALIZED"
        next_transition = "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED"
        next_action = (
            "Materialize the already-built StegVerse-002/micro-node-runtime capsule into a canonical local workload path, then let this "
            "heartbeat worker discover it and launch the verifier automatically. No model selection, source checkout, GitHub token, or hosted provider is required."
        )
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "The canonical micro-node runtime capsule is not present at a StegVerse-local workload path.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": next_action,
            "machine_observable_release_condition": "find_micro_node_root resolves the canonical capsule and run_reference_model_verifier emits a verified local runtime proof",
            "github_token_required": False,
            "third_party_blocker": False,
        }
    else:
        state = "BLOCKED"
        transition = "SOVEREIGN_LOCAL_MODEL_RUNTIME_PROOF_FAILED"
        next_transition = "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED"
        next_action = "Repair the locally materialized canonical runtime or verifier and re-execute on the next heartbeat cycle."
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "The canonical local runtime was found but its real launch/inference proof did not pass.",
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": next_action,
            "machine_observable_release_condition": "run_reference_model_verifier emits state COMPLETE and a verified proof",
            "github_token_required": False,
            "third_party_blocker": False,
        }

    receipt = {
        "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.4",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "local_model_proof_path": str(model_proof_path) if model_proof_path else None,
        "local_model_runtime_root": str(runtime_root) if runtime_root else None,
        "local_model_launch_result": launch_result,
        "reference_model_runtime_verified": reference_ready,
        "reference_model_is_production_scale_llm": False,
        "missing_predicates": missing,
        "next_authorized_action": next_action,
        "third_party_inference_required": False,
        "github_token_required": False,
        "github_models_required": False,
        "github_actions_production_role": False,
        "render_required": False,
        "cloudflare_required": False,
        "third_party_dependency_is_blocker": False,
        "tvc_route_authority_required": True,
        "credential_requirement": "NONE",
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
        "StegVerse-Labs/TVC:TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002",
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
        "cost_observation": {"hb_transition_count": 1, "compute_units": 2 if launch_result and launch_result.get("attempted") else 1, "external_cost_usd": 0, "task_class": "ecosystem_chat_sovereign_inference"},
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
