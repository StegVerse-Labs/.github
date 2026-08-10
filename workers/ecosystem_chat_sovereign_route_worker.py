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

from llm_adapter_sovereign_execution_bridge import (
    execute_admitted_route,
    execution_receipt_verified,
    find_llm_adapter_root,
)
from tvc_sovereign_route_bridge import evaluate_route, find_tvc_root, route_receipt_verified

EXPECTED_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECEIPT_ROOT = (ROOT / "receipts" / "ecosystem-chat-sovereign-inference").resolve()
BASE_RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
ROUTE_RECEIPT = RECEIPT_ROOT / "tvc_local_model_route.json"
LLM_EXECUTION_RECEIPT = RECEIPT_ROOT / "llm_adapter_sovereign_execution.json"


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def _load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def run_base_worker(invocation: dict) -> tuple[int, dict | None, str]:
    process = subprocess.run(
        [sys.executable, str(WORKERS / "ecosystem_chat_sovereign_inference_worker.py")],
        input=json.dumps(invocation),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=50,
        check=False,
        env=os.environ.copy(),
    )
    response: dict | None = None
    if process.returncode == 0:
        try:
            candidate = json.loads(process.stdout)
        except Exception:
            candidate = None
        if isinstance(candidate, dict):
            response = candidate
    return process.returncode, response, process.stderr[-1000:]


