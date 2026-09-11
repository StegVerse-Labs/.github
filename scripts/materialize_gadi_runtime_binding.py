#!/usr/bin/env python3
"""Materialize a non-authorizing GADI runtime-binding observation.

This projector reuses the canonical HB runtime-presence receipt. It does not create a
runtime, lease, claim/fence, InTr admission, credential, or execution authority. A
binding is emitted only when the current runtime-presence receipt names a concrete
runtime_root and resident.node_id and its referenced supervision receipt explicitly
identifies the canonical carrier + WorkerCoordinator runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
PROFILE_ID = "runtime-node:gadi-resident-execution-001"
PRESENCE_REL = Path("receipts/sovereign-host/runtime-presence.latest.json")
OUTPUT_REL = Path("state/gadi-resident-execution/runtime-binding.json")
CANONICAL_CARRIER_RUNTIME = "heartbeat_runtime.engine_v13.HeartbeatRuntime"
CANONICAL_WORKER_RUNTIME = "heartbeat_runtime.worker_runtime.WorkerCoordinator"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def canonical_hash(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def materialize(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    presence_path = runtime / PRESENCE_REL
    blockers: list[str] = []

    if not presence_path.is_file():
        blockers.append("RUNTIME_PRESENCE_RECEIPT_MISSING")
        presence: dict[str, Any] = {}
    else:
        try:
            presence = load(presence_path)
        except Exception:
            presence = {}
            blockers.append("RUNTIME_PRESENCE_RECEIPT_INVALID_JSON")

    resident = presence.get("resident") if isinstance(presence.get("resident"), dict) else {}
    heartbeat = presence.get("heartbeat_reference") if isinstance(presence.get("heartbeat_reference"), dict) else {}
    progress = presence.get("governed_progress") if isinstance(presence.get("governed_progress"), dict) else {}
    authority = presence.get("authority") if isinstance(presence.get("authority"), dict) else {}

    if presence and presence.get("schema") != "stegverse.hb-runtime-presence-resident-observability/v1":
        blockers.append("RUNTIME_PRESENCE_SCHEMA_MISMATCH")
    if presence and presence.get("runtime_root") != str(runtime):
        blockers.append("RUNTIME_ROOT_SUBJECT_MISMATCH")
    if resident.get("runtime_alive_observed") is not True:
        blockers.append("RUNTIME_ALIVE_NOT_OBSERVED")
    if resident.get("present_worker_runtime_observed") is not True:
        blockers.append("PRESENT_WORKER_RUNTIME_NOT_OBSERVED")
    if resident.get("worker_cycle_fresh") is not True:
        blockers.append("WORKER_CYCLE_NOT_FRESH")
    if not nonempty(resident.get("node_id")):
        blockers.append("RESIDENT_NODE_ID_MISSING")
    if heartbeat.get("heartbeat_grants_authority") is not False:
        blockers.append("HEARTBEAT_AUTHORITY_BOUNDARY_INVALID")
    if progress.get("runtime_signal_is_execution_receipt") is not False:
        blockers.append("RUNTIME_SIGNAL_EXECUTION_BOUNDARY_INVALID")
    if authority.get("credential_authority") != "TV/TVC":
        blockers.append("CREDENTIAL_AUTHORITY_MISMATCH")
    if authority.get("hb_authority_effect") != "NONE_REFERENCE_ONLY":
        blockers.append("HB_AUTHORITY_EFFECT_INVALID")
    if authority.get("projection_authority_effect") != "NONE_OBSERVATION_ONLY":
        blockers.append("PROJECTION_AUTHORITY_EFFECT_INVALID")
    if authority.get("github_token_runtime_authority") != "NONE":
        blockers.append("GITHUB_TOKEN_RUNTIME_AUTHORITY_INVALID")

    supervision_ref = resident.get("runtime_evidence_ref")
    supervision: dict[str, Any] = {}
    supervision_path: Path | None = None
    if not nonempty(supervision_ref):
        blockers.append("SUPERVISION_EVIDENCE_REF_MISSING")
    else:
        candidate = Path(str(supervision_ref))
        supervision_path = candidate if candidate.is_absolute() else runtime / candidate
        try:
            supervision_path = supervision_path.resolve()
            supervision_path.relative_to(runtime)
        except Exception:
            supervision_path = None
            blockers.append("SUPERVISION_EVIDENCE_ESCAPES_RUNTIME")
        if supervision_path is not None:
            if not supervision_path.is_file():
                blockers.append("SUPERVISION_EVIDENCE_MISSING")
            else:
                try:
                    supervision = load(supervision_path)
                except Exception:
                    blockers.append("SUPERVISION_EVIDENCE_INVALID_JSON")

    if supervision:
        if supervision.get("canonical_carrier_runtime") != CANONICAL_CARRIER_RUNTIME:
            blockers.append("CANONICAL_CARRIER_RUNTIME_IDENTITY_MISSING")
        if supervision.get("worker_runtime") != CANONICAL_WORKER_RUNTIME:
            blockers.append("CANONICAL_WORKER_RUNTIME_IDENTITY_MISSING")
        if supervision.get("carrier_active") is not True or supervision.get("worker_active") is not True:
            blockers.append("CANONICAL_SUPERVISION_NOT_ACTIVE")
        if supervision.get("separate_carrier_and_worker_processes") is not True:
            blockers.append("CARRIER_WORKER_SEPARATION_NOT_OBSERVED")
        if supervision.get("third_party_process_host_required") is not False:
            blockers.append("THIRD_PARTY_PROCESS_HOST_BOUNDARY_INVALID")
        if supervision.get("heartbeat_grants_execution_authority") is not False:
            blockers.append("SUPERVISION_HEARTBEAT_AUTHORITY_INVALID")

    if blockers:
        result = {
            "schema": "stegverse.gadi-runtime-binding-observation/v1",
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "profile_id": PROFILE_ID,
            "state": "RUNTIME_BINDING_UNOBSERVED_FAIL_CLOSED",
            "runtime_binding_ref": None,
            "runtime_root": str(runtime),
            "node_id": resident.get("node_id"),
            "source_presence_ref": str(PRESENCE_REL),
            "source_presence_sha256": digest(presence_path) if presence_path.is_file() else None,
            "blockers": sorted(set(blockers)),
            "claim_or_fence_granted": False,
            "runtime_lease_granted": False,
            "execution_authority_granted": False,
            "heartbeat_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_OBSERVATION_ONLY",
        }
        write(runtime / OUTPUT_REL, result)
        return result

    core = {
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "profile_id": PROFILE_ID,
        "runtime_root": str(runtime),
        "node_id": str(resident["node_id"]),
        "canonical_carrier_runtime": CANONICAL_CARRIER_RUNTIME,
        "canonical_worker_runtime": CANONICAL_WORKER_RUNTIME,
        "source_presence_sha256": digest(presence_path),
        "source_supervision_sha256": digest(supervision_path) if supervision_path is not None else None,
    }
    binding_hash = canonical_hash(core)
    result = {
        "schema": "stegverse.gadi-runtime-binding-observation/v1",
        **core,
        "state": "CURRENT_RUNTIME_SUBJECT_BOUND",
        "runtime_binding_ref": f"runtime://gadi/{binding_hash}",
        "source_presence_ref": str(PRESENCE_REL),
        "source_supervision_ref": str(supervision_path.relative_to(runtime)) if supervision_path is not None else None,
        "runtime_alive_observed": True,
        "present_worker_runtime_observed": True,
        "worker_cycle_fresh": True,
        "claim_or_fence_granted": False,
        "runtime_lease_granted": False,
        "execution_authority_granted": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    write(runtime / OUTPUT_REL, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "CURRENT_RUNTIME_SUBJECT_BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
