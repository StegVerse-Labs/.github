#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from workers.stegos_sovereign_relay_bridge import find_stegos_root, materialize_relay

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001"
PARENT_TASK_ID = "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001"
PARENT_RECEIPT = ROOT / "receipts" / "stegos-sovereign-relay" / f"{PARENT_TASK_ID}.json"
RECEIPT = ROOT / "receipts" / "stegos-sovereign-relay" / f"{TASK_ID}.json"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def runtime_base() -> Path:
    explicit = os.environ.get("STEGVERSE_RELAY_RUNTIME_BASE")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (Path.home() / ".stegverse" / "runtime" / "ephemeral-relays").resolve()


def response(*, state: str, transition: str, epoch: int, blocker: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "RELAY_NODE_KV_CONTINUITY_VERIFIED",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 8,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [
            str(RECEIPT.relative_to(ROOT)),
            str(PARENT_RECEIPT.relative_to(ROOT)),
            "workers/stegos_relay_node_kv_continuity_worker.py",
            "docs/STEGOS_RELAY_NODE_KV_CONTINUITY_RUNTIME_MIRROR_HANDOFF.md",
            "StegVerse-Labs/StegOS@690b02f4b54271e67717a3180149a07a5aa44ed0",
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 2,
            "external_cost_usd": 0,
            "task_class": "stegos_relay_node_kv_continuity",
        },
    }
    if blocker is not None:
        result["blocker"] = blocker
    return result


def blocker(problem: str, action: str, release: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": action,
        "machine_observable_release_condition": release,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "human_action_required": False,
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _recreation_request(first_request: dict[str, Any], first_evidence: dict[str, Any]) -> dict[str, Any]:
    request = copy.deepcopy(first_request)
    generation = int(first_evidence["generation"]) + 1
    request["capacity_event_id"] = f"{first_request['capacity_event_id']}-RECREATE-G{generation}"
    request["source_receipt_id"] = f"{first_request['source_receipt_id']}-RECREATE-G{generation}"
    request["generation"] = generation
    request["production_capacity_deficit_claimed"] = False
    request["route_admitted"] = False
    request["outbound_egress_authorized"] = False
    return request


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 3

    execution = handoff.get("execution") or {}
    required = {"runtime_observation", "bounded_process_execution", "durable_state_reconstruction"}
    if not required.issubset(set(execution.get("required_capabilities") or [])):
        return 4
    if "receipts/stegos-sovereign-relay/**" not in set(execution.get("allowed_paths") or []):
        return 5

    base = {
        "schema": "stegverse.stegos.relay-node-kv-continuity-worker-receipt/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "github_token_used": False,
        "non_tv_tvc_secret_or_token_used": False,
        "heartbeat_grants_execution_authority": False,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "route_admitted": False,
        "outbound_egress_executed": False,
        "canonical_transition_committed": False,
    }

    parent = _load_json(PARENT_RECEIPT)
    if not parent or parent.get("state") != "COMPLETED" or parent.get("transition_id") != "SOVEREIGN_RELAY_LEASE_OPEN":
        blocked = blocker(
            "The authentic parent SOVEREIGN_RELAY_LEASE_OPEN receipt has not yet been observed.",
            "Allow the already-admitted parent relay-materialization task to complete on the deployment-local sovereign WorkerCoordinator.",
            "the parent receipt is COMPLETED with transition_id SOVEREIGN_RELAY_LEASE_OPEN",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "PARENT_RELAY_LEASE_OPEN_REQUIRED", "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], epoch=epoch, blocker=blocked), sys.stdout)
        print()
        return 0

    first_evidence = parent.get("materialization_evidence")
    first_runtime = parent.get("runtime")
    if not isinstance(first_evidence, dict) or not isinstance(first_runtime, dict):
        blocked = blocker(
            "The parent receipt is terminal but lacks complete runtime materialization evidence.",
            "Repair the parent evidence projection without manufacturing a new runtime observation.",
            "parent receipt contains materialization_evidence and runtime objects from the same LEASE_OPEN execution",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "PARENT_RELAY_EVIDENCE_REPAIR_REQUIRED", "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], epoch=epoch, blocker=blocked), sys.stdout)
        print()
        return 0

    stegos_root = find_stegos_root(ROOT)
    if stegos_root is None:
        blocked = blocker(
            "Merged StegOS continuity source is not materialized on the sovereign carrier.",
            "Materialize the pinned StegOS source through the existing credential-free sovereign source path.",
            "find_stegos_root resolves relay continuity and runtime materialization source surfaces",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "STEGOS_CONTINUITY_SOURCE_REQUIRED", "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], epoch=epoch, blocker=blocked), sys.stdout)
        print()
        return 0

    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))
    from stegos.relay_node_kv_continuity import (
        build_teardown_observation,
        prove_node_kv_recreation_continuity,
        validate_node_kv_continuity_evidence,
    )
    from stegos.sovereign_ephemeral_node_adapter import SovereignEphemeralNodeAdapter

    activation_request = execution.get("parent_activation_request")
    if not isinstance(activation_request, dict):
        return 6

    adapter = SovereignEphemeralNodeAdapter(
        sovereign_source_root=ROOT,
        runtime_base=runtime_base(),
        stegos_source_root=stegos_root,
    )
    try:
        release_result = dict(adapter.release(first_runtime))
        teardown = dict(build_teardown_observation(materialization_evidence=first_evidence, release_result=release_result))
        recreate_request = _recreation_request(activation_request, first_evidence)
        recreated = materialize_relay(
            control_root=ROOT,
            stegos_root=stegos_root,
            runtime_base=runtime_base(),
            request=recreate_request,
        )
        recreated_evidence = dict(recreated["evidence"])
        continuity = dict(
            prove_node_kv_recreation_continuity(
                first=first_evidence,
                teardown=teardown,
                recreated=recreated_evidence,
            )
        )
        validate_node_kv_continuity_evidence(continuity)
    except Exception as exc:
        blocked = blocker(
            f"Relay teardown/recreation continuity failed closed: {type(exc).__name__}: {exc}",
            "Repair the exact deployment-local teardown/recreation predicate and retry under a fresh admitted fence; do not substitute hosted evidence.",
            "a real teardown plus distinct higher-generation recreation produces validated Node-KV continuity evidence",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "RELAY_NODE_KV_CONTINUITY_REPAIR_REQUIRED", "error": f"{type(exc).__name__}:{exc}", "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], epoch=epoch, blocker=blocked), sys.stdout)
        print()
        return 0

    receipt = {
        **base,
        "state": "COMPLETED",
        "transition_id": "RELAY_NODE_KV_CONTINUITY_VERIFIED",
        "first_materialization_evidence": first_evidence,
        "teardown_observation": teardown,
        "recreated_materialization_evidence": recreated_evidence,
        "recreated_runtime": recreated.get("runtime"),
        "recreated_rendezvous": recreated.get("rendezvous"),
        "continuity_evidence": continuity,
    }
    atomic_write(RECEIPT, receipt)
    json.dump(response(state="COMPLETED", transition=receipt["transition_id"], epoch=epoch), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
