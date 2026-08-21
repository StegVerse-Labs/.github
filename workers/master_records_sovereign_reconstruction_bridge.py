#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

EXPECTED_SCHEMA = "stegverse.master_records.ecosystem_chat_sovereign_reconstruction/v1"
EXPECTED_TASK = "MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024"
CREDENTIAL_AUTHORITY = "TV/TVC"


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def hash_without(value: dict, key: str) -> str:
    candidate = dict(value)
    candidate.pop(key, None)
    return stable_hash(candidate)


def local_master_records_roots(root: Path) -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT")
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.extend(
        [
            (root / "workloads" / "master-records" / "orchestration").resolve(),
            (root / "workloads" / "orchestration").resolve(),
            (Path.home() / ".stegverse" / "workloads" / "master-records" / "orchestration").resolve(),
            Path("/var/lib/stegverse/workloads/master-records/orchestration"),
        ]
    )
    return candidates


def find_master_records_root(root: Path) -> Path | None:
    required = (
        Path("scripts/reconstruct_ecosystem_chat_sovereign_execution.py"),
        Path("tasks/MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024.json"),
        Path("ECOSYSTEM_CHAT_SOVEREIGN_RECONSTRUCTION_MIRROR_HANDOFF.md"),
    )
    for candidate in local_master_records_roots(root):
        if all((candidate / relative).is_file() for relative in required):
            return candidate.resolve()
    return None


def credential_free_child_env(master_records_root: Path) -> dict[str, str]:
    allowed = ("PATH", "LANG", "LC_ALL")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env["PYTHONPATH"] = str(master_records_root)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = CREDENTIAL_AUTHORITY
    return env


def reconstruction_receipt_verified(
    receipt: dict | None,
    *,
    proof: dict,
    route: dict,
    execution: dict,
) -> bool:
    if not isinstance(receipt, dict):
        return False
    usage = execution.get("provider_usage_event")
    if not isinstance(usage, dict):
        return False
    return (
        receipt.get("schema") == EXPECTED_SCHEMA
        and receipt.get("task_id") == EXPECTED_TASK
        and receipt.get("state") == "PASS"
        and receipt.get("runtime_proof_hash") == stable_hash(proof)
        and receipt.get("tvc_route_receipt_hash") == route.get("receipt_hash")
        and receipt.get("provider_usage_event_sha256") == usage.get("event_sha256")
        and receipt.get("session_id") == execution.get("session_id")
        and receipt.get("transition_id") == execution.get("transition_id")
        and receipt.get("measurement_id") == execution.get("measurement_id")
        and receipt.get("request_hash") == execution.get("request_hash")
        and receipt.get("response_hash") == execution.get("response_hash")
        and receipt.get("model_id") == execution.get("model_id")
        and receipt.get("model_hash") == execution.get("model_hash")
        and receipt.get("route_authority") == "StegVerse-Labs/TVC"
        and receipt.get("credential_authority") == CREDENTIAL_AUTHORITY
        and receipt.get("credential_requirement") == "NONE"
        and receipt.get("github_token_required") is False
        and receipt.get("third_party_execution_platform_required") is False
        and receipt.get("provider_usage_reconstruction_pass") is True
        and receipt.get("transition_reconstruction_pass") is True
        and receipt.get("same_execution") is True
        and receipt.get("execution_authority") is False
        and receipt.get("admissibility_determined") is False
        and receipt.get("authority_effect") == "NONE"
        and receipt.get("next_transition") == "ECOSYSTEM_CHAT_ZERO_BLOCKER_ACTIVATION_VERIFICATION"
        and receipt.get("reconstruction_receipt_hash") == hash_without(receipt, "reconstruction_receipt_hash")
    )


