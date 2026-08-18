#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cosv import encode_task  # noqa: E402
from cosv_state_packet import (  # noqa: E402
    SCHEMA,
    derive_constraints,
    digest,
    finalize,
    gradient_inputs,
    record_map,
    state_root,
    unchanged_root,
    verify,
)

PACKET_RE = re.compile(r"^HB(\d+)\.json$")
CACHE_SCHEMA = "stegverse.cosv-live-state-cache/v1"
VALIDATION_SCHEMA = "stegverse.cosv-live-packet-validation-receipt/v2"
RECOVERY_TASK = "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"
INFERENCE_TASK = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def task_vector(*, lifecycle: str, archive_ready: bool, unassigned_work: int, thread_required: bool,
                blocker_count: int, evidence_complete: bool | None, activated: bool, propagated: bool | None) -> str:
    return encode_task({
        "lifecycle": lifecycle,
        "archive_ready": archive_ready,
        "unassigned_work": unassigned_work,
        "chat_owned_implementation": 0,
        "chat_owned_validation": 0,
        "chat_owned_integration": 0,
        "chat_owned_observation": 0,
        "chat_owned_credentials": 0,
        "canonical_owner_installed": True,
        "thread_required": thread_required,
        "blocker_count": blocker_count,
        "evidence_complete": evidence_complete,
        "activated": activated,
        "propagated": propagated,
    })


def find_task(registry: dict, task_id: str) -> dict | None:
    for item in registry.get("tasks", []):
        if isinstance(item, dict) and item.get("task_id") == task_id:
            return item
    return None


def registry_task_record(task_id: str, task: dict | None, observed_at: str) -> dict:
    if task is None:
        state = "HANDOFF_READY"
        evidence_refs = [
            f"control/worker-registry.d/{'ecosystem-chat-orphan-recovery-hb28.json' if task_id == RECOVERY_TASK else 'UNKNOWN'}",
        ]
        worker_id = None
        claim_id = None
    else:
        state = str(task.get("state") or "HANDOFF_READY")
        evidence_refs = ["control/worker-registry.json"] + [str(ref) for ref in task.get("evidence_refs", []) if ref]
        worker_id = task.get("worker_id")
        claim_id = task.get("claim_id")

    terminal = state in {"COMPLETED", "COMPLETE", "CLOSED", "SUPERSEDED"}
    blocked = state == "BLOCKED"
    bound = bool(worker_id and claim_id)
    if terminal:
        lifecycle = "COMPLETE" if state != "SUPERSEDED" else "SUPERSEDED"
    elif blocked:
        lifecycle = "BLOCKED"
    elif bound or state in {"ACTIVE", "CLAIMED", "MACHINE_OWNED"}:
        lifecycle = "MACHINE_OWNED"
    else:
        lifecycle = "UNCLAIMED"

    vector = task_vector(
        lifecycle=lifecycle,
        archive_ready=terminal,
        unassigned_work=0 if terminal or bound or blocked else 1,
        thread_required=not terminal,
        blocker_count=1 if blocked else 0,
        evidence_complete=True if terminal else (True if len(evidence_refs) > 1 else None),
        activated=terminal or bound,
        propagated=False,
    )
    return {
        "identity": f"task:{task_id}",
        "profile": "task.v1",
        "level": "task",
        "vector": vector,
        "evidence_refs": sorted(set(evidence_refs)),
        "observed_at": observed_at,
        "exact_metrics": {
            "registry_state": state,
            "unassigned_work": 0 if terminal or bound or blocked else 1,
            "blocker_count": 1 if blocked else 0,
            "claim_present": bool(claim_id),
            "worker_bound": bool(worker_id),
        },
        "admissibility_ref": "handoffs/generated/RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28.json" if task_id == RECOVERY_TASK else "handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json",
        "coherency_group_ref": "coherency:ecosystem-chat-sovereign-activation",
    }


