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
REGISTRY_SHARDS = ROOT / "source-bundles" / "reusable-task-registry.d"
COSV_INDEX = ROOT / "control" / "task-vector-index.json"
COSV_INDEX_SHARDS = ROOT / "control" / "task-vector-index.d"
CONTRACT = ROOT / "data" / "reusable-task-ephemeral-construct-contract.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    tasks = list(registry.get("tasks", []))
    if REGISTRY_SHARDS.is_dir():
        for path in sorted(REGISTRY_SHARDS.glob("*.json")):
            shard = load_json(path)
            if not isinstance(shard, dict) or not shard.get("reusable_task_id"):
                raise SystemExit(f"invalid reusable task registry shard: {path}")
            tasks.append(shard)
    identities = [x.get("reusable_task_id") for x in tasks if isinstance(x, dict)]
    duplicates = sorted({x for x in identities if x and identities.count(x) > 1})
    if duplicates:
        raise SystemExit("duplicate reusable task identities across registry surfaces: " + ",".join(duplicates))
    return {**registry, "tasks": tasks}


def load_effective_cosv_index() -> dict[str, Any]:
    """Resolve aggregate COSV rows plus canonical non-duplicating index shards.

    `control/task-vector-index.d` is an established canonical registration surface.
    A shard may add a task absent from the historical aggregate index, but may not
    rewrite an aggregate task's vector/provenance/non-authority fields.
    """
    aggregate = load_json(COSV_INDEX)
    if not isinstance(aggregate, dict) or aggregate.get("profile") not in (None, "task.v1"):
        raise SystemExit("canonical COSV task-vector index profile is invalid")
    tasks = aggregate.get("tasks")
    if not isinstance(tasks, list):
        raise SystemExit("canonical COSV task-vector index shape is invalid")
    rows: dict[str, dict[str, Any]] = {}
    for raw in tasks:
        if not isinstance(raw, dict) or not isinstance(raw.get("task_id"), str) or not raw.get("task_id"):
            raise SystemExit("canonical COSV task-vector index row is invalid")
        task_id = raw["task_id"]
        if task_id in rows:
            raise SystemExit(f"duplicate canonical COSV task-vector index row: {task_id}")
        rows[task_id] = dict(raw)

    if COSV_INDEX_SHARDS.is_dir():
        for path in sorted(COSV_INDEX_SHARDS.glob("*.json")):
            shard = load_json(path)
            if not isinstance(shard, dict) or shard.get("schema") != "stegverse.cosv-task-vector-index-entry/v1":
                continue
            task_id = shard.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise SystemExit(f"canonical COSV task-vector index shard missing task_id: {path}")
            existing = rows.get(task_id)
            if existing is None:
                rows[task_id] = dict(shard)
                continue
            for key in ("source_state_vector_ref", "vector", "vector_state", "authority_effect"):
                if shard.get(key) != existing.get(key):
                    raise SystemExit(f"canonical COSV task-vector index shard disagrees for {task_id}:{key}")

    return {**aggregate, "tasks": [rows[key] for key in sorted(rows)]}


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
    row = matches[0]
    if row.get("vector") != vector:
        raise SystemExit("task_id/COSV vector binding mismatch")
    if row.get("vector_state") not in (None, "EMITTED") or row.get("authority_effect") not in (None, "NONE"):
        raise SystemExit("canonical COSV task pointer is not non-authorizing EMITTED state")
    source_ref = row.get("source_state_vector_ref")
    if not isinstance(source_ref, str) or not source_ref:
        raise SystemExit("canonical COSV task pointer lacks source state-vector provenance")
    source_path = (ROOT / source_ref.split("#", 1)[0]).resolve()
    try:
        source_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit("canonical COSV source state-vector escaped repository root") from exc
    if not source_path.is_file():
        raise SystemExit("canonical COSV source state-vector is not materialized")
    source_vector = load_json(source_path)
    identity = str(source_vector.get("identity") or "") if isinstance(source_vector, dict) else ""
    if not (
        isinstance(source_vector, dict)
        and source_vector.get("profile") == "task.v1"
        and source_vector.get("level") == "task"
        and identity.endswith(f":task:{task_id}")
        and source_vector.get("vector") == vector
    ):
        raise SystemExit("canonical COSV index/source state-vector parity mismatch")


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
    registry = load_registry()
    index = load_effective_cosv_index()
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
    automation_contract = contract["automation"]

    body = {
        "schema": "stegverse.reusable-task-invocation-manifest/v1",
        "invocation_id": args.invocation_id,
        "reusable_task_id": args.reusable_task_id,
        "task_id": args.task_id,
        "cosv_task_vector": args.cosv_task_vector,
        "parameters": parameters,
        "construct": construct,
        "automation_plan": {
            "mode": automation_contract["mode"],
            "trigger_driver": automation_contract["trigger_driver"],
            "single_trigger": True,
            "manual_coordination_between_machine_admissible_internal_steps_required": False,
            "declared_runner_refs": runner_templates,
            "stop_boundaries": automation_contract["stop_boundaries"],
            "boundary_receipt_required": True,
            "independent_work_may_continue_at_boundary": automation_contract[
                "independent_downstream_or_parallel_work_may_continue_while_reusable_task_is_at_boundary"
            ],
            "dependent_work_waits_for_required_completion_evidence": automation_contract[
                "dependent_work_must_wait_for_required_completion_evidence"
            ],
        },
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
            "automation_trigger": "NON_AUTHORIZING_ORCHESTRATION_ONLY",
            "github_token_runtime_authority": "NONE",
        },
        "source_refs": [
            "data/reusable-task-registry.json",
            "source-bundles/reusable-task-registry.d",
            "data/reusable-task-ephemeral-construct-contract.json",
            "scripts/trigger_reusable_task.py",
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
