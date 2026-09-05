#!/usr/bin/env python3
"""Consume the bounded resident request for Canonical Work coordination bootstrap.

The request is non-authorizing. This consumer only invokes the already-installed
install-and-run wrapper inside the resident checkout. The wrapper uses the existing
shared Universal InTr listener and HB-derived carrier profile. Neither this request
nor this consumer grants WorkerCoordinator claim/fence, task execution, Master
Records authority, credential authority, or HB/oscillator authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/canonical-work-coordination-bootstrap-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/canonical-work-coordination-bootstrap-request-consumption.latest.json")
BOOTSTRAP_RECEIPT_REL = Path("runtime/canonical-work-coordination/receipts/sovereign-host/canonical-work-event-bootstrap.latest.json")
TARGET_TASK = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
TARGET_MODE = "CANONICAL_WORK_EVENT_BOOTSTRAP"
TARGET_ENTRYPOINT = "scripts/install_and_run_canonical_work_event_bootstrap.py"

HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "OAUTH_TOKEN",
)
NONSECRET = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT", "STEGVERSE_SOVEREIGN_NODE",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"canonical work bootstrap resident request {key} mismatch")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume canonical work bootstrap request: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for index in range(len(lines) - 1, -1, -1):
        if not lines[index].startswith("{"):
            continue
        candidate = "\n".join(lines[index:])
        try:
            value = json.loads(candidate)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def terminal_bootstrap(runtime: Path) -> bool:
    path = runtime / BOOTSTRAP_RECEIPT_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    return (
        receipt.get("schema") == "stegverse.canonical-work-event-bootstrap-receipt/v1"
        and receipt.get("state") == "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED"
        and receipt.get("heartbeat_carrier_grants_authority") is False
        and receipt.get("oscillator_advanced_by_bootstrap") is False
        and receipt.get("workercoordinator_claim_or_fence_observed") is False
        and receipt.get("master_records_reconciliation_observed") is False
    )


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.canonical-work-bootstrap-request-consumption/v1", "state": "NO_REQUEST", "authority_effect": "NONE"}

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    consumption_path = runtime / CONSUMPTION_REL
    if consumption_path.is_file():
        previous = load_json(consumption_path)
        if previous.get("request_sha256") == request_hash and previous.get("state") == "COMPLETED" and terminal_bootstrap(runtime):
            return {**previous, "state": "ALREADY_CONSUMED"}

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        receipt = {
            "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
            "state": "ENTRYPOINT_NOT_MATERIALIZED",
            "request_id": request.get("request_id"),
            "request_sha256": request_hash,
            "entrypoint": TARGET_ENTRYPOINT,
            "authority_effect": "NONE_REQUEST_ONLY",
        }
        atomic_json(consumption_path, receipt)
        return receipt

    safe_env = clean_env(env)
    bootstrap_runtime = runtime / "runtime" / "canonical-work-coordination"
    command = [sys.executable, str(entrypoint), "--runtime-root", str(bootstrap_runtime)]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=safe_env, timeout=1200)
    result = parse_last_json(completed.stdout)
    completed_ok = bool(
        completed.returncode == 0
        and isinstance(result, dict)
        and result.get("schema") == "stegverse.canonical-work-event-bootstrap-receipt/v1"
        and result.get("state") == "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED"
        and terminal_bootstrap(runtime)
    )
    receipt = {
        "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
        "state": "COMPLETED" if completed_ok else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "entrypoint": TARGET_ENTRYPOINT,
        "command": command,
        "returncode": completed.returncode,
        "result": result,
        "bootstrap_receipt_ref": str(bootstrap_runtime / "receipts" / "sovereign-host" / "canonical-work-event-bootstrap.latest.json"),
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "second_machine_required": False,
        "authority_effect": "NONE_CONSUMPTION_EVIDENCE_ONLY",
    }
    atomic_json(consumption_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("state") in {"NO_REQUEST", "ALREADY_CONSUMED", "COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
