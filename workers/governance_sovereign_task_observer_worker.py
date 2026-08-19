#!/usr/bin/env python3
"""One-shot sovereign observer for Governance repository task state."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

TASK_ID = "GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001"
WORKER_ID = "governance-sovereign-task-observer-worker"
ROOT_ENV = "STEGVERSE_GOVERNANCE_SOURCE_ROOT"
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GIT_ASKPASS",
    "GOOGLE_ACCESS_TOKEN", "GOOGLE_REFRESH_TOKEN", "OAUTH_TOKEN",
)
REQUIRED_SOURCE_FILES = (
    Path("GOVERNANCE_MIRROR_HANDOFF.md"),
    Path("automation/governance_task_registry.json"),
    Path("scripts/run_governance_tasks.py"),
    Path("docs/governance/CGE_DECISION_ISSUER_ARCHITECTURE_MIRROR_HANDOFF.md"),
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if path.is_file():
            node = read_json(path)
            if node.get("declared") is not True:
                raise RuntimeError("sovereign node is not declared")
            if node.get("credential_authority") != "TV/TVC":
                raise RuntimeError("credential authority must be TV/TVC")
            if node.get("github_token_required") is not False:
                raise RuntimeError("sovereign observer may not require GitHub token")
            return path, node
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> None:
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    authority = (invocation.get("handoff") or {}).get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("handoff credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("handoff may not require GitHub token")
    if authority.get("non_tv_tvc_secret_or_token_allowed") is not False:
        raise RuntimeError("handoff permits non-TV/TVC secret/token")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("observer may not write back to Governance repository")
    if authority.get("heartbeat_authority") is not False:
        raise RuntimeError("observer may not have heartbeat authority")


def local_governance_roots() -> list[Path]:
    roots: list[Path] = []
    explicit = str(os.getenv(ROOT_ENV) or "").strip()
    if explicit:
        roots.append(Path(explicit))
    roots.extend([
        Path.cwd() / "workloads" / "Governance",
        Path.cwd() / "workloads" / "governance",
        Path.home() / ".stegverse" / "workloads" / "Governance",
        Path.home() / ".stegverse" / "workloads" / "governance",
        Path("/var/lib/stegverse/workloads/Governance"),
        Path("/var/lib/stegverse/workloads/governance"),
        Path.home() / ".stegverse" / "source" / "Governance",
        Path.home() / ".stegverse" / "source" / "governance",
        Path("/var/lib/stegverse/source/Governance"),
        Path("/var/lib/stegverse/source/governance"),
    ])
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in roots:
        try:
            key = str(candidate.expanduser().resolve())
        except Exception:
            key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def find_source_root() -> Path | None:
    for candidate in local_governance_roots():
        try:
            root = candidate.expanduser().resolve()
        except Exception:
            continue
        if root.is_dir() and all((root / relative).is_file() for relative in REQUIRED_SOURCE_FILES):
            return root
    return None


def require_source_root() -> Path:
    root = find_source_root()
    if root is None:
        raise RuntimeError(
            "materialized Governance source root is missing from the explicit locator and canonical StegVerse source/workload paths"
        )
    return root


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign Governance task observation")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for Governance observer: " + ",".join(sorted(present)))

    node_path, node = find_node()
    validate_invocation(invocation)
    root = require_source_root()

    registry = read_json(root / "automation" / "governance_task_registry.json")
    task_ids = {str(item.get("id")) for item in registry.get("tasks", []) if isinstance(item, dict)}
    if "CGE-DECISION-ISSUER-ARCHITECTURE-OWNERSHIP-001" not in task_ids:
        raise RuntimeError("Governance registry missing CGE architecture ownership watch")

    state_root = Path.home() / ".stegverse" / "state" / "governance-task-observer"
    receipt_root = Path.home() / ".stegverse" / "receipts"
    state_root.mkdir(parents=True, exist_ok=True)
    receipt_root.mkdir(parents=True, exist_ok=True)
    observed = state_root / "latest.json"

    child = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    proc = subprocess.run(
        [sys.executable, "scripts/run_governance_tasks.py", "--receipt", str(observed)],
        cwd=root,
        env=child,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("Governance task observer failed: " + (proc.stdout + proc.stderr)[-3000:])
    if not observed.is_file():
        raise RuntimeError("Governance observer did not persist task-state evidence")

    state = read_json(observed)
    if state.get("validation_status") != "pass":
        raise RuntimeError("Governance task registry validation did not pass")
    tasks = {str(item.get("id")): item for item in state.get("tasks", []) if isinstance(item, dict)}
    cge = tasks.get("CGE-DECISION-ISSUER-ARCHITECTURE-OWNERSHIP-001")
    if not cge:
        raise RuntimeError("CGE architecture ownership watch absent from observed task state")
    decision_receipt = root / "evidence" / "cge-decision-issuer-architecture" / "latest.json"
    expected_state = "completed" if decision_receipt.is_file() else "blocked"
    if cge.get("state") != expected_state:
        raise RuntimeError(f"CGE architecture watch state mismatch: expected {expected_state}")

    receipt = {
        "schema": "stegverse.governance.sovereign-task-observer-receipt/v0.1",
        "task_id": TASK_ID,
        "state": "COMPLETE",
        "transition_id": "GOVERNANCE_SOVEREIGN_TASK_OBSERVATION_COMPLETE",
        "claim_id": (invocation.get("task") or {}).get("claim_id"),
        "worker_id": WORKER_ID,
        "node_declaration_ref": str(node_path),
        "node_declaration_source": node.get("declaration_source"),
        "source_root": str(root),
        "source_discovery_mode": "explicit" if str(os.getenv(ROOT_ENV) or "").strip() else "canonical_local_path",
        "observed_state_ref": str(observed),
        "registry_validation_status": "pass",
        "cge_architecture_watch_state": cge.get("state"),
        "architecture_decision_receipt_observed": decision_receipt.is_file(),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "authority_effect": "OBSERVATION_ONLY_NO_NEW_AUTHORITY",
        "heartbeat_effect": False,
    }
    target = receipt_root / "governance-sovereign-task-observer-latest.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["local_receipt_ref"] = str(target)
    return receipt


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be a JSON object")
        receipt = execute(invocation)
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETE",
            "transition_id": "GOVERNANCE_SOVEREIGN_TASK_OBSERVATION_COMPLETE",
            "evidence_refs": [receipt["local_receipt_ref"]],
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "repository_writeback_performed": False,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "schema": "stegverse.worker-response/v0.1",
            "state": "BLOCKED",
            "transition_id": "GOVERNANCE_SOVEREIGN_TASK_OBSERVATION_BLOCKED",
            "error": str(exc),
            "evidence_refs": [],
            "credential_authority": "TV/TVC",
            "github_token_used": False,
            "repository_writeback_performed": False,
        }, sort_keys=True))
        return 75


if __name__ == "__main__":
    raise SystemExit(main())
