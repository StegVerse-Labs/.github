#!/usr/bin/env python3
"""Consume the bounded runtime-profile-map Master Records reconciliation request.

This consumer waits for authentic local Master Records custody completion, projects
retained Master Records work events from the already-local Master Records checkout,
and reconciles each canonical task carrying runtime requirements against that
projection. It performs no network fetch, credential use, HB/oscillator progression,
claim/fence minting, task-state transition, runtime selection, or closure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REQUEST_REL = Path("control/resident-execution-request.d/runtime-profile-map-reconciliation-001.json")
CUSTODY_CONSUMPTION_REL = Path("receipts/sovereign-host/runtime-profile-map-custody-request-consumption.latest.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/runtime-profile-map-reconciliation-request-consumption.latest.json")
PROJECTION_REL = Path("receipts/runtime-profile-map/reconciliation/master-records-work-events.latest.json")
RECON_DIR_REL = Path("receipts/runtime-profile-map/reconciliation/tasks")
REGISTRY_REL = Path("data/canonical-task-registry.json")
TARGET_TASK = "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
TARGET_MODE = "RUNTIME_PROFILE_MAP_MASTER_RECORDS_RECONCILIATION"
TARGET_ENTRYPOINT = "control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py"
MR_PROJECTOR_REL = Path("scripts/project_canonical_work_events.py")
LOCAL_RECONCILER_REL = Path("scripts/reconcile_task_registry_master_records.py")
LOCAL_RECON_SCHEMA_REL = Path("schemas/task-master-records-reconciliation.schema.json")
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


def copy_exact(source: Path, target: Path) -> dict[str, Any]:
    require(source.is_file(), f"source missing:{source}")
    digest = sha256(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file() or sha256(target) != digest:
        shutil.copy2(source, target)
    require(target.is_file() and sha256(target) == digest, f"copy mismatch:{target}")
    return {"path": str(target), "sha256": digest, "exact_copy": True}


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    require(not hosted, "hosted environment may not reconcile runtime-profile-map custody:" + ",".join(sorted(hosted)))
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
        require(request.get(key) == wanted, f"runtime profile reconciliation request {key} mismatch")


def run(command: list[str], *, cwd: Path, env: Mapping[str, str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, timeout=1200, env=dict(env))
    return {"returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:]}


def consume(source_root: Path, runtime_root: Path, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1", "state": "NO_REQUEST", "authority_effect": "NONE"}
    request = load_json(request_path)
    validate_request(request)

    custody_path = runtime / CUSTODY_CONSUMPTION_REL
    if not custody_path.is_file():
        return {"schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1", "state": "WAITING_FOR_MASTER_RECORDS_CUSTODY", "task_id": TARGET_TASK, "authority_effect": "NONE_WAIT_ONLY"}
    custody = load_json(custody_path)
    if custody.get("state") != "COMPLETED":
        return {"schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1", "state": "WAITING_FOR_MASTER_RECORDS_CUSTODY", "task_id": TARGET_TASK, "custody_state": custody.get("state"), "authority_effect": "NONE_WAIT_ONLY"}

    registry_path = runtime / REGISTRY_REL
    require(registry_path.is_file(), "canonical task registry missing")
    registry = load_json(registry_path)
    safe_env = clean_env(env)
    mr_root_value = safe_env.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT")
    if not mr_root_value:
        return {"schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1", "state": "MASTER_RECORDS_LOCAL_ROOT_NOT_MATERIALIZED", "task_id": TARGET_TASK, "authority_effect": "NONE_OBSERVATION_ONLY"}
    mr_root = Path(mr_root_value).expanduser().resolve()
    projector = mr_root / MR_PROJECTOR_REL
    if not projector.is_file():
        return {"schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1", "state": "MASTER_RECORDS_PROJECTOR_NOT_MATERIALIZED", "task_id": TARGET_TASK, "master_records_root": str(mr_root), "authority_effect": "NONE_OBSERVATION_ONLY"}

    materialized = [
        copy_exact(source / LOCAL_RECONCILER_REL, runtime / LOCAL_RECONCILER_REL),
        copy_exact(source / LOCAL_RECON_SCHEMA_REL, runtime / LOCAL_RECON_SCHEMA_REL),
    ]
    projection_path = runtime / PROJECTION_REL
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projected = run([sys.executable, str(projector), "--repo-root", str(mr_root), "--output", str(projection_path)], cwd=mr_root, env=safe_env)
    if projected["returncode"] != 0 or not projection_path.is_file():
        receipt = {
            "schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1",
            "state": "ATTEMPT_RECORDED",
            "task_id": TARGET_TASK,
            "projection": projected,
            "authority_effect": "NONE_RECONCILIATION_ATTEMPT_ONLY",
        }
        atomic_json(runtime / CONSUMPTION_REL, receipt)
        return receipt

    rows: list[dict[str, Any]] = []
    recon_dir = runtime / RECON_DIR_REL
    recon_dir.mkdir(parents=True, exist_ok=True)
    for task in registry.get("tasks", []):
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not isinstance(task.get("runtime_requirements"), dict):
            continue
        output = recon_dir / f"{task_id}.json"
        result = run([
            sys.executable, str(runtime / LOCAL_RECONCILER_REL),
            "--registry", str(registry_path),
            "--task-id", task_id,
            "--master-records-projection", str(projection_path),
            "--output", str(output),
        ], cwd=runtime, env=safe_env)
        value = load_json(output) if result["returncode"] == 0 and output.is_file() else None
        rows.append({
            "task_id": task_id,
            "returncode": result["returncode"],
            "reconciliation_ref": str(output),
            "reconciliation_sha256": sha256(output) if output.is_file() else None,
            "state": value.get("state") if isinstance(value, dict) else None,
            "closure_admissible": value.get("closure_admissible") if isinstance(value, dict) else False,
            "proposed_followup": value.get("proposed_followup") if isinstance(value, dict) else None,
            "authority_effect": "NONE_RECONCILIATION_ONLY",
        })

    complete = bool(rows) and all(row.get("returncode") == 0 and row.get("reconciliation_sha256") for row in rows)
    receipt = {
        "schema": "stegverse.runtime-profile-map-reconciliation-consumption/v1",
        "state": "COMPLETED" if complete else "ATTEMPT_RECORDED",
        "task_id": TARGET_TASK,
        "request_id": request.get("request_id"),
        "request_sha256": stable_hash(request),
        "custody_consumption_ref": str(custody_path),
        "custody_consumption_sha256": sha256(custody_path),
        "master_records_root": str(mr_root),
        "master_records_projection_ref": str(projection_path),
        "master_records_projection_sha256": sha256(projection_path),
        "source_materialization": materialized,
        "task_reconciliations": rows,
        "task_reconciliation_count": len(rows),
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "task_coordination_state_changed": False,
        "closure_performed": False,
        "authority_effect": "NONE_MASTER_RECORDS_RECONCILIATION_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"NO_REQUEST", "WAITING_FOR_MASTER_RECORDS_CUSTODY", "MASTER_RECORDS_LOCAL_ROOT_NOT_MATERIALIZED", "MASTER_RECORDS_PROJECTOR_NOT_MATERIALIZED", "COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
