#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from llm_adapter_sovereign_execution_bridge import find_llm_adapter_root
from va_conversational_runtime_bridge import ensure_runtime_gateway, runtime_state_verified

UNDERLYING = WORKERS / "ecosystem_chat_tc_tvc_route_worker.py"
RECEIPT_ROOT = ROOT / "receipts" / "ecosystem-chat-sovereign-inference"
BASE_RECEIPT = RECEIPT_ROOT / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
ROUTE_RECEIPT = RECEIPT_ROOT / "tvc_local_model_route.json"
RUNTIME_STATE = RECEIPT_ROOT / "va_conversational_runtime_process.json"


def load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def child_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(ROOT),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        **({"HOME": os.environ["HOME"]} if "HOME" in os.environ else {}),
    }


def blocked(response: dict, transition: str, problem: str, release: str) -> dict:
    response.update({
        "state": "BLOCKED",
        "transition_id": transition,
        "expected_next_transition": "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
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
        "credential_authority_model": "TV/TVC",
        "github_token_required": False,
    })
    return response


def activate_conversational_runtime(response: dict) -> dict:
    if response.get("transition_id") not in {
        "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
        "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
    }:
        return response

    base = load_json(BASE_RECEIPT)
    route = load_json(ROUTE_RECEIPT)
    if not isinstance(base, dict) or not isinstance(route, dict):
        return blocked(
            response,
            "VA_RUNTIME_INPUT_EVIDENCE_INCOMPLETE",
            "The conversational runtime requires the exact reconstructed sovereign execution lineage and TVC route receipt.",
            "the canonical receipt namespace contains the reconstructed base receipt and exact TVC route receipt",
        )
    if base.get("provider_usage_reconstruction_pass") is not True or base.get("transition_reconstruction_pass") is not True or base.get("same_execution") is not True:
        return blocked(
            response,
            "VA_RUNTIME_RECONSTRUCTION_NOT_PROVEN",
            "The conversational runtime cannot start before same-execution provider-usage and transition reconstruction pass.",
            "Master Records same-execution reconstruction is PASS for provider usage and transition continuity",
        )

    proof_raw = base.get("local_model_proof_path")
    proof_path = Path(proof_raw).resolve() if isinstance(proof_raw, str) else None
    if proof_path is None or not proof_path.is_file():
        return blocked(
            response,
            "VA_RUNTIME_PROOF_MISSING",
            "The exact live local-model proof used by the admitted route is unavailable.",
            "the reconstructed base receipt resolves the exact existing runtime proof",
        )

    adapter_root = find_llm_adapter_root(ROOT)
    if adapter_root is None:
        return blocked(
            response,
            "VA_RUNTIME_ADAPTER_CAPSULE_NOT_MATERIALIZED",
            "The canonical LLM-adapter runtime gateway is not materialized on the sovereign carrier.",
            "find_llm_adapter_root resolves the locally materialized canonical LLM-adapter workload",
        )

    result = ensure_runtime_gateway(
        adapter_root,
        proof_path=proof_path,
        route_path=ROUTE_RECEIPT.resolve(),
        state_path=RUNTIME_STATE.resolve(),
    )
    runtime_state = result.get("runtime_state") if isinstance(result, dict) else None
    if not runtime_state_verified(runtime_state, proof_path=proof_path, route_path=ROUTE_RECEIPT.resolve()):
        return blocked(
            response,
            "VA_CONVERSATIONAL_RUNTIME_START_FAILED",
            "The governed VA conversational gateway did not become live and ready on the sovereign carrier.",
            "the gateway process remains alive and /api/va-claims/v1/readiness returns READY under the exact TVC route and runtime proof",
        )

    base.update({
        "transition_id": "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
        "va_conversational_runtime_result": result,
        "va_conversational_runtime_state_path": str(RUNTIME_STATE),
        "va_conversational_runtime_endpoint": runtime_state.get("endpoint"),
        "va_conversational_runtime_chat_path": runtime_state.get("chat_path"),
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "private_document_upload_active": False,
        "filing_active": False,
        "next_authorized_action": "Bind the verified local conversational gateway to the admitted public HTTPS transport without granting the transport execution or model authority, then perform the Site end-to-end request correlation.",
        "blocker": None,
    })
    write_json(BASE_RECEIPT, base)

    response.update({
        "state": "ACTIVE",
        "transition_id": "VA_CONVERSATIONAL_RUNTIME_LIVE_VERIFIED",
        "expected_next_transition": "VA_PUBLIC_HTTPS_TRANSPORT_BINDING",
        "checkpoint_ref": str(BASE_RECEIPT.relative_to(ROOT)),
        "blocker": None,
        "credential_authority_model": "TV/TVC",
        "github_token_required": False,
    })
    refs = list(response.get("evidence_refs") or [])
    ref = str(RUNTIME_STATE.relative_to(ROOT))
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
        timeout=240,
        check=False,
        env=child_env(),
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode
    try:
        response = json.loads(completed.stdout)
    except Exception:
        sys.stderr.write(completed.stderr)
        return 7
    response = activate_conversational_runtime(response)
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
