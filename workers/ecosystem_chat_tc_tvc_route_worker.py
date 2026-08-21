#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path.cwd().resolve()
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from master_records_sovereign_reconstruction_bridge import (
    _start_conversational_runtime_after_pass,
    find_master_records_root,
    reconstruct_same_execution,
    reconstruction_receipt_verified,
)

UNDERLYING = WORKERS / "ecosystem_chat_sovereign_route_worker.py"
RECEIPT_ROOT = ROOT / "receipts" / "ecosystem-chat-sovereign-inference"
BASE_RECEIPT = RECEIPT_ROOT / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
ROUTE_RECEIPT = RECEIPT_ROOT / "tvc_local_model_route.json"
LLM_EXECUTION_RECEIPT = RECEIPT_ROOT / "llm_adapter_sovereign_execution.json"
MASTER_RECORDS_RECEIPT = RECEIPT_ROOT / "master_records_same_execution_reconstruction.json"
VA_RUNTIME_STATE = RECEIPT_ROOT / "va_conversational_runtime_process.json"
NORMALIZE_FILES = (BASE_RECEIPT, LLM_EXECUTION_RECEIPT, MASTER_RECORDS_RECEIPT)
LEGACY = "TC/TVC"
LEGACY_VALUES = {"StegVerse-Labs/TV+TVC", LEGACY}
CURRENT = "TV/TVC"


def sovereign_child_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if value in LEGACY_VALUES:
        return CURRENT
    return value


def normalize_blocker_contract(response: dict) -> dict:
    if response.get("state") != "BLOCKED":
        return response
    blocker = response.get("blocker")
    if not isinstance(blocker, dict):
        return response
    next_action = blocker.get("next_solution_action")
    if not isinstance(next_action, str) or not next_action.strip():
        candidate = response.get("next_authorized_action") or response.get("expected_next_transition")
        if isinstance(candidate, str) and candidate.strip():
            next_action = candidate.strip()
            blocker["next_solution_action"] = next_action
    candidates = blocker.get("workaround_candidates")
    if (not isinstance(candidates, list) or not any(isinstance(x, str) and x.strip() for x in candidates)) and isinstance(next_action, str) and next_action.strip():
        blocker["workaround_candidates"] = [next_action.strip()]
    blocker["github_token_required"] = False
    response["blocker"] = blocker
    response["github_token_required"] = False
    return response


def load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_file(path: Path) -> None:
    value = load_json(path)
    if value is None:
        return
    normalized = normalize(value)
    if normalized != value:
        write_json(path, normalized)


def blocked(response: dict, transition: str, problem: str, release: str, *, expected: str = "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION") -> dict:
    response.update(
        {
            "state": "BLOCKED",
            "transition_id": transition,
            "expected_next_transition": expected,
            "blocker": {
                "dependency_class": "INTERNAL_CAPABILITY",
                "problem_statement": problem,
                "solution_required": True,
                "may_remain_blocked": False,
                "workaround_candidates": [release],
                "next_solution_action": release,
                "machine_observable_release_condition": release,
                "github_token_required": False,
                "third_party_blocker": False,
            },
            "credential_authority_model": CURRENT,
            "github_token_required": False,
        }
    )
    return response


def _runtime_result_ready(result: dict | None) -> bool:
    if not isinstance(result, dict) or result.get("state") != "COMPLETE":
        return False
    runtime = result.get("runtime_state")
    return isinstance(runtime, dict) and runtime.get("state") == "LIVE_VERIFIED" and runtime.get("github_token_required") is False


