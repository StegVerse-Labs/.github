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
VA_RUNTIME_STATE = RECEIPT_ROOT / "va_conversational_runtime_process.json"
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
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
    "real_model_process_observed", "private_endpoint_only", "ephemeral_e1_e2_execution_observed",
    "measured_usage_persisted", "provider_usage_reconstruction_pass", "transition_reconstruction_pass",
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
    roots.extend([
        ROOT / "workloads" / "micro-node-runtime",
        Path.home() / ".stegverse" / "workloads" / "micro-node-runtime",
        Path("/var/lib/stegverse/workloads/micro-node-runtime"),
    ])
    return roots


def find_micro_node_root() -> Path | None:
    required = (
        Path("tools/verify_sovereign_model_runtime.py"), Path("tools/run_sovereign_model.py"),
        Path("micro_node/local_model_runtime.py"), Path("models/stegverse_reference_language_model.v1.json"),
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
    """Retire only for stale/failed authority or explicit shutdown.

    Successful product activation no longer retires the provider process: the
    conversational runtime must keep serving after proof has been obtained.
    """
    state = load_live_model_state() or {}
    pid = int(state.get("pid") or 0)
    retired = _terminate_pid(pid) if pid else True
    result = {
        "state": "RETIRED" if retired else "FAILED",
        "reason": reason,
        "pid": pid or None,
        "authority_effect": "NONE",
        "github_token_required": False,
    }
    atomic_write(LIVE_MODEL_STATE, result)
    return result


def _launch_persistent_reference_model(root: Path) -> dict:
    verifier = root / "tools" / "verify_sovereign_model_runtime.py"
    if not verifier.is_file():
        return {"state": "BLOCKED", "reason": "LOCAL_MODEL_VERIFIER_NOT_AVAILABLE"}
    proof_result = run_reference_model_verifier(root)
    if proof_result.get("state") != "COMPLETE":
        return proof_result
    proof = proof_result.get("proof") or {}
    if not reference_model_proof_verified(proof):
        return {"state": "BLOCKED", "reason": "REFERENCE_MODEL_PROOF_NOT_VERIFIED"}

    existing = load_live_model_state()
    if isinstance(existing, dict):
        endpoint = existing.get("endpoint")
        pid = int(existing.get("pid") or 0)
        if isinstance(endpoint, str) and _pid_alive(pid):
            health = _health(endpoint)
            if isinstance(health, dict):
                live = dict(proof)
                live.update({
                    "endpoint": endpoint,
                    "process_owned_by_verifier": False,
                    "model_id": existing.get("model_id") or "stegverse-reference-lm-v1",
                    "model_hash": existing.get("model_hash") or proof.get("model_hash"),
                    "proof_hash": existing.get("proof_hash") or proof.get("proof_hash"),
                })
                live.setdefault("predicates", {})["live_endpoint_remains_available"] = True
                return {"state": "COMPLETE", "reason": "EXISTING_LIVE_REFERENCE_MODEL_REUSED", "proof": live}

    port = _free_port()
    endpoint = f"http://127.0.0.1:{port}"
    command = [
        sys.executable,
        str(root / "tools" / "run_sovereign_model.py"),
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    log_dir = RECEIPT_ROOT
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / "sovereign_reference_model.stdout.log"
    stderr_path = log_dir / "sovereign_reference_model.stderr.log"
    stdout_handle = stdout_path.open("ab")
    stderr_handle = stderr_path.open("ab")
    process = subprocess.Popen(
        command,
        cwd=root,
        stdout=stdout_handle,
        stderr=stderr_handle,
        start_new_session=True,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(root),
            "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
        },
    )
    for _ in range(40):
        health = _health(endpoint)
        if isinstance(health, dict):
            break
        if process.poll() is not None:
            break
        time.sleep(0.05)
    else:
        health = None
    if not isinstance(health, dict):
        _terminate_pid(process.pid)
        return {"state": "BLOCKED", "reason": "REFERENCE_MODEL_ENDPOINT_NOT_LIVE"}

    live = dict(proof)
    live.update({
        "endpoint": endpoint,
        "process_owned_by_verifier": False,
        "model_id": proof.get("model_id") or "stegverse-reference-lm-v1",
        "model_hash": proof.get("model_hash"),
        "proof_hash": proof.get("proof_hash"),
    })
    live.setdefault("predicates", {})["live_endpoint_remains_available"] = True
    state = {
        "state": "LIVE",
        "pid": process.pid,
        "endpoint": endpoint,
        "model_id": live.get("model_id"),
        "model_hash": live.get("model_hash"),
        "proof_hash": live.get("proof_hash"),
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_inference_required": False,
        "authority_effect": "NONE",
    }
    atomic_write(LIVE_MODEL_STATE, state)
    return {"state": "COMPLETE", "reason": "LIVE_REFERENCE_MODEL_STARTED", "proof": live}


def run_reference_model_verifier(root: Path) -> dict:
    verifier = root / "tools" / "verify_sovereign_model_runtime.py"
    if not verifier.is_file():
        return {"state": "BLOCKED", "reason": "LOCAL_MODEL_VERIFIER_NOT_AVAILABLE"}
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(root),
        "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
    }
    try:
        proc = subprocess.run(
            [sys.executable, str(verifier)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            env=env,
        )
    except Exception as exc:
        return {"state": "BLOCKED", "reason": f"LOCAL_MODEL_VERIFIER_FAILED:{type(exc).__name__}"}
    if proc.returncode != 0:
        return {"state": "BLOCKED", "reason": "LOCAL_MODEL_VERIFIER_NONZERO", "stderr": proc.stderr[-1200:]}
    try:
        proof = json.loads(proc.stdout)
    except Exception:
        return {"state": "BLOCKED", "reason": "LOCAL_MODEL_VERIFIER_OUTPUT_INVALID"}
    if not reference_model_proof_verified(proof):
        return {"state": "BLOCKED", "reason": "LOCAL_MODEL_PROOF_INVALID"}
    atomic_write(LOCAL_PROOF_RECEIPT, proof)
    return {"state": "COMPLETE", "reason": "REFERENCE_MODEL_PROOF_VERIFIED", "proof": proof}


def activation_receipt_complete(value: dict | None) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        all(value.get(key) is True for key in REQUIRED_TRUE)
        and value.get("same_execution") is True
        and value.get("credential_authority") == "TV/TVC"
        and value.get("credential_requirement") == "NONE"
        and value.get("github_token_required") is False
        and value.get("github_actions_activation_role") is False
        and value.get("third_party_inference_required") is False
    )


