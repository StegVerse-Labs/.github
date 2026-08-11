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
NORMALIZE_FILES = (BASE_RECEIPT, LLM_EXECUTION_RECEIPT, MASTER_RECORDS_RECEIPT)
LEGACY = "StegVerse-Labs/TV+TVC"
CURRENT = "TC/TVC"


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
    if value == LEGACY:
        return CURRENT
    return value


def normalize_blocker_contract(response: dict) -> dict:
    """Make legacy child BLOCKED responses satisfy the current heartbeat policy.

    This does not change task state, authority, dependency class, or the proposed
    solution. It only makes the existing concrete next action explicit as a
    workaround candidate so ProcessWorkerAdapter can validate the response.
    """
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


def blocked(response: dict, transition: str, problem: str, release: str) -> dict:
    next_action = release
    response.update(
        {
            "state": "BLOCKED",
            "transition_id": transition,
            "expected_next_transition": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION",
            "blocker": {
                "dependency_class": "INTERNAL_CAPABILITY",
                "problem_statement": problem,
                "solution_required": True,
                "may_remain_blocked": False,
                "workaround_candidates": [next_action],
                "next_solution_action": next_action,
                "machine_observable_release_condition": release,
                "github_token_required": False,
                "third_party_blocker": False,
            },
            "credential_authority_model": CURRENT,
            "github_token_required": False,
        }
    )
    return response


def apply_master_records_reconstruction(response: dict) -> dict:
    if response.get("transition_id") not in {"LLM_ADAPTER_SAME_ENDPOINT_EXECUTED", "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED"}:
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
    if reconstruction_receipt_verified(existing, execution=execution):
        reconstruction = existing
        result = {
            "attempted": False,
            "state": "COMPLETE",
            "reason": "REUSED_VERIFIED_MASTER_RECORDS_RECONSTRUCTION",
            "reconstruction_receipt": existing,
            "reconstruction_receipt_path": str(MASTER_RECORDS_RECEIPT),
            "credential_authority": CURRENT,
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
            "authority_effect": "NONE",
        }
    else:
        master_records_root = find_master_records_root(ROOT)
        if master_records_root is None:
            return blocked(response, "MASTER_RECORDS_LOCAL_CAPSULE_NOT_MATERIALIZED", "The released Master Records sovereign reconstruction verifier is not materialized on the StegVerse carrier.", "find_master_records_root resolves PR #24/#25 reconstruction script, task, and scoped handoff locally")
        result = reconstruct_same_execution(master_records_root, proof=proof, route=route, execution=execution, output_path=MASTER_RECORDS_RECEIPT)
        reconstruction = result.get("reconstruction_receipt") if isinstance(result, dict) else None

    if not reconstruction_receipt_verified(reconstruction, execution=execution):
        return blocked(response, "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_FAILED", "Canonical Master Records did not reconstruct the exact same sovereign execution with provider usage and transition continuity PASS.", "the released verifier emits PASS with provider_usage_reconstruction_pass, transition_reconstruction_pass, and same_execution all true")

    base.update(
        {
            "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            "master_records_reconstruction_result": result,
            "master_records_reconstruction_receipt_path": str(MASTER_RECORDS_RECEIPT),
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
            "credential_authority": CURRENT,
            "credential_requirement": "NONE",
            "github_token_required": False,
            "next_authorized_action": "Advance only to the immutable zero-blocker Ecosystem Chat activation verifier under the existing heartbeat lineage.",
            "blocker": None,
        }
    )
    write_json(BASE_RECEIPT, base)
    response.update(
        {
            "state": "ACTIVE",
            "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            "expected_next_transition": "ECOSYSTEM_CHAT_ZERO_BLOCKER_ACTIVATION_VERIFICATION",
            "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
            "blocker": None,
            "credential_authority_model": CURRENT,
            "github_token_required": False,
        }
    )
    refs = list(response.get("evidence_refs") or [])
    ref = str(MASTER_RECORDS_RECEIPT.relative_to(ROOT))
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
