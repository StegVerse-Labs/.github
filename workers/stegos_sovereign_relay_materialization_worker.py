#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from workers.stegos_sovereign_relay_bridge import find_stegos_root, materialize_relay

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001"
RECEIPT = ROOT / "receipts" / "stegos-sovereign-relay" / f"{TASK_ID}.json"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def response(*, state: str, transition: str, sequence: int, epoch: int, blocker: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": sequence,
        "expected_next_transition": None if state == "COMPLETED" else "SOVEREIGN_RELAY_LEASE_OPEN",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 8,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [
            str(RECEIPT.relative_to(ROOT)),
            "workers/stegos_sovereign_relay_materialization_worker.py",
            "workers/stegos_sovereign_relay_bridge.py",
            "docs/STEGOS_SOVEREIGN_RELAY_MATERIALIZATION_MIRROR_HANDOFF.md",
            "StegVerse-Labs/StegOS@a91838bf1c20eaacbbdada7e391aa462a862d72e",
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "stegos_sovereign_relay_materialization",
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


def runtime_base() -> Path:
    explicit = os.environ.get("STEGVERSE_RELAY_RUNTIME_BASE")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (Path.home() / ".stegverse" / "runtime" / "ephemeral-relays").resolve()


def main() -> int:
    invocation = json.load(__import__("sys").stdin)
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 3

    execution = handoff.get("execution") or {}
    required = {"runtime_observation", "bounded_process_execution", "sovereign_relay_materialization"}
    if not required.issubset(set(execution.get("required_capabilities") or [])):
        return 4
    if "receipts/stegos-sovereign-relay/**" not in set(execution.get("allowed_paths") or []):
        return 5

    base = {
        "schema": "stegverse.stegos.sovereign-relay-worker-receipt/v1",
        "task_id": TASK_ID,
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

    stegos_root = find_stegos_root(ROOT)
    if stegos_root is None:
        blocked = blocker(
            "The merged StegOS sovereign relay source is not materialized on this sovereign carrier.",
            "Materialize the pinned StegOS source on the existing sovereign carrier through an admitted credential-free source path; do not add another machine or hosted runtime.",
            "find_stegos_root resolves the merged ESRL controller, relay adapter, relay service, and capacity binding source surfaces",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "STEGOS_RELAY_SOURCE_MATERIALIZATION_REQUIRED", "relay_lease_open": False, "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], sequence=1, epoch=epoch, blocker=blocked), __import__("sys").stdout)
        print()
        return 0

    request = execution.get("relay_activation_request")
    if not isinstance(request, dict):
        blocked = blocker(
            "The worker handoff does not contain an admitted sovereign relay activation request.",
            "Project one admitted capacity-event request into the executable handoff under the existing StegOS capacity policy.",
            "execution.relay_activation_request has schema v1 and admission_state ADMITTED",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "RELAY_ACTIVATION_REQUEST_REQUIRED", "stegos_root": str(stegos_root), "relay_lease_open": False, "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], sequence=2, epoch=epoch, blocker=blocked), __import__("sys").stdout)
        print()
        return 0

    try:
        result = materialize_relay(control_root=ROOT, stegos_root=stegos_root, runtime_base=runtime_base(), request=request)
    except Exception as exc:
        blocked = blocker(
            f"Sovereign relay materialization failed closed: {type(exc).__name__}: {exc}",
            "Repair the exact deployment-local source/runtime predicate and retry this same fenced task; preserve G18, TV/TVC, and route authority boundaries.",
            "the merged ESRL controller returns validated runtime materialization evidence with lease_state LEASE_OPEN",
        )
        receipt = {**base, "state": "ACTIVE", "transition_id": "SOVEREIGN_RELAY_MATERIALIZATION_REPAIR_REQUIRED", "stegos_root": str(stegos_root), "relay_lease_open": False, "error": f"{type(exc).__name__}:{exc}", "blocker": blocked}
        atomic_write(RECEIPT, receipt)
        json.dump(response(state="ACTIVE", transition=receipt["transition_id"], sequence=3, epoch=epoch, blocker=blocked), __import__("sys").stdout)
        print()
        return 0

    evidence = result.get("evidence") or {}
    predicates = {
        "lease_open": evidence.get("lease_state") == "LEASE_OPEN",
        "runtime_instantiated": evidence.get("runtime_instantiated") is True,
        "local_identity_verified": evidence.get("local_identity_verified") is True,
        "bounded_rendezvous_open": evidence.get("bounded_rendezvous_open") is True,
        "public_identity_verified": evidence.get("public_identity_verified") is True,
        "route_not_admitted": evidence.get("route_admitted") is False,
        "egress_not_executed": evidence.get("outbound_egress_executed") is False,
        "credential_authority_preserved": evidence.get("credential_authority") == "TV/TVC",
        "credential_material_absent": evidence.get("credential_material_present") is False,
        "canonical_transition_not_committed": evidence.get("canonical_transition_committed") is False,
    }
    complete = all(predicates.values())
    receipt = {
        **base,
        "state": "COMPLETED" if complete else "ACTIVE",
        "transition_id": "SOVEREIGN_RELAY_LEASE_OPEN" if complete else "SOVEREIGN_RELAY_EVIDENCE_INCOMPLETE",
        "stegos_root": str(stegos_root),
        "runtime_base": str(runtime_base()),
        "relay_lease_open": complete,
        "predicates": predicates,
        "materialization_evidence": evidence,
        "runtime": result.get("runtime"),
        "rendezvous": result.get("rendezvous"),
    }
    atomic_write(RECEIPT, receipt)
    json.dump(response(state=receipt["state"], transition=receipt["transition_id"], sequence=4, epoch=epoch), __import__("sys").stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
