#!/usr/bin/env python3
"""Resident Canonical Work bootstrap consumer carried by the copied control request directory.

This consumer exists in `control/resident-execution-request.d`, which is already
materialized wholesale by the sovereign worker source refresh. It therefore does
not require expanding the resident static-script manifest merely to make bounded
Canonical Work task ingress discoverable.

On an admitted native resident host it copies only the explicitly enumerated
Canonical Work source files from the already-local canonical source root into the
resident checkout, verifies byte equality, preserves an already-existing resident
canonical task registry, then invokes the registered bounded bootstrap wrapper for
explicit task specifications. Request specifications are visited independently so
one task-local failure does not prevent a later task from being attempted. No
network source fetch, credential use, HB/oscillator advance, claim/fence minting,
or second runtime implementation is permitted here.
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

TARGET_MODE = "CANONICAL_WORK_EVENT_BOOTSTRAP"
TARGET_ENTRYPOINT = Path("scripts/install_and_run_canonical_work_event_bootstrap.py")
DEFAULT_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-coordination-bootstrap-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-coordination-bootstrap-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-coordination"),
    "task_id": "STEGVERSE-CANONICAL-WORK-COORDINATION-001",
}
QUANTUM_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-quantum-resilience-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-quantum-resilience-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-quantum-resilience"),
    "task_id": "QUANTUM-RESILIENCE-001",
}
OBJECT_PROVENANCE_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-object-provenance-continuity-190.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-object-provenance-continuity-190-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-object-provenance-continuity-190"),
    "task_id": "STEGVERSE-OBJECT-PROVENANCE-CONTINUITY-190",
}
RUNTIME_PROFILE_MAP_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-runtime-profile-map-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-runtime-profile-map-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-runtime-profile-map"),
    "task_id": "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001",
}
REQUEST_SPECS = (DEFAULT_SPEC, QUANTUM_SPEC, OBJECT_PROVENANCE_SPEC, RUNTIME_PROFILE_MAP_SPEC)

MATERIALIZE = (
    Path("scripts/install_and_run_canonical_work_event_bootstrap.py"),
    Path("scripts/run_canonical_work_event_bootstrap.py"),
    Path("scripts/install_canonical_work_universal_intr_route.py"),
    Path("scripts/build_canonical_work_intr_request.py"),
    Path("scripts/apply_admitted_canonical_work_projection.py"),
    Path("scripts/consume_canonical_work_intr_materialization_request.py"),
    Path("scripts/project_worker_claim_into_canonical_task.py"),
    Path("scripts/reconcile_admitted_canonical_work.py"),
    Path("scripts/reevaluate_canonical_task_dependencies.py"),
    Path("scripts/consume_admitted_dependency_resolution.py"),
    Path("workers/canonical_work_intr_ingress.py"),
    Path("control/canonical-work-runtime-profile.json"),
)
PRESERVE_IF_PRESENT = (
    Path("data/canonical-task-registry.json"),
)

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


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_spec(spec: Mapping[str, Any]) -> None:
    for key in ("request_rel", "consumption_rel", "bootstrap_runtime_rel", "task_id"):
        require(key in spec, f"canonical work consumer spec missing {key}")
    require(isinstance(spec["request_rel"], Path), "request_rel must be Path")
    require(isinstance(spec["consumption_rel"], Path), "consumption_rel must be Path")
    require(isinstance(spec["bootstrap_runtime_rel"], Path), "bootstrap_runtime_rel must be Path")
    require(isinstance(spec["task_id"], str) and bool(spec["task_id"]), "task_id required")


def validate_request(request: Mapping[str, Any], spec: Mapping[str, Any] = DEFAULT_SPEC) -> None:
    validate_spec(spec)
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": spec["task_id"],
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
        require(request.get(key) == wanted, f"canonical work bootstrap resident request {key} mismatch")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    require(not hosted, "hosted environment may not consume canonical work bootstrap request: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def parse_json_object(stdout: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(stdout):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout[index:])
        except Exception:
            continue
        if isinstance(value, dict) and value.get("schema") == "stegverse.canonical-work-event-bootstrap-receipt/v1":
            return value
    return None


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def copy_exact(source: Path, destination: Path) -> dict[str, Any]:
    require(source.is_file(), f"canonical source file missing:{source}")
    source_hash = sha256(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file() or sha256(destination) != source_hash:
        shutil.copy2(source, destination)
    require(destination.is_file() and sha256(destination) == source_hash, f"materialized byte mismatch:{destination}")
    return {
        "path": str(destination),
        "sha256": source_hash,
        "exact_copy": True,
        "preserved_existing_runtime_projection": False,
    }


def materialize(source: Path, runtime: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in MATERIALIZE:
        copied = copy_exact(source / rel, runtime / rel)
        copied["path"] = rel.as_posix()
        rows.append(copied)

    for rel in PRESERVE_IF_PRESENT:
        src = source / rel
        dst = runtime / rel
        require(src.is_file(), f"canonical source file missing:{rel}")
        if dst.is_file():
            rows.append({
                "path": rel.as_posix(),
                "sha256": sha256(dst),
                "exact_copy": False,
                "preserved_existing_runtime_projection": True,
                "source_sha256": sha256(src),
            })
        else:
            copied = copy_exact(src, dst)
            copied["path"] = rel.as_posix()
            rows.append(copied)
    return rows


def consume_for_spec(
    source_root: Path,
    runtime_root: Path,
    spec: Mapping[str, Any],
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    validate_spec(spec)
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / spec["request_rel"]
    if not request_path.is_file():
        return {
            "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
            "state": "NO_REQUEST",
            "task_id": spec["task_id"],
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request, spec)
    request_hash = stable_hash(request)
    consumption_path = runtime / spec["consumption_rel"]
    if consumption_path.is_file():
        previous = load_json(consumption_path)
        if previous.get("request_sha256") == request_hash and previous.get("state") == "COMPLETED":
            bootstrap_ref = previous.get("bootstrap_receipt_ref")
            if isinstance(bootstrap_ref, str) and Path(bootstrap_ref).is_file():
                return {**previous, "state": "ALREADY_CONSUMED"}

    materialized = materialize(source, runtime)
    entrypoint = runtime / TARGET_ENTRYPOINT
    safe_env = clean_env(env)
    bootstrap_runtime = runtime / spec["bootstrap_runtime_rel"]
    command = [
        sys.executable,
        str(entrypoint),
        "--task-id",
        spec["task_id"],
        "--runtime-root",
        str(bootstrap_runtime),
        "--registry",
        str(runtime / "data/canonical-task-registry.json"),
    ]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=safe_env, timeout=1200)
    result = parse_json_object(completed.stdout)
    bootstrap_receipt = bootstrap_runtime / "receipts/sovereign-host/canonical-work-event-bootstrap.latest.json"
    completed_ok = bool(
        completed.returncode == 0
        and isinstance(result, dict)
        and result.get("state") == "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED"
        and result.get("task_id") == spec["task_id"]
        and bootstrap_receipt.is_file()
    )
    receipt = {
        "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
        "state": "COMPLETED" if completed_ok else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": spec["task_id"],
        "entrypoint": str(TARGET_ENTRYPOINT),
        "source_materialization": materialized,
        "source_materialization_count": len(materialized),
        "existing_canonical_task_registry_preserved": any(
            row.get("path") == "data/canonical-task-registry.json" and row.get("preserved_existing_runtime_projection") is True
            for row in materialized
        ),
        "command": command,
        "returncode": completed.returncode,
        "result": result,
        "bootstrap_receipt_ref": str(bootstrap_receipt),
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


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    return consume_for_spec(source_root, runtime_root, DEFAULT_SPEC, runner=runner, env=env)


def consume_all(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    for spec in REQUEST_SPECS:
        try:
            outcomes.append(consume_for_spec(source_root, runtime_root, spec, runner=runner, env=env))
        except Exception as exc:
            outcomes.append({
                "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
                "state": "REQUEST_CONSUMPTION_EXCEPTION",
                "task_id": spec["task_id"],
                "error_type": type(exc).__name__,
                "authority_effect": "NONE_FAIL_CLOSED",
            })
    acceptable = {"NO_REQUEST", "ALREADY_CONSUMED", "COMPLETED", "ATTEMPT_RECORDED"}
    all_acceptable = all(row.get("state") in acceptable for row in outcomes)
    return {
        "schema": "stegverse.canonical-work-bootstrap-request-set-consumption/v1",
        "state": "COMPLETED" if all_acceptable else "ATTEMPT_RECORDED",
        "request_count": len(REQUEST_SPECS),
        "outcomes": outcomes,
        "later_request_attempts_blocked_by_earlier_failure": False,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_set_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "second_machine_required": False,
        "authority_effect": "NONE_CONSUMPTION_EVIDENCE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume_all(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("state") in {"COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
