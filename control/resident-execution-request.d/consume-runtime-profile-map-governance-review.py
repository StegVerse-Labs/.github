#!/usr/bin/env python3
"""Consume the bounded post-transition-readiness governance-review request.

This consumer packages exact local evidence for the authority class that must review
the next transition. It performs no network fetch, credential use, HB/oscillator
progression, task-state transition, claim/fence minting, Interlock/InTr admission,
or execution.
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

REQUEST_REL = Path("control/resident-execution-request.d/runtime-profile-map-governance-review-001.json")
UPSTREAM_REL = Path("receipts/sovereign-host/runtime-profile-map-transition-readiness-request-consumption.latest.json")
REGISTRY_REL = Path("data/canonical-task-registry.json")
WORKER_REL = Path("control/worker-registry.json")
ROUTING_DIR = Path("receipts/runtime-profile-map/routing-readiness")
RECON_DIR = Path("receipts/runtime-profile-map/reconciliation/tasks")
TRANSITION_DIR = Path("receipts/runtime-profile-map/transition-readiness")
OUTPUT_DIR = Path("receipts/runtime-profile-map/governance-review")
CONSUMPTION_REL = Path("receipts/sovereign-host/runtime-profile-map-governance-review-request-consumption.latest.json")
BUILDER_REL = Path("scripts/build_runtime_profile_map_governance_review.py")
TARGET_TASK = "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
TARGET_MODE = "RUNTIME_PROFILE_MAP_GOVERNANCE_REVIEW_PACKAGE"
TARGET_ENTRYPOINT = "control/resident-execution-request.d/consume-runtime-profile-map-governance-review.py"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "OAUTH_TOKEN")
NONSECRET = ("PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_SOVEREIGN_NODE")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load(path: Path) -> dict[str, Any]:
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
    require(not hosted, "hosted environment may not package runtime governance review:" + ",".join(sorted(hosted)))
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
        require(request.get(key) == wanted, f"governance review request {key} mismatch")


def consume(source_root: Path, runtime_root: Path, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.runtime-profile-map-governance-review-consumption/v1", "state": "NO_REQUEST", "authority_effect": "NONE"}
    request = load(request_path)
    validate_request(request)

    upstream_path = runtime / UPSTREAM_REL
    if not upstream_path.is_file() or load(upstream_path).get("state") != "COMPLETED":
        return {"schema": "stegverse.runtime-profile-map-governance-review-consumption/v1", "state": "WAITING_FOR_TRANSITION_READINESS", "task_id": TARGET_TASK, "authority_effect": "NONE_WAIT_ONLY"}

    safe_env = clean_env(env)
    source_builder = source / BUILDER_REL
    runtime_builder = runtime / BUILDER_REL
    require(source_builder.is_file(), "governance review builder source missing")
    runtime_builder.parent.mkdir(parents=True, exist_ok=True)
    if not runtime_builder.is_file() or sha256(runtime_builder) != sha256(source_builder):
        shutil.copy2(source_builder, runtime_builder)
    require(sha256(runtime_builder) == sha256(source_builder), "governance review builder materialization mismatch")

    registry_path = runtime / REGISTRY_REL
    worker_path = runtime / WORKER_REL
    require(registry_path.is_file(), "canonical task registry missing")
    require(worker_path.is_file(), "WorkerCoordinator registry missing")
    registry = load(registry_path)

    rows: list[dict[str, Any]] = []
    for task in registry.get("tasks", []):
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not isinstance(task.get("runtime_requirements"), dict):
            continue
        routing = runtime / ROUTING_DIR / f"{task_id}.json"
        reconciliation = runtime / RECON_DIR / f"{task_id}.json"
        transition = runtime / TRANSITION_DIR / f"{task_id}.json"
        output = runtime / OUTPUT_DIR / f"{task_id}.json"
        require(routing.is_file() and reconciliation.is_file() and transition.is_file(), f"governance review evidence missing:{task_id}")
        output.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run([
            sys.executable, str(runtime_builder), task_id,
            "--registry", str(registry_path),
            "--worker-registry", str(worker_path),
            "--routing-readiness", str(routing),
            "--reconciliation", str(reconciliation),
            "--transition-readiness", str(transition),
            "--output", str(output),
        ], cwd=runtime, capture_output=True, text=True, check=False, timeout=1200, env=safe_env)
        value = load(output) if completed.returncode == 0 and output.is_file() else None
        rows.append({
            "task_id": task_id,
            "returncode": completed.returncode,
            "governance_review_ref": str(output),
            "governance_review_sha256": sha256(output) if output.is_file() else None,
            "review_authority_class": value.get("review_authority_class") if isinstance(value, dict) else None,
            "next_governance_review": value.get("next_governance_review") if isinstance(value, dict) else None,
            "disposition": value.get("transition_readiness_disposition") if isinstance(value, dict) else None,
        })

    complete = bool(rows) and all(row.get("returncode") == 0 and row.get("governance_review_sha256") for row in rows)
    receipt = {
        "schema": "stegverse.runtime-profile-map-governance-review-consumption/v1",
        "state": "COMPLETED" if complete else "ATTEMPT_RECORDED",
        "task_id": TARGET_TASK,
        "request_id": request.get("request_id"),
        "request_sha256": stable_hash(request),
        "transition_readiness_consumption_ref": str(upstream_path),
        "transition_readiness_consumption_sha256": sha256(upstream_path),
        "source_builder_ref": str(source_builder),
        "source_builder_sha256": sha256(source_builder),
        "task_governance_reviews": rows,
        "task_governance_review_count": len(rows),
        "task_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "interlock_intr_admission_granted": False,
        "heartbeat_or_oscillator_advanced": False,
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_GOVERNANCE_REVIEW_PACKAGING_ONLY",
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
    return 0 if result.get("state") in {"NO_REQUEST", "WAITING_FOR_TRANSITION_READINESS", "COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
