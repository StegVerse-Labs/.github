#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path.cwd().resolve()
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from master_records_sovereign_reconstruction_bridge import (
    execute_reconstruction,
    find_master_records_root,
    reconstruction_receipt_verified,
)

UNDERLYING = WORKERS / "ecosystem_chat_tc_tvc_route_worker.py"
EXPECTED_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECEIPT_ROOT = (ROOT / "receipts" / "ecosystem-chat-sovereign-inference").resolve()
BASE_RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
ROUTE_RECEIPT = RECEIPT_ROOT / "tvc_local_model_route.json"
LLM_EXECUTION_RECEIPT = RECEIPT_ROOT / "llm_adapter_sovereign_execution.json"
MASTER_RECORDS_PACKET = RECEIPT_ROOT / "master_records_same_execution_packet.json"
MASTER_RECORDS_RECEIPT = RECEIPT_ROOT / "master_records_same_execution_reconstruction.json"


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def load_json(path: Path | None) -> dict | None:
    if path is None:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def sovereign_child_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def run_underlying(invocation: str) -> tuple[int, dict | None, str]:
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
    response = None
    if completed.returncode == 0:
        try:
            candidate = json.loads(completed.stdout)
        except Exception:
            candidate = None
        if isinstance(candidate, dict):
            response = candidate
    return completed.returncode, response, completed.stderr[-1200:]


def blocked(base: dict, *, transition: str, problem: str, release: str) -> dict:
    return {
        **base,
        "state": "BLOCKED",
        "transition_id": transition,
        "expected_next_transition": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION",
        "credential_authority_model": "TC/TVC",
        "github_token_required": False,
        "blocker": {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": problem,
            "solution_required": True,
            "may_remain_blocked": False,
            "machine_observable_release_condition": release,
            "github_token_required": False,
            "third_party_blocker": False,
        },
    }


def main() -> int:
    invocation_raw = sys.stdin.read()
    try:
        invocation = json.loads(invocation_raw)
    except Exception:
        return 2
    task = invocation.get("task") or {}
    if task.get("task_id") != EXPECTED_TASK:
        return 2

    returncode, response, stderr_tail = run_underlying(invocation_raw)
    if returncode != 0 or not isinstance(response, dict):
        json.dump(
            blocked(
                {"schema": "stegverse.worker-response/v0.1", "evidence_refs": []},
                transition="SOVEREIGN_ROUTE_WORKER_FAILED",
                problem="The canonical TC/TVC sovereign route and LLM-adapter worker failed before Master Records reconstruction.",
                release="ecosystem_chat_tc_tvc_route_worker returns a valid worker response",
            ) | {"stderr_tail": stderr_tail},
            sys.stdout,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0

    if response.get("transition_id") != "LLM_ADAPTER_SAME_ENDPOINT_EXECUTED":
        response["credential_authority_model"] = "TC/TVC"
        response["github_token_required"] = False
        json.dump(response, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    base_receipt = load_json(BASE_RECEIPT)
    route = load_json(ROUTE_RECEIPT)
    execution = load_json(LLM_EXECUTION_RECEIPT)
    proof_path_raw = base_receipt.get("local_model_proof_path") if isinstance(base_receipt, dict) else None
    proof_path = Path(proof_path_raw).resolve() if isinstance(proof_path_raw, str) else None
    proof = load_json(proof_path)
    if not all(isinstance(item, dict) for item in (base_receipt, route, execution, proof)):
        result = blocked(
            response,
            transition="MASTER_RECORDS_RECONSTRUCTION_PACKET_INCOMPLETE",
            problem="Same-execution Master Records reconstruction requires the exact model proof, TVC route receipt and LLM-adapter execution receipt.",
            release="all exact packet components exist in the sovereign inference receipt namespace",
        )
        if isinstance(base_receipt, dict):
            base_receipt.update({"transition_id": result["transition_id"], "blocker": result["blocker"]})
            atomic_write(BASE_RECEIPT, base_receipt)
        json.dump(result, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    existing = load_json(MASTER_RECORDS_RECEIPT)
    if reconstruction_receipt_verified(existing, proof=proof, route=route, execution=execution):
        reconstruction_result = {
            "attempted": False,
            "state": "COMPLETE",
            "reason": "REUSED_EXACT_MASTER_RECORDS_RECONSTRUCTION",
            "reconstruction_receipt_path": str(MASTER_RECORDS_RECEIPT),
            "reconstruction_receipt": existing,
            "credential_requirement": "NONE",
            "credential_authority": "TC/TVC",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
            "master_records_bearer_auth_forwarded": False,
        }
    else:
        master_records_root = find_master_records_root(ROOT)
        if master_records_root is None:
            result = blocked(
                response,
                transition="MASTER_RECORDS_LOCAL_CAPSULE_NOT_MATERIALIZED",
                problem="The canonical Master Records sovereign reconstruction verifier is not materialized on this StegVerse carrier.",
                release="find_master_records_root resolves merged task 024, verifier and scoped handoff locally without source checkout",
            )
            base_receipt.update({"transition_id": result["transition_id"], "blocker": result["blocker"]})
            atomic_write(BASE_RECEIPT, base_receipt)
            json.dump(result, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0
        reconstruction_result = execute_reconstruction(
            master_records_root,
            proof=proof,
            route=route,
            execution=execution,
            packet_path=MASTER_RECORDS_PACKET,
            output_path=MASTER_RECORDS_RECEIPT,
        )

    reconstruction = reconstruction_result.get("reconstruction_receipt") if isinstance(reconstruction_result, dict) else None
    if not reconstruction_receipt_verified(reconstruction, proof=proof, route=route, execution=execution):
        result = blocked(
            response,
            transition="MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_FAILED",
            problem="Master Records did not independently reconstruct provider usage and transition identity for the exact same sovereign execution.",
            release="task 024 emits PASS for the exact proof/route/execution packet with same_execution and both reconstruction predicates true",
        )
        base_receipt.update({
            "transition_id": result["transition_id"],
            "blocker": result["blocker"],
            "master_records_reconstruction_result": reconstruction_result,
        })
        atomic_write(BASE_RECEIPT, base_receipt)
        json.dump(result, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    base_receipt.update(
        {
            "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.8",
            "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            "master_records_reconstruction_result": reconstruction_result,
            "master_records_packet_path": str(MASTER_RECORDS_PACKET),
            "master_records_reconstruction_receipt_path": str(MASTER_RECORDS_RECEIPT),
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
            "credential_requirement": "NONE",
            "credential_authority": "TC/TVC",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
            "master_records_bearer_auth_forwarded": False,
            "next_authorized_action": "Run immutable zero-blocker Ecosystem Chat activation verification for this exact reconstructed execution; do not infer activation from reconstruction alone.",
            "blocker": None,
        }
    )
    atomic_write(BASE_RECEIPT, base_receipt)

    response.update(
        {
            "state": "ACTIVE",
            "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            "expected_next_transition": "ECOSYSTEM_CHAT_ZERO_BLOCKER_ACTIVATION_VERIFICATION",
            "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
            "credential_authority_model": "TC/TVC",
            "github_token_required": False,
            "blocker": None,
        }
    )
    refs = list(response.get("evidence_refs") or [])
    for candidate in (MASTER_RECORDS_PACKET, MASTER_RECORDS_RECEIPT):
        ref = str(candidate.relative_to(ROOT))
        if ref not in refs:
            refs.append(ref)
    response["evidence_refs"] = refs
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
