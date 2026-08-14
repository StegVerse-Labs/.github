#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
CONFIG_PATH = ROOT / "control" / "formalism-manifold-implementation-admission.json"
RECEIPT_ROOT = (ROOT / "receipts" / "formalism-manifold-implementation-admission").resolve()
TASK_ID = "SHWP-FORMALISM-MANIFOLD-IMPLEMENTATION-ADMISSION-001"
CAPABILITY = "formalism_manifold_implementation_admission"
CURRENT_AUTHORITY = "TV/TVC"
TERMINAL_TASK_STATES = {"COMPLETED", "SUPERSEDED", "MERGED", "CANCELLED"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def roots_from_environment() -> dict[str, Path]:
    raw = os.environ.get("STEGVERSE_FORMALISM_ROOTS_JSON", "")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    roots: dict[str, Path] = {}
    for repository, value in parsed.items():
        if isinstance(repository, str) and isinstance(value, str):
            roots[repository] = Path(value).expanduser().resolve()
    return roots


def mirror_handoffs(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for base in (repo_root, repo_root / "docs"):
        if not base.is_dir():
            continue
        paths.extend(path for path in sorted(base.glob("*_MIRROR_HANDOFF.md")) if path.is_file())
    return paths


def path_overlaps(left: str, right: str) -> bool:
    if left == right:
        return True
    if fnmatch.fnmatch(left, right) or fnmatch.fnmatch(right, left):
        return True
    left_prefix = left[:-3] if left.endswith("/**") else left.rstrip("/")
    right_prefix = right[:-3] if right.endswith("/**") else right.rstrip("/")
    return bool(left_prefix and right_prefix and (left_prefix.startswith(right_prefix + "/") or right_prefix.startswith(left_prefix + "/")))


def active_registry_scopes() -> list[dict[str, Any]]:
    fragments = sorted((ROOT / "control" / "worker-registry.d").glob("*.json"))
    task_rows: dict[str, dict[str, Any]] = {}
    registry = ROOT / "control" / "worker-registry.json"
    if registry.is_file():
        for task in load(registry).get("tasks", []):
            if isinstance(task, dict) and isinstance(task.get("task_id"), str):
                task_rows[task["task_id"]] = task
    for fragment in fragments:
        value = load(fragment)
        if value.get("schema") != "stegverse.worker-registry-fragment/v0.1":
            continue
        for task in value.get("tasks", []):
            if isinstance(task, dict) and isinstance(task.get("task_id"), str):
                task_rows.setdefault(task["task_id"], task)

    scopes: list[dict[str, Any]] = []
    for task_id, task in sorted(task_rows.items()):
        if task.get("state") in TERMINAL_TASK_STATES or task_id == TASK_ID:
            continue
        handoff_ref = task.get("handoff_ref")
        if not isinstance(handoff_ref, str):
            continue
        handoff_path = ROOT / handoff_ref
        if not handoff_path.is_file():
            continue
        handoff = load(handoff_path)
        task_spec = handoff.get("task") if isinstance(handoff.get("task"), dict) else {}
        execution = handoff.get("execution") if isinstance(handoff.get("execution"), dict) else {}
        repository = task_spec.get("repository")
        allowed_paths = execution.get("allowed_paths")
        if not isinstance(repository, str) or not isinstance(allowed_paths, list):
            continue
        scopes.append({
            "task_id": task_id,
            "state": task.get("state"),
            "repository": repository,
            "allowed_paths": [item for item in allowed_paths if isinstance(item, str)],
            "handoff_ref": handoff_ref,
        })
    return scopes


def evaluate(config: dict[str, Any], roots: dict[str, Path]) -> dict[str, Any]:
    reconciliation_path = ROOT / str(config["reconciliation_receipt"])
    if not reconciliation_path.is_file():
        return {
            "state": "BLOCKED",
            "reason": "RECONCILIATION_RECEIPT_MISSING",
            "reconciliation_ref": str(config["reconciliation_receipt"]),
            "owner_work_manifests": [],
            "authority_effect": "NONE_ADMISSION_NOT_REACHED",
        }
    reconciliation = load(reconciliation_path)
    if reconciliation.get("state") != "COMPLETED" or not bool((reconciliation.get("result") or {}).get("reconciled")):
        return {
            "state": "BLOCKED",
            "reason": "RECONCILIATION_NOT_COMPLETE",
            "reconciliation_ref": str(config["reconciliation_receipt"]),
            "reconciliation_sha256": canonical_hash(reconciliation),
            "owner_work_manifests": [],
            "authority_effect": "NONE_ADMISSION_NOT_REACHED",
        }

    owners = config.get("owners") if isinstance(config.get("owners"), dict) else {}
    active_scopes = active_registry_scopes()
    manifests: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    for delta in config.get("seed_deltas", []):
        if not isinstance(delta, dict):
            continue
        delta_id = delta.get("delta_id")
        owner = delta.get("owner_repository")
        proposed_paths = delta.get("proposed_paths")
        if not isinstance(delta_id, str) or not isinstance(owner, str) or owner not in owners:
            review.append({"delta_id": delta_id, "reason": "OWNER_MISSING_OR_NOT_CANONICAL"})
            continue
        if not isinstance(proposed_paths, list) or not proposed_paths or not all(isinstance(path, str) and path for path in proposed_paths):
            review.append({"delta_id": delta_id, "reason": "PROPOSED_SCOPE_MISSING"})
            continue

        owner_root = roots.get(owner)
        if owner_root is None or not owner_root.is_dir():
            blocked.append({
                "delta_id": delta_id,
                "owner_repository": owner,
                "reason": "OWNER_SOURCE_NOT_MATERIALIZED",
                "machine_observable_release_condition": f"{owner} is present in STEGVERSE_FORMALISM_ROOTS_JSON and resolves to a local directory",
            })
            continue
        handoffs = mirror_handoffs(owner_root)
        if owners[owner].get("requires_mirror_handoff") is True and not handoffs:
            blocked.append({
                "delta_id": delta_id,
                "owner_repository": owner,
                "reason": "OWNER_MIRROR_HANDOFF_MISSING",
                "machine_observable_release_condition": f"{owner} exposes at least one *_MIRROR_HANDOFF.md at repo root or docs/",
            })
            continue

        collisions: list[dict[str, Any]] = []
        for scope in active_scopes:
            if scope["repository"] != owner:
                continue
            overlap = sorted({
                proposed for proposed in proposed_paths
                for existing in scope["allowed_paths"]
                if path_overlaps(proposed, existing)
            })
            if overlap:
                collisions.append({"task_id": scope["task_id"], "handoff_ref": scope["handoff_ref"], "overlap": overlap})
        if collisions:
            blocked.append({
                "delta_id": delta_id,
                "owner_repository": owner,
                "reason": "ACTIVE_OWNER_SCOPE_COLLISION",
                "collisions": collisions,
                "machine_observable_release_condition": "Conflicting owner task reaches a terminal state or releases/narrows the overlapping scope",
            })
            continue

        owner_handoff_refs = []
        for path in handoffs:
            try:
                owner_handoff_refs.append(path.relative_to(owner_root).as_posix())
            except ValueError:
                owner_handoff_refs.append(path.as_posix())
        manifest = {
            "schema": "stegverse.owner-implementation-work-manifest/v0.1",
            "delta_id": delta_id,
            "kind": delta.get("kind"),
            "objective": delta.get("objective"),
            "owner_repository": owner,
            "owner_authority_class": owners[owner].get("authority_class"),
            "owner_handoff_refs": owner_handoff_refs,
            "proposed_paths": proposed_paths,
            "authority_ceiling": delta.get("authority_ceiling", []),
            "source_reconciliation_ref": str(config["reconciliation_receipt"]),
            "source_reconciliation_sha256": canonical_hash(reconciliation),
            "claim_state": "READY_FOR_SEPARATE_OWNER_ADMISSION",
            "coordinator_mutation_authority": false,
            "credential_authority": CURRENT_AUTHORITY,
            "github_token_required": false,
        }
        manifests.append(manifest)

    state = "REVIEW_REQUIRED" if review else ("BLOCKED" if blocked else "COMPLETED")
    return {
        "state": state,
        "reason": "OWNER_REVIEW_REQUIRED" if review else ("OWNER_ADMISSION_BLOCKED" if blocked else "OWNER_WORK_MANIFESTS_READY"),
        "reconciliation_ref": str(config["reconciliation_receipt"]),
        "reconciliation_sha256": canonical_hash(reconciliation),
        "owner_work_manifests": manifests,
        "blocked_deltas": blocked,
        "review_deltas": review,
        "active_scope_count": len(active_scopes),
        "authority_effect": "NONE_OWNER_ADMISSION_EVIDENCE_ONLY",
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception:
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 3
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or task.get("task_id") != TASK_ID:
        return 4
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 5
    execution = handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []):
        return 6
    if "receipts/formalism-manifold-implementation-admission/**" not in set(execution.get("allowed_paths") or []):
        return 7

    config = load(CONFIG_PATH)
    if config.get("schema") != "stegverse.formalism-manifold-implementation-admission/v0.1":
        return 8
    if config.get("credential_authority") != CURRENT_AUTHORITY or config.get("github_token_required") is not False:
        return 9

    result = evaluate(config, roots_from_environment())
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema": "stegverse.formalism-manifold-implementation-admission-receipt/v0.1",
        "goal_id": config["goal_id"],
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": fence,
        "generated_at": now,
        "state": result["state"],
        "transition_id": f"FORMALISM_MANIFOLD_IMPLEMENTATION_ADMISSION_{result['state']}",
        "result": result,
        "fail_closed": True,
        "credential_authority": CURRENT_AUTHORITY,
        "github_token_required": False,
        "owner_source_mutation_performed": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_OWNER_ADMISSION_EVIDENCE_ONLY",
    }
    receipt_path = RECEIPT_ROOT / f"{TASK_ID}.json"
    atomic_write(receipt_path, receipt)
    for manifest in result.get("owner_work_manifests", []):
        atomic_write(RECEIPT_ROOT / "owner-work" / f"{manifest['delta_id']}.json", manifest)

    state = result["state"]
    blocker = None
    if state != "COMPLETED":
        blocker = {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": result["reason"],
            "solution_required": True,
            "may_remain_blocked": state == "BLOCKED",
            "next_solution_action": "RECHECK_RECONCILIATION_OWNER_MATERIALIZATION_AND_ACTIVE_SCOPE_COLLISIONS"
        }
    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": receipt["transition_id"],
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "FORMALISM_MANIFOLD_IMPLEMENTATION_ADMISSION_RECHECK",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": f"receipts/formalism-manifold-implementation-admission/{TASK_ID}.json",
        "evidence_refs": [
            "control/formalism-manifold-implementation-admission.json",
            f"receipts/formalism-manifold-implementation-admission/{TASK_ID}.json"
        ],
        "blocker": blocker,
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "formalism_manifold_implementation_admission"}
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
