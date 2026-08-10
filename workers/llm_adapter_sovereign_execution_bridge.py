#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

GITHUB_AUTH_ENV = {
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
}


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def local_llm_adapter_roots(root: Path) -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("STEGVERSE_LLM_ADAPTER_ROOT")
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.extend(
        [
            (root / "workloads" / "LLM-adapter").resolve(),
            (Path.home() / ".stegverse" / "workloads" / "LLM-adapter").resolve(),
            Path("/var/lib/stegverse/workloads/LLM-adapter"),
        ]
    )
    return candidates


def find_llm_adapter_root(root: Path) -> Path | None:
    required = (
        Path("scripts/execute_canonical_sovereign_route.py"),
        Path("llm_adapter/sovereign_local_model_binding.py"),
        Path("llm_adapter/http_provider_clients.py"),
        Path("tasks/LLMA-SOVEREIGN-CARRIER-EXECUTION-020.json"),
        Path("LLM_ADAPTER_MIRROR_HANDOFF.md"),
    )
    for candidate in local_llm_adapter_roots(root):
        if all((candidate / relative).is_file() for relative in required):
            return candidate.resolve()
    return None


def credential_free_child_env(adapter_root: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in GITHUB_AUTH_ENV}
    env["PYTHONPATH"] = str(adapter_root)
    env["STEGVERSE_LOCAL_MODEL_CREDENTIAL_REQUIREMENT"] = "NONE"
    env["STEGVERSE_TC_TVC_CREDENTIAL_AUTHORITY"] = "TC/TVC"
    return env


def execution_receipt_verified(receipt: dict | None, *, proof: dict, route: dict) -> bool:
    if not isinstance(receipt, dict):
        return False
    return (
        receipt.get("schema") == "stegverse.llm_adapter.canonical_sovereign_route_execution/v1"
        and receipt.get("state") == "EXECUTED"
        and receipt.get("route_authority") == "StegVerse-Labs/TVC"
        and receipt.get("route_receipt_hash") == route.get("receipt_hash")
        and receipt.get("runtime_proof_hash") == stable_hash(proof)
        and receipt.get("credential_requirement") == "NONE"
        and receipt.get("github_token_required") is False
        and receipt.get("third_party_execution_platform_required") is False
        and receipt.get("execution_authority") is False
        and receipt.get("authority_effect") == "NONE"
        and isinstance(receipt.get("measured_usage"), dict)
    )


def execute_admitted_route(
    adapter_root: Path,
    *,
    proof_path: Path,
    route_path: Path,
    proof: dict,
    route: dict,
    session_id: str,
    transition_id: str,
    measurement_id: str,
    output_path: Path,
) -> dict:
    script = adapter_root / "scripts" / "execute_canonical_sovereign_route.py"
    command = [
        sys.executable,
        str(script),
        "--proof",
        str(proof_path),
        "--route",
        str(route_path),
        "--session-id",
        session_id,
        "--transition-id",
        transition_id,
        "--measurement-id",
        measurement_id,
        "--output",
        str(output_path),
    ]
    process = subprocess.run(
        command,
        cwd=adapter_root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=credential_free_child_env(adapter_root),
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
    verified = execution_receipt_verified(receipt, proof=proof, route=route)
    return {
        "attempted": True,
        "state": "COMPLETE" if verified else "FAILED",
        "reason": "LLM_ADAPTER_SAME_ENDPOINT_EXECUTED" if verified else "LLM_ADAPTER_SAME_ENDPOINT_EXECUTION_FAILED",
        "returncode": process.returncode,
        "adapter_root": str(adapter_root),
        "execution_receipt_path": str(output_path) if verified else None,
        "execution_receipt": receipt if verified else None,
        "stdout_tail": None if verified else process.stdout[-1200:],
        "stderr_tail": None if verified else process.stderr[-1200:],
        "credential_requirement": "NONE",
        "credential_authority": "TC/TVC",
        "github_token_required": False,
        "github_auth_env_forwarded": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
    }


__all__ = [
    "credential_free_child_env",
    "execute_admitted_route",
    "execution_receipt_verified",
    "find_llm_adapter_root",
    "local_llm_adapter_roots",
    "stable_hash",
]
