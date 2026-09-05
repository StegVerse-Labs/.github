#!/usr/bin/env python3
"""Consume the bounded Master Records custody request for a runtime-profile map cycle.

This requires an already-generated custody input package and an already-local
master-records/orchestration checkout. It performs no network fetch, credential use,
HB/oscillator progression, task-state transition, claim/fence minting, or runtime
selection. It invokes only the Master Records custody consumer against exact local
artifacts, then invokes the non-authorizing reconciliation consumer when available.
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

REQUEST_REL = Path("control/resident-execution-request.d/runtime-profile-map-custody-001.json")
PACKAGE_REL = Path("receipts/runtime-profile-map/custody/runtime-profile-map-custody-package.latest.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/runtime-profile-map-custody-request-consumption.latest.json")
TARGET_TASK = "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
TARGET_MODE = "RUNTIME_PROFILE_MAP_MASTER_RECORDS_CUSTODY"
TARGET_ENTRYPOINT = "control/resident-execution-request.d/consume-runtime-profile-map-custody.py"
MR_CONSUMER_REL = Path("scripts/ingest_runtime_profile_map_custody.py")
RECON_CONSUMER_REL = Path("control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py")
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "OAUTH_TOKEN")
NONSECRET = ("PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_SOVEREIGN_NODE")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object required:{path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    require(not hosted, "hosted environment may not perform runtime-profile-map custody:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


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
        require(request.get(key) == wanted, f"runtime profile custody request {key} mismatch")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def consume(source_root: Path | None, runtime_root: Path, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    source = source_root.expanduser().resolve() if source_root is not None else None
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.runtime-profile-map-custody-consumption/v1", "state": "NO_REQUEST", "authority_effect": "NONE"}
    request = load_json(request_path)
    validate_request(request)
    package = runtime / PACKAGE_REL
    if not package.is_file():
        return {
            "schema": "stegverse.runtime-profile-map-custody-consumption/v1",
            "state": "WAITING_FOR_CUSTODY_PACKAGE",
            "task_id": TARGET_TASK,
            "authority_effect": "NONE_WAIT_ONLY"
        }

    safe_env = clean_env(env)
    mr_root_value = safe_env.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT")
    if not mr_root_value:
        return {
            "schema": "stegverse.runtime-profile-map-custody-consumption/v1",
            "state": "MASTER_RECORDS_LOCAL_ROOT_NOT_MATERIALIZED",
            "task_id": TARGET_TASK,
            "authority_effect": "NONE_OBSERVATION_ONLY"
        }
    mr_root = Path(mr_root_value).expanduser().resolve()
    consumer = mr_root / MR_CONSUMER_REL
    if not consumer.is_file():
        return {
            "schema": "stegverse.runtime-profile-map-custody-consumption/v1",
            "state": "MASTER_RECORDS_CUSTODY_CONSUMER_NOT_MATERIALIZED",
            "task_id": TARGET_TASK,
            "master_records_root": str(mr_root),
            "authority_effect": "NONE_OBSERVATION_ONLY"
        }

    command = [
        sys.executable, str(consumer),
        "--package", str(package),
        "--artifact-root", str(runtime),
        "--custody-root", str(mr_root / "custody/runtime-profile-map"),
    ]
    completed = subprocess.run(command, cwd=mr_root, capture_output=True, text=True, check=False, timeout=1200, env=safe_env)
    result = parse_last_json(completed.stdout)
    success = completed.returncode == 0 and isinstance(result, dict) and result.get("state") == "CUSTODY_ACCEPTED"

    reconciliation: dict[str, Any] = {"state": "NOT_ATTEMPTED", "authority_effect": "NONE"}
    if success:
        recon = runtime / RECON_CONSUMER_REL
        if source is None:
            reconciliation = {"state": "SOURCE_ROOT_NOT_SUPPLIED", "authority_effect": "NONE_OBSERVATION_ONLY"}
        elif not recon.is_file():
            reconciliation = {"state": "RECONCILIATION_CONSUMER_NOT_MATERIALIZED", "consumer_ref": str(recon), "authority_effect": "NONE_OBSERVATION_ONLY"}
        else:
            recon_completed = subprocess.run(
                [sys.executable, str(recon), "--source-root", str(source), "--runtime-root", str(runtime)],
                cwd=runtime, capture_output=True, text=True, check=False, timeout=1200, env=safe_env,
            )
            reconciliation = {
                "state": "ATTEMPTED",
                "returncode": recon_completed.returncode,
                "result": parse_last_json(recon_completed.stdout),
                "stdout_tail": recon_completed.stdout[-4000:],
                "stderr_tail": recon_completed.stderr[-4000:],
                "authority_effect": "NONE_RECONCILIATION_CHAIN_ONLY",
            }

    receipt = {
        "schema": "stegverse.runtime-profile-map-custody-consumption/v1",
        "state": "COMPLETED" if success else "ATTEMPT_RECORDED",
        "task_id": TARGET_TASK,
        "request_id": request.get("request_id"),
        "request_sha256": stable_hash(request),
        "package_ref": str(package),
        "package_sha256": sha256(package),
        "master_records_root": str(mr_root),
        "master_records_consumer_ref": str(consumer),
        "returncode": completed.returncode,
        "result": result,
        "post_custody_reconciliation": reconciliation,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "task_coordination_state_changed": False,
        "authority_effect": "NONE_MASTER_RECORDS_CUSTODY_AND_RECONCILIATION_CHAIN_ONLY"
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"NO_REQUEST", "WAITING_FOR_CUSTODY_PACKAGE", "MASTER_RECORDS_LOCAL_ROOT_NOT_MATERIALIZED", "MASTER_RECORDS_CUSTODY_CONSUMER_NOT_MATERIALIZED", "COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