def main() -> int:
    if third_party_hosted_environment():
        print(json.dumps({
            "schema": "stegverse.sovereign-inference-worker/v1",
            "task_id": EXPECTED_TASK,
            "state": "BLOCKED",
            "reason": "THIRD_PARTY_HOSTED_ENVIRONMENT_NOT_SOVEREIGN_RUNTIME",
            "credential_authority": "TV/TVC",
            "github_token_required": False,
        }, sort_keys=True))
        return 2

    evidence_path, evidence = load_first_json(CANDIDATE_EVIDENCE)
    if activation_receipt_complete(evidence):
        runtime_state = load_live_model_state()
        endpoint = runtime_state.get("endpoint") if isinstance(runtime_state, dict) else None
        pid = int(runtime_state.get("pid") or 0) if isinstance(runtime_state, dict) else 0
        if isinstance(endpoint, str) and endpoint and _pid_alive(pid) and isinstance(_health(endpoint), dict):
            result = {
                "schema": "stegverse.sovereign-inference-worker/v1",
                "task_id": EXPECTED_TASK,
                "state": "COMPLETE",
                "evidence": str(evidence_path),
                "live_model_endpoint": endpoint,
                "live_model_pid": pid,
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "third_party_inference_required": False,
                "authority_effect": "NONE",
                "runtime_persistence": "LIVE_UNTIL_STALE_AUTHORITY_OR_EXPLICIT_SHUTDOWN",
            }
            print(json.dumps(result, sort_keys=True))
            return 0
        result = {
            "schema": "stegverse.sovereign-inference-worker/v1",
            "task_id": EXPECTED_TASK,
            "state": "BLOCKED",
            "reason": "ACTIVATION_RECEIPT_PRESENT_BUT_LIVE_MODEL_NOT_SERVING",
            "evidence": str(evidence_path),
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 2

    root = find_micro_node_root()
    if root is None:
        result = {
            "schema": "stegverse.sovereign-inference-worker/v1",
            "task_id": EXPECTED_TASK,
            "state": "BLOCKED",
            "reason": "LOCAL_MODEL_RUNTIME_NOT_MATERIALIZED",
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "third_party_inference_required": False,
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 2

    launched = _launch_persistent_reference_model(root)
    if launched.get("state") != "COMPLETE":
        result = {
            "schema": "stegverse.sovereign-inference-worker/v1",
            "task_id": EXPECTED_TASK,
            "state": "BLOCKED",
            "reason": launched.get("reason"),
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "third_party_inference_required": False,
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 2

    proof = launched.get("proof") or {}
    result = {
        "schema": "stegverse.sovereign-inference-worker/v1",
        "task_id": EXPECTED_TASK,
        "state": "HANDOFF_READY",
        "reason": "LIVE_REFERENCE_MODEL_READY_FOR_TVC_ROUTE_LLM_ADAPTER_AND_MASTER_RECORDS",
        "runtime_proof": proof,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_inference_required": False,
        "authority_effect": "NONE",
        "next_transition": "TVC_ROUTE_LLM_ADAPTER_MASTER_RECORDS",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
