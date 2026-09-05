#!/usr/bin/env python3
"""Consume the bounded resident request for canonical runtime-profile map generation.

Uses only already-local source. It materializes immutable profile-map/coordination
surfaces into the existing resident checkout, preserves mutable resident state,
builds/validates the profile map, emits integrity evidence, resolves canonical-task
runtime requirements, persists those projections, validates coordination consistency,
and emits per-task routing-readiness plus custody-input evidence. No network fetch,
credential use, HB/oscillator advance, claim/fence minting, task-state transition,
Master Records custody, or second runtime is permitted.
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

REQUEST_REL = Path("control/resident-execution-request.d/runtime-profile-map-build-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/runtime-profile-map-build-request-consumption.latest.json")
TARGET_TASK = "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
TARGET_MODE = "CANONICAL_RUNTIME_PROFILE_MAP_BUILD"
TARGET_ENTRYPOINT = Path("control/resident-execution-request.d/consume-runtime-profile-map-build.py")
BOOTSTRAP_MAP_REL = Path("control/runtime-profile-map.json")
CANONICAL_REGISTRY_REL = Path("data/canonical-task-registry.json")
TASK_RESOLUTION_DIR_REL = Path("receipts/runtime-profile-map/task-resolutions")

IMMUTABLE_FILES = (
    Path("schemas/runtime-profile-map.schema.json"),
    Path("schemas/runtime-profile-map-custody-package.schema.json"),
    Path("schemas/canonical-task-record.schema.json"),
    Path("schemas/task-master-records-reconciliation.schema.json"),
    Path("control/runtime-profile-sources.json"),
    Path("control/canonical-resident-carrier-contract.json"),
    Path("control/worker-capability-profiles.json"),
    Path("control/canonical-work-runtime-profile.json"),
    Path("data/task-coordination-policy.json"),
    Path("docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md"),
    Path("scripts/build_runtime_profile_map.py"),
    Path("scripts/validate_runtime_profile_map.py"),
    Path("scripts/query_runtime_profile_map.py"),
    Path("scripts/match_runtime_profile.py"),
    Path("scripts/resolve_task_runtime_candidates.py"),
    Path("scripts/apply_task_runtime_resolution_projection.py"),
    Path("scripts/apply_all_task_runtime_resolutions.py"),
    Path("scripts/evaluate_task_runtime_routing_readiness.py"),
    Path("scripts/finalize_runtime_profile_map_cycle.py"),
    Path("scripts/build_runtime_profile_map_custody_package.py"),
    Path("scripts/validate_canonical_work_coordination.py"),
    Path("scripts/emit_runtime_profile_map_receipt.py"),
)
OBSERVABILITY_DIR = Path("control/runtime-observability-consumers")
PRESERVED_RUNTIME_REQUIRED = (
    Path("control/worker-registry.json"),
    Path("workers/universal_intr_profiled_ingress.py"),
)
BOOTSTRAP_IF_MISSING_PRESERVE_IF_PRESENT = (
    CANONICAL_REGISTRY_REL,
    BOOTSTRAP_MAP_REL,
)
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "OAUTH_TOKEN")
NONSECRET = ("PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT", "STEGVERSE_SOVEREIGN_NODE")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object required:{path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": str(TARGET_ENTRYPOINT),
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
        require(request.get(key) == wanted, f"runtime profile map request {key} mismatch")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    require(not hosted, "hosted environment may not consume runtime profile map request:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def copy_exact(src: Path, dst: Path) -> dict[str, Any]:
    require(src.is_file(), f"source missing:{src}")
    digest = sha256(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.is_file() or sha256(dst) != digest:
        shutil.copy2(src, dst)
    require(dst.is_file() and sha256(dst) == digest, f"copy mismatch:{dst}")
    return {"path": str(dst), "sha256": digest, "exact_copy": True, "mutable_runtime_state_overwritten": False}


def materialize(source: Path, runtime: Path) -> list[dict[str, Any]]:
    rows = [copy_exact(source / rel, runtime / rel) for rel in IMMUTABLE_FILES]
    obs = source / OBSERVABILITY_DIR
    require(obs.is_dir(), "runtime observability directory missing")
    for src in sorted(obs.glob("*.json")):
        rel = src.relative_to(source)
        rows.append(copy_exact(src, runtime / rel))

    for rel in PRESERVED_RUNTIME_REQUIRED:
        current = runtime / rel
        require(current.is_file(), f"required existing resident state/source missing:{rel}")
        rows.append({"path": str(current), "sha256": sha256(current), "exact_copy": False, "preserved_existing_runtime_file": True, "mutable_runtime_state_overwritten": False})

    for rel in BOOTSTRAP_IF_MISSING_PRESERVE_IF_PRESENT:
        current = runtime / rel
        if not current.is_file():
            rows.append(copy_exact(source / rel, current))
        else:
            rows.append({"path": str(current), "sha256": sha256(current), "exact_copy": False, "preserved_existing_runtime_projection": True, "mutable_runtime_state_overwritten": False})
    return rows


def run(command: list[str], *, cwd: Path, env: Mapping[str, str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, timeout=1200, env=dict(env))
    return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:]}


def resolve_tasks(runtime: Path, safe_env: Mapping[str, str]) -> list[dict[str, Any]]:
    registry = load_json(runtime / CANONICAL_REGISTRY_REL)
    rows: list[dict[str, Any]] = []
    output_dir = runtime / TASK_RESOLUTION_DIR_REL
    output_dir.mkdir(parents=True, exist_ok=True)
    for task in registry.get("tasks", []):
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not isinstance(task.get("runtime_requirements"), dict):
            continue
        output = output_dir / f"{task_id}.json"
        result = run([
            sys.executable,
            str(runtime / "scripts/resolve_task_runtime_candidates.py"),
            task_id,
            "--registry", str(runtime / CANONICAL_REGISTRY_REL),
            "--map", str(runtime / BOOTSTRAP_MAP_REL),
            "--output", str(output),
        ], cwd=runtime, env=safe_env)
        rows.append({
            "task_id": task_id,
            "returncode": result["returncode"],
            "resolution_ref": str(output),
            "resolution_sha256": sha256(output) if output.is_file() else None,
            "projection_only": True,
            "selection_grants_authority": False,
            "command_result": result,
        })
    return rows


def finalize_cycle(runtime: Path, safe_env: Mapping[str, str]) -> dict[str, Any]:
    result = run([
        sys.executable,
        str(runtime / "scripts/finalize_runtime_profile_map_cycle.py"),
        "--root", str(runtime),
    ], cwd=runtime, env=safe_env)
    result["registry_ref"] = str(runtime / CANONICAL_REGISTRY_REL)
    result["registry_sha256"] = sha256(runtime / CANONICAL_REGISTRY_REL) if (runtime / CANONICAL_REGISTRY_REL).is_file() else None
    custody_package = runtime / "receipts/runtime-profile-map/custody/runtime-profile-map-custody-package.latest.json"
    result["custody_package_ref"] = str(custody_package)
    result["custody_package_sha256"] = sha256(custody_package) if custody_package.is_file() else None
    result["custody_performed"] = False
    result["coordination_state_changed"] = False
    result["claim_or_fence_minted"] = False
    result["execution_authority_granted"] = False
    return result


def consume(source_root: Path, runtime_root: Path, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.runtime-profile-map-build-consumption/v1", "state": "NO_REQUEST", "authority_effect": "NONE"}
    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    materialized = materialize(source, runtime)
    safe_env = clean_env(env)
    map_path = runtime / BOOTSTRAP_MAP_REL
    build = run([sys.executable, str(runtime / "scripts/build_runtime_profile_map.py"), "--root", str(runtime)], cwd=runtime, env=safe_env)
    validate = run([sys.executable, str(runtime / "scripts/validate_runtime_profile_map.py"), "--map", str(map_path)], cwd=runtime, env=safe_env)
    receipt_path = runtime / "receipts/runtime-profile-map/runtime-profile-map.latest.json"
    evidence = run([sys.executable, str(runtime / "scripts/emit_runtime_profile_map_receipt.py"), "--map", str(map_path), "--output", str(receipt_path)], cwd=runtime, env=safe_env)
    task_resolutions = resolve_tasks(runtime, safe_env) if build["returncode"] == validate["returncode"] == evidence["returncode"] == 0 else []
    resolutions_ok = bool(task_resolutions) and all(row.get("returncode") == 0 and row.get("resolution_sha256") for row in task_resolutions)
    finalization = finalize_cycle(runtime, safe_env) if resolutions_ok else {"returncode": None, "state": "NOT_ATTEMPTED"}
    finalization_ok = finalization.get("returncode") == 0 and bool(finalization.get("registry_sha256")) and bool(finalization.get("custody_package_sha256"))
    success = build["returncode"] == validate["returncode"] == evidence["returncode"] == 0 and receipt_path.is_file() and resolutions_ok and finalization_ok
    receipt = {
        "schema": "stegverse.runtime-profile-map-build-consumption/v1",
        "state": "COMPLETED" if success else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "source_materialization": materialized,
        "source_materialization_count": len(materialized),
        "existing_worker_registry_preserved": True,
        "existing_shared_intr_router_preserved": True,
        "existing_canonical_task_registry_preserved_before_projection": True,
        "previous_projection_generation_preserved_until_builder_write": True,
        "build": build,
        "validation": validate,
        "projection_receipt": evidence,
        "projection_receipt_ref": str(receipt_path),
        "task_runtime_resolutions": task_resolutions,
        "task_runtime_resolution_count": len(task_resolutions),
        "cycle_finalization": finalization,
        "custody_input_package_generated": bool(finalization.get("custody_package_sha256")),
        "master_records_custody_performed": False,
        "task_runtime_resolution_selection_grants_authority": False,
        "task_coordination_state_changed_by_runtime_resolution": False,
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_PROJECTION_BUILD_PERSISTENCE_READINESS_AND_CUSTODY_INPUT_ONLY"
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("state") in {"NO_REQUEST", "COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