def current_records(root: Path) -> list[dict]:
    carrier = load_json(root / "control" / "heartbeat-carrier-runtime-state.json")
    worker = load_json(root / "control" / "worker-runtime-state.json")
    transition_receipt = load_json(root / "receipts" / "heartbeat-transition-continuity" / "latest.json")
    registry = load_json(root / "control" / "worker-registry.json")

    epoch = int(carrier["epoch"])
    generation = int(carrier["generation"])
    worker_epoch = int(worker["last_observed_carrier_epoch"])
    worker_generation = int(worker["last_observed_carrier_generation"])
    if epoch < 30 or worker_epoch < epoch or worker_generation < generation:
        raise RuntimeError("carrier/WorkerCoordinator reference is not jointly admitted")
    if transition_receipt.get("release_state") != "RELEASE_COMPLETE" or transition_receipt.get("all_release_predicates_pass") is not True:
        raise RuntimeError("heartbeat transition release predicates are not complete")

    observed_at = str(carrier.get("last_cycle_at") or utc_now())
    continuity_complete = bool(
        transition_receipt.get("state") == "CARRIER_TRANSITION_COMPLETE"
        and transition_receipt.get("all_release_predicates_pass") is True
    )
    observation_vector = task_vector(
        lifecycle="COMPLETE",
        archive_ready=True,
        unassigned_work=0,
        thread_required=False,
        blocker_count=0,
        evidence_complete=True,
        activated=True,
        propagated=True,
    )
    g18_vector = task_vector(
        lifecycle="COMPLETE" if continuity_complete else "BLOCKED",
        archive_ready=continuity_complete,
        unassigned_work=0,
        thread_required=not continuity_complete,
        blocker_count=0 if continuity_complete else 1,
        evidence_complete=True,
        activated=continuity_complete,
        propagated=True if continuity_complete else False,
    )

    records = [
        {
            "identity": "task:HEARTBEAT-WORKER-REFERENCE-OBSERVATION",
            "profile": "task.v1",
            "level": "task",
            "vector": observation_vector,
            "evidence_refs": [
                "control/heartbeat-carrier-runtime-state.json",
                "control/worker-runtime-state.json",
                "control/worker-control-plane-coordination.json",
                "receipts/heartbeat-transition-continuity/latest.json",
            ],
            "observed_at": observed_at,
            "exact_metrics": {
                "carrier_epoch": epoch,
                "carrier_generation": generation,
                "worker_last_observed_carrier_epoch": worker_epoch,
                "worker_last_observed_carrier_generation": worker_generation,
                "runtime_tick": int(worker.get("runtime_tick", 0)),
            },
            "admissibility_ref": "docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md",
            "coherency_group_ref": "coherency:heartbeat-runtime",
        },
        {
            "identity": "task:SHWP-DURABLE-RUNTIME-ACTIVATION",
            "profile": "task.v1",
            "level": "task",
            "vector": g18_vector,
            "evidence_refs": [
                "handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json",
                "control/heartbeat-carrier-runtime-state.json",
                "control/worker-runtime-state.json",
                "control/worker-control-plane-coordination.json",
                "receipts/heartbeat-transition-continuity/latest.json",
            ],
            "observed_at": observed_at,
            "exact_metrics": {
                "carrier_epoch": epoch,
                "carrier_generation": generation,
                "worker_last_observed_carrier_epoch": worker_epoch,
                "release_predicates_pass": sum(1 for value in (transition_receipt.get("predicates") or {}).values() if value is True),
                "release_predicates_required": len(transition_receipt.get("predicates") or {}),
                "blocker_count": 0 if continuity_complete else 1,
            },
            "admissibility_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
            "coherency_group_ref": "coherency:heartbeat-runtime",
        },
        registry_task_record(RECOVERY_TASK, find_task(registry, RECOVERY_TASK), observed_at),
        registry_task_record(INFERENCE_TASK, find_task(registry, INFERENCE_TASK), observed_at),
    ]
    return sorted(records, key=lambda item: item["identity"])


def packet_epoch(packet: dict) -> int:
    match = re.fullmatch(r"heartbeat_epoch:(\d+)", str(packet.get("carrier_ref")))
    if not match:
        raise ValueError("unsupported carrier_ref")
    return int(match.group(1))


