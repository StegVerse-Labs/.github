#!/usr/bin/env python3
"""Shared WorkerCoordinator bridge for governed StegAgents runtime proofs.

The existing worker/process adapter remains the single execution bridge. It can
serve the original proposal-only CodeRepair proof or the bounded TT-purpose
successor, but it never mints claims/fences, transition authority, credentials,
or Master Records truth.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

OWNER_TASK_ID = "STEGAGENTS-GOVERNED-RUNTIME-001"
OWNER_COSV = "71000000101001"
PURPOSE_TASK_ID = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"
PURPOSE_COSV = "71000000111111"
TEST3_TASK_ID = "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"
TEST3_COSV = "20010000110000"
TASK_ID = OWNER_TASK_ID  # backwards-compatible constant for existing tests/source refs
COSV = OWNER_COSV
AGENT_ID = "CodeRepair-001"
WORKER_ID = "stegagents-governed-runtime-worker"
STEGAGENTS_REPO = "StegVerse-Labs/StegAgents"
EXPECTED_MANIFEST_GIT_BLOB_SHA = "061649a4b0b43c01f3009ed3e6c8c4829559fb5b"
REGISTERED_MANIFEST_SOURCE_MERGE = "b768eeeb0ceca14fcfd50ce665cd6c0885e2774f"
OWNER_RESULT_REL = Path("receipts/sovereign-host/stegagents-governed-runtime")
OWNER_LATEST_REL = Path("receipts/sovereign-host/stegagents-governed-runtime.latest.json")
PURPOSE_RESULT_REL = Path("receipts/sovereign-host/sdk-tt-purpose-bound-worker-runtime-proof")
PURPOSE_LATEST_REL = Path("receipts/sovereign-host/sdk-tt-purpose-bound-worker-runtime-proof.latest.json")
TEST3_RESULT_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime")
TEST3_LATEST_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime.latest.json")
PURPOSE_CAPABILITY = "stegagents_purpose_bound_worker_lifecycle"
TEST3_CAPABILITY = "stegagents_atomic_task_worker_activation"
OWNER_CAPABILITY = "stegagents_governed_coderepair_roundtrip"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def _profile(task_id: str) -> dict[str, str]:
    if task_id == OWNER_TASK_ID:
        return {
            "task_id": OWNER_TASK_ID,
            "cosv": OWNER_COSV,
            "capability": OWNER_CAPABILITY,
            "runtime_module": "src.governed_coderepair_runtime",
            "result_state": "GOVERNED_PROPOSAL_RETURNED",
            "transition_id": "STEGAGENTS_GOVERNED_ROUNDTRIP_OBSERVED",
        }
    if task_id == PURPOSE_TASK_ID:
        return {
            "task_id": PURPOSE_TASK_ID,
            "cosv": PURPOSE_COSV,
            "capability": PURPOSE_CAPABILITY,
            "runtime_module": "src.purpose_bound_worker_runtime",
            "result_state": "GOVERNED_PURPOSE_BOUND_WORKER_RETURNED",
            "transition_id": "STEGAGENTS_PURPOSE_BOUND_WORKER_LIFECYCLE_OBSERVED",
        }
    if task_id == TEST3_TASK_ID:
        return {
            "task_id": TEST3_TASK_ID,
            "cosv": TEST3_COSV,
            "capability": TEST3_CAPABILITY,
            "runtime_module": "src.atomic_task_worker_activation_runtime",
            "result_state": "GOVERNED_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED",
            "transition_id": "STEGAGENTS_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED",
        }
    raise RuntimeError("worker invocation task mismatch")


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    require(invocation.get("schema") == "stegverse.worker-invocation/v0.1", "worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    require(isinstance(task, Mapping) and isinstance(scope, Mapping), "worker invocation task/scope missing")
    profile = _profile(str(task.get("task_id") or ""))
    if profile["task_id"] == TEST3_TASK_ID:
        require(task.get("state") == "HANDOFF_READY", "Test 3 preactivation task must remain HANDOFF_READY")
        require(task.get("constitutive_activation_phase") == "PREPARE_ATOMIC_ACTIVATION", "Test 3 preactivation phase missing")
    else:
        require(task.get("state") == "ACTIVE", "worker invocation task is not ACTIVE")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    fence = timing.get("fencing_token")
    require(isinstance(claim_id, str) and claim_id, "worker claim missing")
    require(isinstance(fence, int) and fence >= 1, "worker fence missing")
    require(scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence, "worker invocation scope claim/fence mismatch")
    require(claim_id.endswith(f"-G{fence}"), "worker claim generation mismatch")
    require(task.get("worker_id") == WORKER_ID, "worker identity mismatch")
    if profile["task_id"] in {PURPOSE_TASK_ID, TEST3_TASK_ID}:
        instance = task.get("worker_instance_id")
        require(isinstance(instance, str) and instance, "task-bound worker requires WorkerCoordinator worker_instance_id")
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


def _required_capability(handoff: Mapping[str, Any], capability: str) -> None:
    execution = handoff.get("execution") if isinstance(handoff.get("execution"), Mapping) else {}
    required = execution.get("required_capabilities")
    require(isinstance(required, list) and capability in required, f"handoff missing required capability:{capability}")


def build_request(task: Mapping[str, Any], handoff: Mapping[str, Any] | None = None) -> dict[str, Any]:
    task_id = str(task.get("task_id") or "")
    profile = _profile(task_id)
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    claim = {
        "claim_id": task["claim_id"],
        "fencing_token": timing["fencing_token"],
        "worker_id": task.get("worker_id"),
    }
    if task_id == OWNER_TASK_ID:
        return {
            "schema": "stegverse.stegagents-governed-coderepair-request/v1",
            "task_id": OWNER_TASK_ID,
            "cosv_task_vector": OWNER_COSV,
            "agent_id": AGENT_ID,
            "proposal_only": True,
            "execution_authority": False,
            "self_authorization_allowed": False,
            "credential_material_present": False,
            "worker_claim": claim,
            "code_repair_request": {
                "intent": "Prove the first complete governed CodeRepair-001 proposal-only roundtrip without applying repository changes.",
                "language": "python",
                "canonical_repository": "StegVerse-Labs/StegAgents",
                "handoff_path": "docs/STEGAGENTS_GOVERNED_RUNTIME_MIRROR_HANDOFF.md",
                "authority_effect": "NONE",
                "code_bank_references": [],
            },
        }

    require(isinstance(handoff, Mapping), "purpose-bound worker executable handoff required")
    _required_capability(handoff, profile["capability"])
    contract = handoff.get("purpose_bound_worker_request")
    require(isinstance(contract, Mapping), "purpose_bound worker request missing from executable handoff")
    candidate = ((contract.get("transition_cell") or {}).get("candidate") if isinstance(contract.get("transition_cell"), Mapping) else None)
    require(contract.get("schema") == "stegverse.sdk.tt-purpose-bound-worker.v1", "purpose-bound SDK request schema mismatch")
    require(isinstance(candidate, Mapping), "purpose-bound candidate missing")
    require(candidate.get("required_capability") == "text.integrity_summary", "purpose-bound capability mismatch")
    lifetime = candidate.get("max_lifetime_seconds")
    require(isinstance(lifetime, int) and not isinstance(lifetime, bool) and lifetime > 0, "purpose-bound lifetime invalid")
    claim["worker_instance_id"] = task.get("worker_instance_id")
    if task_id == TEST3_TASK_ID:
        return {
            "schema": "stegverse.stegagents-atomic-task-worker-request/v1",
            "task_id": TEST3_TASK_ID,
            "cosv_task_vector": TEST3_COSV,
            "parent_agent_id": AGENT_ID,
            "operation_mode": "PREPARE_ATOMIC_ACTIVATION",
            "execution_authority": False,
            "self_authorization_allowed": False,
            "credential_material_present": False,
            "worker_claim": claim,
            "purpose_bound_worker_request": dict(contract),
        }
    return {
        "schema": "stegverse.stegagents-purpose-bound-worker-request/v1",
        "task_id": PURPOSE_TASK_ID,
        "cosv_task_vector": PURPOSE_COSV,
        "parent_agent_id": AGENT_ID,
        "execution_authority": False,
        "self_authorization_allowed": False,
        "credential_material_present": False,
        "worker_claim": claim,
        "purpose_bound_worker_request": dict(contract),
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


def _validate_result(profile: Mapping[str, str], result: Mapping[str, Any]) -> None:
    if profile["task_id"] == TEST3_TASK_ID:
        require(result.get("state") == profile["result_state"], "Test 3 activation result state mismatch")
        require(result.get("execution_authority") is False, "Test 3 execution authority invariant violated")
        require(result.get("self_authorization_allowed") is False, "Test 3 self-authorization invariant violated")
        require(result.get("credential_authority") == "TV/TVC", "Test 3 credential authority drift")
        require(result.get("credential_material_present") is False, "Test 3 credential material exposed")
        require(result.get("authoritative_task_projection_performed") is False, "Test 3 worker projected ACTIVE state before WorkerCoordinator")
        require(result.get("task_invocation_performed") is False, "Test 3 task invoked during activation preparation")
        transition = result.get("constitutive_activation_master_records_transition")
        require(isinstance(transition, Mapping), "Test 3 constitutive transition proof missing")
        require(transition.get("transition_id") == "ACTIVATE_TASK_AND_CREATE_BIND_WORKER", "Test 3 transition id mismatch")
        require(transition.get("state") == "RECORDED", "Test 3 constitutive transition not RECORDED")
        require(transition.get("reconstruction_status") == "PASS", "Test 3 constitutive reconstruction not PASS")
        require(transition.get("required_evidence_validation_status") == "PASS", "Test 3 constitutive evidence not PASS")
        receipt_sha = transition.get("receipt_sha256")
        require(isinstance(receipt_sha, str) and receipt_sha == transition.get("reconstructed_receipt_sha256"), "Test 3 constitutive digest mismatch")
        reconstruction = result.get("master_records_reconstruction")
        require(isinstance(reconstruction, Mapping), "Test 3 reconstruction missing")
        require(reconstruction.get("operation_transition_custody_status") == "RECORDED", "Test 3 reconstruction custody missing")
        return
    require(result.get("state") == profile["result_state"], "governed runtime result state mismatch")
    require(result.get("execution_authority") is False, "agent execution authority invariant violated")
    require(result.get("self_authorization_allowed") is False, "agent self-authorization invariant violated")
    require(result.get("provider_operation_required") is False, "unexpected provider operation requirement")
    require(result.get("credential_authority") == "TV/TVC", "provider credential authority drift")
    require(result.get("credential_material_present") is False, "provider credential material exposed to StegAgents")
    governance = result.get("governance")
    require(isinstance(governance, Mapping), "governance result missing")
    require(governance.get("chain_verified") is True, "governance chain not verified")
    require(governance.get("transaction_identity_continuous") is True, "governance transaction continuity missing")
    require(governance.get("master_records_custody_status") == "RECORDED", "Master Records custody missing")
    require(governance.get("external_side_effect") is False, "unexpected external side effect")
    reconstruction = result.get("master_records_reconstruction")
    require(isinstance(reconstruction, Mapping), "Master Records reconstruction missing")
    require(reconstruction.get("operation_transition_custody_status") == "RECORDED", "reconstruction custody missing")
    require(isinstance(reconstruction.get("operation_receipt_ids"), list) and bool(reconstruction.get("operation_receipt_ids")), "reconstruction receipts missing")

    if profile["task_id"] == OWNER_TASK_ID:
        require(result.get("proposal_only") is True, "proposal-only invariant violated")
        return
    require(result.get("records_only") is True, "purpose-bound records-only closeout missing")
    require(result.get("worker_live_after_close") is False, "purpose-bound worker remained live")
    require(result.get("continued_authority_after_retirement") is False, "purpose-bound authority continued after retirement")
    lifecycle = result.get("purpose_bound_worker_result")
    require(isinstance(lifecycle, Mapping), "purpose-bound lifecycle result missing")
    require(lifecycle.get("callable_retained") is False, "records-only lifecycle retained callable")
    require(lifecycle.get("executor_reference_retained") is False, "records-only lifecycle retained executor reference")
    phases = [row.get("phase") for row in lifecycle.get("lifecycle_receipts", []) if isinstance(row, Mapping)]
    require(phases == ["MATERIALIZED", "INVOCATION_STARTED", "TASK_COMPLETED", "RETIRED"], "purpose-bound lifecycle order mismatch")


def retain_result(root: Path, task: Mapping[str, Any], request: Mapping[str, Any], result: Mapping[str, Any], manifest_blob_sha: str, warrant_policy_binding: Mapping[str, Any]) -> Path:
    profile = _profile(str(task["task_id"]))
    claim_id = str(task["claim_id"])
    purpose = profile["task_id"] == PURPOSE_TASK_ID
    test3 = profile["task_id"] == TEST3_TASK_ID
    receipt = {
        "schema": "stegverse.stegagents-atomic-task-worker-activation-receipt/v1" if test3 else ("stegverse.stegagents-governed-runtime-receipt/v1" if not purpose else "stegverse.stegagents-purpose-bound-worker-runtime-receipt/v1"),
        "state": "AUTHENTIC_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED" if test3 else ("AUTHENTIC_GOVERNED_ROUNDTRIP_OBSERVED" if not purpose else "AUTHENTIC_PURPOSE_BOUND_WORKER_LIFECYCLE_OBSERVED"),
        "task_id": profile["task_id"],
        "runtime_owner_task_id": OWNER_TASK_ID,
        "cosv_task_vector": profile["cosv"],
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
        "execution_authority": result.get("execution_authority"),
        "self_authorization_allowed": result.get("self_authorization_allowed"),
        "provider_operation_required": result.get("provider_operation_required"),
        "credential_authority": result.get("credential_authority"),
        "credential_material_present": result.get("credential_material_present"),
        "github_runtime_authority": "NONE",
        "external_side_effect": ((result.get("governance") or {}).get("external_side_effect")),
        "master_records_reconstruction": result.get("master_records_reconstruction"),
        "authority_effect": "NONE_EVIDENCE_RETENTION_ONLY",
    }
    if test3:
        receipt.update({
            "authoritative_task_projection_performed": result.get("authoritative_task_projection_performed"),
            "task_invocation_performed": result.get("task_invocation_performed"),
            "constitutive_activation_master_records_transition": result.get("constitutive_activation_master_records_transition"),
        })
        result_rel, latest_rel = TEST3_RESULT_REL, TEST3_LATEST_REL
    elif purpose:
        receipt.update({
            "records_only": result.get("records_only"),
            "worker_live_after_close": result.get("worker_live_after_close"),
            "continued_authority_after_retirement": result.get("continued_authority_after_retirement"),
            "purpose_bound_worker_result": result.get("purpose_bound_worker_result"),
        })
        result_rel, latest_rel = PURPOSE_RESULT_REL, PURPOSE_LATEST_REL
    else:
        receipt["proposal_only"] = result.get("proposal_only") is True
        result_rel, latest_rel = OWNER_RESULT_REL, OWNER_LATEST_REL

    target = root / result_rel / f"{claim_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        require(existing == receipt, "write-once governed runtime receipt collision")
    else:
        target.write_text(raw, encoding="utf-8")
    latest = root / latest_rel
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return target


def run(invocation: Mapping[str, Any]) -> dict[str, Any]:
    task = validate_invocation(invocation)
    profile = _profile(str(task["task_id"]))
    handoff = invocation.get("handoff") if isinstance(invocation.get("handoff"), Mapping) else {}
    roots = repo_roots()
    agents_root = roots.get(STEGAGENTS_REPO)
    require(agents_root is not None, "already-local StegAgents source root not materialized")
    manifest = agents_root / "agents/governed/CodeRepair-001.manifest.json"
    require(manifest.is_file(), "CodeRepair-001 governed manifest missing")
    manifest_blob_sha = git_blob_sha(manifest)
    require(manifest_blob_sha == EXPECTED_MANIFEST_GIT_BLOB_SHA, "CodeRepair-001 governed manifest does not match merged registered blob")

    request = build_request(task, handoff)
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    completed = subprocess.run(
        [sys.executable, "-m", profile["runtime_module"]],
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
    _validate_result(profile, result)
    warrant_policy_binding = validate_warrant_policy_binding(result)
    receipt = retain_result(runtime_root(), task, request, result, manifest_blob_sha, warrant_policy_binding)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY" if profile["task_id"] == TEST3_TASK_ID else "COMPLETED",
        "transition_id": profile["transition_id"],
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
