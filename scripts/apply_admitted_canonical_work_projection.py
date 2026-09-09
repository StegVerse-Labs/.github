#!/usr/bin/env python3
"""Project an authentic CanonicalWork ingress transition into canonical task state."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"
CONSUMPTION_SCHEMA = "stegverse.canonical-work-intr-materialization-consumption/v1"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"FAIL_CLOSED: object required: {path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def validate_receipts(ingress: dict[str, Any], consumption: dict[str, Any]) -> tuple[str, str]:
    require(ingress.get("schema") == INGRESS_SCHEMA, "ingress schema mismatch")
    require(ingress.get("state") == "INGRESS_ADMITTED", "ingress not admitted")
    require(ingress.get("authority_effect") == "INGRESS_TRANSITION_ONLY", "ingress authority effect mismatch")
    require(ingress.get("claim_or_fence_minted") is False, "ingress minted claim/fence")
    require(ingress.get("credential_authority") == "TV/TVC", "credential authority drift")
    require(ingress.get("github_token_runtime_authority") == "NONE", "GitHub token authority drift")

    require(consumption.get("schema") == CONSUMPTION_SCHEMA, "consumption schema mismatch")
    require(consumption.get("state") == "INGRESS_BOUND_COORDINATION_PROJECTED", "consumption state mismatch")
    require(consumption.get("claim_or_fence_minted") is False, "consumption minted claim/fence")
    for key in ("materialization_id", "request_hash", "payload_hash", "operation_id"):
        require(consumption.get(key) == ingress.get(key), f"ingress/consumption binding mismatch:{key}")

    task_id = consumption.get("task_id")
    correlation_id = consumption.get("correlation_id")
    require(isinstance(task_id, str) and task_id, "task_id required")
    require(isinstance(correlation_id, str) and correlation_id, "correlation_id required")
    return task_id, correlation_id


def project_task(task: dict[str, Any], *, correlation_id: str, ingress: dict[str, Any], consumption: dict[str, Any]) -> dict[str, Any]:
    proposed = copy.deepcopy(task)
    require(proposed.get("correlation_id") == correlation_id, "correlation identity drift")
    require(proposed.get("coordination_state") in {"PROPOSED", "INGRESS_ADMITTED"}, "current task state is not ingress-projectable")

    ingress_ref = consumption.get("ingress_receipt_ref")
    require(isinstance(ingress_ref, str) and ingress_ref, "ingress receipt ref required")
    consumption_ref = consumption.get("consumption_receipt_ref") or f"runtime://canonical-work-consumption/{ingress['materialization_id']}"

    proposed["coordination_state"] = "INGRESS_ADMITTED"
    proposed.setdefault("runtime_refs", {})
    proposed["runtime_refs"].update({
        "materialization_id": ingress["materialization_id"],
        "ingress_receipt_ref": ingress_ref,
        "consumption_receipt_ref": consumption_ref,
        "request_hash": ingress["request_hash"],
        "payload_hash": ingress["payload_hash"],
    })
    evidence = proposed.setdefault("existing_evidence_refs", [])
    for ref in (ingress_ref, consumption_ref):
        if ref not in evidence:
            evidence.append(ref)
    proposed["allowed_next_transitions"] = ["CLAIMABLE", "RECONCILIATION_REQUIRED"]
    return proposed


def find_source(*, registry: dict[str, Any], task_id: str, task_shards: Path) -> tuple[str, dict[str, Any], Path | None]:
    matches = [task for task in registry.get("tasks", []) if task.get("task_id") == task_id]
    require(len(matches) <= 1, "canonical task identity must resolve exactly once")
    if matches:
        return "MONOLITHIC_REGISTRY", matches[0], None

    shard_matches: list[tuple[dict[str, Any], Path]] = []
    if task_shards.is_dir():
        preferred = task_shards / f"{task_id}.json"
        candidates = [preferred] if preferred.is_file() else list(task_shards.glob("*.json"))
        for path in candidates:
            value = load(path)
            if value.get("task_id") == task_id:
                shard_matches.append((value, path))
    require(len(shard_matches) == 1, "canonical task identity must resolve exactly once")
    return "SHARDED_REGISTRY", shard_matches[0][0], shard_matches[0][1]


def project(registry: dict[str, Any], ingress: dict[str, Any], consumption: dict[str, Any], *, task_shards: Path) -> tuple[str, dict[str, Any], Path | None]:
    task_id, correlation_id = validate_receipts(ingress, consumption)
    source_kind, task, shard_path = find_source(registry=registry, task_id=task_id, task_shards=task_shards)
    projected_task = project_task(task, correlation_id=correlation_id, ingress=ingress, consumption=consumption)

    if source_kind == "SHARDED_REGISTRY":
        return source_kind, projected_task, shard_path

    proposed = copy.deepcopy(registry)
    for index, row in enumerate(proposed.get("tasks", [])):
        if row.get("task_id") == task_id:
            proposed["tasks"][index] = projected_task
            break
    proposed["generation"] = int(registry.get("generation", 0)) + 1
    proposed["status"] = "AUTHENTIC_INGRESS_PROJECTED_PRE_EXECUTION_RECONCILIATION_PENDING"
    proposed.setdefault("nonclaims", [])
    for claim in (
        "INGRESS_ADMISSION_DOES_NOT_MINT_WORKERCOORDINATOR_CLAIM_OR_FENCE",
        "INGRESS_ADMISSION_DOES_NOT_PROVE_TASK_EXECUTION",
        "INGRESS_ADMISSION_DOES_NOT_PROVE_COMPLETION",
        "HB32_OSCILLATOR_REFERENCE_DOES_NOT_GRANT_TASK_AUTHORITY",
    ):
        if claim not in proposed["nonclaims"]:
            proposed["nonclaims"].append(claim)
    return source_kind, proposed, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/canonical-task-registry.json")
    parser.add_argument("--task-shards", default="data/canonical-task-records")
    parser.add_argument("--ingress-receipt", required=True)
    parser.add_argument("--consumption-receipt", required=True)
    parser.add_argument("--output")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    source_kind, proposed, shard_path = project(
        load(registry_path),
        load(Path(args.ingress_receipt)),
        load(Path(args.consumption_receipt)),
        task_shards=Path(args.task_shards),
    )
    text = json.dumps(proposed, indent=2, sort_keys=True) + "\n"
    if args.apply:
        target = shard_path if source_kind == "SHARDED_REGISTRY" else registry_path
        require(target is not None, "projection target missing")
        target.write_text(text, encoding="utf-8")
    elif args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
