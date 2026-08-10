#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

AUTH_ENV = {
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "MASTER_RECORDS_AUTH_TOKEN",
    "MASTER_RECORDS_RECEIPT_KEY",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
}


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
            (Path.home() / ".stegverse" / "workloads" / "orchestration").resolve(),
            Path("/var/lib/stegverse/workloads/master-records/orchestration"),
            Path("/var/lib/stegverse/workloads/orchestration"),
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
    env = {key: value for key, value in os.environ.items() if key not in AUTH_ENV}
    env["PYTHONPATH"] = str(master_records_root)
    env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"] = "NONE"
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "StegVerse-Labs/TV+TVC"
    env["STEGVERSE_MASTER_RECORDS_RECONSTRUCTION_MODE"] = "CREDENTIAL_FREE_LOCAL"
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
    expected_receipt_hash = hash_without(receipt, "reconstruction_receipt_hash")
    return (
        receipt.get("schema") == "stegverse.master_records.ecosystem_chat_sovereign_reconstruction/v1"
        and receipt.get("task_id") == "MR-ECOSYSTEM-CHAT-SOVEREIGN-RECONSTRUCTION-024"
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
        and receipt.get("credential_authority") == "StegVerse-Labs/TV+TVC"
        and receipt.get("credential_requirement") == "NONE"
        and receipt.get("github_token_required") is False
        and receipt.get("third_party_execution_platform_required") is False
        and receipt.get("provider_usage_reconstruction_pass") is True
        and receipt.get("transition_reconstruction_pass") is True
        and receipt.get("same_execution") is True
        and receipt.get("execution_authority") is False
        and receipt.get("admissibility_determined") is False
        and receipt.get("authority_effect") == "NONE"
        and receipt.get("reconstruction_receipt_hash") == expected_receipt_hash
    )


def execute_reconstruction(
    master_records_root: Path,
    *,
    proof: dict,
    route: dict,
    execution: dict,
    packet_path: Path,
    output_path: Path,
) -> dict:
    packet = {
        "runtime_proof": proof,
        "tvc_route_receipt": route,
        "llm_adapter_execution_receipt": execution,
    }
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(master_records_root / "scripts" / "reconstruct_ecosystem_chat_sovereign_execution.py"),
        "--packet",
        str(packet_path),
        "--output",
        str(output_path),
    ]
    process = subprocess.run(
        command,
        cwd=master_records_root,
        capture_output=True,
        text=True,
        timeout=60,
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
    return {
        "attempted": True,
        "state": "COMPLETE" if verified else "FAILED",
        "reason": "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_PASS" if verified else "MASTER_RECORDS_SAME_EXECUTION_RECONSTRUCTION_FAILED",
        "returncode": process.returncode,
        "master_records_root": str(master_records_root),
        "packet_path": str(packet_path),
        "reconstruction_receipt_path": str(output_path) if verified else None,
        "reconstruction_receipt": receipt if verified else None,
        "stdout_tail": None if verified else process.stdout[-1200:],
        "stderr_tail": None if verified else process.stderr[-1200:],
        "credential_requirement": "NONE",
        "credential_authority": "StegVerse-Labs/TV+TVC",
        "github_token_required": False,
        "github_auth_env_forwarded": False,
        "master_records_bearer_auth_forwarded": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
        "authority_effect": "NONE",
    }


__all__ = [
    "AUTH_ENV",
    "credential_free_child_env",
    "execute_reconstruction",
    "find_master_records_root",
    "hash_without",
    "local_master_records_roots",
    "reconstruction_receipt_verified",
    "stable_hash",
]
