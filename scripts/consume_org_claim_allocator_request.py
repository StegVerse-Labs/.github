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




def validate_source_catalog_floor(source: Path, request: dict[str, Any]) -> dict[str, Any]:
    floor = request.get("source_catalog_floor")
    if not isinstance(floor, dict):
        raise RuntimeError("organization allocator request source catalog floor missing")
    task_id = floor.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise RuntimeError("organization allocator source catalog floor task missing")
    task_path = source / "tasks" / f"{task_id}.json"
    if not task_path.is_file():
        raise RuntimeError(f"STALE_SOURCE_CATALOG: required task missing: {task_id}")
    task = load_json(task_path)
    if task.get("task_id") != task_id:
        raise RuntimeError("STALE_SOURCE_CATALOG: task identity mismatch")
    if task.get("requested_at") != floor.get("requested_at"):
        raise RuntimeError("STALE_SOURCE_CATALOG: requested_at floor mismatch")
    mandatory = (task.get("requirements") or {}).get("mandatory") or []
    repository = floor.get("repository_full_name")
    surface = floor.get("required_dependency_surface")
    matched = False
    for requirement in mandatory:
        if not isinstance(requirement, dict):
            continue
        repo = (requirement.get("repository") or {}).get("full_name")
        surfaces = ((requirement.get("scope") or {}).get("dependency_surfaces") or [])
        if repo == repository and surface in surfaces:
            matched = True
            break
    if not matched:
        raise RuntimeError("STALE_SOURCE_CATALOG: required repository/dependency surface missing")
    if floor.get("purpose") != "MINIMUM_SOURCE_CATALOG_FRESHNESS_ONLY":
        raise RuntimeError("source catalog floor purpose mismatch")
    if floor.get("task_eligibility_effect") != "NONE":
        raise RuntimeError("source catalog floor may not determine task eligibility")
    return {
        "state": "SOURCE_CATALOG_FLOOR_SATISFIED",
        "task_id": task_id,
        "requested_at": task.get("requested_at"),
        "repository_full_name": repository,
        "required_dependency_surface": surface,
        "task_status_observed": task.get("status"),
        "task_eligibility_effect": "NONE",
        "network_fetch_performed": False,
        "authority_effect": "NONE_FRESHNESS_ONLY",
    }

def materialize_org_control_inputs(source: Path, runtime: Path) -> dict[str, Any]:
    """Append missing organization task definitions without overwriting runtime task state."""
    source_tasks = source / "tasks"
    runtime_tasks = runtime / "tasks"
    if not source_tasks.is_dir():
        raise RuntimeError("canonical organization task catalog missing")
    runtime_tasks.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    preserved: list[str] = []
    superseded_queued: list[str] = []
    supersession_deferred_active: list[str] = []
    source_values: list[dict[str, Any]] = []
    for task_path in sorted(source_tasks.glob("TASK-*.json")):
        value = load_json(task_path)
        if value.get("task_id") != task_path.stem:
            raise RuntimeError(f"organization task identity mismatch: {task_path.name}")
        source_values.append(value)
        destination = runtime_tasks / task_path.name
        if destination.exists():
            preserved.append(task_path.name)
            continue
        destination.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        imported.append(task_path.name)

    for value in source_values:
        supersedes = value.get("supersedes")
        if not isinstance(supersedes, str) or not supersedes:
            continue
        prior_path = runtime_tasks / f"{supersedes}.json"
        if not prior_path.is_file():
            continue
        prior = load_json(prior_path)
        prior_status = prior.get("status")
        if prior_status in {"queued", "proposed"}:
            prior["status"] = "proposed"
            prior["flags"] = sorted(set((prior.get("flags") or []) + ["superseded"]))
            prior_path.write_text(json.dumps(prior, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            superseded_queued.append(supersedes)
        elif prior_status in {"active", "checkin_pending"}:
            supersession_deferred_active.append(supersedes)

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
        "superseded_queued_task_ids": superseded_queued,
        "supersession_deferred_active_task_ids": supersession_deferred_active,
        "initialized_control_files": initialized,
        "runtime_task_state_overwritten": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_LOCAL_MATERIALIZATION_ONLY",
    }


def retain_claim_grant_evidence(runtime: Path, selected_task_id: str) -> dict[str, Any]:
    claims_path = runtime / "control/claims-active.json"
    if not claims_path.is_file():
        raise RuntimeError("post-allocation claim registry missing")
    claims_state = load_json(claims_path)
    generation = claims_state.get("generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise RuntimeError("post-allocation claim registry generation invalid")
    granted = [
        claim for claim in (claims_state.get("claims") or [])
        if isinstance(claim, dict) and claim.get("task_id") == selected_task_id
    ]
    if not granted:
        raise RuntimeError("selected task has no retained canonical claim")
    dependency_surfaces: set[str] = set()
    fences: list[int] = []
    for claim in granted:
        lease = claim.get("lease") or {}
        fence = lease.get("fencing_token")
        if not isinstance(fence, int) or isinstance(fence, bool) or fence < 1:
            raise RuntimeError("selected task claim fence invalid")
        fences.append(fence)
        for value in ((claim.get("scope") or {}).get("dependency_surfaces") or []):
            if str(value).strip():
                dependency_surfaces.add(str(value).strip())
    snapshot = {
        "task_id": selected_task_id,
        "claim_registry_generation": generation,
        "claims": granted,
    }
    receipt = {
        "schema": "stegverse.org-claim-grant-observation/v1",
        "state": "CLAIM_GRANT_OBSERVED",
        "task_id": selected_task_id,
        "claim_registry_generation": generation,
        "fencing_tokens": sorted(fences),
        "dependency_surfaces": sorted(dependency_surfaces),
        "claims": granted,
        "claim_snapshot_sha256": stable_hash(snapshot),
        "allocator_remains_claim_authority": True,
        "observation_grants_claim_authority": False,
        "heartbeat_grants_claim_authority": False,
        "github_token_required": False,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    root = runtime / "receipts/sovereign-host/org-claim-allocator-grants"
    root.mkdir(parents=True, exist_ok=True)
    generation_path = root / f"{selected_task_id}-G{generation}.json"
    latest_path = root / f"{selected_task_id}.latest.json"
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    generation_path.write_text(rendered, encoding="utf-8")
    latest_path.write_text(rendered, encoding="utf-8")
    return {
        "state": "CLAIM_GRANT_EVIDENCE_RETAINED",
        "task_id": selected_task_id,
        "claim_registry_generation": generation,
        "generation_receipt": str(generation_path.relative_to(runtime)),
        "latest_receipt": str(latest_path.relative_to(runtime)),
        "claim_snapshot_sha256": receipt["claim_snapshot_sha256"],
        "authority_effect": "NONE_OBSERVATION_ONLY",
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
    safe_env = clean_env(env)
    source_catalog_floor = validate_source_catalog_floor(source, request)
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
        env=safe_env,
    )
    result = parse_last_json(completed.stdout)
    selected = result.get("selected") if isinstance(result, dict) else None
    allocator_state = result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT"
    claim_grant_evidence = None
    if isinstance(selected, str) and selected:
        claim_grant_evidence = retain_claim_grant_evidence(runtime, selected)
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
        "source_catalog_floor": source_catalog_floor,
        "control_inputs": control_inputs,
        "allocator_result": result,
        "allocator_state": allocator_state,
        "selected_task_id": selected,
        "claim_grant_occurred": isinstance(selected, str) and bool(selected),
        "claim_grant_evidence": claim_grant_evidence,
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
