#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

EXPECTED_CAPABILITIES = {"repository_resolution", "sandbox_validation"}
RECEIPT_ROOT = Path("receipts/sovereign-runtime-activation")
NODE_MARKERS = [Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json"]
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def hosted_environment() -> bool:
    return any(truthy(os.environ.get(name)) for name in THIRD_PARTY_ENV_VARS)


def node_declaration() -> tuple[bool, str | None]:
    if truthy(os.environ.get("STEGVERSE_SOVEREIGN_NODE")):
        return True, "env:STEGVERSE_SOVEREIGN_NODE"
    for path in NODE_MARKERS:
        if path.is_file():
            return True, str(path)
    return False, None


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    scope = invocation.get("scope") or {}
    if not isinstance(epoch, int):
        return 3
    task_id = str(task.get("task_id") or "")
    if not task_id or "SHWP-DURABLE-RUNTIME-ACTIVATION" not in task_id:
        return 4
    required = set(scope.get("required_capabilities") or handoff.get("execution", {}).get("required_capabilities") or [])
    if not EXPECTED_CAPABILITIES.issubset(required):
        return 5
    claim_id = str(task.get("claim_id") or "")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not claim_id or not isinstance(fence, int) or fence < 1:
        return 6

    declared, declaration_ref = node_declaration()
    third_party = hosted_environment()
    if declared and not third_party:
        state = "COMPLETED"
        transition = "SOVEREIGN_NODE_DECLARATION_RESOLVED"
        expected = None
        blocker = None
    else:
        state = "BLOCKED"
        transition = "SOVEREIGN_NODE_COMPONENT_ESCALATION_REQUIRED"
        expected = "DERIVE_AND_REGISTER_RESOLUTION_TASK"
        blocker = {
            "trigger_type": "CONDITIONAL_CONSTRAINT",
            "dependency_class": "PHYSICAL_RESOURCE",
            "problem_statement": (
                "Repository-owner resolution cannot observe an eligible declared StegVerse-owned/federated node on this execution surface."
            ),
            "solution_required": True,
            "workaround_candidates": [
                "Component authority selects an existing declared StegVerse-owned/federated node and binds the resident heartbeat to it.",
                "Component authority promotes an already materialized StegVerse-002 micro-node only after its ownership, durable-state, and native-supervision predicates are machine-observable.",
                "Component authority constructs a new StegVerse-owned/federated carrier from the already released repository-local runtime capsule without hosted-provider production authority."
            ],
            "next_solution_action": "Escalate the unchanged physical-resource constraint to component authority; do not fabricate a node declaration or substitute a hosted platform.",
            "resolvable_by_current_worker": False,
            "escalation_target": "COMPONENT_AUTHORITY",
            "required_capabilities": ["component_resolution", "governance_validation"],
            "completion_evidence": [
                "A StegVerse-owned/federated node declaration is machine-observable.",
                "The node can execute the canonical native installer and verifier without GitHub-token or hosted-provider production authority."
            ],
        }

    receipt = {
        "schema": "stegverse.sovereign-node-repository-resolution-receipt/v0.1",
        "task_id": task_id,
        "claim_id": claim_id,
        "fencing_token": fence,
        "heartbeat_epoch": epoch,
        "state": state,
        "transition_id": transition,
        "node_declared": declared,
        "node_declaration_ref": declaration_ref,
        "hosted_environment_rejected": third_party,
        "github_token_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "NONE_RESOLUTION_ONLY",
    }
    receipt_path = RECEIPT_ROOT / f"{task_id}.repository-resolution.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": expected,
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": receipt_path.as_posix(),
        "evidence_refs": [receipt_path.as_posix()],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "sovereign_node_repository_resolution",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
