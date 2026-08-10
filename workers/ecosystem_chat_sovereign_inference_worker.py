#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import urllib.request

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
RECEIPT_ROOT = (ROOT / "receipts" / "ecosystem-chat-sovereign-inference").resolve()
LOCAL_PROOF_RECEIPT = RECEIPT_ROOT / "sovereign_local_model_proof.generated.json"
LIVE_MODEL_STATE = RECEIPT_ROOT / "live_model_process.json"
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
CANDIDATE_EVIDENCE = [
    Path("/var/lib/stegverse/ecosystem-chat/activation.latest.json"),
    Path.home() / ".stegverse" / "ecosystem-chat" / "activation.latest.json",
    ROOT / "runtime" / "sovereign" / "ecosystem-chat-activation.latest.json",
]
LOCAL_MODEL_PROOF_CANDIDATES = [
    Path("/var/lib/stegverse/models/sovereign_local_model_proof.generated.json"),
    Path.home() / ".stegverse" / "models" / "sovereign_local_model_proof.generated.json",
    ROOT / "runtime" / "sovereign" / "sovereign_local_model_proof.generated.json",
    LOCAL_PROOF_RECEIPT,
]
REQUIRED_TRUE = [
    "real_model_process_observed",
    "private_endpoint_only",
    "ephemeral_e1_e2_execution_observed",
    "measured_usage_persisted",
    "provider_usage_reconstruction_pass",
    "transition_reconstruction_pass",
]


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment() -> bool:
    return any(truthy(os.environ.get(name)) for name in THIRD_PARTY_ENV_VARS)


def local_runtime_roots() -> list[Path]:
    roots: list[Path] = []
    override = os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT")
    if override:
        roots.append(Path(override).expanduser().resolve())
    roots.extend(
        [
            ROOT / "workloads" / "micro-node-runtime",
            Path.home() / ".stegverse" / "workloads" / "micro-node-runtime",
            Path("/var/lib/stegverse/workloads/micro-node-runtime"),
        ]
    )
    return roots


def find_micro_node_root() -> Path | None:
    required = (
        Path("tools/verify_sovereign_model_runtime.py"),
        Path("tools/run_sovereign_model.py"),
        Path("micro_node/local_model_runtime.py"),
        Path("models/stegverse_reference_language_model.v1.json"),
        Path("models/stegverse_reference_corpus.v1.txt"),
    )
    for root in local_runtime_roots():
        if all((root / relative).is_file() for relative in required):
            return root.resolve()
    return None


def load_first_json(paths: list[Path]) -> tuple[Path | None, dict | None]:
    for path in paths:
        if not path.exists():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(value, dict):
            return path, value
    return None, None


def reference_model_proof_verified(proof: dict | None) -> bool:
    if not isinstance(proof, dict):
        return False
    predicates = proof.get("predicates") or {}
    return (
        proof.get("schema") == "stegverse.sovereign-local-model-proof/v1"
        and proof.get("state") == "VERIFIED_REFERENCE_MODEL_RUNTIME"
        and proof.get("authority_effect") == "NONE"
        and proof.get("qualifies_as_large_production_llm") is False
        and predicates.get("real_model_process_observed") is True
        and predicates.get("private_endpoint_only") is True
        and predicates.get("real_inference_response_observed") is True
        and predicates.get("measured_usage_persistable") is True
        and predicates.get("local_training_observed") is True
        and predicates.get("third_party_inference_required") is False
        and predicates.get("model_output_grants_authority") is False
    )


