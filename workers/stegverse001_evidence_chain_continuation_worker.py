#!/usr/bin/env python3
"""WorkerCoordinator-selectable post-terminal SV001 evidence-chain continuation.

This worker never reruns terminal SV001. It reuses the existing continuation script
and remains fail-closed on missing downstream evidence. Selection/claim/fence state
is WorkerCoordinator-owned; any custody mutation remains subject to the current
Interlock/InTr and Master Records semantics required by the canonical handoff.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001"
WORKER_ID = "stegverse001-evidence-chain-continuation-worker"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
CONTINUATION_REL = Path("scripts/continue_stegverse001_evidence_chain.py")
SITE_PROOF_REL = Path("observed/site-master-records-custody.latest.json")
SITE_PROOF_SCHEMA = "stegos.master-records.portable-sv001-custody-proof/v1"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)
RETRYABLE_STATES = {
    "SV001_RECEIPT_NOT_OBSERVED",
    "SITE_GOVERNED_CUSTODY_PENDING",
    "SITE_GOVERNED_CUSTODY_PROOF_INVALID",
    "SV002_SOURCE_NOT_CURRENT",
}


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("WorkerCoordinator claim required")
    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("GitHub token may not be required")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("non-TV/TVC secret/token authority forbidden")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("HB32 may not grant execution authority")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("continuation worker may not write repository state")


def require_bound_state_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    if not raw:
        raise RuntimeError("bound state root unavailable")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def materialize_invocation_evidence(invocation: Mapping[str, Any], bound: Path) -> Path | None:
    """Persist non-authorizing Site custody proof in the admitted observed/** lane.

    The proof never mints a claim, fence, custody authority, or execution authority.
    It is only carried into already-admitted bound state and is revalidated by the
    canonical continuation before it can satisfy any downstream predicate.
    """
    evidence = invocation.get("evidence") or {}
    if not isinstance(evidence, Mapping):
        raise RuntimeError("invocation evidence must be an object")
    proof = evidence.get("site_governed_custody_proof")
    existing = bound / SITE_PROOF_REL
    if proof is None:
        return existing if existing.is_file() else None
    if not isinstance(proof, Mapping):
        raise RuntimeError("site_governed_custody_proof must be an object")
    if proof.get("schema") != SITE_PROOF_SCHEMA:
        raise RuntimeError("site governed custody proof schema mismatch")
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text(json.dumps(dict(proof), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return existing


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environment cannot execute sovereign continuation")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden: " + ",".join(sorted(present)))

    validate_invocation(invocation)
    root = Path(__file__).resolve().parents[1]
    continuation = root / CONTINUATION_REL
    if not continuation.is_file():
        raise RuntimeError("canonical SV001 evidence-chain continuation source missing")
    bound = require_bound_state_root()
    site_proof = materialize_invocation_evidence(invocation, bound)

    child = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
    }
    command = [sys.executable, str(continuation), "--source-root", str(root)]
    if site_proof is not None:
        command.extend(["--site-custody-proof", str(site_proof)])

    proc = subprocess.run(
        command,
        cwd=root,
        env=child,
        capture_output=True,
        text=True,
        check=False,
        timeout=840,
    )
    result = parse_last_json(proc.stdout)
    if not isinstance(result, dict):
        raise RuntimeError("continuation returned no machine-readable result")

    state = str(result.get("state") or "UNKNOWN")
    receipt = {
        "schema": "stegverse.sv001-evidence-chain-worker-receipt/v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "continuation_state": state,
        "continuation_returncode": proc.returncode,
        "continuation_result": result,
        "site_governed_custody_proof_supplied": site_proof is not None,
        "site_governed_custody_proof_ref": SITE_PROOF_REL.as_posix() if site_proof is not None else None,
        "site_governed_custody_proof_authority_effect": "NONE_EVIDENCE_ONLY",
        "sv001_reexecution_performed": False,
        "master_records_mutation_performed": bool(result.get("master_records_mutation_performed", False)),
        "heartbeat_grants_execution_authority": False,
        "prior_receipt_authorizes_next_transition": False,
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "authority_effect": "NONE_CONTINUATION_ORCHESTRATION_ONLY",
    }
    target = bound / "receipts" / "latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = "receipts/latest.json"
    return receipt


def worker_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    state = str(receipt.get("continuation_state") or "UNKNOWN")
    evidence = [str(receipt.get("local_receipt_ref") or "receipts/latest.json")]
    if state == "PASS":
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETED",
            "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
            "transition_sequence": 2,
            "expected_next_transition": None,
            "evidence_refs": evidence,
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "repository_writeback_performed": False,
        }
    if state in RETRYABLE_STATES or bool((receipt.get("continuation_result") or {}).get("retry_allowed")):
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_PENDING",
            "transition_sequence": 1,
            "expected_next_transition": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
            "evidence_refs": evidence,
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "repository_writeback_performed": False,
        }
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
        "evidence_refs": evidence,
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "trigger_type": "DOWNSTREAM_EVIDENCE_CHAIN_DEFECT",
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": f"continuation state {state}",
            "solution_required": True,
            "workaround_candidates": [
                "re-evaluate the existing HB32/self-heal/source-refresh runtime solutions",
                "repair only the exact continuation defect without rerunning terminal SV001"
            ],
            "next_solution_action": "Diagnose existing runtime solution registry before any successor runtime implementation.",
            "resolvable_by_current_worker": False,
            "escalation_target": "SOVEREIGN_RUNTIME_SANDBOX_RESOLUTION",
            "required_capabilities": ["repository_resolution", "sandbox_validation"],
            "completion_evidence": ["continuation retry state returns PASS"],
            "same_level_retry_authorized": False
        },
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_WORKER_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE",
        "error": str(exc),
        "evidence_refs": [],
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        receipt = execute(invocation)
        print(json.dumps(worker_response(receipt), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