def _blocked_response(base: dict, *, transition: str, next_transition: str, problem: str, release: str) -> dict:
    blocker = {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "machine_observable_release_condition": release,
        "github_token_required": False,
        "third_party_blocker": False,
    }
    return {
        **base,
        "state": "BLOCKED",
        "transition_id": transition,
        "expected_next_transition": next_transition,
        "blocker": blocker,
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    if task.get("task_id") != EXPECTED_TASK:
        return 2
    epoch = invocation.get("heartbeat_epoch")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    claim_id = str(task.get("claim_id") or "")

    returncode, response, stderr_tail = run_base_worker(invocation)
    if returncode != 0 or not isinstance(response, dict):
        json.dump(
            {
                "schema": "stegverse.worker-response/v0.1",
                "state": "FAILED",
                "transition_id": "BASE_INFERENCE_WORKER_FAILED",
                "expected_next_transition": "BASE_INFERENCE_WORKER_RETRY",
                "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
                "evidence_refs": [],
                "blocker": {
                    "dependency_class": "INTERNAL_CAPABILITY",
                    "problem_statement": "The canonical heartbeat inference worker failed before route evaluation.",
                    "solution_required": True,
                    "may_remain_blocked": False,
                    "machine_observable_release_condition": "base worker returns a valid worker response",
                    "stderr_tail": stderr_tail,
                    "github_token_required": False,
                },
            },
            sys.stdout,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0

    if response.get("transition_id") not in {"SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED", "TVC_LOCAL_MODEL_ROUTE_ADMITTED"}:
        json.dump(response, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    receipt = _load_json(BASE_RECEIPT)
    if not isinstance(receipt, dict):
        failed = _blocked_response(
            response,
            transition="SOVEREIGN_LIVE_MODEL_RECEIPT_MISSING",
            next_transition="TVC_LOCAL_MODEL_ROUTE_ADMISSION",
            problem="The live-model worker response exists but its canonical receipt is unavailable.",
            release="base inference receipt exists in the admitted receipt namespace",
        )
        json.dump(failed, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    proof_path_raw = receipt.get("local_model_proof_path")
    endpoint = receipt.get("live_model_endpoint")
    proof_path = Path(proof_path_raw).resolve() if isinstance(proof_path_raw, str) else None
    proof = _load_json(proof_path) if proof_path is not None else None
    if proof_path is None or not isinstance(proof, dict) or not isinstance(endpoint, str):
        failed = _blocked_response(
            response,
            transition="TVC_ROUTE_INPUT_EVIDENCE_INCOMPLETE",
            next_transition="TVC_LOCAL_MODEL_ROUTE_ADMISSION",
            problem="TVC route admission requires the exact persistent local-model proof and live endpoint.",
            release="base receipt supplies an existing proof path and live endpoint",
        )
        receipt["transition_id"] = failed["transition_id"]
        receipt["blocker"] = failed["blocker"]
        atomic_write(BASE_RECEIPT, receipt)
        json.dump(failed, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    existing_route = _load_json(ROUTE_RECEIPT)
    if route_receipt_verified(existing_route, proof, endpoint):
        route_result = {
            "attempted": False,
            "state": "COMPLETE",
            "reason": "REUSED_VERIFIED_TVC_LOCAL_MODEL_ROUTE",
            "route_receipt_path": str(ROUTE_RECEIPT),
            "route_receipt": existing_route,
            "github_token_required": False,
            "credential_requirement": "NONE",
            "execution_authority": False,
        }
    else:
        tvc_root = find_tvc_root(ROOT)
        if tvc_root is None:
            failed = _blocked_response(
                response,
                transition="TVC_LOCAL_ROUTE_CAPSULE_NOT_MATERIALIZED",
                next_transition="TVC_LOCAL_MODEL_ROUTE_ADMISSION",
                problem="The canonical TVC sovereign local-route evaluator is not materialized on the StegVerse carrier.",
                release="find_tvc_root resolves the canonical TVC task/module/CLI surfaces locally",
            )
            receipt.update({
                "transition_id": failed["transition_id"],
                "blocker": failed["blocker"],
                "tvc_route_authority_required": True,
                "credential_requirement": "NONE",
                "github_token_required": False,
            })
            atomic_write(BASE_RECEIPT, receipt)
            json.dump(failed, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0
        route_result = evaluate_route(
            tvc_root,
            proof_path=proof_path,
            proof=proof,
            endpoint=endpoint,
            output_path=ROUTE_RECEIPT,
        )

    route = route_result.get("route_receipt") if isinstance(route_result, dict) else None
    if not route_receipt_verified(route, proof, endpoint):
        failed = _blocked_response(
            response,
            transition="TVC_LOCAL_MODEL_ROUTE_DENIED",
            next_transition="TVC_LOCAL_MODEL_ROUTE_ADMISSION",
            problem="TVC did not admit the exact persistent sovereign local-model proof and endpoint.",
            release="TVC emits ROUTE_ADMITTED for the exact proof hash and endpoint with credential_requirement NONE",
        )
        receipt.update({"transition_id": failed["transition_id"], "blocker": failed["blocker"], "tvc_route_result": route_result})
        atomic_write(BASE_RECEIPT, receipt)
        json.dump(failed, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    receipt.update(
        {
            "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.7",
            "transition_id": "TVC_LOCAL_MODEL_ROUTE_ADMITTED",
            "tvc_route_result": route_result,
            "tvc_route_receipt_path": str(ROUTE_RECEIPT),
            "tvc_route_receipt_hash": route.get("receipt_hash"),
            "credential_requirement": "NONE",
            "credential_authority": "StegVerse-Labs/TV+TVC",
            "github_token_required": False,
            "next_authorized_action": "Execute the exact admitted endpoint through the canonical local LLM-adapter carrier executor.",
            "blocker": None,
        }
    )
    atomic_write(BASE_RECEIPT, receipt)

    existing_execution = _load_json(LLM_EXECUTION_RECEIPT)
    if execution_receipt_verified(existing_execution, proof=proof, route=route):
        execution_result = {
            "attempted": False,
            "state": "COMPLETE",
            "reason": "REUSED_SAME_ROUTE_LLM_ADAPTER_EXECUTION",
            "execution_receipt_path": str(LLM_EXECUTION_RECEIPT),
            "execution_receipt": existing_execution,
            "credential_requirement": "NONE",
            "credential_authority": "StegVerse-Labs/TV+TVC",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
        }
    else:
        adapter_root = find_llm_adapter_root(ROOT)
        if adapter_root is None:
            failed = _blocked_response(
                response,
                transition="LLM_ADAPTER_LOCAL_CAPSULE_NOT_MATERIALIZED",
                next_transition="LLM_ADAPTER_SAME_ENDPOINT_EXECUTION",
                problem="The canonical LLM-adapter sovereign carrier executor is not materialized on the StegVerse carrier.",
                release="find_llm_adapter_root resolves task 020, its carrier executor, transport binding, and canonical handoff locally",
            )
            receipt.update({"transition_id": failed["transition_id"], "blocker": failed["blocker"]})
            atomic_write(BASE_RECEIPT, receipt)
            json.dump(failed, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0
        session_id = f"ecosystem-chat-hb-{epoch}-{claim_id[:12]}"
        transition_id = f"ecosystem-chat-sovereign-{epoch}-{fence}"
        measurement_id = f"ecosystem-chat-usage-{epoch}-{fence}"
        execution_result = execute_admitted_route(
            adapter_root,
            proof_path=proof_path,
            route_path=ROUTE_RECEIPT,
            proof=proof,
            route=route,
            session_id=session_id,
            transition_id=transition_id,
            measurement_id=measurement_id,
            output_path=LLM_EXECUTION_RECEIPT,
        )

    execution = execution_result.get("execution_receipt") if isinstance(execution_result, dict) else None
    if not execution_receipt_verified(execution, proof=proof, route=route):
        failed = _blocked_response(
            response,
            transition="LLM_ADAPTER_SAME_ENDPOINT_EXECUTION_FAILED",
            next_transition="LLM_ADAPTER_SAME_ENDPOINT_EXECUTION",
            problem="The canonical LLM-adapter did not execute the exact TVC-admitted sovereign endpoint under the credential-free route.",
            release="task 020 emits EXECUTED for the same proof and route with measured usage, credential_requirement NONE, and no GitHub auth forwarded",
        )
        receipt.update({"transition_id": failed["transition_id"], "blocker": failed["blocker"], "llm_adapter_execution_result": execution_result})
        atomic_write(BASE_RECEIPT, receipt)
        json.dump(failed, sys.stdout, sort_keys=True); sys.stdout.write("\n"); return 0

    receipt.update(
        {
            "transition_id": "LLM_ADAPTER_SAME_ENDPOINT_EXECUTED",
            "llm_adapter_execution_result": execution_result,
            "llm_adapter_execution_receipt_path": str(LLM_EXECUTION_RECEIPT),
            "provider_usage_custody_recorded": execution.get("provider_usage_custody_recorded") is True,
            "provider_usage_reconstruction_pass": execution.get("provider_usage_reconstruction_pass") is True,
            "credential_requirement": "NONE",
            "credential_authority": "StegVerse-Labs/TV+TVC",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
            "next_authorized_action": "Obtain same-execution provider-usage and transition reconstruction PASS through canonical master-records/orchestration; then satisfy the terminal activation receipt and retire the heartbeat-owned model process.",
            "blocker": None,
        }
    )
    atomic_write(BASE_RECEIPT, receipt)
    response.update(
        {
            "state": "ACTIVE",
            "transition_id": "LLM_ADAPTER_SAME_ENDPOINT_EXECUTED",
            "expected_next_transition": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION",
            "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
            "blocker": None,
        }
    )
    refs = list(response.get("evidence_refs") or [])
    for candidate in (ROUTE_RECEIPT, LLM_EXECUTION_RECEIPT):
        ref = str(candidate.relative_to(ROOT))
        if ref not in refs:
            refs.append(ref)
    response["evidence_refs"] = refs
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