def _start_conversational_runtime_after_pass(
    *,
    proof: dict,
    route: dict,
    output_path: Path,
) -> dict[str, Any]:
    """Keep the admitted model useful after proof by starting the bounded chat gateway.

    The exact proof and route are projected into the same admitted receipt namespace.
    They are runtime inputs, not new authority. The gateway binds only to loopback;
    public HTTPS transport remains a separate admitted transport transition.
    """
    try:
        workers = Path(__file__).resolve().parent
        if str(workers) not in sys.path:
            sys.path.insert(0, str(workers))
        from llm_adapter_sovereign_execution_bridge import find_llm_adapter_root
        from va_conversational_runtime_bridge import ensure_runtime_gateway

        carrier_root = Path.cwd().resolve()
        adapter_root = find_llm_adapter_root(carrier_root)
        if adapter_root is None:
            return {
                "state": "BLOCKED",
                "reason": "VA_RUNTIME_ADAPTER_CAPSULE_NOT_MATERIALIZED",
                "github_token_required": False,
            }
        receipt_root = output_path.parent.resolve()
        proof_path = receipt_root / "va_runtime_canonical_proof.json"
        route_path = receipt_root / "va_runtime_tvc_route.json"
        state_path = receipt_root / "va_conversational_runtime_process.json"
        proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        route_path.write_text(json.dumps(route, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = ensure_runtime_gateway(
            adapter_root,
            proof_path=proof_path,
            route_path=route_path,
            state_path=state_path,
        )
        return {
            **result,
            "proof_path": str(proof_path),
            "route_path": str(route_path),
            "runtime_state_path": str(state_path),
            "authority_effect": "NONE",
            "activation_effect": False,
            "github_token_required": False,
        }
    except Exception as exc:
        return {
            "state": "FAILED",
            "reason": f"VA_RUNTIME_POST_RECONSTRUCTION_START_FAILED:{type(exc).__name__}:{exc}",
            "authority_effect": "NONE",
            "activation_effect": False,
            "github_token_required": False,
        }


def reconstruct_same_execution(
    master_records_root: Path,
    *,
    proof: dict,
    route: dict,
    execution: dict,
    output_path: Path,
) -> dict[str, Any]:
    packet = {
        "runtime_proof": proof,
        "tvc_route_receipt": route,
        "llm_adapter_execution_receipt": execution,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix="mr-reconstruction-packet-",
            suffix=".json",
            delete=False,
        ) as handle:
            json.dump(packet, handle, sort_keys=True)
            handle.write("\n")
            packet_path = Path(handle.name)

        script = master_records_root / "scripts" / "reconstruct_ecosystem_chat_sovereign_execution.py"
        process = subprocess.run(
            [sys.executable, str(script), "--packet", str(packet_path), "--output", str(output_path)],
            cwd=master_records_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=credential_free_child_env(master_records_root),
        )
        receipt: dict | None = None
        try:
            candidate = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            try:
                candidate = json.loads(process.stdout)
            except Exception:
                candidate = None
        if isinstance(candidate, dict):
            receipt = candidate
        verified = reconstruction_receipt_verified(receipt, proof=proof, route=route, execution=execution)
        runtime_result = (
            _start_conversational_runtime_after_pass(proof=proof, route=route, output_path=output_path)
            if verified else None
        )
        runtime_ready = isinstance(runtime_result, dict) and runtime_result.get("state") == "COMPLETE"
        return {
            "attempted": True,
            "state": "COMPLETE" if verified and runtime_ready else ("RECONSTRUCTED_RUNTIME_PENDING" if verified else "FAILED"),
            "reason": (
                "MASTER_RECORDS_RECONSTRUCTED_AND_VA_RUNTIME_LIVE"
                if verified and runtime_ready
                else "MASTER_RECORDS_RECONSTRUCTED_VA_RUNTIME_NOT_LIVE"
                if verified
                else "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_FAILED"
            ),
            "returncode": process.returncode,
            "master_records_root": str(master_records_root),
            "reconstruction_receipt_path": str(output_path) if verified else None,
            "reconstruction_receipt": receipt if verified else None,
            "va_conversational_runtime": runtime_result,
            "stdout_tail": None if verified else process.stdout[-1200:],
            "stderr_tail": None if verified else process.stderr[-1200:],
            "credential_authority": CREDENTIAL_AUTHORITY,
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_auth_env_forwarded": False,
            "third_party_execution_platform_required": False,
            "execution_authority": False,
            "authority_effect": "NONE",
        }
    finally:
        if packet_path is not None:
            try:
                packet_path.unlink()
            except FileNotFoundError:
                pass


__all__ = [
    "CREDENTIAL_AUTHORITY",
    "credential_free_child_env",
    "find_master_records_root",
    "hash_without",
    "local_master_records_roots",
    "reconstruct_same_execution",
    "reconstruction_receipt_verified",
    "stable_hash",
]
