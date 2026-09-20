#!/usr/bin/env python3
"""Consume bounded Canonical Work resident requests from already-local canonical source.

The consumer is sovereign-only and non-authorizing. It may self-materialize an
explicit staged request and, when a preserved resident monolithic registry is
older than the request, install a task-specific fallback shard from the same
already-local canonical source. This prevents stale resident source projection
from turning a newly registered task into a permanent NO_REQUEST / task-not-found
condition without overwriting resident registry state.

After the explicit request set is visited, this same existing resident consumer
returns to the canonical Task Registry and attempts one bounded registry-first
Canonical Work cycle. No second dispatcher, scheduler, WorkerCoordinator, listener,
heartbeat, credential path, or runtime authority is created.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

TARGET_MODE = "CANONICAL_WORK_EVENT_BOOTSTRAP"
TARGET_ENTRYPOINT = Path("scripts/install_and_run_canonical_work_event_bootstrap.py")
TASK_REGISTRY_CYCLE_ENTRYPOINT = Path("scripts/run_task_registry_canonical_work_cycle.py")
TASK_RECORDS_REL = Path("data/canonical-task-records")
TASK_REGISTRY_CYCLE_RECEIPT = Path("receipts/sovereign-host/task-registry-canonical-work-cycle.latest.json")
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
ERL_REVIEW_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-erl-ai-economic-transparency-review-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-erl-ai-economic-transparency-review-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-erl-ai-economic-transparency-review"),
    "task_id": "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001",
}
CRYPTO_LIVE_AUTO_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-crypto-live-auto-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-crypto-live-auto-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-crypto-live-auto"),
    "task_id": "CRYPTO-LIVE-AUTO-001",
}
STEGBROWSER_RUNTIME_CONSUMPTION_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-stegbrowser-runtime-consumption"),
    "task_id": "STEG-BROWSER-RUNTIME-CONSUMPTION-001",
}
GLOBAL_MEASUREMENT_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-global-runtime-evidence-measurement-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-global-runtime-evidence-measurement-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-global-runtime-evidence-measurement"),
    "task_id": "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001",
}
AUTONOMOUS_PROGRESSION_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-entity-autonomous-governed-progression-runtime-adoption-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-entity-autonomous-governed-progression-runtime-adoption-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-entity-autonomous-governed-progression-runtime-adoption"),
    "task_id": "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001",
}
STEGAGENTS_GOVERNED_RUNTIME_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-stegagents-governed-runtime-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-stegagents-governed-runtime-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-stegagents-governed-runtime"),
    "task_id": "STEGAGENTS-GOVERNED-RUNTIME-001",
}
CONVERSATION_EVIDENCE_INGESTION_CUSTODY_SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-conversation-evidence-ingestion-custody-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-conversation-evidence-ingestion-custody-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-conversation-evidence-ingestion-custody"),
    "task_id": "CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001",
}
REQUEST_SPECS = (
    DEFAULT_SPEC,
    QUANTUM_SPEC,
    OBJECT_PROVENANCE_SPEC,
    RUNTIME_PROFILE_MAP_SPEC,
    ERL_REVIEW_SPEC,
    CRYPTO_LIVE_AUTO_SPEC,
    STEGBROWSER_RUNTIME_CONSUMPTION_SPEC,
    GLOBAL_MEASUREMENT_SPEC,
    AUTONOMOUS_PROGRESSION_SPEC,
    STEGAGENTS_GOVERNED_RUNTIME_SPEC,
    CONVERSATION_EVIDENCE_INGESTION_CUSTODY_SPEC,
)

MATERIALIZE = (
    Path("scripts/install_and_run_canonical_work_event_bootstrap.py"),
    Path("scripts/run_canonical_work_event_bootstrap.py"),
    Path("scripts/run_task_registry_canonical_work_cycle.py"),
    Path("scripts/evaluate_task_registry_collision_checkin.py"),
    Path("scripts/task_registry_checkin_event_history.py"),
    Path("scripts/validate_task_registration_substrate_resolution.py"),
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
    Path("data/task-registry-global-invariants.json"),
    Path("data/task-registry-general-checkin-caller-policy.json"),
)
PRESERVE_IF_PRESENT = (
    Path("data/canonical-task-registry.json"),
    Path("data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"),
    Path("data/canonical-task-records/CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001.json"),
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


def source_complete(root: Path) -> bool:
    return (
        (root / "data/canonical-task-registry.json").is_file()
        and (root / TASK_RECORDS_REL).is_dir()
        and all((root / rel).is_file() for rel in MATERIALIZE)
    )


def resolve_local_canonical_source(
    source_root: Path,
    runtime_root: Path,
    env: Mapping[str, str] | None = None,
) -> Path:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if source_complete(source):
        return source
    values = dict(os.environ if env is None else env)
    raw = str(values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    require(raw, "canonical work local source incomplete and STEGVERSE_HEARTBEAT_SOURCE_ROOT is not set")
    candidate = Path(raw).expanduser().resolve()
    require(candidate != runtime or source_complete(candidate), "canonical work runtime root is not a complete canonical source tree")
    require(source_complete(candidate), f"canonical work local source locator incomplete:{candidate}")
    return candidate


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


def parse_json_schema(stdout: str, schema: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(stdout):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout[index:])
        except Exception:
            continue
        if isinstance(value, dict) and value.get("schema") == schema:
            return value
    return None


def parse_json_object(stdout: str) -> dict[str, Any] | None:
    return parse_json_schema(stdout, "stegverse.canonical-work-event-bootstrap-receipt/v1")


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
    return {"path": str(destination), "sha256": source_hash, "exact_copy": True, "preserved_existing_runtime_projection": False}


def materialize(source: Path, runtime: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in MATERIALIZE:
        copied = copy_exact(source / rel, runtime / rel)
        copied["path"] = rel.as_posix()
        rows.append(copied)
    for rel in PRESERVE_IF_PRESENT:
        src, dst = source / rel, runtime / rel
        require(src.is_file(), f"canonical source file missing:{rel}")
        if dst.is_file():
            rows.append({"path": rel.as_posix(), "sha256": sha256(dst), "exact_copy": False, "preserved_existing_runtime_projection": True, "source_sha256": sha256(src)})
        else:
            copied = copy_exact(src, dst)
            copied["path"] = rel.as_posix()
            rows.append(copied)
    return rows


def materialize_registry_task_shards(source: Path, runtime: Path) -> list[dict[str, Any]]:
    source_dir = source / TASK_RECORDS_REL
    runtime_dir = runtime / TASK_RECORDS_REL
    require(source_dir.is_dir(), "canonical source task-record directory missing")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for src in sorted(source_dir.glob("*.json")):
        dst = runtime_dir / src.name
        if dst.is_file():
            rows.append({"path": (TASK_RECORDS_REL / src.name).as_posix(), "sha256": sha256(dst), "exact_copy": False, "preserved_existing_runtime_projection": True, "source_sha256": sha256(src)})
            continue
        copied = copy_exact(src, dst)
        copied["path"] = (TASK_RECORDS_REL / src.name).as_posix()
        rows.append(copied)
    return rows


def ensure_request_materialized(source: Path, runtime: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    rel = spec["request_rel"]
    copied = copy_exact(source / rel, runtime / rel)
    copied["path"] = rel.as_posix()
    copied["purpose"] = "EXPLICIT_STAGED_REQUEST_SELF_MATERIALIZATION"
    return copied


def ensure_task_identity_materialized(source: Path, runtime: Path, task_id: str) -> dict[str, Any]:
    runtime_registry = runtime / "data/canonical-task-registry.json"
    source_registry = source / "data/canonical-task-registry.json"
    require(source_registry.is_file(), "canonical source registry missing")
    source_doc = load_json(source_registry)
    source_matches = [row for row in source_doc.get("tasks", []) if isinstance(row, dict) and row.get("task_id") == task_id]
    require(len(source_matches) <= 1, "source canonical task identity duplicated")
    if source_matches:
        source_task = source_matches[0]
        source_kind = "MONOLITHIC_SOURCE_REGISTRY"
    else:
        source_shard = source / "data/canonical-task-records" / f"{task_id}.json"
        require(source_shard.is_file(), "source canonical task identity missing from registry and shard")
        source_task = load_json(source_shard)
        require(source_task.get("task_id") == task_id, "source canonical task shard identity mismatch")
        source_kind = "SOURCE_TASK_SHARD"
    if runtime_registry.is_file():
        runtime_doc = load_json(runtime_registry)
        runtime_matches = [row for row in runtime_doc.get("tasks", []) if isinstance(row, dict) and row.get("task_id") == task_id]
        require(len(runtime_matches) <= 1, "runtime canonical task identity duplicated")
        if len(runtime_matches) == 1:
            return {"task_id": task_id, "state": "MONOLITHIC_RUNTIME_IDENTITY_PRESENT", "materialized": False, "registry_preserved": True, "source_kind": source_kind}
    shard = runtime / "data/canonical-task-records" / f"{task_id}.json"
    atomic_json(shard, source_task)
    require(load_json(shard).get("task_id") == task_id, "materialized task shard identity mismatch")
    return {"task_id": task_id, "state": "SOURCE_TASK_SHARD_MATERIALIZED", "materialized": True, "registry_preserved": runtime_registry.is_file(), "source_kind": source_kind, "shard_ref": str(shard), "sha256": sha256(shard)}


def refresh_current_goal_registry_projection(runtime: Path, task_id: str) -> dict[str, Any]:
    """Reuse the existing bootstrap stale-registry projection repair for one current Goal."""
    entrypoint = runtime / TARGET_ENTRYPOINT
    require(entrypoint.is_file(), "canonical work bootstrap entrypoint not materialized")
    spec = importlib.util.spec_from_file_location("canonical_work_projection_refresh", entrypoint)
    require(spec is not None and spec.loader is not None, "canonical work projection refresh loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    refresh = getattr(module, "refresh_registry_projection_from_shard", None)
    require(callable(refresh), "canonical work projection refresh function unavailable")
    result = refresh(task_id, runtime / "data/canonical-task-registry.json")
    require(isinstance(result, dict), "canonical work projection refresh returned invalid result")
    require(result.get("task_id") == task_id, "canonical work projection refresh identity mismatch")
    require(result.get("authority_effect") == "NONE", "canonical work projection refresh attempted authority effect")
    return result


def consume_for_spec(source_root: Path, runtime_root: Path, spec: Mapping[str, Any], *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    validate_spec(spec)
    runtime = runtime_root.expanduser().resolve()
    source = resolve_local_canonical_source(source_root, runtime, env)
    request_materialization = ensure_request_materialized(source, runtime, spec)
    request_path = runtime / spec["request_rel"]
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
    task_identity = ensure_task_identity_materialized(source, runtime, spec["task_id"])
    entrypoint = runtime / TARGET_ENTRYPOINT
    safe_env = clean_env(env)
    bootstrap_runtime = runtime / spec["bootstrap_runtime_rel"]
    command = [sys.executable, str(entrypoint), "--task-id", spec["task_id"], "--runtime-root", str(bootstrap_runtime), "--registry", str(runtime / "data/canonical-task-registry.json")]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=safe_env, timeout=1200)
    result = parse_json_object(completed.stdout)
    bootstrap_receipt = bootstrap_runtime / "receipts/sovereign-host/canonical-work-event-bootstrap.latest.json"
    completed_ok = bool(completed.returncode == 0 and isinstance(result, dict) and result.get("state") == "INGRESS_CONSUMPTION_AND_PROJECTION_OBSERVED" and result.get("task_id") == spec["task_id"] and bootstrap_receipt.is_file())
    receipt = {
        "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
        "state": "COMPLETED" if completed_ok else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": spec["task_id"],
        "entrypoint": str(TARGET_ENTRYPOINT),
        "resolved_local_source_root": str(source),
        "request_self_materialization": request_materialization,
        "task_identity_materialization": task_identity,
        "source_materialization": materialized,
        "source_materialization_count": len(materialized),
        "existing_canonical_task_registry_preserved": any(row.get("path") == "data/canonical-task-registry.json" and row.get("preserved_existing_runtime_projection") is True for row in materialized),
        "existing_target_task_shard_preserved": any(row.get("path") == f"data/canonical-task-records/{spec['task_id']}.json" and row.get("preserved_existing_runtime_projection") is True for row in materialized),
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


def run_registry_cycle(
    source_root: Path,
    runtime_root: Path,
    *,
    goal_task_id: str | None = None,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    source = resolve_local_canonical_source(source_root, runtime, env)
    materialized = materialize(source, runtime)
    task_shards = materialize_registry_task_shards(source, runtime)
    current_goal_identity = None
    current_goal_registry_projection = None
    if goal_task_id:
        current_goal_identity = ensure_task_identity_materialized(source, runtime, goal_task_id)
        current_goal_registry_projection = refresh_current_goal_registry_projection(runtime, goal_task_id)
    entrypoint = runtime / TASK_REGISTRY_CYCLE_ENTRYPOINT
    safe_env = clean_env(env)
    cycle_runtime = runtime / "runtime/task-registry-canonical-work-cycle"
    command = [sys.executable, str(entrypoint), "--runtime-root", str(cycle_runtime)]
    if goal_task_id:
        command.extend(["--goal-task-id", str(goal_task_id)])
    for spec in REQUEST_SPECS:
        command.extend(["--exclude-task-id", spec["task_id"]])
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=safe_env, timeout=1200)
    result = parse_json_schema(completed.stdout, "stegverse.task-registry-canonical-work-cycle/v1")
    accepted_states = {"DELEGATED_TO_EXISTING_CANONICAL_WORK_PATH", "NO_ADMISSIBLE_NONCOLLIDING_TASK"}
    completed_ok = bool(completed.returncode == 0 and isinstance(result, dict) and result.get("state") in accepted_states)
    receipt = {
        "schema": "stegverse.resident-task-registry-canonical-work-cycle-consumption/v1",
        "state": "COMPLETED" if completed_ok else "ATTEMPT_RECORDED",
        "start_point": "CANONICAL_TASK_REGISTRY",
        "entrypoint": str(TASK_REGISTRY_CYCLE_ENTRYPOINT),
        "current_goal_task_id": goal_task_id,
        "current_goal_identity_materialization": current_goal_identity,
        "current_goal_registry_projection": current_goal_registry_projection,
        "resolved_local_source_root": str(source),
        "command": command,
        "returncode": completed.returncode,
        "result": result,
        "source_materialization": materialized,
        "task_registry_shard_projection": task_shards,
        "task_registry_shard_projection_count": len(task_shards),
        "existing_runtime_task_shards_preserved": all(row.get("preserved_existing_runtime_projection") is True or row.get("exact_copy") is True for row in task_shards),
        "explicit_request_task_ids_excluded": sorted(spec["task_id"] for spec in REQUEST_SPECS),
        "second_dispatcher_created": False,
        "second_scheduler_created": False,
        "claim_or_fence_minted": False,
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REGISTRY_SELECTION_AND_DELEGATION_EVIDENCE_ONLY",
    }
    atomic_json(runtime / TASK_REGISTRY_CYCLE_RECEIPT, receipt)
    return receipt


def retain_request_consumption_exception(
    runtime_root: Path,
    spec: Mapping[str, Any],
    exc: Exception,
) -> dict[str, Any]:
    """Retain a task-specific fail-closed receipt for pre-receipt consumer exceptions."""
    validate_spec(spec)
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / spec["request_rel"]
    request_id = None
    request_hash = None
    if request_path.is_file():
        try:
            request = load_json(request_path)
            request_id = request.get("request_id")
            request_hash = stable_hash(request)
        except Exception:
            request_id = None
            request_hash = None
    consumption_path = runtime / spec["consumption_rel"]
    receipt = {
        "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
        "state": "REQUEST_CONSUMPTION_EXCEPTION",
        "request_id": request_id,
        "request_sha256": request_hash,
        "task_id": spec["task_id"],
        "request_ref": str(spec["request_rel"]),
        "consumption_ref": str(spec["consumption_rel"]),
        "error_type": type(exc).__name__,
        "error": str(exc),
        "attempted": True,
        "retained_failure_evidence": True,
        "network_source_fetch_performed": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "second_machine_required": False,
        "authority_effect": "NONE_FAIL_CLOSED",
    }
    atomic_json(consumption_path, receipt)
    return receipt


def consume_all(
    source_root: Path,
    runtime_root: Path,
    *,
    goal_task_id: str | None = None,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    for spec in REQUEST_SPECS:
        try:
            outcomes.append(consume_for_spec(source_root, runtime_root, spec, runner=runner, env=env))
        except Exception as exc:
            try:
                outcomes.append(retain_request_consumption_exception(runtime_root, spec, exc))
            except Exception as retention_exc:
                outcomes.append({
                    "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
                    "state": "REQUEST_CONSUMPTION_EXCEPTION",
                    "task_id": spec.get("task_id"),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "retention_error_type": type(retention_exc).__name__,
                    "retention_error": str(retention_exc),
                    "retained_failure_evidence": False,
                    "authority_effect": "NONE_FAIL_CLOSED",
                })
    try:
        registry_cycle = run_registry_cycle(
            source_root,
            runtime_root,
            goal_task_id=goal_task_id,
            runner=runner,
            env=env,
        )
    except Exception as exc:
        registry_cycle = {"schema": "stegverse.resident-task-registry-canonical-work-cycle-consumption/v1", "state": "REGISTRY_CYCLE_EXCEPTION", "error_type": type(exc).__name__, "error": str(exc), "authority_effect": "NONE_FAIL_CLOSED"}
    acceptable = {"ALREADY_CONSUMED", "COMPLETED", "ATTEMPT_RECORDED"}
    all_acceptable = all(row.get("state") in acceptable for row in outcomes)
    registry_acceptable = registry_cycle.get("state") in {"COMPLETED", "ATTEMPT_RECORDED"}
    return {
        "schema": "stegverse.canonical-work-bootstrap-request-set-consumption/v1",
        "state": "COMPLETED" if all_acceptable and registry_cycle.get("state") == "COMPLETED" else "ATTEMPT_RECORDED",
        "request_count": len(REQUEST_SPECS),
        "outcomes": outcomes,
        "task_registry_cycle": registry_cycle,
        "task_registry_cycle_attempted": True,
        "task_registry_cycle_result_acceptable": registry_acceptable,
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