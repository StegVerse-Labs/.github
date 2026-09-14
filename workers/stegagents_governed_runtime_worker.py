#!/usr/bin/env python3
"""WorkerCoordinator bridge for the first governed StegAgents runtime proof.

This worker consumes, but never mints, the current WorkerCoordinator claim/fence.
It resolves the already-local StegAgents source, verifies the exact merged
CodeRepair-001 governed manifest blob, invokes the existing StegAgents governed
CodeRepair runtime, and retains the exact returned proposal/governance/
reconstruction result in the resident evidence root.

No second scheduler, WorkerCoordinator, InTr implementation, agent registry,
provider route, credential path, or consequential execution authority is created.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "STEGAGENTS-GOVERNED-RUNTIME-001"
COSV = "71000000101001"
AGENT_ID = "CodeRepair-001"
WORKER_ID = "stegagents-governed-runtime-worker"
STEGAGENTS_REPO = "StegVerse-Labs/StegAgents"
EXPECTED_MANIFEST_GIT_BLOB_SHA = "061649a4b0b43c01f3009ed3e6c8c4829559fb5b"
REGISTERED_MANIFEST_SOURCE_MERGE = "b768eeeb0ceca14fcfd50ce665cd6c0885e2774f"
RUNTIME_RESULT_REL = Path("receipts/sovereign-host/stegagents-governed-runtime")
LATEST_REL = Path("receipts/sovereign-host/stegagents-governed-runtime.latest.json")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_uri(value: Any) -> str:
    raw = canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    require(invocation.get("schema") == "stegverse.worker-invocation/v0.1", "worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    require(isinstance(task, Mapping) and isinstance(scope, Mapping), "worker invocation task/scope missing")
    require(task.get("task_id") == TASK_ID, "worker invocation task mismatch")
    require(task.get("state") == "ACTIVE", "worker invocation task is not ACTIVE")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    fence = timing.get("fencing_token")
    require(isinstance(claim_id, str) and claim_id, "worker claim missing")
    require(isinstance(fence, int) and fence >= 1, "worker fence missing")
    require(scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence, "worker invocation scope claim/fence mismatch")
    require(claim_id.endswith(f"-G{fence}"), "worker claim generation mismatch")
    return dict(task)


def repo_roots() -> dict[str, Path]:
    raw = str(os.getenv("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    require(bool(raw), "STEGVERSE_REPO_ROOTS_JSON required")
    value = json.loads(raw)
    require(isinstance(value, dict), "STEGVERSE_REPO_ROOTS_JSON must be object")
    roots: dict[str, Path] = {}
    for repo, location in value.items():
        if isinstance(repo, str) and isinstance(location, str):
            path = Path(location).expanduser().resolve()
            if path.is_dir():
                roots[repo] = path
    return roots


def runtime_root() -> Path:
    raw = str(os.getenv("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    require(bool(raw), "STEGVERSE_HEARTBEAT_ROOT required")
    root = Path(raw).expanduser().resolve()
    require(root.is_dir(), "resident runtime root not materialized")
    return root


def build_request(task: Mapping[str, Any]) -> dict[str, Any]:
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    return {
        "schema": "stegverse.stegagents-governed-coderepair-request/v1",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "agent_id": AGENT_ID,
        "proposal_only": True,
        "execution_authority": False,
        "self_authorization_allowed": False,
        "credential_material_present": False,
        "worker_claim": {
            "claim_id": task["claim_id"],
            "fencing_token": timing["fencing_token"],
            "worker_id": task.get("worker_id"),
        },
        "code_repair_request": {
            "intent": "Prove the first complete governed CodeRepair-001 proposal-only roundtrip without applying repository changes.",
            "language": "python",
            "canonical_repository": "StegVerse-Labs/StegAgents",
            "handoff_path": "docs/STEGAGENTS_GOVERNED_RUNTIME_MIRROR_HANDOFF.md",
            "authority_effect": "NONE",
            "code_bank_references": [],
        },
    }


def validate_warrant_policy_binding(result: Mapping[str, Any]) -> dict[str, Any]:
    binding = result.get("warrant_policy_binding")
    require(isinstance(binding, Mapping), "warrant/policy verification binding missing")
    require(binding.get("warrant_verified") is True, "TV warrant not verified")
    require(binding.get("policy_bundle_verified") is True, "policy bundle not verified")
    warrant_id = binding.get("warrant_id")
    policy_sha = binding.get("policy_bundle_sha256")
    payload_sha = binding.get("warrant_payload_sha256")
    observed_repo = binding.get("observed_repository")
    observed_commit = binding.get("observed_commit_sha")
    require(isinstance(warrant_id, str) and warrant_id, "verified warrant_id missing")
    require(isinstance(policy_sha, str) and len(policy_sha) == 64, "verified policy bundle SHA-256 missing")
    require(isinstance(payload_sha, str) and len(payload_sha) == 64, "verified warrant payload SHA-256 missing")
    require(observed_repo == STEGAGENTS_REPO, "warrant repository binding mismatch")
    require(isinstance(observed_commit, str) and len(observed_commit) == 40, "warrant commit binding missing")
    return dict(binding)


def retain_result(root: Path, task: Mapping[str, Any], request: Mapping[str, Any], result: Mapping[str, Any], manifest_blob_sha: str, warrant_policy_binding: Mapping[str, Any]) -> Path:
    claim_id = str(task["claim_id"])
    receipt = {
        "schema": "stegverse.stegagents-governed-runtime-receipt/v1",
        "state": "AUTHENTIC_GOVERNED_ROUNDTRIP_OBSERVED",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "agent_id": AGENT_ID,
        "registered_manifest": {
            "repository": STEGAGENTS_REPO,
            "path": "agents/governed/CodeRepair-001.manifest.json",
            "git_blob_sha": manifest_blob_sha,
            "expected_git_blob_sha": EXPECTED_MANIFEST_GIT_BLOB_SHA,
            "source_registration_merge": REGISTERED_MANIFEST_SOURCE_MERGE,
            "exact_merged_manifest_verified": manifest_blob_sha == EXPECTED_MANIFEST_GIT_BLOB_SHA,
        },
        "warrant_policy_binding": dict(warrant_policy_binding),
        "request": dict(request),
        "request_sha256": sha256_uri(request),
        "result": dict(result),
        "result_sha256": sha256_uri(result),
        "worker_claim": dict(request["worker_claim"]),
        "proposal_only": result.get("proposal_only") is True,
        "execution_authority": result.get("execution_authority"),
        "self_authorization_allowed": result.get("self_authorization_allowed"),
        "provider_operation_required": result.get("provider_operation_required"),
        "credential_authority": result.get("credential_authority"),
        "credential_material_present": result.get("credential_material_present"),
        "github_runtime_authority": "NONE",
        "kv_skap_user_verification_authority_preserved": True,
        "kv_skap_user_verification_required_for_this_roundtrip": False,
        "external_side_effect": ((result.get("governance") or {}).get("external_side_effect")),
        "master_records_reconstruction": result.get("master_records_reconstruction"),
        "authority_effect": "NONE_EVIDENCE_RETENTION_ONLY",
    }
    target = root / RUNTIME_RESULT_REL / f"{claim_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        require(existing == receipt, "write-once governed runtime receipt collision")
    else:
        target.write_text(raw, encoding="utf-8")
    latest = root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return target


def run(invocation: Mapping[str, Any]) -> dict[str, Any]:
    task = validate_invocation(invocation)
    roots = repo_roots()
    agents_root = roots.get(STEGAGENTS_REPO)
    require(agents_root is not None, "already-local StegAgents source root not materialized")
    manifest = agents_root / "agents/governed/CodeRepair-001.manifest.json"
    require(manifest.is_file(), "CodeRepair-001 governed manifest missing")
    manifest_blob_sha = git_blob_sha(manifest)
    require(manifest_blob_sha == EXPECTED_MANIFEST_GIT_BLOB_SHA, "CodeRepair-001 governed manifest does not match merged registered blob")

    request = build_request(task)
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    completed = subprocess.run(
        [sys.executable, "-m", "src.governed_coderepair_runtime"],
        cwd=str(agents_root),
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    require(completed.returncode == 0, "StegAgents governed runtime returned nonzero")
    try:
        result = json.loads(completed.stdout)
    except Exception as exc:
        raise RuntimeError("StegAgents governed runtime returned invalid JSON") from exc
    require(isinstance(result, dict), "StegAgents governed result must be object")
    require(result.get("state") == "GOVERNED_PROPOSAL_RETURNED", "governed proposal was not returned")
    require(result.get("proposal_only") is True, "proposal-only invariant violated")
    require(result.get("execution_authority") is False, "agent execution authority invariant violated")
    require(result.get("self_authorization_allowed") is False, "agent self-authorization invariant violated")
    require(result.get("provider_operation_required") is False, "unexpected provider operation requirement")
    require(result.get("credential_authority") == "TV/TVC", "provider credential authority drift")
    require(result.get("credential_material_present") is False, "provider credential material exposed to StegAgents")
    warrant_policy_binding = validate_warrant_policy_binding(result)
    governance = result.get("governance")
    require(isinstance(governance, Mapping), "governance result missing")
    require(governance.get("chain_verified") is True, "governance chain not verified")
    require(governance.get("transaction_identity_continuous") is True, "governance transaction continuity missing")
    require(governance.get("master_records_custody_status") == "RECORDED", "Master Records custody missing")
    require(governance.get("external_side_effect") is False, "agent caused consequential external side effect")
    reconstruction = result.get("master_records_reconstruction")
    require(isinstance(reconstruction, Mapping), "Master Records reconstruction missing")
    require(reconstruction.get("operation_transition_custody_status") == "RECORDED", "reconstruction custody missing")
    require(isinstance(reconstruction.get("operation_receipt_ids"), list) and bool(reconstruction.get("operation_receipt_ids")), "reconstruction receipts missing")

    receipt = retain_result(runtime_root(), task, request, result, manifest_blob_sha, warrant_policy_binding)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "STEGAGENTS_GOVERNED_ROUNDTRIP_OBSERVED",
        "transition_sequence": 1,
        "expected_next_transition": None,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(receipt),
        "evidence_refs": [str(receipt)],
        "cost_observation": {
            "compute_units": 1,
            "token_units": 0,
            "storage_bytes": receipt.stat().st_size,
            "network_bytes": 0,
            "operator_seconds": 0,
            "external_cost_usd": 0,
            "latency_ms": None,
            "failure_recovery_units": 0,
            "services_used": [],
        },
        "authority_effect": "NONE_WORKER_PROTOCOL_TRANSLATION_ONLY",
    }


def fail_closed(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": "STEGAGENTS_GOVERNED_RUNTIME_FAIL_CLOSED",
        "transition_sequence": 1,
        "expected_next_transition": "STEGAGENTS_GOVERNED_RUNTIME_EVIDENCE_READY",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": None,
        "evidence_refs": [],
        "cost_observation": {
            "compute_units": 1,
            "token_units": 0,
            "storage_bytes": 0,
            "network_bytes": 0,
            "operator_seconds": 0,
            "external_cost_usd": 0,
            "latency_ms": None,
            "failure_recovery_units": 1,
            "services_used": [],
        },
        "error_type": type(exc).__name__,
        "error": str(exc),
        "authority_effect": "NONE_FAIL_CLOSED",
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        require(isinstance(invocation, dict), "worker invocation must be JSON object")
        response = run(invocation)
    except Exception as exc:
        response = fail_closed(exc)
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