def live_reference_model_proof_verified(proof: dict | None) -> bool:
    if not reference_model_proof_verified(proof):
        return False
    predicates = proof.get("predicates") or {}
    endpoint = proof.get("endpoint")
    return (
        isinstance(endpoint, str)
        and endpoint.startswith(("http://127.0.0.1:", "http://localhost:", "https://127.0.0.1:", "https://localhost:"))
        and proof.get("process_owned_by_verifier") is False
        and predicates.get("live_endpoint_remains_available") is True
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _health(endpoint: str) -> dict | None:
    try:
        with urllib.request.urlopen(f"{endpoint.rstrip('/')}/health", timeout=2) as response:
            value = json.loads(response.read())
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_live_model_state() -> dict | None:
    try:
        value = json.loads(LIVE_MODEL_STATE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _terminate_pid(pid: int) -> bool:
    if not _pid_alive(pid):
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    for _ in range(20):
        if not _pid_alive(pid):
            return True
        time.sleep(0.05)
    return not _pid_alive(pid)


def retire_live_model_process(reason: str) -> dict:
    state = load_live_model_state() or {}
    pid = state.get("pid")
    terminated = True
    if isinstance(pid, int) and state.get("heartbeat_owned") is True:
        terminated = _terminate_pid(pid)
    retired = {
        **state,
        "state": "RETIRED" if terminated else "RETIRE_FAILED",
        "retired_reason": reason,
        "retired_at_heartbeat_worker": True,
        "github_token_required": False,
    }
    atomic_write(LIVE_MODEL_STATE, retired)
    return retired


def run_reference_model_verifier(root: Path, endpoint: str | None = None) -> dict:
    verifier = root / "tools" / "verify_sovereign_model_runtime.py"
    if not verifier.is_file():
        return {"attempted": False, "state": "BLOCKED", "reason": "CANONICAL_LOCAL_MODEL_VERIFIER_NOT_INSTALLED", "runtime_root": str(root)}
    command = [sys.executable, str(verifier)]
    if endpoint:
        command.extend(["--endpoint", endpoint])
    process = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        env={**os.environ, "PYTHONPATH": str(root)},
    )
    proof: dict | None = None
    if process.returncode == 0:
        try:
            candidate = json.loads(process.stdout)
        except Exception:
            candidate = None
        if isinstance(candidate, dict):
            proof = candidate
    verified = live_reference_model_proof_verified(proof) if endpoint else reference_model_proof_verified(proof)
    if verified and proof is not None:
        atomic_write(LOCAL_PROOF_RECEIPT, proof)
    return {
        "attempted": True,
        "state": "COMPLETE" if verified else "FAILED",
        "reason": "SOVEREIGN_REFERENCE_MODEL_RUNTIME_VERIFIED" if verified else "LOCAL_MODEL_RUNTIME_PROOF_FAILED",
        "returncode": process.returncode,
        "runtime_root": str(root),
        "endpoint": endpoint,
        "proof_path": str(LOCAL_PROOF_RECEIPT) if verified else None,
        "proof": proof if verified else None,
        "stdout_tail": process.stdout[-1000:] if not verified else None,
        "stderr_tail": process.stderr[-1000:] if process.stderr else None,
        "github_token_required": False,
        "third_party_execution_platform_required": False,
    }


def ensure_live_reference_model(root: Path, *, heartbeat_epoch: int, claim_id: str, fencing_token: int) -> dict:
    existing = load_live_model_state()
    if isinstance(existing, dict):
        pid = existing.get("pid")
        endpoint = existing.get("endpoint")
        if (
            existing.get("state") == "LIVE_VERIFIED"
            and isinstance(pid, int)
            and isinstance(endpoint, str)
            and _pid_alive(pid)
            and (_health(endpoint) or {}).get("state") == "READY"
        ):
            proof_path, proof = load_first_json([LOCAL_PROOF_RECEIPT])
            if live_reference_model_proof_verified(proof):
                return {"attempted": False, "state": "COMPLETE", "reason": "REUSED_LIVE_VERIFIED_MODEL_PROCESS", "runtime_root": str(root), "pid": pid, "endpoint": endpoint, "proof": proof, "proof_path": str(proof_path), "github_token_required": False}
        if isinstance(pid, int) and existing.get("heartbeat_owned") is True:
            _terminate_pid(pid)

    port = _free_port()
    endpoint = f"http://127.0.0.1:{port}"
    server = root / "tools" / "run_sovereign_model.py"
    process = subprocess.Popen(
        [sys.executable, str(server), "--host", "127.0.0.1", "--port", str(port)],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        env={**os.environ, "PYTHONPATH": str(root)},
    )
    for _ in range(60):
        if process.poll() is not None:
            return {"attempted": True, "state": "FAILED", "reason": "LIVE_MODEL_PROCESS_EXITED_EARLY", "returncode": process.returncode, "runtime_root": str(root), "github_token_required": False}
        health = _health(endpoint)
        if health and health.get("state") == "READY":
            break
        time.sleep(0.05)
    else:
        _terminate_pid(process.pid)
        return {"attempted": True, "state": "FAILED", "reason": "LIVE_MODEL_PROCESS_NOT_READY", "runtime_root": str(root), "github_token_required": False}

    proof_result = run_reference_model_verifier(root, endpoint=endpoint)
    proof = proof_result.get("proof") if isinstance(proof_result, dict) else None
    if not live_reference_model_proof_verified(proof):
        _terminate_pid(process.pid)
        return {**proof_result, "pid": process.pid, "endpoint": endpoint, "state": "FAILED", "reason": "LIVE_MODEL_ENDPOINT_PROOF_FAILED"}

    lifecycle = {
        "schema": "stegverse.sovereign-live-model-process/v0.1",
        "state": "LIVE_VERIFIED",
        "task_id": EXPECTED_TASK,
        "heartbeat_owned": True,
        "pid": process.pid,
        "endpoint": endpoint,
        "runtime_root": str(root),
        "model_id": proof.get("model_id"),
        "model_hash": proof.get("model_hash"),
        "proof_hash": proof.get("proof_hash"),
        "heartbeat_epoch_started": heartbeat_epoch,
        "claim_id": claim_id,
        "fencing_token": fencing_token,
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "release_condition": "retire after governed E1-to-model-to-E2 execution and same-execution Master Records reconstruction, or on stale/failed lease",
    }
    atomic_write(LIVE_MODEL_STATE, lifecycle)
    return {**proof_result, "pid": process.pid, "endpoint": endpoint, "lifecycle_path": str(LIVE_MODEL_STATE), "state": "COMPLETE"}


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return 4
    execution = handoff.get("execution") or {}
    required_caps = set(execution.get("required_capabilities") or [])
    for cap in ("runtime_observation", "durable_state_reconstruction", "bounded_repository_mutation"):
        if cap not in required_caps:
            return 5
    if "receipts/ecosystem-chat-sovereign-inference/**" not in set(execution.get("allowed_paths") or []):
        return 6

    evidence_path, evidence = load_first_json(CANDIDATE_EVIDENCE)
    model_proof_path, model_proof = load_first_json(LOCAL_MODEL_PROOF_CANDIDATES)
    reference_ready = live_reference_model_proof_verified(model_proof)
    runtime_root = find_micro_node_root()
    launch_result: dict | None = None

    if not reference_ready and not third_party_hosted_environment() and runtime_root is not None:
        launch_result = ensure_live_reference_model(runtime_root, heartbeat_epoch=epoch, claim_id=claim_id, fencing_token=fence)
        candidate = launch_result.get("proof") if isinstance(launch_result, dict) else None
        if live_reference_model_proof_verified(candidate):
            model_proof = candidate
            model_proof_path = LOCAL_PROOF_RECEIPT
            reference_ready = True

    passed = bool(evidence) and all(evidence.get(k) is True for k in REQUIRED_TRUE) and evidence.get("third_party_inference_required") is False
    missing = REQUIRED_TRUE if evidence is None else [k for k in REQUIRED_TRUE if evidence.get(k) is not True]
    if evidence is not None and evidence.get("third_party_inference_required") is not False:
        missing.append("third_party_inference_required=false")

    live_state = load_live_model_state()
    live_endpoint = (model_proof or {}).get("endpoint") if reference_ready else None

    if passed:
        retirement = retire_live_model_process("ECOSYSTEM_CHAT_SOVEREIGN_INFERENCE_VERIFIED")
        state = "COMPLETED"
        transition = "ECOSYSTEM_CHAT_SOVEREIGN_INFERENCE_VERIFIED"
        next_transition = None
        next_action = None
        blocker = None
    elif reference_ready:
        retirement = None
        state = "ACTIVE"
        transition = "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED"
        next_transition = "TVC_LOCAL_MODEL_ROUTE_ADMISSION"
        next_action = (
            f"Evaluate the exact live endpoint {live_endpoint} and its proof through TVC sovereign-local route authority, require ROUTE_ADMITTED "
            "with credential_requirement=NONE, then consume exactly that endpoint through StegVerseLocalHTTPProviderClient, execute governed "
            "E1-to-worker-to-E2, persist measured usage, obtain same-execution Master Records reconstruction, and only then retire the heartbeat-owned model process."
        )
        blocker = None
    elif third_party_hosted_environment():
        retirement = None
        state = "BLOCKED"
        transition = "SOVEREIGN_LOCAL_MODEL_RUNTIME_AWAITS_STEGVERSE_CARRIER"
        next_transition = "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED"
        next_action = "Execute the installed heartbeat worker on the StegVerse-owned/federated carrier; hosted runners are validation-only and may not launch the persistent production model process."
        blocker = {"dependency_class": "INTERNAL_CAPABILITY", "problem_statement": "Current invocation is on a hosted validation surface; production model lifecycle belongs to the StegVerse carrier.", "solution_required": True, "may_remain_blocked": False, "next_solution_action": next_action, "machine_observable_release_condition": "heartbeat carrier emits SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED with a live_model_process receipt", "github_token_required": False, "third_party_blocker": False}
    elif runtime_root is None:
        retirement = None
        state = "BLOCKED"
        transition = "SOVEREIGN_LOCAL_MODEL_CAPSULE_NOT_MATERIALIZED"
        next_transition = "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED"
        next_action = "Materialize the already-built micro-node-runtime capsule into a canonical StegVerse-local workload path; the heartbeat then discovers, launches, proves, leases, and retains the live endpoint automatically."
        blocker = {"dependency_class": "INTERNAL_CAPABILITY", "problem_statement": "The canonical micro-node runtime capsule is not present at a StegVerse-local workload path.", "solution_required": True, "may_remain_blocked": False, "next_solution_action": next_action, "machine_observable_release_condition": "find_micro_node_root resolves the capsule and ensure_live_reference_model emits LIVE_VERIFIED", "github_token_required": False, "third_party_blocker": False}
    else:
        retirement = None
        state = "BLOCKED"
        transition = "SOVEREIGN_LIVE_MODEL_ENDPOINT_PROOF_FAILED"
        next_transition = "SOVEREIGN_LIVE_MODEL_ENDPOINT_VERIFIED"
        next_action = "Repair the locally materialized runtime/server/verifier and re-execute on the next heartbeat cycle."
        blocker = {"dependency_class": "INTERNAL_CAPABILITY", "problem_statement": "The canonical local runtime was found but the persistent live endpoint proof did not pass.", "solution_required": True, "may_remain_blocked": False, "next_solution_action": next_action, "machine_observable_release_condition": "ensure_live_reference_model emits state COMPLETE with live_endpoint_remains_available=true", "github_token_required": False, "third_party_blocker": False}

    receipt = {
        "schema": "stegverse.ecosystem-chat-sovereign-inference-worker-receipt/v0.5",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "local_model_proof_path": str(model_proof_path) if model_proof_path else None,
        "live_model_process_path": str(LIVE_MODEL_STATE) if live_state else None,
        "live_model_endpoint": live_endpoint,
        "live_model_process": live_state,
        "local_model_runtime_root": str(runtime_root) if runtime_root else None,
        "local_model_launch_result": launch_result,
        "model_process_retirement": retirement,
        "reference_model_runtime_verified": reference_ready,
        "reference_model_is_production_scale_llm": False,
        "missing_predicates": missing,
        "next_authorized_action": next_action,
        "third_party_inference_required": False,
        "github_token_required": False,
        "github_models_required": False,
        "github_actions_production_role": False,
        "render_required": False,
        "cloudflare_required": False,
        "third_party_dependency_is_blocker": False,
        "tvc_route_authority_required": True,
        "credential_requirement": "NONE",
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "authority_effect": "none_beyond_admitted_receipt_namespace",
        "completed": passed,
    }
    atomic_write(RECEIPT_ROOT / f"{EXPECTED_TASK}.json", receipt)
    evidence_refs = ["StegVerse-org/LLM-adapter#18", "StegVerse-Labs/.github#60", "StegVerse-002/micro-node-runtime#22", "StegVerse-Labs/TVC:TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002", f"receipts/ecosystem-chat-sovereign-inference/{EXPECTED_TASK}.json", "control/blocker-resolution-policy.json"]
    if model_proof_path:
        evidence_refs.append(str(model_proof_path))
    if live_state:
        evidence_refs.append(str(LIVE_MODEL_STATE))
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 2 if reference_ready and not passed else (3 if passed else 1),
        "expected_next_transition": next_transition,
        "expected_next_earliest_epoch": None if passed else epoch + 1,
        "expected_next_latest_epoch": None if passed else epoch + 1,
        "checkpoint_ref": f"receipts/ecosystem-chat-sovereign-inference/{EXPECTED_TASK}.json",
        "evidence_refs": evidence_refs,
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 3 if launch_result and launch_result.get("attempted") else 1, "external_cost_usd": 0, "task_class": "ecosystem_chat_sovereign_inference"},
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
