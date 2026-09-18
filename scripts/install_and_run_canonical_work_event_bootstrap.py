#!/usr/bin/env python3
"""Install the CanonicalWork route and run one bounded event bootstrap.

This wrapper is intended for an admitted StegVerse resident execution context.
Before any route installation or task mutation, it performs a non-authorizing
Task Registry collision check-in. Only CONTINUE may proceed automatically.
COORDINATE_CONVERGENCE and every STOP_* disposition fail closed before mutation.

A newly registered task may reach a resident as an exact canonical task shard
before that resident's monolithic Task Registry projection has refreshed. In that
case this wrapper may refresh only the resident monolithic *projection* by adding
the exact shard row before collision preflight. This does not create task identity,
mint authority, or overwrite an existing task row.
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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK_ID = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RUNTIME_PROFILE_MAP_TASK_ID = "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
GLOBAL_MEASUREMENT_TASK_ID = "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001"
STEGBROWSER_TASK_ID = "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
STEGBROWSER_RUNTIME_CONSUMPTION_TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
GLOBAL_CONVERGENCE_TASK_IDS = {
    RUNTIME_PROFILE_MAP_TASK_ID,
    GLOBAL_MEASUREMENT_TASK_ID,
    STEGBROWSER_TASK_ID,
    STEGBROWSER_RUNTIME_CONSUMPTION_TASK_ID,
}
GLOBAL_HELPER_REL = Path("scripts/run_global_runtime_node_profile_convergence.py")
GLOBAL_BASE_HELPER_REL = Path("scripts/run_global_runtime_evidence_convergence.py")
GLOBAL_PROJECTION_REL = Path("control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json")
GLOBAL_NODE_PROFILES_REL = Path("control/runtime-node-profiles.json")
COLLISION_EVALUATOR_REL = Path("scripts/evaluate_task_registry_collision_checkin.py")
COLLISION_SCHEMA = "stegverse.task-registry-checkin-disposition/v1"
CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=str(ROOT), check=True)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def refresh_registry_projection_from_shard(task_id: str, registry_path: Path) -> dict:
    """Refresh a stale resident monolithic projection from one exact task shard.

    The shard must already exist in the same canonical source/runtime tree. Existing
    monolithic task rows are never replaced. The operation is idempotent and has no
    authority effect; it only makes an already-registered identity visible to the
    existing collision/bootstrap path.
    """
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("tasks"), list):
        raise RuntimeError("canonical registry projection invalid")
    matches = [row for row in registry["tasks"] if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) > 1:
        raise RuntimeError("canonical task identity duplicated in monolithic projection")
    if matches:
        return {"state": "MONOLITHIC_IDENTITY_PRESENT", "task_id": task_id, "projection_refreshed": False, "authority_effect": "NONE"}

    shard_path = ROOT / "data" / "canonical-task-records" / f"{task_id}.json"
    if not shard_path.is_file():
        raise RuntimeError("canonical task identity absent from monolithic projection and exact shard")
    shard = json.loads(shard_path.read_text(encoding="utf-8"))
    if not isinstance(shard, dict) or shard.get("task_id") != task_id:
        raise RuntimeError("canonical task shard identity mismatch")

    projected = dict(registry)
    projected["tasks"] = list(registry["tasks"]) + [shard]
    projected["generation"] = int(registry.get("generation", 0)) + 1
    projected["status"] = "STALE_REGISTRY_EXACT_SHARD_PROJECTION_REFRESHED"
    nonclaims = list(projected.get("nonclaims") or [])
    claim = "EXACT_SHARD_PROJECTION_REFRESH_DOES_NOT_CREATE_TASK_IDENTITY_OR_EXECUTION_AUTHORITY"
    if claim not in nonclaims:
        nonclaims.append(claim)
    projected["nonclaims"] = nonclaims
    atomic_json(registry_path, projected)

    check = json.loads(registry_path.read_text(encoding="utf-8"))
    post = [row for row in check.get("tasks", []) if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(post) != 1 or post[0] != shard:
        raise RuntimeError("canonical task shard projection refresh verification failed")
    return {
        "state": "EXACT_SHARD_PROJECTED_INTO_MONOLITHIC_RUNTIME_REGISTRY",
        "task_id": task_id,
        "projection_refreshed": True,
        "shard_ref": str(shard_path),
        "registry_ref": str(registry_path),
        "authority_effect": "NONE",
    }


def collision_preflight(task_id: str, registry_path: Path) -> dict:
    evaluator = ROOT / COLLISION_EVALUATOR_REL
    if not evaluator.is_file():
        raise RuntimeError("Task Registry collision evaluator missing; fail closed before Canonical Work mutation")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_generation = registry.get("generation")
    if not isinstance(registry_generation, int) or registry_generation < 0:
        raise RuntimeError("canonical Task Registry generation unavailable")
    proc = subprocess.run(
        [sys.executable, str(evaluator)],
        cwd=str(ROOT),
        input=json.dumps({"task_id": task_id, "caller_surface": CALLER_SURFACE, "observed_registry_generation": registry_generation}),
        text=True,
        capture_output=True,
        check=True,
    )
    try:
        result = json.loads(proc.stdout)
    except Exception as exc:
        raise RuntimeError("Task Registry collision evaluator returned non-JSON output") from exc
    if result.get("schema") != COLLISION_SCHEMA or result.get("task_id") != task_id:
        raise RuntimeError("Task Registry collision disposition identity/schema mismatch")
    if result.get("authority_effect") != "NONE":
        raise RuntimeError("Task Registry collision disposition attempted authority effect")
    if result.get("caller_surface") != CALLER_SURFACE:
        raise RuntimeError("Task Registry collision disposition caller surface mismatch")
    if result.get("caller_surface_attestation_proven") is not False:
        raise RuntimeError("Task Registry collision disposition may not claim authentic caller attestation")
    disposition = str(result.get("disposition") or "")
    if disposition != "CONTINUE":
        raise RuntimeError("TASK_REGISTRY_CHECKIN:" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_exact(source_root: Path, rel: Path) -> Path:
    source = source_root / rel
    destination = ROOT / rel
    if not source.is_file():
        raise RuntimeError(f"global convergence source missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        if not destination.is_file() or sha256(destination) != sha256(source):
            shutil.copy2(source, destination)
    if not destination.is_file() or sha256(destination) != sha256(source):
        raise RuntimeError(f"global convergence materialization mismatch: {rel}")
    return destination


def resolve_local_source_root() -> Path:
    candidates = []
    configured = str(os.environ.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    if configured:
        candidates.append(Path(configured).expanduser().resolve())
    candidates.append(ROOT)
    for candidate in candidates:
        required = (GLOBAL_HELPER_REL, GLOBAL_BASE_HELPER_REL, GLOBAL_PROJECTION_REL, GLOBAL_NODE_PROFILES_REL)
        if all((candidate / rel).is_file() for rel in required):
            return candidate
    raise RuntimeError("already-local global runtime-node convergence source is not materialized")


def run_global_convergence_if_applicable(task_id: str) -> None:
    if task_id not in GLOBAL_CONVERGENCE_TASK_IDS:
        return
    source_root = resolve_local_source_root()
    helper = materialize_exact(source_root, GLOBAL_HELPER_REL)
    materialize_exact(source_root, GLOBAL_BASE_HELPER_REL)
    materialize_exact(source_root, GLOBAL_PROJECTION_REL)
    materialize_exact(source_root, GLOBAL_NODE_PROFILES_REL)
    run([sys.executable, str(helper), "--source-root", str(source_root), "--runtime-root", str(ROOT)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--consumer-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--without-carrier-binding", action="store_true")
    args = parser.parse_args()

    registry_path = Path(args.registry).expanduser().resolve()
    refresh = refresh_registry_projection_from_shard(args.task_id, registry_path)
    print("TASK_REGISTRY_PROJECTION_REFRESH:" + json.dumps(refresh, sort_keys=True, separators=(",", ":")))
    checkin = collision_preflight(args.task_id, registry_path)
    print("TASK_REGISTRY_CHECKIN:" + json.dumps(checkin, sort_keys=True, separators=(",", ":")))

    installer = str(ROOT / "scripts" / "install_canonical_work_universal_intr_route.py")
    bootstrap = str(ROOT / "scripts" / "run_canonical_work_event_bootstrap.py")
    run([sys.executable, installer])
    run([sys.executable, installer, "--check"])

    command = [
        sys.executable,
        bootstrap,
        "--task-id", args.task_id,
        "--runtime-root", str(Path(args.runtime_root).expanduser().resolve()),
        "--registry", str(registry_path),
        "--consumer-timeout-seconds", str(args.consumer_timeout_seconds),
    ]
    if args.without_carrier_binding:
        command.append("--without-carrier-binding")
    run(command)
    run_global_convergence_if_applicable(args.task_id)

    print(f"PASS: route installation/check completed and bounded CanonicalWork bootstrap returned success for {args.task_id}")
    if args.task_id in GLOBAL_CONVERGENCE_TASK_IDS:
        print("PASS: global HB-synchronized runtime-node profile convergence completed through the existing resident dispatcher")
    print("NONCLAIM: this wrapper does not itself prove WorkerCoordinator claim/fence, governed work, Master Records reconciliation, egress, or closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
