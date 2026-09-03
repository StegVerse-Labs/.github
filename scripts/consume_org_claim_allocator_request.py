#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REQUEST_REL = Path("control/resident-execution-request.d/org-claim-allocator-001.json")
RECEIPT_REL = Path("receipts/sovereign-host/org-claim-allocator-request-consumption.latest.json")
ALLOCATOR_REL = Path("scripts/allocate_claims.py")
TASK_ID = "SHWP-ORG-CLAIM-ALLOCATOR-001"
MODE = "CANONICAL_ORGANIZATION_CLAIM_ALLOCATION"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": "scripts/consume_org_claim_allocator_request.py",
        "canonical_allocator": "scripts/allocate_claims.py",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"organization allocator request {key} mismatch")
    if request.get("repeat_on_resident_dispatch") is not True:
        raise RuntimeError("organization allocator request must be repeatable on resident dispatch")
    if request.get("github_token_required") is not False:
        raise RuntimeError("organization allocator request may not require GitHub token")
    if request.get("network_source_fetch_allowed") is not False:
        raise RuntimeError("organization allocator request may not allow network source fetch")
    if request.get("second_machine_required") is not False:
        raise RuntimeError("organization allocator request may not require a second machine")
    if request.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant organization allocator authority")
    if request.get("request_grants_claim_authority") is not False:
        raise RuntimeError("resident request may not grant claim authority")
    if request.get("allocator_remains_claim_authority") is not True:
        raise RuntimeError("canonical allocator must remain claim authority")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def clean_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    hosted = [name for name in HOSTED_ENV if truthy(source.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not execute resident organization allocator: " + ",".join(sorted(hosted)))
    env = {}
    for key in ("PATH", "HOME", "LANG", "LC_ALL"):
        if source.get(key):
            env[key] = source[key]
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env



def materialize_org_control_inputs(source: Path, runtime: Path) -> dict[str, Any]:
    """Append missing organization task definitions without overwriting runtime task state."""
    source_tasks = source / "tasks"
    runtime_tasks = runtime / "tasks"
    if not source_tasks.is_dir():
        raise RuntimeError("canonical organization task catalog missing")
    runtime_tasks.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    preserved: list[str] = []
    for task_path in sorted(source_tasks.glob("TASK-*.json")):
        destination = runtime_tasks / task_path.name
        if destination.exists():
            preserved.append(task_path.name)
            continue
        value = load_json(task_path)
        if value.get("task_id") != task_path.stem:
            raise RuntimeError(f"organization task identity mismatch: {task_path.name}")
        destination.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        imported.append(task_path.name)

    initialized: list[str] = []
    for rel in (Path("control/claims-active.json"), Path("control/queue.json")):
        destination = runtime / rel
        if destination.exists():
            continue
        source_path = source / rel
        if not source_path.is_file():
            raise RuntimeError(f"canonical organization control input missing: {rel}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source_path.read_bytes())
        initialized.append(rel.as_posix())

    return {
        "state": "CONTROL_INPUTS_READY",
        "imported_task_files": imported,
        "preserved_runtime_task_files": preserved,
        "initialized_control_files": initialized,
        "runtime_task_state_overwritten": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_LOCAL_MATERIALIZATION_ONLY",
    }

def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "NO_REQUEST",
            "task_id": TASK_ID,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    control_inputs = materialize_org_control_inputs(source, runtime)
    allocator = runtime / ALLOCATOR_REL
    if not allocator.is_file():
        raise RuntimeError("canonical organization allocator not materialized")

    completed = runner(
        [sys.executable, str(allocator)],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=clean_env(env),
    )
    result = parse_last_json(completed.stdout)
    selected = result.get("selected") if isinstance(result, dict) else None
    allocator_state = result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT"
    accepted_state = allocator_state in {"ALLOCATION_COMPLETE", "ALLOCATOR_BUSY"}
    receipt = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "state": "ATTEMPT_RECORDED" if accepted_state else "BLOCKED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "mode": MODE,
        "runtime_execution_attempted": True,
        "execution_returncode": completed.returncode,
        "control_inputs": control_inputs,
        "allocator_result": result,
        "allocator_state": allocator_state,
        "selected_task_id": selected,
        "claim_grant_occurred": isinstance(selected, str) and bool(selected),
        "request_granted_claim_authority": False,
        "allocator_remains_claim_authority": True,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "repeat_on_resident_dispatch": True,
        "authority_effect": "CANONICAL_ALLOCATOR_ONLY_IF_SELECTED" if selected else "NONE_REQUEST_ONLY",
    }
    receipt_path = runtime / RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Invoke the canonical organization claim allocator from resident dispatch.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        receipt = {
            "schema": "stegverse.resident-execution-request-consumption/v1",
            "state": "BLOCKED",
            "task_id": TASK_ID,
            "runtime_execution_attempted": False,
            "reason": str(exc),
            "authority_effect": "NONE",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] in {"NO_REQUEST", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