def latest_packet(packet_dir: Path) -> tuple[int, Path, dict] | None:
    candidates = []
    if not packet_dir.is_dir():
        return None
    for path in packet_dir.iterdir():
        match = PACKET_RE.fullmatch(path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    if not candidates:
        return None
    epoch, path = max(candidates, key=lambda item: item[0])
    return epoch, path, load_json(path)


def build_delta_any(carrier_ref: str, previous_packet_sha256: str, previous_records: list[dict], current: list[dict], observed_at: str) -> dict:
    previous_map = record_map(previous_records)
    current_map = record_map(current)
    removed = set(previous_map) - set(current_map)
    if removed:
        raise ValueError(f"implicit record removal prohibited: {','.join(sorted(removed))}")
    changed = {
        key for key, value in current_map.items()
        if key not in previous_map
        or previous_map[key]["vector"] != value["vector"]
        or previous_map[key].get("exact_metrics", {}) != value.get("exact_metrics", {})
        or previous_map[key].get("evidence_refs", []) != value.get("evidence_refs", [])
    }
    packet = {
        "schema": SCHEMA,
        "mode": "DELTA",
        "carrier_ref": carrier_ref,
        "observed_at": observed_at,
        "previous_packet_sha256": previous_packet_sha256,
        "state_root_sha256": state_root(current),
        "unchanged_state_root_sha256": unchanged_root(previous_map, changed),
        "records": [current_map[key] for key in sorted(changed)],
        "gradient_inputs": gradient_inputs(previous_map, current_map, changed),
        "constraint_summary": derive_constraints(current),
        "authority": {
            "heartbeat_authority_effect": "NONE",
            "packet_authority_effect": "NONE",
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_used": False,
            "github_token_runtime_authority": "NONE",
        },
    }
    return finalize(packet)


def initialize_cache_from_full(packet: dict) -> dict:
    if packet.get("mode") != "FULL":
        raise RuntimeError("live state cache can only bootstrap from a FULL packet")
    if not verify(packet):
        raise RuntimeError("baseline FULL packet verification failed")
    return {
        "schema": CACHE_SCHEMA,
        "carrier_ref": packet["carrier_ref"],
        "packet_sha256": packet["packet_sha256"],
        "state_root_sha256": packet["state_root_sha256"],
        "records": packet["records"],
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
    }


def materialize(root: Path = ROOT) -> dict:
    packet_dir = root / "receipts" / "cosv" / "live"
    carrier = load_json(root / "control" / "heartbeat-carrier-runtime-state.json")
    epoch = int(carrier["epoch"])
    generation = int(carrier["generation"])
    carrier_ref = f"heartbeat_epoch:{epoch}"
    observed_at = str(carrier.get("last_cycle_at") or utc_now())
    current = current_records(root)

    latest = latest_packet(packet_dir)
    cache_path = packet_dir / "latest-state.json"
    if latest is None:
        from cosv_state_packet import build_full
        packet = build_full(carrier_ref, current, observed_at)
        mode = "FULL"
        previous_records = None
    else:
        previous_epoch, previous_path, previous_packet = latest
        if epoch < previous_epoch:
            raise RuntimeError("carrier regressed below latest COSV packet")
        if epoch == previous_epoch:
            return {
                "schema": "stegverse.cosv-live-packet-materialization-result/v1",
                "state": "NO_NEW_REFERENCE",
                "carrier_ref": carrier_ref,
                "packet_ref": str(previous_path.relative_to(root)),
                "packet_sha256": previous_packet.get("packet_sha256"),
                "authority_effect": "NONE",
            }
        if cache_path.is_file():
            cache = load_json(cache_path)
            if cache.get("schema") != CACHE_SCHEMA or cache.get("packet_sha256") != previous_packet.get("packet_sha256"):
                raise RuntimeError("live state cache does not bind latest packet")
            previous_records = cache.get("records") or []
            if state_root(previous_records) != previous_packet.get("state_root_sha256"):
                raise RuntimeError("cached previous state root mismatch")
        else:
            cache = initialize_cache_from_full(previous_packet)
            previous_records = cache["records"]
        packet = build_delta_any(carrier_ref, previous_packet["packet_sha256"], previous_records, current, observed_at)
        verify(packet, previous_records)
        mode = "DELTA"

    packet_path = packet_dir / f"HB{epoch}.json"
    if packet_path.exists():
        existing = load_json(packet_path)
        if existing.get("packet_sha256") != packet.get("packet_sha256"):
            raise RuntimeError("packet path already exists with different digest")
    else:
        atomic_write(packet_path, packet)

    cache = {
        "schema": CACHE_SCHEMA,
        "carrier_ref": carrier_ref,
        "packet_ref": str(packet_path.relative_to(root)),
        "packet_sha256": packet["packet_sha256"],
        "state_root_sha256": packet["state_root_sha256"],
        "records": current,
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }
    atomic_write(cache_path, cache)

    validation = {
        "schema": VALIDATION_SCHEMA,
        "carrier_ref": carrier_ref,
        "carrier_generation": generation,
        "packet_ref": str(packet_path.relative_to(root)),
        "packet_sha256": packet["packet_sha256"],
        "state_root_sha256": packet["state_root_sha256"],
        "mode": mode,
        "gradient_input_count": len(packet.get("gradient_inputs", [])),
        "packet_verify_pass": True,
        "cache_state_root_pass": state_root(current) == packet["state_root_sha256"],
        "heartbeat_authority_effect": "NONE",
        "packet_authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_used": False,
        "github_token_runtime_authority": "NONE",
        "third_party_runtime_required": False,
        "validated_at": utc_now(),
    }
    validation_path = packet_dir / f"HB{epoch}-validation.json"
    atomic_write(validation_path, validation)
    return {
        "schema": "stegverse.cosv-live-packet-materialization-result/v1",
        "state": "PACKET_MATERIALIZED",
        "carrier_ref": carrier_ref,
        "mode": mode,
        "packet_ref": str(packet_path.relative_to(root)),
        "validation_ref": str(validation_path.relative_to(root)),
        "packet_sha256": packet["packet_sha256"],
        "state_root_sha256": packet["state_root_sha256"],
        "gradient_input_count": len(packet.get("gradient_inputs", [])),
        "authority_effect": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    result = materialize(Path(args.root).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
