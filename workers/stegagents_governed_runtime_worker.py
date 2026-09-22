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
TEST3_ACTIVATION_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/activation")
TEST3_ACTIVATION_LATEST_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/activation.latest.json")
TEST3_EXECUTION_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/execution")
TEST3_EXECUTION_LATEST_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/execution.latest.json")
TEST3_CLOSE_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/close")
TEST3_CLOSE_LATEST_REL = Path("receipts/sovereign-host/sdk-tt-richard-seam-authentic-runtime/close.latest.json")
PURPOSE_CAPABILITY = "stegagents_purpose_bound_worker_lifecycle"
PURPOSE_GRAPH_CAPABILITY = "stegagents_purpose_bound_worker_state_graph"
PURPOSE_GRAPH_SCHEMA = "stegverse.stegagents-purpose-bound-worker-state-graph/v1"
PURPOSE_GRAPH_RESULT_SCHEMA = "stegverse.stegagents-purpose-bound-worker-state-graph-result/v1"
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


TVC_WARRANT_REQUEST_ROOT = Path("/var/lib/stegverse/tv-credential-processing/execution-warrants/requests")
TVC_WARRANT_RECEIPT_ROOT = Path("/var/lib/stegverse/tv-credential-processing/execution-warrants/receipts")
TVC_WARRANT_SERVICE_TEMPLATE = "stegtvc-tv-execution-warrant@{instance}.service"