def apply_master_records_reconstruction(response: dict) -> dict:
    if response.get("transition_id") not in {"LLM_ADAPTER_SAME_ENDPOINT_EXECUTED", "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED", "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED"}:
        return response

    base = load_json(BASE_RECEIPT)
    route = load_json(ROUTE_RECEIPT)
    execution = load_json(LLM_EXECUTION_RECEIPT)
    if not all(isinstance(value, dict) for value in (base, route, execution)):
        return blocked(response, "MASTER_RECORDS_RECONSTRUCTION_INPUT_INCOMPLETE", "Same-execution reconstruction requires the exact local-model proof, TVC route receipt, and LLM-adapter execution receipt.", "the canonical receipt namespace contains the exact proof path, TVC route receipt, and LLM-adapter execution receipt")

    proof_path_raw = base.get("local_model_proof_path")
    proof_path = Path(proof_path_raw).resolve() if isinstance(proof_path_raw, str) else None
    proof = load_json(proof_path) if proof_path is not None else None
    if not isinstance(proof, dict):
        return blocked(response, "MASTER_RECORDS_RUNTIME_PROOF_MISSING", "The exact local-model runtime proof used for the admitted route is unavailable.", "the base receipt resolves an existing canonical runtime proof")

    existing = load_json(MASTER_RECORDS_RECEIPT)
    if reconstruction_receipt_verified(existing, proof=proof, route=route, execution=execution):
        reconstruction = existing
        runtime_result = _start_conversational_runtime_after_pass(proof=proof, route=route, output_path=MASTER_RECORDS_RECEIPT)
        result = {
            "attempted": False,
            "state": "COMPLETE" if _runtime_result_ready(runtime_result) else "RECONSTRUCTED_RUNTIME_PENDING",
            "reason": "REUSED_VERIFIED_MASTER_RECORDS_RECONSTRUCTION",
            "reconstruction_receipt": existing,
            "reconstruction_receipt_path": str(MASTER_RECORDS_RECEIPT),
            "va_conversational_runtime": runtime_result,
            "credential_authority": CURRENT,
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
            "authority_effect": "NONE",
        }
    else:
        master_records_root = find_master_records_root(ROOT)
        if master_records_root is None:
            return blocked(response, "MASTER_RECORDS_LOCAL_CAPSULE_NOT_MATERIALIZED", "The released Master Records sovereign reconstruction verifier is not materialized on the StegVerse carrier.", "find_master_records_root resolves the released reconstruction script, task, and scoped handoff locally")
        result = reconstruct_same_execution(master_records_root, proof=proof, route=route, execution=execution, output_path=MASTER_RECORDS_RECEIPT)
        reconstruction = result.get("reconstruction_receipt") if isinstance(result, dict) else None
        runtime_result = result.get("va_conversational_runtime") if isinstance(result, dict) else None

    if not reconstruction_receipt_verified(reconstruction, proof=proof, route=route, execution=execution):
        return blocked(response, "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_FAILED", "Canonical Master Records did not reconstruct the exact same sovereign execution with provider usage and transition continuity PASS.", "the released verifier emits PASS with provider_usage_reconstruction_pass, transition_reconstruction_pass, and same_execution all true")
    if not _runtime_result_ready(runtime_result):
        return blocked(
            response,
            "VA_CONVERSATIONAL_RUNTIME_NOT_LIVE",
            "Same-execution reconstruction passed but the persistent VA conversational runtime did not become live on the sovereign carrier.",
            "the exact reconstructed proof and TVC route start a live VACC gateway and /api/va-claims/v1/readiness returns READY",
            expected="VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
        )

    runtime_state = runtime_result["runtime_state"]
    base.update(
        {
            "transition_id": "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
            "master_records_reconstruction_result": result,
            "master_records_reconstruction_receipt_path": str(MASTER_RECORDS_RECEIPT),
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
            "va_conversational_runtime_result": runtime_result,
            "va_conversational_runtime_endpoint": runtime_state.get("endpoint"),
            "va_conversational_runtime_state_path": str(VA_RUNTIME_STATE),
            "credential_authority": CURRENT,
            "credential_requirement": "NONE",
            "github_token_required": False,
            "next_authorized_action": "Bind the live VACC gateway to the admitted public HTTPS transport and execute a correlated Site request.",
            "blocker": None,
        }
    )
    write_json(BASE_RECEIPT, base)
    response.update(
        {
            "state": "ACTIVE",
            "transition_id": "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
            "expected_next_transition": "VA_PUBLIC_HTTPS_TRANSPORT_BINDING",
            "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
            "blocker": None,
            "credential_authority_model": CURRENT,
            "github_token_required": False,
        }
    )
    refs = list(response.get("evidence_refs") or [])
    for path in (MASTER_RECORDS_RECEIPT, VA_RUNTIME_STATE):
        ref = str(path.relative_to(ROOT))
        if ref not in refs:
            refs.append(ref)
    response["evidence_refs"] = refs
    return response


def main() -> int:
    invocation = sys.stdin.read()
    completed = subprocess.run(
        [sys.executable, str(UNDERLYING)],
        input=invocation,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env=sovereign_child_env(),
    )
    for path in NORMALIZE_FILES:
        normalize_file(path)
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode
    try:
        response = json.loads(completed.stdout)
    except Exception:
        sys.stderr.write(completed.stderr)
        return 7
    response = normalize(response)
    response["credential_authority_model"] = CURRENT
    response["github_token_required"] = False
    response = normalize_blocker_contract(response)
    response = apply_master_records_reconstruction(response)
    response = normalize_blocker_contract(response)
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
