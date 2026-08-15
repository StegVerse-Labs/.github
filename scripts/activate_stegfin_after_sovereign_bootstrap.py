#!/usr/bin/env python3
"""Activate the released bounded StegFin executor after sovereign proof.

This is a post-bootstrap integration adapter only. It does not acquire a StegFin
claim, select/provider credentials, contact a wallet, sign, broadcast, or claim
WALLET_HANDOFF_READY. It requires the canonical sovereign nine-predicate proof
before invoking the already-released rootless StegFin continuity service installer.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]

HOSTED_ENV_VARS = (
    "GITHUB_ACTIONS",
    "CI",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
REQUIRED_PREDICATES = (
    "runtime_materialized",
    "native_service_active",
    "continuous_runtime_live",
    "heartbeat_epoch_advanced",
    "worker_coordination_checkpoint_observed",
    "controlled_restart_observed",
    "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
)
ALLOWED_NODE_AUTHORITY_EFFECTS = {
    "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
}
SAFE_ENV_NAMES = {
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "PATH",
    "LANG",
    "LC_ALL",
    "XDG_CONFIG_HOME",
    "XDG_STATE_HOME",
    "TMPDIR",
}


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = dict(os.environ if env is None else env)
    return any(truthy(values.get(name)) for name in HOSTED_ENV_VARS)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def sovereign_proof_valid(proof: dict[str, Any] | None) -> bool:
    if not proof or proof.get("all_predicates_pass") is not True:
        return False
    return all(proof.get(name) is True for name in REQUIRED_PREDICATES)


def node_declaration_valid(node: dict[str, Any] | None) -> bool:
    if not node or node.get("declared") is not True:
        return False
    if node.get("credential_authority") != "TV/TVC":
        return False
    if node.get("github_token_required") is not False:
        return False
    if node.get("third_party_runtime_required") not in (False, None):
        return False
    if node.get("authority_effect") not in ALLOWED_NODE_AUTHORITY_EFFECTS:
        return False
    return True


def child_env(env: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    clean = {name: values[name] for name in SAFE_ENV_NAMES if values.get(name)}
    clean["STEGVERSE_POST_BOOTSTRAP_INTEGRATION"] = "1"
    return clean


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def default_proof_path() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json").resolve()


def default_node_marker() -> Path:
    return (Path.home() / ".stegverse" / "node.json").resolve()


def default_executor_activation_receipt() -> Path:
    return (Path.home() / ".stegverse" / "continuity" / "executor-activation.latest.json").resolve()


def default_integration_receipt() -> Path:
    return (Path.home() / ".stegverse" / "continuity" / "sovereign-post-bootstrap.latest.json").resolve()


def activate(
    root: Path,
    *,
    proof_path: Path,
    node_marker: Path,
    executor_activation_receipt: Path,
    integration_receipt: Path,
    env: dict[str, str] | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    proof_path = proof_path.expanduser().resolve()
    node_marker = node_marker.expanduser().resolve()
    executor_activation_receipt = executor_activation_receipt.expanduser().resolve()
    integration_receipt = integration_receipt.expanduser().resolve()

    result: dict[str, Any] = {
        "schema": "stegverse.sovereign-stegfin-post-bootstrap/v1",
        "task_id": "SOVEREIGN-STEGFIN-POST-BOOTSTRAP-001",
        "root": str(root),
        "sovereign_proof_ref": str(proof_path),
        "node_declaration_ref": str(node_marker),
        "executor_activation_receipt_ref": str(executor_activation_receipt),
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "provider_contacted": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
        "wallet_handoff_ready_claimed": False,
        "authority_effect": "SERVICE_ACTIVATION_INTEGRATION_ONLY_NO_CLAIM_ROUTE_WALLET_OR_EXECUTION_AUTHORITY",
        "installer_returncode": None,
        "executor_service_active": False,
        "state": "FAIL_CLOSED",
        "reason": None,
    }

    if hosted_environment(env):
        result["reason"] = "HOSTED_ENVIRONMENT_IS_NOT_AUTHORIZED_LOCAL_INTEGRATION_SURFACE"
        atomic_write(integration_receipt, result)
        return result

    proof = load_json(proof_path)
    if not sovereign_proof_valid(proof):
        result["reason"] = "SOVEREIGN_NINE_PREDICATE_PROOF_NOT_ESTABLISHED"
        result["missing_predicates"] = [name for name in REQUIRED_PREDICATES if not proof or proof.get(name) is not True]
        atomic_write(integration_receipt, result)
        return result

    node = load_json(node_marker)
    if not node_declaration_valid(node):
        result["reason"] = "SOVEREIGN_NODE_DECLARATION_AUTHORITY_BOUNDARY_INVALID"
        atomic_write(integration_receipt, result)
        return result

    installer = root / "scripts" / "install_stegfin_continuity_machine_service.py"
    executor = root / "scripts" / "run_stegfin_continuity_machine_executor.py"
    if not installer.is_file() or not executor.is_file():
        result["reason"] = "STEGFIN_EXECUTOR_SOURCE_INCOMPLETE"
        atomic_write(integration_receipt, result)
        return result

    cmd = [sys.executable, str(installer), "--root", str(root)]
    completed = runner(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
        env=child_env(env),
    )
    result["installer_returncode"] = completed.returncode

    activation = load_json(executor_activation_receipt)
    active = bool(
        completed.returncode == 0
        and activation
        and activation.get("active") is True
        and activation.get("credential_authority") == "TV/TVC"
        and activation.get("github_token_runtime_authority") is False
        and activation.get("non_tv_tvc_secret_or_token_embedded") is False
        and activation.get("wallet_signing_authority") == "USER_ONLY"
        and activation.get("broadcast_authority") == "USER_ONLY"
        and activation.get("execution_authority_created") is False
    )
    result["executor_service_active"] = active

    if active:
        result["state"] = "COMPLETE"
        result["reason"] = "BOUNDED_STEGFIN_EXECUTOR_SERVICE_ACTIVE_AFTER_SOVEREIGN_PROOF"
    else:
        result["state"] = "REVIEW_REQUIRED"
        result["reason"] = "STEGFIN_EXECUTOR_SERVICE_ACTIVATION_NOT_PROVEN"

    atomic_write(integration_receipt, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--proof-path", type=Path, default=None)
    parser.add_argument("--node-marker", type=Path, default=None)
    parser.add_argument("--executor-activation-receipt", type=Path, default=None)
    parser.add_argument("--integration-receipt", type=Path, default=None)
    args = parser.parse_args()

    result = activate(
        args.root,
        proof_path=(args.proof_path or default_proof_path()),
        node_marker=(args.node_marker or default_node_marker()),
        executor_activation_receipt=(args.executor_activation_receipt or default_executor_activation_receipt()),
        integration_receipt=(args.integration_receipt or default_integration_receipt()),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
