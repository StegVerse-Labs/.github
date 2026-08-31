#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001"
RECEIPT_ROOT = (ROOT / "receipts" / "sovereign-base-rpc-activation").resolve()
RECEIPT = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
FORBIDDEN_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PRIVATE_KEY", "API_KEY", "GITHUB_TOKEN", "GH_TOKEN")
FORBIDDEN_COMMAND_MARKERS = ("token", "secret", "password", "private-key", "private_key", "api-key", "api_key", "bearer")


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    for key in ("STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_MICRO_NODE_ROOT"):
        explicit = os.environ.get(key, "").strip()
        if explicit:
            roots.append(Path(explicit))
    raw_repo_roots = os.environ.get("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    if raw_repo_roots:
        try:
            repo_roots = json.loads(raw_repo_roots)
        except Exception:
            repo_roots = {}
        if isinstance(repo_roots, dict):
            mapped = repo_roots.get("StegVerse-002/micro-node-runtime")
            if isinstance(mapped, str) and mapped.strip():
                roots.append(Path(mapped))
    roots.extend(
        [
            ROOT / "workloads" / "micro-node-runtime",
            Path.home() / ".stegverse" / "workloads" / "micro-node-runtime",
            Path.home() / ".stegverse" / "source" / "micro-node-runtime",
            Path("/var/lib/stegverse/workloads/micro-node-runtime"),
            Path("/var/lib/stegverse/source/micro-node-runtime"),
        ]
    )
    unique: list[Path] = []
    seen: set[str] = set()
    for path in roots:
        try:
            resolved = path.expanduser().resolve()
        except Exception:
            continue
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def find_micro_node_root() -> Path | None:
    required = (
        Path("micro_node/base_rpc_runtime.py"),
        Path("tools/run_sovereign_base_rpc.py"),
        Path("docs/SOVEREIGN_BASE_RPC_MIRROR_HANDOFF.md"),
    )
    for root in candidate_roots():
        if all((root / relative).is_file() for relative in required):
            return root
    return None


def credential_free_endpoint(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )


def credential_free_command(value: str) -> bool:
    lowered = value.lower()
    if not value.strip() or any(marker in lowered for marker in FORBIDDEN_COMMAND_MARKERS):
        return False
    if re.search(r"https?://[^\s/@]+:[^\s/@]+@", value, flags=re.IGNORECASE):
        return False
    return True


def child_env(micro_root: Path, endpoint: str | None = None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(micro_root),
        "HOME": str(Path.home()),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if endpoint:
        env["STEGVERSE_BASE_RPC_URL"] = endpoint
    return env


def proof_is_live(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    methods = value.get("method_proofs")
    return (
        value.get("schema") == "stegverse.sovereign-base-rpc-proof/v1"
        and value.get("private_endpoint") is True
        and value.get("validation_only") is False
        and str(value.get("observed_chain_id", "")).lower() == "0x2105"
        and value.get("credential_authority") == "TV/TVC"
        and value.get("credential_requirement") == "NONE"
        and value.get("github_token_required") is False
        and value.get("non_tv_tvc_secret_or_token_used") is False
        and value.get("render_required") is False
        and value.get("trade_authority") == "NONE"
        and value.get("wallet_authority") == "NONE"
        and value.get("passed") is True
        and isinstance(methods, list)
        and len(methods) >= 7
        and all(isinstance(row, dict) and row.get("passed") is True for row in methods)
    )


def response(state: str, transition: str, blocker: dict[str, Any] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "TVC_SOVEREIGN_BASE_ROUTE_ADMISSION" if state == "COMPLETED" else "SOVEREIGN_BASE_RPC_PROOF",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [str(RECEIPT.relative_to(ROOT))],
    }
    if blocker:
        value["blocker"] = blocker
    return value


def emit_blocked(epoch: int, claim_id: str, fence: int, transition: str, problem: str, release: str) -> int:
    blocker = {
        "dependency_class": "LOCAL_RUNTIME",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": release,
        "machine_observable_release_condition": release,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "third_party_blocker": False,
    }
    atomic_write(
        RECEIPT,
        {
            "schema": "stegverse.sovereign-base-rpc-activation-receipt/v1",
            "task_id": EXPECTED_TASK,
            "heartbeat_epoch": epoch,
            "claim_id": claim_id,
            "fencing_token": fence,
            "state": "BLOCKED",
            "transition_id": transition,
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_used": False,
            "render_required": False,
            "route_authority": "StegVerse-Labs/TVC",
            "trade_authority": "NONE",
            "wallet_authority": "NONE",
            "blocker": blocker,
        },
    )
    json.dump(response("BLOCKED", transition, blocker), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


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
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 4
    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    if not {"runtime_observation", "bounded_process_execution", "bounded_repository_mutation", "sovereign_base_rpc_activation"}.issubset(required):
        return 5
    if "receipts/sovereign-base-rpc-activation/**" not in set(execution.get("allowed_paths") or []):
        return 6

    for name in os.environ:
        upper = name.upper()
        if any(marker in upper for marker in FORBIDDEN_ENV_MARKERS) and name not in {"STEGVERSE_BASE_RPC_URL"}:
            # Parent environments often contain unrelated credentials. They are never inherited by children.
            continue

    micro_root = find_micro_node_root()
    if micro_root is None:
        return emit_blocked(
            epoch,
            claim_id,
            fence,
            "MICRO_NODE_RUNTIME_NOT_MATERIALIZED",
            "The released StegVerse-002/micro-node-runtime source is not present at an admitted local source/workload path.",
            "Materialize the already-released micro-node runtime through the sovereign capsule/source path; do not fetch it with GitHub credentials from this worker.",
        )

    endpoint = os.environ.get("STEGVERSE_BASE_RPC_URL", "").strip() or None
    command = os.environ.get("STEGVERSE_BASE_RPC_COMMAND", "").strip() or None
    if endpoint and not credential_free_endpoint(endpoint):
        return emit_blocked(epoch, claim_id, fence, "BASE_RPC_ENDPOINT_CREDENTIAL_INPUT_REJECTED", "The configured endpoint contains userinfo, query, fragment, or another credential-bearing form.", "Provide only a credential-free loopback/private endpoint descriptor admitted by the sovereign node runtime.")
    if command and not credential_free_command(command):
        return emit_blocked(epoch, claim_id, fence, "BASE_RPC_COMMAND_CREDENTIAL_INPUT_REJECTED", "The configured local process command contains a credential-like argument or URL userinfo.", "Use a credential-free local Base process command; TV/TVC remains the only credential authority.")

    if not endpoint:
        # Discovery is useful evidence, but no endpoint means no live proof can be claimed.
        completed = subprocess.run(
            [sys.executable, str(micro_root / "tools" / "run_sovereign_base_rpc.py"), "--discover"],
            cwd=micro_root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=child_env(micro_root),
        )
        detail = completed.stdout[-2000:] if completed.stdout else "no candidates reported"
        return emit_blocked(epoch, claim_id, fence, "REAL_BASE_RPC_ENDPOINT_NOT_CONFIGURED", "No credential-free real private Base endpoint is configured for the activation worker. Discovery completed without granting authority. " + detail, "Expose an already-running private synchronized Base endpoint through STEGVERSE_BASE_RPC_URL, or pair it with a credential-free STEGVERSE_BASE_RPC_COMMAND local process descriptor.")

    args = [sys.executable, str(micro_root / "tools" / "run_sovereign_base_rpc.py"), "--endpoint", endpoint]
    if command:
        args.extend(["--command", command, "--startup-seconds", "3"])
    completed = subprocess.run(
        args,
        cwd=micro_root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env=child_env(micro_root, endpoint),
    )
    try:
        proof = json.loads(completed.stdout)
    except Exception:
        proof = None

    if completed.returncode != 0 or not proof_is_live(proof):
        return emit_blocked(
            epoch,
            claim_id,
            fence,
            "SOVEREIGN_BASE_RPC_PROOF_NOT_LIVE",
            "The released micro-node runner did not return a passing validation_only=false Base proof for the configured private endpoint.",
            "Keep the task heartbeat-visible and retry only after the local endpoint is synchronized and the released proof contract passes all required read methods on chain 0x2105.",
        )

    durable = {
        "schema": "stegverse.sovereign-base-rpc-activation-receipt/v1",
        "task_id": EXPECTED_TASK,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "state": "COMPLETE",
        "transition_id": "SOVEREIGN_BASE_RPC_PROOF_COMPLETE",
        "endpoint": proof.get("endpoint"),
        "proof_hash": proof.get("proof_hash"),
        "observed_chain_id": proof.get("observed_chain_id"),
        "private_endpoint": True,
        "validation_only": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
        "render_required": False,
        "route_authority": "StegVerse-Labs/TVC",
        "trade_authority": "NONE",
        "wallet_authority": "NONE",
        "signed": False,
        "broadcast": False,
        "next_authorized_action": "Submit the exact endpoint/proof binding to the released TVC sovereign Base route evaluator. Do not infer ROUTE_ADMITTED here.",
        "proof": proof,
    }
    atomic_write(RECEIPT, durable)
    json.dump(response("COMPLETED", "SOVEREIGN_BASE_RPC_PROOF_COMPLETE"), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
