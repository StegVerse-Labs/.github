#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def local_tvc_roots(root: Path) -> list[Path]:
    values: list[Path] = []
    override = os.environ.get("STEGVERSE_TVC_ROOT")
    if override:
        values.append(Path(override).expanduser().resolve())
    values.extend(
        [
            root / "workloads" / "TVC",
            Path.home() / ".stegverse" / "workloads" / "TVC",
            Path("/var/lib/stegverse/workloads/TVC"),
        ]
    )
    return values


def find_tvc_root(root: Path) -> Path | None:
    required = (
        Path("scripts/evaluate_sovereign_local_model_route.py"),
        Path("tvc_sovereign_local_model_route.py"),
        Path("tasks/TVC-SOVEREIGN-LOCAL-MODEL-ROUTE-002.json"),
    )
    for candidate in local_tvc_roots(root):
        if all((candidate / relative).is_file() for relative in required):
            return candidate.resolve()
    return None


def route_receipt_verified(receipt: dict | None, proof: dict | None, endpoint: str | None) -> bool:
    if not isinstance(receipt, dict) or not isinstance(proof, dict) or not isinstance(endpoint, str):
        return False
    return (
        receipt.get("state") == "ROUTE_ADMITTED"
        and receipt.get("route_authority") == "StegVerse-Labs/TVC"
        and receipt.get("endpoint") == endpoint
        and receipt.get("runtime_proof_hash") == stable_hash(proof)
        and receipt.get("credential_requirement") == "NONE"
        and receipt.get("github_token_required") is False
        and receipt.get("third_party_execution_platform_required") is False
        and receipt.get("execution_authority") is False
        and receipt.get("authority_effect") == "NONE"
        and receipt.get("canonical_micro_node_proof_consumed") is True
    )


def evaluate_route(
    tvc_root: Path,
    *,
    proof_path: Path,
    proof: dict,
    endpoint: str,
    output_path: Path,
) -> dict:
    cli = tvc_root / "scripts" / "evaluate_sovereign_local_model_route.py"
    if not cli.is_file():
        return {
            "attempted": False,
            "state": "BLOCKED",
            "reason": "TVC_SOVEREIGN_ROUTE_CLI_NOT_INSTALLED",
            "github_token_required": False,
        }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--proof",
            str(proof_path),
            "--endpoint",
            endpoint,
            "--output",
            str(output_path),
        ],
        cwd=tvc_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={**os.environ, "PYTHONPATH": str(tvc_root)},
    )
    receipt: dict | None = None
    if output_path.is_file():
        try:
            candidate = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            candidate = None
        if isinstance(candidate, dict):
            receipt = candidate
    verified = process.returncode == 0 and route_receipt_verified(receipt, proof, endpoint)
    return {
        "attempted": True,
        "state": "COMPLETE" if verified else "FAILED",
        "reason": "TVC_LOCAL_MODEL_ROUTE_ADMITTED" if verified else "TVC_LOCAL_MODEL_ROUTE_NOT_ADMITTED",
        "returncode": process.returncode,
        "tvc_root": str(tvc_root),
        "endpoint": endpoint,
        "route_receipt_path": str(output_path) if verified else None,
        "route_receipt": receipt if verified else None,
        "stdout_tail": process.stdout[-1000:] if not verified else None,
        "stderr_tail": process.stderr[-1000:] if process.stderr else None,
        "credential_requirement": "NONE",
        "github_token_required": False,
        "third_party_execution_platform_required": False,
        "execution_authority": False,
    }


__all__ = [
    "evaluate_route",
    "find_tvc_root",
    "local_tvc_roots",
    "route_receipt_verified",
    "stable_hash",
]
