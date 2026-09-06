#!/usr/bin/env python3
"""Refresh static WorkerCoordinator source from an already-local canonical checkout.

This is deliberately not a source transport. It performs no network lookup, clone,
fetch, pull, credential acquisition, or repository mutation. Mutable runtime state
(receipts, checkpoints, carrier/worker state, claims/fences) is never copied from
source and is never deleted by refresh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

STATIC_DIRS = (
    Path("heartbeat_runtime"),
    Path("workers"),
    Path("handoffs"),
    Path("authorizations"),
    Path("schemas"),
    Path("cost-basis"),
    Path("management"),
    Path("state_language"),
    Path("source-bundles"),
    Path("review-packages"),
)
STATIC_FILES = (
    Path("scripts/run_worker_runtime.py"),
    Path("scripts/repair_resident_worker_presence.py"),
    Path("scripts/project_hb_runtime_presence.py"),
    Path("scripts/project_de006_runtime_observability.py"),
    Path("scripts/verify_stegos_parent_evidence_candidate.py"),
    Path("control/runtime-observability-consumers/decision-envelope-de006.json"),
    Path("scripts/refresh_and_execute_resident_task.py"),
    Path("scripts/run_independent_ecosystem_chat_parent.py"),
    Path("scripts/consume_resident_execution_request.py"),
    Path("scripts/consume_g18_resident_execution_request.py"),
    Path("scripts/consume_hil_resident_execution_request.py"),
    Path("scripts/consume_evaluator_intr_resident_execution_request.py"),
    Path("scripts/materialize_evaluator_intr_route_config.py"),
    Path("scripts/consume_sv002_public_observation_request.py"),
    Path("scripts/materialize_sv002_observation_route_config.py"),
    Path("scripts/serve_sv002_observation_intr_runtime.py"),
    Path("scripts/consume_hil_intr_materialization_request.py"),
    Path("scripts/consume_device_kv_intr_materialization_request.py"),
    Path("scripts/consume_device_kv_intr_materialization_request_base.py"),
    Path("scripts/workspace_device_kv_query_extension.py"),
    Path("scripts/personal_profile_device_kv_extension.py"),
    Path("scripts/materialize_personal_kv_provider_root.py"),
    Path("scripts/consume_publisher_intr_materialization_request.py"),
    Path("scripts/consume_kv_publisher_return_materialization_request.py"),
    Path("scripts/consume_hil_tvc_lifecycle_outbox.py"),
    Path("scripts/watch_hil_tvc_lifecycle_outbox.py"),
    Path("scripts/serve_hil_intr_materialization_ingress.py"),
    Path("scripts/serve_evaluator_intr_runtime.py"),
    Path("scripts/consume_ara_graph_resident_execution_request.py"),
    Path("scripts/consume_cmc028_resident_execution_request.py"),
    Path("scripts/run_sv_dn1_first_round_chain.py"),
    Path("scripts/consume_sv_dn1_resident_execution_request.py"),
    Path("scripts/run_bootstrap_v1_release_prep_chain.py"),
    Path("scripts/consume_bootstrap_v1_release_prep_request.py"),
    Path("scripts/serve_bootstrap_v1_intr_bundle_delivery.py"),
    Path("scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py"),
    Path("scripts/consume_stegos_kv_intr_chain_request.py"),
    Path("scripts/consume_resident_rendezvous.py"),
    Path("scripts/consume_tvc_broker_validation_request.py"),
    Path("scripts/bootstrap_tvc_pr92_validation_source.py"),
    Path("scripts/consume_sv002_self_characterization_request.py"),
    Path("scripts/consume_sv002_org_runtime_activation_request.py"),
    Path("scripts/consume_healer_sovereign_scheduler_request.py"),
    Path("scripts/consume_universal_governance_enforced_reference_request.py"),
    Path("scripts/consume_cross_framework_current_basis_v04_request.py"),
    Path("scripts/consume_stegverse001_bounded_autonomy_request.py"),
    Path("scripts/consume_one_shot_resident_stack_activation_request.py"),
    Path("scripts/consume_sv011_phase5_source_materialization_request.py"),
    Path("scripts/consume_sv011_phase5_resident_execution_request.py"),
    Path("scripts/consume_glm53_sovereign_lane_request.py"),
    Path("scripts/consume_erl_ai_economic_transparency_review_request.py"),
    Path("scripts/activate_resident_stack.py"),
    Path("scripts/continue_stegverse001_evidence_chain.py"),
    Path("scripts/dispatch_resident_execution_requests.py"),
    Path("scripts/consume_org_claim_allocator_request.py"),
    Path("scripts/allocate_claims.py"),
    Path("control/resident-execution-request.d/org-claim-allocator-001.json"),
    Path("scripts/refresh_and_dispatch_resident_requests.py"),
    Path("scripts/run_stegverse001_activation_progression.py"),
    Path("scripts/materialize_live_cosv_packet.py"),
    Path("scripts/cosv.py"),
    Path("scripts/cosv_state_packet.py"),
    Path("scripts/advance_heartbeat_transition.py"),
    Path("scripts/refresh_heartbeat_transition_receipt.py"),
    Path("scripts/project_worker_control_plane_from_carrier.py"),
    Path("scripts/verify_iphone_heartbeat_transition_receipt.py"),
    Path("scripts/refresh_sovereign_worker_runtime_source.py"),
    Path("scripts/run_stegindex_preflight.py"),
    Path("scripts/verify_stegindex_resident_operational_proof.py"),
)
CONTROL_DIRS = (
    Path("control/worker-registry.d"),
    Path("control/process-worker-adapters.d"),
    Path("control/task-vectors"),
    Path("control/resident-execution-request.d"),
)
CONTROL_FILES = (
    Path("control/process-worker-adapters.json"),
    Path("control/worker-capability-profiles.json"),
    Path("control/blocker-resolution-policy.json"),
    Path("control/stegindex-preflight-policy.json"),
    Path("control/task-vector-index.json"),
    Path("control/resident-execution-request.json"),
)
MUTABLE_FORBIDDEN_PREFIXES = (
    "receipts/",
    "checkpoints/",
    "events/",
    "heartbeats/",
)
MUTABLE_FORBIDDEN_FILES = {
    "control/heartbeat-state.json",
    "control/heartbeat-carrier-runtime-state.json",
    "control/worker-runtime-state.json",
    "control/worker-registry.json",
    "control/worker-control-plane-coordination.json",
    "control/worker-status.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    value = completed.stdout.strip().lower()
    return value if completed.returncode == 0 and len(value) == 40 else None


def _validate_roots(source_root: Path, runtime_root: Path) -> tuple[Path, Path]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if source == runtime:
        raise ValueError("source_root and runtime_root must be distinct")
    required = (
        source / "heartbeat_runtime/worker_runtime.py",
        source / "heartbeat_runtime/intr_derived_carrier.py",
        source / "scripts/run_worker_runtime.py",
        source / "control/worker-registry.json",
        source / "control/process-worker-adapters.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError("canonical source incomplete: " + ",".join(missing))
    runtime.mkdir(parents=True, exist_ok=True)
    return source, runtime


def _iter_copy_paths(source: Path) -> Iterable[Path]:
    for rel in STATIC_DIRS + CONTROL_DIRS:
        if (source / rel).is_dir():
            yield rel
    for rel in STATIC_FILES + CONTROL_FILES:
        if (source / rel).is_file():
            yield rel


def _assert_static_path(rel: Path) -> None:
    value = rel.as_posix()
    if value in MUTABLE_FORBIDDEN_FILES or any(value.startswith(prefix) for prefix in MUTABLE_FORBIDDEN_PREFIXES):
        raise ValueError(f"mutable runtime state may not be refreshed from source: {value}")


def _replace_dir(source: Path, destination: Path, staging_root: Path, rel: Path) -> int:
    _assert_static_path(rel)
    staged = staging_root / rel
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / rel, staged)
    backup = destination.with_name(destination.name + ".refresh-backup")
    if backup.exists():
        shutil.rmtree(backup)
    if destination.exists():
        destination.replace(backup)
    try:
        staged.replace(destination)
    except Exception:
        if backup.exists() and not destination.exists():
            backup.replace(destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)
    return sum(1 for path in destination.rglob("*") if path.is_file())


def _replace_file(source: Path, destination: Path, rel: Path) -> int:
    _assert_static_path(rel)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=destination.parent, delete=False) as handle:
        handle.write((source / rel).read_bytes())
        tmp = Path(handle.name)
    os.chmod(tmp, (source / rel).stat().st_mode & 0o777)
    tmp.replace(destination)
    return 1


def refresh(source_root: Path, runtime_root: Path) -> dict:
    source, runtime = _validate_roots(source_root, runtime_root)
    lock = runtime / ".worker-source-refresh.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError("worker source refresh already in progress") from exc

    staging = runtime / ".worker-source-refresh-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    copied_files = 0
    copied_paths: list[str] = []
    try:
        for rel in _iter_copy_paths(source):
            destination = runtime / rel
            if (source / rel).is_dir():
                copied_files += _replace_dir(source, destination, staging, rel)
            else:
                copied_files += _replace_file(source, destination, rel)
            copied_paths.append(rel.as_posix())
        source_head = _git_head(source)
        worker_sha = _sha256(runtime / "heartbeat_runtime/worker_runtime.py")
        receipt = {
            "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
            "refreshed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "source_root": str(source),
            "runtime_root": str(runtime),
            "source_git_head": source_head,
            "copied_static_paths": copied_paths,
            "copied_file_count": copied_files,
            "worker_runtime_sha256": worker_sha,
            "mutable_runtime_state_preserved": True,
            "network_fetch_performed": False,
            "source_repository_mutated": False,
            "credential_read_or_acquired": False,
            "github_token_required": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_LOCAL_SOURCE_REFRESH",
        }
        receipt_path = runtime / "receipts/sovereign-host/worker-source-refresh.latest.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        try:
            lock.rmdir()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh static sovereign WorkerCoordinator source from an already-local checkout.")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args()
    receipt = refresh(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
