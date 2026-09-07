#!/usr/bin/env python3
"""Materialize a manifest-bound reusable-task RTG/GTG/TT construct envelope.

This is a source-side deterministic constructor. It does not execute the task,
obtain WorkerCoordinator claims/fences, perform Interlock/InTr transitions,
acquire credentials, call providers, prove runtime execution, or write Master
Records. Those authority boundaries remain external and canonical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "reusable-task-registry.json"
COSV_INDEX = ROOT / "control" / "task-vector-index.json"
CONTRACT = ROOT / "data" / "reusable-task-ephemeral-construct-contract.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def resolve_reusable_task(registry: dict[str, Any], reusable_task_id: str) -> dict[str, Any]:
    matches = [x for x in registry.get("tasks", []) if x.get("reusable_task_id") == reusable_task_id]
    if len(matches) != 1:
        raise SystemExit(f"reusable task identity must resolve exactly once: {reusable_task_id}")
    return matches[0]


def verify_task_pointer(task_id: str | None, vector: str | None, index: dict[str, Any]) -> None:
    if (task_id is None) != (vector is None):
        raise SystemExit("task_id and cosv_task_vector must be provided together")
    if task_id is None:
        return
    matches = [x for x in index.get("tasks", []) if x.get("task_id") == task_id]
    if len(matches) != 1:
        raise SystemExit(f"canonical COSV task pointer must resolve exactly once: {task_id}")
    if matches[0].get("vector") != vector:
        raise SystemExit("task_id/COSV vector binding mismatch")


def derive_construct(definition: dict[str, Any], parameters: dict[str, Any], task_id: str | None) -> dict[str, Any]:
    identity = definition["reusable_task_id"]
    purpose = definition.get("purpose")
    authority_effect = definition.get("authority_effect", "NONE")
    common = {
        "reusable_task_id": identity,
        "task_id": task_id,
        "parameter_hash": sha256_json(parameters),
        "purpose": purpose,
    }
    return {
        "rtg": {
            **common,
            "role": "DESCRIBE_REALIZED_OR_CANDIDATE_RELATIONAL_TRANSITION_GEOMETRY",
            "candidate_context": parameters,
            "allow_authority": False,
        },
        "gtg": {
            **common,
            "role": "EVALUATE_WHETHER_CANDIDATE_REALIZATION_MAY_COMMIT",
            "authority_effect_from_reusable_definition": authority_effect,
            "interlock_intr_transition_required": True,
            "execution_proof": False,
        },
        "tt": {
            **common,
            "role": "RECORD_DECISION_COMMIT_EXECUTION_OBSERVATION_AND_CONTINUATION",
            "execution_observation_separation_required": True,
            "receipt_chain_required": True,
        },
    }


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_json(REGISTRY)
    index = load_json(COSV_INDEX)
    contract = load_json(CONTRACT)
    definition = resolve_reusable_task(registry, args.reusable_task_id)
    parameters = json.loads(args.parameters_json)
    if not isinstance(parameters, dict):
        raise SystemExit("parameters_json must decode to a JSON object")
    verify_task_pointer(args.task_id, args.cosv_task_vector, index)

    construct = derive_construct(definition, parameters, args.task_id)
    runner_templates = definition.get("runner_templates", [])
    recording_levels = definition.get("recording_levels", ["task", "goal", "master_records"])
    expiry_conditions = definition.get(
        "runner_expiry_conditions",
        ["INVOCATION_TERMINAL_BOUNDARY_REACHED", "OR_EXECUTION_AUTHORITY_EXPIRES"],
    )

    body = {
        "schema": "stegverse.reusable-task-invocation-manifest/v1",
        "invocation_id": args.invocation_id,
        "reusable_task_id": args.reusable_task_id,
        "task_id": args.task_id,
        "cosv_task_vector": args.cosv_task_vector,
        "parameters": parameters,
        "construct": construct,
        "runner_plan": {
            "ephemeral_where_possible": True,
            "materialization_refs": runner_templates,
            "expiry_conditions": expiry_conditions,
            "post_expiry_residual": "NON_EXECUTING_RECORDING_CONSTRUCT_IF_REQUIRED_RECORDING_REMAINS",
        },
        "recording": {
            "levels": recording_levels,
            "receipt_chain_required": True,
            "master_records_required_before_entropy_recovery": True,
            "entropy_recovery_conditions": contract["entropy_recovery"]["requires"],
        },
        "authority": {
            "execution_claim_and_fence": "WORKERCOORDINATOR",
            "governed_transition": "INTERLOCK_INTR",
            "credential_authority": "TV/TVC",
            "observed_reality_and_reconstruction": "MASTER_RECORDS",
            "github_token_runtime_authority": "NONE",
        },
        "source_refs": [
            "data/reusable-task-registry.json",
            "data/reusable-task-ephemeral-construct-contract.json",
            "management/COSV_PROFILE_V1.json",
            "StegVerse-Labs/StegScholar:papers/rtg-gtg-tt/cross-layer-contract.md",
        ],
    }
    body["manifest_hash"] = sha256_json(body)
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reusable-task-id", required=True)
    parser.add_argument("--invocation-id", required=True)
    parser.add_argument("--parameters-json", required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--cosv-task-vector")
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest = build_manifest(args)
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
