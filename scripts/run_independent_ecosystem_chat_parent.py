#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKERS = ROOT / "workers"
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from llm_adapter_sovereign_execution_bridge import execution_receipt_verified
from master_records_sovereign_reconstruction_bridge import (
    find_master_records_root,
    reconstruct_same_execution,
    reconstruction_receipt_verified,
)
from tvc_sovereign_route_bridge import route_receipt_verified

TASK_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
WORKER_ID = "ecosystem-chat-sovereign-inference-worker"
ROUTE_WORKER = WORKERS / "ecosystem_chat_sovereign_route_worker.py"
HANDOFF_PATH = Path("handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json")
FRAGMENT_PATH = Path("control/worker-registry.d/ecosystem-chat-sovereign-inference-parent-001.json")
AUTH_PATH = Path("authorizations/SHWP-ECOSYSTEM-CHAT-INFERENCE-001-independent-parent.json")
REGISTRY_PATH = Path("control/worker-registry.json")
CARRIER_PATH = Path("control/heartbeat-carrier-runtime-state.json")
RECEIPT_ROOT = Path("receipts/ecosystem-chat-sovereign-inference")
BASE_RECEIPT = RECEIPT_ROOT / f"{TASK_ID}.json"
ROUTE_RECEIPT = RECEIPT_ROOT / "tvc_local_model_route.json"
LLM_EXECUTION_RECEIPT = RECEIPT_ROOT / "llm_adapter_sovereign_execution.json"
MR_RECEIPT = RECEIPT_ROOT / "master_records_same_execution_reconstruction.json"
ACTIVATION_RECEIPT = RECEIPT_ROOT / "independent_parent_activation.latest.json"
TERMINAL_RECOVERY_FENCE = 22
MINIMUM_FENCE_EXCLUSIVE = 24
DEVICE_LOCAL_MODEL_ENDPOINT = "https://stegverse.org/stegos-bootstrap/local-model"
DEVICE_SERVICE_WORKER_SCOPE = "https://stegverse.org/stegos-bootstrap/"
NONSECRET_LOCATORS = (
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
)
SAFE_ENV = ("PATH", "LANG", "LC_ALL", "HOME")
FORBIDDEN_AUTH_ENV = {
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "RENDER_API_KEY",
    "VERCEL_TOKEN",
    "CLOUDFLARE_API_TOKEN",
}
HOSTED_MARKERS = {
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temp_name = stream.name
    os.replace(temp_name, path)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def task_by_id(registry: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    row = next((item for item in registry.get("tasks", []) if item.get("task_id") == task_id), None)
    return row if isinstance(row, dict) else None


def max_projected_fence(registry: dict[str, Any]) -> int:
    maximum = int(registry.get("generation", 0) or 0)
    for task in registry.get("tasks", []):
        if not isinstance(task, dict):
            continue
        timing = task.get("heartbeat_timing") or {}
        timer = task.get("assignment_timer") or {}
        for value in (timing.get("fencing_token"), timer.get("fencing_token")):
            if isinstance(value, int):
                maximum = max(maximum, value)
    return maximum


def current_reference_epoch(root: Path) -> tuple[int, bool]:
    path = root / CARRIER_PATH
    if not path.is_file():
        return 0, False
    try:
        state = load_json(path)
    except Exception:
        return 0, False
    epoch = state.get("epoch")
    if not isinstance(epoch, int) or epoch < 0:
        return 0, False
    return epoch, True


def clean_exec_env(source: dict[str, str] | None = None) -> dict[str, str]:
    source = source if source is not None else dict(os.environ)
    env: dict[str, str] = {}
    for name in SAFE_ENV + NONSECRET_LOCATORS:
        value = source.get(name)
        if isinstance(value, str) and value:
            env[name] = value
    env["PYTHONPATH"] = str(ROOT)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"] = "NONE"
    for name in FORBIDDEN_AUTH_ENV | HOSTED_MARKERS:
        env.pop(name, None)
    return env


def validate_registered_executor(root: Path) -> None:
    fragment = load_json(root / FRAGMENT_PATH)
    handoff = load_json(root / HANDOFF_PATH)
    auth = load_json(root / AUTH_PATH)
    task = next((row for row in fragment.get("tasks", []) if row.get("task_id") == TASK_ID), None)
    worker = next((row for row in fragment.get("workers", []) if row.get("worker_id") == WORKER_ID), None)
    if not isinstance(task, dict) or task.get("state") != "HANDOFF_READY":
        raise RuntimeError("parent registry fragment is not HANDOFF_READY")
    if task.get("executor_binding") != "AUTHORIZED":
        raise RuntimeError("parent registry fragment executor is not AUTHORIZED")
    admission = task.get("admission") or {}
    if admission.get("authority_domain") != "INDEPENDENT_TASK_CONTROL":
        raise RuntimeError("parent is not bound to independent task control")
    if admission.get("minimum_fencing_token_exclusive") != MINIMUM_FENCE_EXCLUSIVE:
        raise RuntimeError("parent current fresh-fence floor mismatch")
    if MINIMUM_FENCE_EXCLUSIVE <= TERMINAL_RECOVERY_FENCE:
        raise RuntimeError("current parent fresh-fence floor does not supersede terminal recovery provenance")
    if admission.get("heartbeat_required_for_admission") is not False:
        raise RuntimeError("heartbeat may not be an admission prerequisite")
    if admission.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant parent execution authority")
    if admission.get("g18_terminalization_required") is not False:
        raise RuntimeError("G18 terminalization may not gate parent execution")
    if admission.get("recovery_grants_parent_execution_authority") is not False:
        raise RuntimeError("recovery may not grant parent execution authority")
    if not isinstance(worker, dict) or worker.get("status") != "AVAILABLE":
        raise RuntimeError("sovereign inference worker is not AVAILABLE")
    if worker.get("adapter_ref") != "process:ecosystem-chat-sovereign-inference-v1":
        raise RuntimeError("sovereign inference worker adapter binding mismatch")
    required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if not required.issubset(set(worker.get("capabilities") or [])):
        raise RuntimeError("sovereign inference worker capabilities do not satisfy handoff")
    activation = handoff.get("activation") or {}
    if activation.get("minimum_fencing_token_exclusive") != MINIMUM_FENCE_EXCLUSIVE:
        raise RuntimeError("handoff fresh-fence floor mismatch")
    if activation.get("checkout_policy") != "fenced_atomic_checkout":
        raise RuntimeError("handoff checkout policy is not fenced_atomic_checkout")
    if auth.get("state") != "AUTHORIZED" or auth.get("authority_domain") != "INDEPENDENT_TASK_CONTROL":
        raise RuntimeError("independent parent authorization is not active")
    if auth.get("minimum_fencing_token_exclusive") != MINIMUM_FENCE_EXCLUSIVE:
        raise RuntimeError("authorization fresh-fence floor mismatch")
    if auth.get("github_token_required") is not False or auth.get("render_required") is not False:
        raise RuntimeError("authorization introduces prohibited hosted authority")
    if auth.get("recovery_reacquisition_allowed") is not False:
        raise RuntimeError("authorization permits terminal recovery reacquisition")
    if not (root / ROUTE_WORKER.relative_to(ROOT)).is_file():
        raise RuntimeError("canonical sovereign route worker is missing")


def _replace_task(registry: dict[str, Any], replacement: dict[str, Any]) -> None:
    tasks = registry.setdefault("tasks", [])
    for index, row in enumerate(tasks):
        if isinstance(row, dict) and row.get("task_id") == TASK_ID:
            tasks[index] = json.loads(json.dumps(replacement))
            return
    tasks.append(json.loads(json.dumps(replacement)))


def project_claimable_parent(registry: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    current = task_by_id(registry, TASK_ID)
    if isinstance(current, dict):
        current_timing = current.get("heartbeat_timing") or {}
        current_fence = current_timing.get("fencing_token")
        if current.get("claim_id") or current.get("worker_id"):
            if isinstance(current_fence, int) and current_fence > MINIMUM_FENCE_EXCLUSIVE:
                raise RuntimeError("a current or newer parent claim already exists")
            raise RuntimeError("parent has unreleased historical claim state")
    projected = next((row for row in fragment.get("tasks", []) if row.get("task_id") == TASK_ID), None)
    if not isinstance(projected, dict):
        raise RuntimeError("parent registry fragment task missing")
    if projected.get("state") != "HANDOFF_READY" or projected.get("claim_id") is not None:
        raise RuntimeError("parent registry fragment is not atomically claimable")
    _replace_task(registry, projected)
    return task_by_id(registry, TASK_ID) or {}


def acquire_parent_claim(
    registry: dict[str, Any],
    fragment: dict[str, Any],
    *,
    reference_epoch: int,
) -> tuple[dict[str, Any], int]:
    task = project_claimable_parent(registry, fragment)
    fence = max(MINIMUM_FENCE_EXCLUSIVE, max_projected_fence(registry)) + 1
    claim_id = f"SHWP-{TASK_ID}-G{fence}"
    worker_instance_id = f"{WORKER_ID}-REF{reference_epoch}-G{fence}"
    registry["generation"] = fence
    task.update(
        {
            "state": "ACTIVE",
            "executor_binding": "BOUND",
            "worker_id": WORKER_ID,
            "worker_instance_id": worker_instance_id,
            "claim_id": claim_id,
            "archive_eligible": False,
            "archive_reason_codes": [],
            "block_ref": None,
            "lease": None,
            "heartbeat_timing": {
                "start_epoch": reference_epoch,
                "last_response_epoch": reference_epoch,
                "last_transition_epoch": reference_epoch,
                "current_transition": "INDEPENDENT_PARENT_EXECUTION",
                "transition_sequence": 0,
                "expected_next_transition": "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED",
                "expected_next_earliest_epoch": None,
                "expected_next_latest_epoch": None,
                "expiry_epoch": None,
                "expiry_basis": "BOUNDED_INDEPENDENT_TASK_CONTROL_ATTEMPT",
                "fencing_token": fence,
            },
            "independent_task_control": {
                "authority_domain": "INDEPENDENT_TASK_CONTROL",
                "authorization_ref": str(AUTH_PATH),
                "heartbeat_reference_only": True,
                "heartbeat_granted_authority": False,
                "g18_authority_used": False,
                "g20_authority_reused": False,
                "g22_recovery_authority_reused": False,
                "recovery_reacquired": False,
            },
        }
    )
    return task, fence


def release_parent_claim(
    registry: dict[str, Any],
    *,
    response_state: str,
    transition_id: str,
    evidence_refs: list[str],
    terminal_verified: bool = False,
) -> dict[str, Any]:
    task = task_by_id(registry, TASK_ID)
    if not isinstance(task, dict):
        raise RuntimeError("parent task missing during release")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not isinstance(fence, int) or fence <= MINIMUM_FENCE_EXCLUSIVE:
        raise RuntimeError(f"cannot release parent without fresh fence >{MINIMUM_FENCE_EXCLUSIVE}")
    if response_state == "COMPLETED" and terminal_verified is not True:
        raise RuntimeError("parent completion requires independently verified terminal evidence")

    task.setdefault("evidence_refs", [])
    for ref in evidence_refs:
        if ref not in task["evidence_refs"]:
            task["evidence_refs"].append(ref)
    task.setdefault("transition_history", []).append(
        {
            "response_state": response_state,
            "transition_id": transition_id,
            "released_claim_id": claim_id,
            "released_fencing_token": fence,
            "authority_effect": "NONE_AFTER_BOUNDED_ATTEMPT",
        }
    )
    if response_state == "COMPLETED":
        task["state"] = "COMPLETED"
        task["executor_binding"] = "UNBOUND"
        task["archive_eligible"] = True
        task["archive_reason_codes"] = []
        task["block_ref"] = None
    else:
        task["state"] = "HANDOFF_READY"
        task["executor_binding"] = "AUTHORIZED"
        task["archive_eligible"] = False
        task["archive_reason_codes"] = [f"LAST_ATTEMPT_{transition_id}"]
        task["block_ref"] = None
    task["worker_id"] = None
    task["worker_instance_id"] = None
    task["claim_id"] = None
    task["lease"] = None
    task["heartbeat_timing"] = None
    task["independent_task_control"] = {
        "last_released_claim_id": claim_id,
        "last_released_fencing_token": fence,
        "heartbeat_granted_authority": False,
        "g18_authority_used": False,
        "g20_authority_reused": False,
        "g22_recovery_authority_reused": False,
        "recovery_reacquired": False,
        "terminal_verified": terminal_verified,
    }
    return task


def _ignored_snapshot_path(relative: str) -> bool:
    return (
        relative.startswith(".git/")
        or "/__pycache__/" in f"/{relative}"
        or relative.endswith(".pyc")
        or relative == REGISTRY_PATH.as_posix()
        or relative.startswith(RECEIPT_ROOT.as_posix() + "/")
    )


def snapshot_protected_tree(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if _ignored_snapshot_path(relative):
            continue
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def assert_protected_tree_unchanged(before: dict[str, str], after: dict[str, str]) -> None:
    if before != after:
        changed = sorted(set(before) | set(after))
        changed = [path for path in changed if before.get(path) != after.get(path)]
        raise RuntimeError(f"independent parent worker mutated out-of-scope repository paths: {changed[:20]}")


def invoke_route_worker(root: Path, task: dict[str, Any], handoff: dict[str, Any], epoch: int) -> dict[str, Any]:
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": epoch,
        "task": task,
        "handoff": handoff,
    }
    process = subprocess.run(
        [sys.executable, str(root / ROUTE_WORKER.relative_to(ROOT))],
        input=json.dumps(invocation),
        cwd=root,
        capture_output=True,
        text=True,
        timeout=150,
        check=False,
        env=clean_exec_env(),
    )
    if process.returncode != 0:
        raise RuntimeError(f"sovereign route worker failed rc={process.returncode}: {process.stderr[-1200:]}")
    try:
        response = json.loads(process.stdout)
    except Exception as exc:
        raise RuntimeError("sovereign route worker returned invalid JSON") from exc
    if not isinstance(response, dict) or response.get("schema") != "stegverse.worker-response/v0.1":
        raise RuntimeError("sovereign route worker returned invalid response schema")
    return response


def load_terminal_chain(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = load_json(root / BASE_RECEIPT)
    proof_path_raw = base.get("local_model_proof_path")
    if not isinstance(proof_path_raw, str):
        raise RuntimeError("base receipt does not bind a local-model proof path")
    proof_path = Path(proof_path_raw)
    if not proof_path.is_absolute():
        proof_path = (root / proof_path).resolve()
    proof = load_json(proof_path)
    route = load_json(root / ROUTE_RECEIPT)
    execution = load_json(root / LLM_EXECUTION_RECEIPT)
    if not route_receipt_verified(route, proof, str(base.get("live_model_endpoint") or "")):
        raise RuntimeError("TVC route receipt does not verify against live model proof")
    if not execution_receipt_verified(execution, proof=proof, route=route):
        raise RuntimeError("LLM-adapter execution receipt does not verify against proof and route")
    return base, proof, route, execution


def classify_sovereign_runtime_surface(proof: dict[str, Any]) -> dict[str, Any]:
    predicates = proof.get("predicates") or {}
    process_observed = predicates.get("real_model_process_observed") is True
    private_only = predicates.get("private_endpoint_only") is True
    browser_observed = predicates.get("browser_service_worker_runtime_observed") is True
    device_intercepted = predicates.get("device_local_intercepted_endpoint") is True
    no_network_egress = predicates.get("network_egress_required") is False
    inference_observed = predicates.get("real_inference_response_observed") is True
    process_path = process_observed and private_only
    device_path = (
        browser_observed
        and device_intercepted
        and no_network_egress
        and inference_observed
        and proof.get("endpoint_transport") == "SERVICE_WORKER_LOCAL_INTERCEPT"
        and str(proof.get("endpoint") or "").rstrip("/") == DEVICE_LOCAL_MODEL_ENDPOINT
        and str(proof.get("service_worker_scope") or "") == DEVICE_SERVICE_WORKER_SCOPE
    )
    if process_path:
        runtime_surface = "PRIVATE_PROCESS"
    elif device_path:
        runtime_surface = "CURRENT_USER_IPHONE_SERVICE_WORKER"
    else:
        runtime_surface = "UNVERIFIED"
    return {
        "sovereign_runtime_execution_surface_observed": process_path or device_path,
        "runtime_execution_surface": runtime_surface,
        "real_model_process_observed": process_observed,
        "private_endpoint_only": private_only,
        "browser_service_worker_runtime_observed": browser_observed,
        "device_local_intercepted_endpoint": device_intercepted,
        "network_egress_required": predicates.get("network_egress_required"),
        "device_local_runtime_observed": device_path,
    }


def finalize_same_execution(root: Path, task: dict[str, Any], epoch: int) -> tuple[bool, dict[str, Any]]:
    base, proof, route, execution = load_terminal_chain(root)
    mr_root = find_master_records_root(root)
    if mr_root is None:
        return False, {
            "state": "HANDOFF_READY",
            "transition_id": "MASTER_RECORDS_LOCAL_CAPSULE_NOT_MATERIALIZED",
            "problem_statement": "Canonical master-records/orchestration reconstruction capsule is not materialized on this StegVerse execution surface.",
        }
    reconstruction_result = reconstruct_same_execution(
        mr_root,
        proof=proof,
        route=route,
        execution=execution,
        output_path=(root / MR_RECEIPT).resolve(),
    )
    reconstruction = reconstruction_result.get("reconstruction_receipt") if isinstance(reconstruction_result, dict) else None
    verified = reconstruction_receipt_verified(reconstruction, proof=proof, route=route, execution=execution)
    runtime = reconstruction_result.get("va_conversational_runtime") if isinstance(reconstruction_result, dict) else None
    runtime_ready = isinstance(runtime, dict) and runtime.get("state") == "COMPLETE"
    terminal = bool(verified and runtime_ready and reconstruction_result.get("state") == "COMPLETE")
    if not terminal:
        return False, {
            "state": "HANDOFF_READY",
            "transition_id": "MASTER_RECORDS_RECONSTRUCTED_RUNTIME_PENDING" if verified else "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_FAILED",
            "reconstruction_result": reconstruction_result,
        }

    runtime_surface = classify_sovereign_runtime_surface(proof)
    activation = {
        "schema": "stegverse.ecosystem-chat-independent-parent-activation/v1",
        "task_id": TASK_ID,
        "claim_id": task.get("claim_id"),
        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
        "heartbeat_reference_epoch": epoch,
        "heartbeat_reference_is_causal": False,
        "state": "PASS",
        "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
        **runtime_surface,
        "ephemeral_e1_e2_execution_observed": execution.get("state") == "EXECUTED",
        "measured_usage_persisted": isinstance(execution.get("measured_usage"), dict),
        "provider_usage_reconstruction_pass": reconstruction.get("provider_usage_reconstruction_pass") is True,
        "transition_reconstruction_pass": reconstruction.get("transition_reconstruction_pass") is True,
        "same_execution": reconstruction.get("same_execution") is True,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_actions_activation_role": False,
        "third_party_inference_required": False,
        "persistent_conversational_runtime_ready": runtime_ready,
        "runtime_proof_hash": stable_hash(proof),
        "tvc_route_receipt_hash": route.get("receipt_hash"),
        "provider_usage_event_sha256": (execution.get("provider_usage_event") or {}).get("event_sha256"),
        "reconstruction_receipt_hash": reconstruction.get("reconstruction_receipt_hash"),
        "authority_effect": "NONE_BEYOND_ADMITTED_PARENT_TASK_CONTROL",
    }
    required_true = (
        "sovereign_runtime_execution_surface_observed",
        "ephemeral_e1_e2_execution_observed",
        "measured_usage_persisted",
        "provider_usage_reconstruction_pass",
        "transition_reconstruction_pass",
        "same_execution",
        "persistent_conversational_runtime_ready",
    )
    if not all(activation.get(key) is True for key in required_true):
        raise RuntimeError("terminal activation predicates are not all satisfied")
    activation["activation_receipt_hash"] = stable_hash(activation)
    atomic_write(root / ACTIVATION_RECEIPT, activation)

    base.update(
        {
            "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.9",
            "transition_id": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED",
            "completed": True,
            **runtime_surface,
            "ephemeral_e1_e2_execution_observed": True,
            "measured_usage_persisted": True,
            "provider_usage_reconstruction_pass": True,
            "transition_reconstruction_pass": True,
            "same_execution": True,
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_actions_production_role": False,
            "third_party_inference_required": False,
            "master_records_reconstruction_receipt_path": str(MR_RECEIPT),
            "independent_parent_activation_receipt_path": str(ACTIVATION_RECEIPT),
            "persistent_conversational_runtime_ready": True,
            "next_authorized_action": None,
            "blocker": None,
        }
    )
    atomic_write(root / BASE_RECEIPT, base)
    return True, activation


def release_attempt_guarded(
    root: Path,
    *,
    registry_path: Path,
    before: dict[str, str],
    response_state: str,
    transition_id: str,
    evidence_refs: list[str],
    terminal_verified: bool,
) -> BaseException | None:
    """Always release bounded parent authority, even when scope validation fails.

    A worker scope violation remains fatal and is returned to the caller for
    re-raising after the claim has been durably released. This prevents a
    fail-closed mutation denial from accidentally stranding a live claim/fence.
    """
    scope_error: BaseException | None = None
    try:
        after = snapshot_protected_tree(root)
        assert_protected_tree_unchanged(before, after)
    except BaseException as exc:
        scope_error = exc
        response_state = "HANDOFF_READY"
        transition_id = "OUT_OF_SCOPE_MUTATION_DENIED"
        terminal_verified = False

    registry = load_json(registry_path)
    release_parent_claim(
        registry,
        response_state=response_state,
        transition_id=transition_id,
        evidence_refs=evidence_refs,
        terminal_verified=terminal_verified,
    )
    atomic_write(registry_path, registry)
    return scope_error


def execute_once(root: Path, *, reference_epoch: int | None = None) -> dict[str, Any]:
    validate_registered_executor(root)
    registry_path = root / REGISTRY_PATH
    registry = load_json(registry_path)
    fragment = load_json(root / FRAGMENT_PATH)
    handoff = load_json(root / HANDOFF_PATH)
    if reference_epoch is None:
        epoch, reference_observed = current_reference_epoch(root)
    else:
        epoch, reference_observed = int(reference_epoch), True
    task, fence = acquire_parent_claim(registry, fragment, reference_epoch=epoch)
    atomic_write(registry_path, registry)

    before = snapshot_protected_tree(root)
    evidence_refs: list[str] = []
    terminal_verified = False
    transition_id = "INDEPENDENT_PARENT_EXECUTOR_ERROR"
    response_state = "HANDOFF_READY"
    route_response: dict[str, Any] | None = None
    terminal_receipt: dict[str, Any] | None = None
    execution_error: BaseException | None = None

    try:
        route_response = invoke_route_worker(root, task, handoff, epoch)
        transition_id = str(route_response.get("transition_id") or "UNKNOWN_PARENT_TRANSITION")
        evidence_refs.extend(str(ref) for ref in route_response.get("evidence_refs") or [] if isinstance(ref, str))
        if transition_id == "LLM_ADAPTER_SAME_ENDPOINT_EXECUTED":
            terminal_verified, terminal_receipt = finalize_same_execution(root, task, epoch)
            if terminal_verified:
                response_state = "COMPLETED"
                transition_id = "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTED"
                evidence_refs.extend([str(MR_RECEIPT), str(ACTIVATION_RECEIPT), str(BASE_RECEIPT)])
            else:
                response_state = "HANDOFF_READY"
                transition_id = str((terminal_receipt or {}).get("transition_id") or transition_id)
    except BaseException as exc:
        execution_error = exc
        response_state = "HANDOFF_READY"
        transition_id = f"INDEPENDENT_PARENT_EXECUTOR_ERROR_{type(exc).__name__}"
        terminal_verified = False

    scope_error: BaseException | None = None
    release_error: BaseException | None = None
    try:
        scope_error = release_attempt_guarded(
            root,
            registry_path=registry_path,
            before=before,
            response_state=response_state,
            transition_id=transition_id,
            evidence_refs=evidence_refs,
            terminal_verified=terminal_verified,
        )
    except BaseException as exc:
        release_error = exc

    if release_error is not None:
        if scope_error is not None:
            raise RuntimeError("parent claim release failed after scope violation") from release_error
        if execution_error is not None:
            raise RuntimeError("parent claim release failed after execution error") from release_error
        raise release_error
    if scope_error is not None:
        raise scope_error
    if execution_error is not None:
        raise execution_error

    return {
        "schema": "stegverse.independent-ecosystem-chat-parent-execution/v1",
        "task_id": TASK_ID,
        "attempt_fencing_token": fence,
        "heartbeat_reference_epoch": epoch,
        "heartbeat_reference_observed": reference_observed,
        "heartbeat_reference_is_causal": False,
        "state": "COMPLETED" if terminal_verified else "HANDOFF_READY",
        "transition_id": transition_id,
        "route_worker_response": route_response,
        "terminal_activation_receipt": terminal_receipt if terminal_verified else None,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_actions_activation_role": False,
        "render_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "BOUNDED_PARENT_TASK_CONTROL_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one independently admitted Ecosystem Chat parent attempt.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--reference-epoch", type=int, default=None)
    args = parser.parse_args()
    result = execute_once(Path(args.root).resolve(), reference_epoch=args.reference_epoch)
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result.get("state") in {"COMPLETED", "HANDOFF_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
