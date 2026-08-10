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

from tvc_sovereign_route_bridge import evaluate_route, find_tvc_root, route_receipt_verified

EXPECTED_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECEIPT_ROOT = (ROOT / "receipts" / "ecosystem-chat-sovereign-inference").resolve()
BASE_RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
ROUTE_RECEIPT = RECEIPT_ROOT / "tvc_local_model_route.json"


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

    if response.get("transition_id") != "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED":
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
            "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.6",
            "transition_id": "TVC_LOCAL_MODEL_ROUTE_ADMITTED",
            "tvc_route_result": route_result,
            "tvc_route_receipt_path": str(ROUTE_RECEIPT),
            "tvc_route_receipt_hash": route.get("receipt_hash"),
            "credential_requirement": "NONE",
            "github_token_required": False,
            "next_authorized_action": (
                f"Consume exactly {endpoint} through StegVerseLocalHTTPProviderClient under TVC receipt {ROUTE_RECEIPT}; "
                "execute governed E1-to-model-to-E2, persist measured usage, obtain same-execution Master Records reconstruction, then retire the heartbeat-owned model process."
            ),
            "blocker": None,
        }
    )
    atomic_write(BASE_RECEIPT, receipt)
    response.update(
        {
            "state": "ACTIVE",
            "transition_id": "TVC_LOCAL_MODEL_ROUTE_ADMITTED",
            "expected_next_transition": "LLM_ADAPTER_SAME_ENDPOINT_EXECUTION",
            "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
            "blocker": None,
        }
    )
    refs = list(response.get("evidence_refs") or [])
    route_ref = str(ROUTE_RECEIPT.relative_to(ROOT))
    if route_ref not in refs:
        refs.append(route_ref)
    response["evidence_refs"] = refs
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