def _fresh_tvc_warrant_env(
    *,
    task: Mapping[str, Any],
    agents_root: Path,
    runner=subprocess.run,
    request_root: Path = TVC_WARRANT_REQUEST_ROOT,
    receipt_root: Path = TVC_WARRANT_RECEIPT_ROOT,
) -> dict[str, str]:
    """Issue one fresh TV/TVC warrant after WorkerCoordinator claim/fence closure."""
    claim_transition = task.get("claim_fence_master_records_transition")
    _closed_transition(claim_transition, "WORKERCOORDINATOR_CLAIM_FENCE_BOUND")
    claim_id = str(task.get("claim_id") or "")
    require(bool(claim_id), "purpose-bound post-claim warrant issuance requires claim_id")
    safe_instance = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in claim_id)
    require(bool(safe_instance), "purpose-bound post-claim warrant instance invalid")

    head = runner(
        ["git", "-C", str(agents_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    commit_sha = head.stdout.strip().lower()
    require(head.returncode == 0 and len(commit_sha) == 40 and all(ch in "0123456789abcdef" for ch in commit_sha), "StegAgents commit identity unavailable for TVC warrant")

    request = {
        "schema": "stegverse.tv.execution-warrant-request/v1",
        "request_id": claim_id,
        "repository": STEGAGENTS_REPO,
        "commit_sha": commit_sha,
        "action": "run_agent",
        "module": STEGAGENTS_REPO,
        "ttl_seconds": 900,
        "task_id": PURPOSE_TASK_ID,
    }
    request_root.mkdir(parents=True, exist_ok=True)
    receipt_root.mkdir(parents=True, exist_ok=True)
    request_path = request_root / f"{safe_instance}.json"
    receipt_path = receipt_root / f"{safe_instance}.json"
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    service = runner(
        ["systemctl", "start", TVC_WARRANT_SERVICE_TEMPLATE.format(instance=safe_instance)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    require(service.returncode == 0, "TV/TVC execution-warrant service failed")
    require(receipt_path.is_file(), "TV/TVC execution-warrant receipt missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(isinstance(receipt, dict), "TV/TVC execution-warrant receipt invalid")
    require(receipt.get("schema") == "stegverse.tvc.execution-warrant-issuance/v1", "TV/TVC warrant receipt schema mismatch")
    require(receipt.get("state") == "ISSUED", "TV/TVC warrant not issued")
    require(receipt.get("credential_authority") == "TV/TVC", "TV/TVC warrant credential authority drift")
    require(receipt.get("private_key_exposed") is False and receipt.get("private_key_persisted") is False, "TV/TVC private-key boundary violated")
    warrant = receipt.get("warrant")
    require(isinstance(warrant, Mapping), "TV/TVC warrant payload missing")
    claims = warrant.get("claims") if isinstance(warrant.get("claims"), Mapping) else {}
    require(claims.get("repo") == STEGAGENTS_REPO and claims.get("commit_sha") == commit_sha and claims.get("task_id") == PURPOSE_TASK_ID, "TV/TVC warrant claim binding mismatch")
    policy_sha = str(receipt.get("policy_bundle_sha256") or "")
    issuer_key = str(receipt.get("issuer_pubkey_b64") or "")
    max_ttl = receipt.get("max_ttl_seconds")
    require(len(policy_sha) == 64 and bool(issuer_key) and isinstance(max_ttl, int), "TV/TVC warrant verification inputs incomplete")
    return {
        "STEGVERSE_WARRANT_JSON": json.dumps(dict(warrant), sort_keys=True, separators=(",", ":")),
        "TV_POLICY_BUNDLE_SHA256": policy_sha,
        "TV_WARRANT_ISSUER_PUBKEY_B64": issuer_key,
        "TV_WARRANT_MAX_TTL_SECONDS": str(max_ttl),
    }

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
    raise RuntimeError("worker invocation task mismatch")


def validate_test3_invocation(invocation: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    require(invocation.get("schema") == "stegverse.worker-invocation/v0.1", "worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    require(isinstance(task, Mapping) and isinstance(scope, Mapping), "worker invocation task/scope missing")
    require(task.get("task_id") == TEST3_TASK_ID, "Test 3 task binding mismatch")
    if task.get("state") == "HANDOFF_READY":
        pending = task.get("pending_atomic_activation")
        require(isinstance(pending, Mapping), "pending atomic activation missing")
        require(task.get("claim_id") is None and task.get("worker_id") is None and task.get("worker_instance_id") is None, "Test 3 preactivation exposed live task-bound worker state")
        claim_id = pending.get("claim_id")
        fence = pending.get("fencing_token")
        worker_id = pending.get("worker_id")
        proposed = pending.get("proposed_worker_instance_id")
        require(isinstance(claim_id, str) and claim_id, "pending claim missing")
        require(isinstance(fence, int) and fence >= 1, "pending fence missing")
        require(claim_id.endswith(f"-G{fence}"), "pending claim generation mismatch")
        require(worker_id == WORKER_ID, "pending worker identity mismatch")
        require(isinstance(proposed, str) and proposed, "proposed worker instance missing")
        require(scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence, "pending invocation scope claim/fence mismatch")
        return dict(task), "ATOMIC_ACTIVATION"

    require(task.get("state") == "ACTIVE", "Test 3 worker invocation task is not ACTIVE")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    fence = timing.get("fencing_token")
    require(isinstance(claim_id, str) and claim_id, "worker claim missing")
    require(isinstance(fence, int) and fence >= 1, "worker fence missing")
    require(scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence, "worker invocation scope claim/fence mismatch")
    require(claim_id.endswith(f"-G{fence}"), "worker claim generation mismatch")
    require(task.get("worker_id") == WORKER_ID, "worker identity mismatch")
    require(isinstance(task.get("worker_instance_id"), str) and task.get("worker_instance_id"), "worker_instance_id missing")
    receipt_ref = task.get("atomic_activation_receipt_ref")
    require(isinstance(receipt_ref, str) and receipt_ref, "atomic activation receipt ref missing")
    if task.get("test3_waiting_for_governed_close") is True:
        require(isinstance(task.get("last_checkpoint_ref"), str) and task.get("last_checkpoint_ref"), "Test 3 execution receipt ref missing before governed close")
        return dict(task), "GOVERNED_CLOSE"
    return dict(task), "TASK_EXECUTION"


def build_test3_request(task: Mapping[str, Any], handoff: Mapping[str, Any], mode: str) -> dict[str, Any]:
    _required_capability(handoff, PURPOSE_CAPABILITY)
    contract = handoff.get("purpose_bound_worker_request")
    require(isinstance(contract, Mapping), "purpose-bound worker request missing from Test 3 handoff")
    candidate = ((contract.get("transition_cell") or {}).get("candidate") if isinstance(contract.get("transition_cell"), Mapping) else None)
    require(contract.get("schema") == "stegverse.sdk.tt-purpose-bound-worker.v1", "purpose-bound SDK request schema mismatch")
    require(isinstance(candidate, Mapping) and candidate.get("required_capability") == "text.integrity_summary", "Test 3 capability mismatch")
    if mode == "ATOMIC_ACTIVATION":
        pending = task["pending_atomic_activation"]
        return {
            "schema": "stegverse.stegagents-atomic-task-worker-activation-request/v1",
            "task_id": TEST3_TASK_ID,
            "cosv_task_vector": TEST3_COSV,
            "parent_agent_id": AGENT_ID,
            "execution_authority": False,
            "self_authorization_allowed": False,
            "credential_material_present": False,
            "task_pre_state": {
                "state": "HANDOFF_READY",
                "claim_id": None,
                "worker_id": None,
                "worker_instance_id": None,
            },
            "pending_worker_claim": {
                "claim_id": pending["claim_id"],
                "fencing_token": pending["fencing_token"],
                "worker_id": pending["worker_id"],
                "proposed_worker_instance_id": pending["proposed_worker_instance_id"],
            },
            "purpose_bound_worker_request": dict(contract),
        }

    root = runtime_root()
    receipt_path = Path(str(task["atomic_activation_receipt_ref"]))
    if not receipt_path.is_absolute():
        receipt_path = root / receipt_path
    require(receipt_path.is_file(), "atomic activation receipt not retained")
    activation_evidence = json.loads(receipt_path.read_text(encoding="utf-8"))
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    if mode == "GOVERNED_CLOSE":
        execution_ref = Path(str(task["last_checkpoint_ref"]))
        if not execution_ref.is_absolute():
            execution_ref = root / execution_ref
        require(execution_ref.is_file(), "Test 3 execution receipt not retained")
        execution_evidence = json.loads(execution_ref.read_text(encoding="utf-8"))
        return {
            "schema": "stegverse.stegagents-atomic-task-worker-close-request/v1",
            "task_id": TEST3_TASK_ID,
            "cosv_task_vector": TEST3_COSV,
            "parent_agent_id": AGENT_ID,
            "execution_authority": False,
            "self_authorization_allowed": False,
            "credential_material_present": False,
            "worker_claim": {
                "claim_id": task["claim_id"],
                "fencing_token": timing["fencing_token"],
                "worker_id": task["worker_id"],
                "worker_instance_id": task["worker_instance_id"],
            },
            "activation_evidence": activation_evidence,
            "execution_evidence": execution_evidence,
            "purpose_bound_worker_request": dict(contract),
        }

    return {
        "schema": "stegverse.stegagents-atomic-task-worker-execution-request/v1",
        "task_id": TEST3_TASK_ID,
        "cosv_task_vector": TEST3_COSV,
        "parent_agent_id": AGENT_ID,
        "execution_authority": False,
        "self_authorization_allowed": False,
        "credential_material_present": False,
        "worker_claim": {
            "claim_id": task["claim_id"],
            "fencing_token": timing["fencing_token"],
            "worker_id": task["worker_id"],
            "worker_instance_id": task["worker_instance_id"],
        },
        "activation_evidence": activation_evidence,
        "purpose_bound_worker_request": dict(contract),
    }


def _require_closed_transition(row: Any, transition_id: str) -> None:
    require(isinstance(row, Mapping), f"{transition_id} transition missing")
    require(row.get("transition_id") == transition_id, f"{transition_id} transition id mismatch")
    require(row.get("state") == "RECORDED", f"{transition_id} state not RECORDED")
    require(row.get("reconstruction_status") == "PASS", f"{transition_id} reconstruction not PASS")
    require(row.get("required_evidence_validation_status") == "PASS", f"{transition_id} required evidence not PASS")
    digest = row.get("receipt_sha256")
    require(isinstance(digest, str) and digest == row.get("reconstructed_receipt_sha256"), f"{transition_id} digest mismatch")


def validate_test3_result(mode: str, result: Mapping[str, Any]) -> None:
    require(result.get("task_id") == TEST3_TASK_ID, "Test 3 result task mismatch")
    require(result.get("execution_authority") is False, "Test 3 execution authority invariant violated")
    require(result.get("self_authorization_allowed") is False, "Test 3 self-authorization invariant violated")
    require(result.get("provider_operation_required") is False, "unexpected provider operation requirement")
    require(result.get("credential_authority") == "TV/TVC", "credential authority drift")
    require(result.get("credential_material_present") is False, "credential material exposed")

    if mode == "ATOMIC_ACTIVATION":
        require(result.get("state") == "GOVERNED_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED", "atomic activation result state mismatch")
        validate_warrant_policy_binding(result)
        _require_closed_transition(result.get("warrant_policy_master_records_transition"), "TV_TVC_WARRANT_POLICY_VERIFIED")
        _require_closed_transition(result.get("atomic_activation_master_records_transition"), "ACTIVATE_TASK_AND_CREATE_BIND_WORKER")
        projection = result.get("activation_projection")
        require(isinstance(projection, Mapping), "activation projection missing")
        require(projection.get("task_pre_state") == "HANDOFF_READY" and projection.get("task_post_state") == "ACTIVE", "activation projection state mismatch")
        require(projection.get("worker_bound_task_id") == TEST3_TASK_ID, "activation projection binding mismatch")
        require(projection.get("invocation_started") is False, "activation projection invoked task")
        governance = result.get("governance")
        require(isinstance(governance, Mapping) and governance.get("state") == "ALLOW", "atomic activation governance not ALLOW")
        require(governance.get("chain_verified") is True and governance.get("master_records_custody_status") == "RECORDED", "atomic activation governance evidence incomplete")
        reconstruction = result.get("master_records_reconstruction")
        require(isinstance(reconstruction, Mapping) and reconstruction.get("operation_transition_custody_status") == "RECORDED", "atomic activation reconstruction missing")
        return

    if mode == "GOVERNED_CLOSE":
        require(result.get("state") == "GOVERNED_TASK_CLOSED_WORKER_RETIRED_RECORDS_ONLY", "Test 3 governed-close result state mismatch")
        _require_closed_transition(result.get("close_master_records_transition"), "CLOSE_TASK_AND_RETIRE_WORKER")
        require(result.get("records_only") is True, "records-only terminal result missing")
        require(result.get("worker_live_after_close") is False, "worker remained live after close")
        require(result.get("continued_authority_after_retirement") is False, "continued authority after retirement")
        require(result.get("callable_retained") is False, "records-only result retained callable")
        require(result.get("executor_reference_retained") is False, "records-only result retained executor reference")
        reconstruction = result.get("records_only_reconstruction")
        require(isinstance(reconstruction, Mapping) and reconstruction.get("operation_transition_custody_status") == "RECORDED", "records-only reconstruction missing")
        return

    require(result.get("state") == "GOVERNED_TASK_RESULT_READY_FOR_CLOSE", "Test 3 execution result state mismatch")
    _require_closed_transition(result.get("invocation_master_records_transition"), "TASK_BOUND_WORKER_INVOCATION_STARTED")
    _require_closed_transition(result.get("task_completed_master_records_transition"), "TASK_BOUND_WORKER_TASK_COMPLETED")
    require(result.get("worker_live") is True, "task-bound worker unexpectedly retired before governed close")
    require(result.get("governed_close_required") is True, "governed close requirement missing")
    require(isinstance(result.get("task_result_hash"), str) and result.get("task_result_hash"), "task result hash missing")


def retain_test3_result(root: Path, task: Mapping[str, Any], request: Mapping[str, Any], result: Mapping[str, Any], manifest_blob_sha: str, mode: str) -> Path:
    if mode == "ATOMIC_ACTIVATION":
        pending = request["pending_worker_claim"]
        claim_id = str(pending["claim_id"])
        result_rel, latest_rel = TEST3_ACTIVATION_REL, TEST3_ACTIVATION_LATEST_REL
        state = "AUTHENTIC_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED"
        worker_claim = dict(pending)
    elif mode == "GOVERNED_CLOSE":
        claim_id = str(request["worker_claim"]["claim_id"])
        result_rel, latest_rel = TEST3_CLOSE_REL, TEST3_CLOSE_LATEST_REL
        state = "AUTHENTIC_TASK_CLOSED_WORKER_RETIRED_RECORDS_ONLY"
        worker_claim = dict(request["worker_claim"])
    else:
        claim_id = str(request["worker_claim"]["claim_id"])
        result_rel, latest_rel = TEST3_EXECUTION_REL, TEST3_EXECUTION_LATEST_REL
        state = "AUTHENTIC_TASK_RESULT_READY_FOR_GOVERNED_CLOSE"
        worker_claim = dict(request["worker_claim"])
    receipt = {
        "schema": "stegverse.stegagents-test3-runtime-receipt/v1",
        "state": state,
        "mode": mode,
        "task_id": TEST3_TASK_ID,
        "runtime_owner_task_id": OWNER_TASK_ID,
        "cosv_task_vector": TEST3_COSV,
        "agent_id": AGENT_ID,
        "registered_manifest": {
            "repository": STEGAGENTS_REPO,
            "path": "agents/governed/CodeRepair-001.manifest.json",
            "git_blob_sha": manifest_blob_sha,
            "expected_git_blob_sha": EXPECTED_MANIFEST_GIT_BLOB_SHA,
            "source_registration_merge": REGISTERED_MANIFEST_SOURCE_MERGE,
            "exact_merged_manifest_verified": manifest_blob_sha == EXPECTED_MANIFEST_GIT_BLOB_SHA,
        },
        "request": dict(request),
        "request_sha256": sha256_uri(request),
        "result": dict(result),
        "result_sha256": sha256_uri(result),
        "worker_claim": worker_claim,
        "execution_authority": False,
        "github_runtime_authority": "NONE",
        "authority_effect": "NONE_EVIDENCE_RETENTION_ONLY",
    }
    if mode == "ATOMIC_ACTIVATION":
        receipt["activation_projection"] = result.get("activation_projection")
        receipt["warrant_policy_binding"] = result.get("warrant_policy_binding")
        receipt["warrant_policy_master_records_transition"] = result.get("warrant_policy_master_records_transition")
        receipt["atomic_activation_master_records_transition"] = result.get("atomic_activation_master_records_transition")
        receipt["master_records_reconstruction"] = result.get("master_records_reconstruction")
    elif mode == "GOVERNED_CLOSE":
        receipt["close_master_records_transition"] = result.get("close_master_records_transition")
        receipt["records_only_result"] = result.get("records_only_result")
        receipt["records_only_reconstruction"] = result.get("records_only_reconstruction")
        receipt["records_only"] = result.get("records_only")
        receipt["worker_live_after_close"] = result.get("worker_live_after_close")
        receipt["continued_authority_after_retirement"] = result.get("continued_authority_after_retirement")
        receipt["callable_retained"] = result.get("callable_retained")
        receipt["executor_reference_retained"] = result.get("executor_reference_retained")
    else:
        receipt["activation_transition_receipt_sha256"] = result.get("activation_transition_receipt_sha256")
        receipt["invocation_master_records_transition"] = result.get("invocation_master_records_transition")
        receipt["task_completed_master_records_transition"] = result.get("task_completed_master_records_transition")
        receipt["task_result"] = result.get("task_result")
        receipt["task_result_hash"] = result.get("task_result_hash")
        receipt["worker_live"] = result.get("worker_live")
        receipt["governed_close_required"] = result.get("governed_close_required")

    target = root / result_rel / f"{claim_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        require(existing == receipt, "write-once Test 3 runtime receipt collision")
    else:
        target.write_text(raw, encoding="utf-8")
    latest = root / latest_rel
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return target


def run_test3(invocation: Mapping[str, Any]) -> dict[str, Any]:
    task, mode = validate_test3_invocation(invocation)
    handoff = invocation.get("handoff") if isinstance(invocation.get("handoff"), Mapping) else {}
    roots = repo_roots()
    agents_root = roots.get(STEGAGENTS_REPO)
    require(agents_root is not None, "already-local StegAgents source root not materialized")
    manifest = agents_root / "agents/governed/CodeRepair-001.manifest.json"
    require(manifest.is_file(), "CodeRepair-001 governed manifest missing")
    manifest_blob_sha = git_blob_sha(manifest)
    require(manifest_blob_sha == EXPECTED_MANIFEST_GIT_BLOB_SHA, "CodeRepair-001 governed manifest does not match merged registered blob")

    request = build_test3_request(task, handoff, mode)
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    if profile["task_id"] == PURPOSE_TASK_ID:
        env.update(_fresh_tvc_warrant_env(task=task, agents_root=agents_root))
    completed = subprocess.run(
        [sys.executable, "-m", "src.purpose_bound_worker_runtime"],
        cwd=str(agents_root),
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    require(completed.returncode == 0, "StegAgents Test 3 runtime returned nonzero")
    try:
        result = json.loads(completed.stdout)
    except Exception as exc:
        raise RuntimeError("StegAgents Test 3 runtime returned invalid JSON") from exc
    require(isinstance(result, dict), "StegAgents Test 3 result must be object")
    validate_test3_result(mode, result)
    receipt = retain_test3_result(runtime_root(), task, request, result, manifest_blob_sha, mode)
    if mode == "ATOMIC_ACTIVATION":
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "ACTIVE",
            "transition_id": "STEGAGENTS_ATOMIC_TASK_WORKER_ACTIVATION_ADMITTED",
            "transition_sequence": 1,
            "expected_next_transition": "STEGAGENTS_TASK_BOUND_WORKER_INVOCATION_READY",
            "expected_next_earliest_epoch": None,
            "expected_next_latest_epoch": None,
            "checkpoint_ref": str(receipt),
            "evidence_refs": [str(receipt)],
            "cost_observation": {"compute_units": 1, "token_units": 0, "storage_bytes": receipt.stat().st_size, "network_bytes": 0, "operator_seconds": 0, "external_cost_usd": 0, "latency_ms": None, "failure_recovery_units": 0, "services_used": []},
            "authority_effect": "NONE_ATOMIC_ACTIVATION_ADMISSION_ONLY",
        }
    if mode == "GOVERNED_CLOSE":
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETED",
            "transition_id": "STEGAGENTS_GOVERNED_CLOSE_RETIRED",
            "transition_sequence": 3,
            "expected_next_transition": None,
            "expected_next_earliest_epoch": None,
            "expected_next_latest_epoch": None,
            "checkpoint_ref": str(receipt),
            "evidence_refs": [str(receipt)],
            "cost_observation": {"compute_units": 1, "token_units": 0, "storage_bytes": receipt.stat().st_size, "network_bytes": 0, "operator_seconds": 0, "external_cost_usd": 0, "latency_ms": None, "failure_recovery_units": 0, "services_used": []},
            "authority_effect": "NONE_GOVERNED_CLOSE_RECORDS_ONLY",
        }
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "ACTIVE",
        "transition_id": "STEGAGENTS_TASK_RESULT_READY_FOR_GOVERNED_CLOSE",
        "transition_sequence": 2,
        "expected_next_transition": "STEGAGENTS_GOVERNED_CLOSE_REQUIRED",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(receipt),
        "evidence_refs": [str(receipt)],
        "cost_observation": {"compute_units": 1, "token_units": 0, "storage_bytes": receipt.stat().st_size, "network_bytes": 0, "operator_seconds": 0, "external_cost_usd": 0, "latency_ms": None, "failure_recovery_units": 0, "services_used": []},
        "authority_effect": "NONE_TASK_RESULT_PENDING_GOVERNED_CLOSE",
    }


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    require(invocation.get("schema") == "stegverse.worker-invocation/v0.1", "worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    require(isinstance(task, Mapping) and isinstance(scope, Mapping), "worker invocation task/scope missing")
    profile = _profile(str(task.get("task_id") or ""))
    require(task.get("state") == "ACTIVE", "worker invocation task is not ACTIVE")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    fence = timing.get("fencing_token")
    require(isinstance(claim_id, str) and claim_id, "worker claim missing")
    require(isinstance(fence, int) and fence >= 1, "worker fence missing")
    require(scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence, "worker invocation scope claim/fence mismatch")
    require(claim_id.endswith(f"-G{fence}"), "worker claim generation mismatch")
    require(task.get("worker_id") == WORKER_ID, "worker identity mismatch")
    if profile["task_id"] == PURPOSE_TASK_ID:
        instance = task.get("worker_instance_id")
        require(isinstance(instance, str) and instance, "purpose-bound worker requires WorkerCoordinator worker_instance_id")
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


def _manifest_state_transition_request(task_id: str) -> dict[str, Any] | None:
    path = runtime_root() / "runtime-state" / "sdk-manifest-state-transition" / f"{task_id}.latest.json"
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "manifest state-transition request must be an object")
    require(value.get("schema") == "stegverse.sdk.manifest-state-transition-request/v1", "manifest state-transition request schema mismatch")
    require(value.get("canonical_task_id") == task_id, "manifest state-transition task binding mismatch")
    require(value.get("request_grants_authority") is False, "manifest state-transition request authority drift")
    require(value.get("claim_fence_authority") == "WORKERCOORDINATOR", "manifest state-transition claim authority drift")
    require(value.get("transition_authority") == "INTERLOCK_INTR", "manifest state-transition transition authority drift")
    require(value.get("credential_authority") == "TV/TVC", "manifest state-transition credential authority drift")
    require(value.get("custody_replay_reconstruction_authority") == "MASTER_RECORDS", "manifest state-transition custody authority drift")
    graph = value.get("state_graph")
    require(isinstance(graph, Mapping), "manifest state-transition graph missing")
    require(graph.get("canonical_task_id") == task_id, "manifest state-transition graph task mismatch")
    return dict(value)


def build_manifest_bound_purpose_request(task: Mapping[str, Any], runtime_request: Mapping[str, Any]) -> dict[str, Any]:
    graph = runtime_request.get("state_graph")
    require(isinstance(graph, Mapping), "manifest state-transition graph missing")
    contract = graph.get("request")
    require(isinstance(contract, Mapping), "manifest state-transition purpose request missing")
    require(contract.get("schema") == "stegverse.sdk.tt-purpose-bound-worker.v1", "manifest purpose request schema mismatch")
    transition_cell = contract.get("transition_cell")
    candidate = transition_cell.get("candidate") if isinstance(transition_cell, Mapping) else None
    require(isinstance(candidate, Mapping), "manifest purpose candidate missing")
    require(isinstance(candidate.get("required_capability"), str) and candidate.get("required_capability"), "manifest purpose capability missing")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), Mapping) else {}
    claim = {
        "claim_id": task["claim_id"],
        "fencing_token": timing["fencing_token"],
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
    }
    predecessor = _closed_transition(
        task.get("claim_fence_master_records_transition"),
        "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
    )
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
        "graph_predecessor_master_records_transition": predecessor,
        "sdk_manifest_state_transition_binding": {
            "canonical_manifest_sha256": runtime_request.get("canonical_manifest_sha256"),
            "graph_id": runtime_request.get("graph_id"),
            "processing_capability": runtime_request.get("processing_capability"),
            "route_id": runtime_request.get("route_id"),
            "request_sha256": runtime_request.get("request_sha256"),
            "authority_effect": "NONE_INPUT_BINDING_ONLY",
        },
    }


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


def _closed_transition(row: Any, transition_id: str) -> dict[str, Any]:
    require(isinstance(row, Mapping), f"{transition_id} transition missing")
    require(row.get("transition_id") == transition_id, f"{transition_id} transition mismatch")
    require(row.get("state") == "RECORDED", f"{transition_id} state not RECORDED")
    require(row.get("reconstruction_status") == "PASS", f"{transition_id} reconstruction not PASS")
    require(row.get("required_evidence_validation_status") == "PASS", f"{transition_id} required evidence not PASS")
    digest = row.get("receipt_sha256")
    require(isinstance(digest, str) and digest == row.get("reconstructed_receipt_sha256"), f"{transition_id} digest mismatch")
    return dict(row)


def build_state_graph_request(task: Mapping[str, Any], handoff: Mapping[str, Any]) -> dict[str, Any]:
    graph = handoff.get("state_dependent_graph")
    require(isinstance(graph, Mapping) and graph.get("enabled") is True, "state-dependent graph contract missing")
    bundle = task.get("purpose_bound_state_graph_claim_bundle")
    require(isinstance(bundle, Mapping), "WorkerCoordinator graph claim bundle missing")
    require(bundle.get("claim_authority") == "WORKERCOORDINATOR", "graph claim authority mismatch")
    claims = bundle.get("claims")
    require(isinstance(claims, list) and len(claims) == 6, "exact six-claim graph bundle required")
    by_label = {row.get("label"): row for row in claims if isinstance(row, Mapping)}
    require(set(by_label) == {"CASE_1","CASE_2","CASE_3","TASK4_A","TASK4_B","TASK4_C"}, "graph claim labels mismatch")
    assignment = _closed_transition(task.get("claim_fence_master_records_transition"), "WORKERCOORDINATOR_CLAIM_FENCE_BOUND")

    def wrap(label: str, contract: Mapping[str, Any], predecessor: Mapping[str, Any] | None = None) -> dict[str, Any]:
        claim = by_label[label]
        require(isinstance(contract, Mapping), f"{label} purpose request missing")
        row = {
            "schema": "stegverse.stegagents-purpose-bound-worker-request/v1",
            "task_id": PURPOSE_TASK_ID,
            "cosv_task_vector": PURPOSE_COSV,
            "parent_agent_id": AGENT_ID,
            "execution_authority": False,
            "self_authorization_allowed": False,
            "credential_material_present": False,
            "worker_claim": {
                "claim_id": claim["claim_id"],
                "fencing_token": claim["fencing_token"],
                "worker_id": claim["worker_id"],
                "worker_instance_id": claim["worker_instance_id"],
            },
            "purpose_bound_worker_request": dict(contract),
        }
        if predecessor is not None:
            row["graph_predecessor_master_records_transition"] = dict(predecessor)
        return row

    singles = graph.get("single_worker_requests")
    task4 = graph.get("task4_worker_requests")
    require(isinstance(singles, list) and len(singles) == 3, "graph single-worker request count mismatch")
    require(isinstance(task4, list) and len(task4) == 3, "graph Task 4 request count mismatch")
    return {
        "schema": PURPOSE_GRAPH_SCHEMA,
        "single_worker_requests": [
            wrap("CASE_1", singles[0], assignment),
            wrap("CASE_2", singles[1]),
            wrap("CASE_3", singles[2]),
        ],
        "task4_worker_requests": [
            wrap("TASK4_A", task4[0]),
            wrap("TASK4_B", task4[1]),
            wrap("TASK4_C", task4[2]),
        ],
    }


def _validate_graph_worker_result(row: Any, label: str) -> dict[str, Any]:
    require(isinstance(row, Mapping), f"{label} governed worker result missing")
    require(row.get("state") == "GOVERNED_PURPOSE_BOUND_WORKER_RETURNED", f"{label} governed worker state mismatch")
    binding = validate_warrant_policy_binding(row)
    require(binding.get("warrant_verified") is True, f"{label} warrant not verified")
    require(binding.get("policy_bundle_verified") is True, f"{label} policy bundle not verified")
    _closed_transition(row.get("warrant_policy_master_records_transition"), "TV_TVC_WARRANT_POLICY_VERIFIED")
    _closed_transition(row.get("intr_admission_master_records_transition"), "STEGCORE_INTR_MATERIALIZATION_ADMITTED")
    lifecycle = row.get("purpose_bound_worker_result")
    require(isinstance(lifecycle, Mapping), f"{label} lifecycle missing")
    transitions = lifecycle.get("canonical_master_records_transitions")
    require(isinstance(transitions, list) and len(transitions) == 4, f"{label} lifecycle closure count mismatch")
    for expected, transition in zip(
        (
            "PURPOSE_BOUND_WORKER_MATERIALIZED",
            "PURPOSE_BOUND_WORKER_INVOCATION_STARTED",
            "PURPOSE_BOUND_WORKER_TASK_COMPLETED",
            "PURPOSE_BOUND_WORKER_RETIRED",
        ),
        transitions,
    ):
        _closed_transition(transition, expected)
    require(row.get("records_only") is True, f"{label} records-only result missing")
    require(row.get("worker_live_after_close") is False, f"{label} worker remained live")
    require(row.get("continued_authority_after_retirement") is False, f"{label} retained authority")
    return dict(binding)


def validate_state_graph_result(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    require(result.get("schema") == PURPOSE_GRAPH_RESULT_SCHEMA, "state graph result schema mismatch")
    require(result.get("state") == "GOVERNED_FOUR_CASE_STATE_GRAPH_RETURNED", "state graph result state mismatch")
    warrant_bindings = []
    for name, label in (
        ("case1_result", "CASE_1"),
        ("case2_result", "CASE_2"),
        ("case3_result", "CASE_3"),
    ):
        warrant_bindings.append(_validate_graph_worker_result(result.get(name), label))
    for name in ("case1_terminal", "case2_terminal", "case3_terminal"):
        _closed_transition(result.get(name), "PURPOSE_BOUND_WORKER_RETIRED")
    _closed_transition(result.get("task4_parent_transition"), "PURPOSE_BOUND_WORKER_TASK4_PARENT_ADMITTED")
    children = result.get("task4_workers")
    require(isinstance(children, list) and len(children) == 3, "Task 4 requires three worker results")
    for index, child in enumerate(children, start=1):
        require(isinstance(child, Mapping), f"TASK4_{index} worker row missing")
        warrant_bindings.append(_validate_graph_worker_result(child.get("result"), f"TASK4_{index}"))
        _closed_transition(child.get("terminal"), "PURPOSE_BOUND_WORKER_RETIRED")
    _closed_transition(result.get("task4_three_way_join"), "PURPOSE_BOUND_WORKER_TASK4_THREE_WAY_JOIN")
    require(result.get("task4_simultaneous_overlap_observed") is True, "Task 4 overlap not observed")
    terminal = result.get("records_only_terminal")
    require(isinstance(terminal, Mapping) and terminal.get("records_only") is True, "graph terminal records-only packet missing")
    require(terminal.get("worker_live_after_close") is False, "graph terminal retained live worker")
    require(terminal.get("continued_authority_after_retirement") is False, "graph terminal retained authority")
    return warrant_bindings


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
    receipt = {
        "schema": "stegverse.stegagents-governed-runtime-receipt/v1" if not purpose else "stegverse.stegagents-purpose-bound-worker-runtime-receipt/v1",
        "state": "AUTHENTIC_GOVERNED_ROUNDTRIP_OBSERVED" if not purpose else "AUTHENTIC_PURPOSE_BOUND_WORKER_LIFECYCLE_OBSERVED",
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
    if purpose:
        if result.get("schema") == PURPOSE_GRAPH_RESULT_SCHEMA:
            terminal = result.get("records_only_terminal") if isinstance(result.get("records_only_terminal"), Mapping) else {}
            receipt.update({
                "state_graph_result": dict(result),
                "records_only": terminal.get("records_only"),
                "worker_live_after_close": terminal.get("worker_live_after_close"),
                "continued_authority_after_retirement": terminal.get("continued_authority_after_retirement"),
                "purpose_bound_state_graph_claim_bundle": task.get("purpose_bound_state_graph_claim_bundle"),
                "claim_fence_master_records_transition": task.get("claim_fence_master_records_transition"),
            })
        else:
            receipt.update({
                "records_only": result.get("records_only"),
                "worker_live_after_close": result.get("worker_live_after_close"),
                "continued_authority_after_retirement": result.get("continued_authority_after_retirement"),
                "purpose_bound_worker_result": result.get("purpose_bound_worker_result"),
                "claim_fence_master_records_transition": task.get("claim_fence_master_records_transition"),
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
    raw_task = invocation.get("task") if isinstance(invocation.get("task"), Mapping) else {}
    if raw_task.get("task_id") == TEST3_TASK_ID:
        return run_test3(invocation)
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

    manifest_runtime_request = _manifest_state_transition_request(str(task["task_id"])) if profile["task_id"] == PURPOSE_TASK_ID else None
    manifest_runtime_mode = isinstance(manifest_runtime_request, Mapping)
    graph_mode = bool(
        profile["task_id"] == PURPOSE_TASK_ID
        and not manifest_runtime_mode
        and isinstance(handoff.get("state_dependent_graph"), Mapping)
        and handoff["state_dependent_graph"].get("enabled") is True
    )
    request = (
        build_manifest_bound_purpose_request(task, manifest_runtime_request)
        if manifest_runtime_mode
        else (build_state_graph_request(task, handoff) if graph_mode else build_request(task, handoff))
    )
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    completed = subprocess.run(
        [sys.executable, "-m", ("src.purpose_bound_worker_state_graph" if graph_mode else profile["runtime_module"])],
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
    if graph_mode:
        graph_warrant_bindings = validate_state_graph_result(result)
        warrant_policy_binding = {
            "graph_mode": True,
            "credential_authority": "TV/TVC",
            "worker_warrant_policy_bindings": graph_warrant_bindings,
            "all_worker_warrants_verified": all(row.get("warrant_verified") is True for row in graph_warrant_bindings),
            "all_worker_policy_bundles_verified": all(row.get("policy_bundle_verified") is True for row in graph_warrant_bindings),
        }
    else:
        _validate_result(profile, result)
        warrant_policy_binding = validate_warrant_policy_binding(result)
    receipt = retain_result(runtime_root(), task, request, result, manifest_blob_sha, warrant_policy_binding)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
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
