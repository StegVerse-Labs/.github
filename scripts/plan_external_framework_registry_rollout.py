#!/usr/bin/env python3
"""Plan bounded reusable rollout eligibility across an external-framework registry.

This script is coordination/source logic only. It does not execute external calls,
create runtime authority, or promote registry metadata into transition authority.
Each emitted row remains one independent invocation of
RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RESOLVER_PATH = HERE / "resolve_external_framework_roundtrip_rollout.py"
REQUIRED_ENDPOINT_EVIDENCE_FIELDS = (
    "endpoint_evidence_ref",
    "endpoint_observed_at",
    "endpoint_evidence_class",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolver():
    spec = importlib.util.spec_from_file_location("external_framework_rollout", RESOLVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _endpoint_entries(endpoint_map: dict[str, Any]) -> dict[str, Any]:
    bindings = endpoint_map.get("bindings")
    if isinstance(bindings, dict):
        return bindings
    return endpoint_map


def _endpoint_binding(endpoint_map: dict[str, Any], framework_id: str) -> tuple[str | None, str, str, dict[str, str | None]]:
    value = _endpoint_entries(endpoint_map).get(framework_id)
    empty_evidence = {field: None for field in REQUIRED_ENDPOINT_EVIDENCE_FIELDS}
    if value is None:
        return None, "UNBOUND_NO_RUNTIME_ENDPOINT_REF", "no explicit endpoint binding supplied", empty_evidence
    if isinstance(value, str):
        return None, "UNQUALIFIED_ENDPOINT_REJECTED", "bare endpoint string lacks required endpoint evidence metadata", empty_evidence
    if not isinstance(value, dict):
        return None, "INVALID_ENDPOINT_BINDING", "endpoint binding must be an object", empty_evidence

    ref = value.get("runtime_endpoint_ref")
    endpoint = ref.strip() if isinstance(ref, str) and ref.strip() else None
    evidence: dict[str, str | None] = {}
    for field in REQUIRED_ENDPOINT_EVIDENCE_FIELDS:
        item = value.get(field)
        evidence[field] = item.strip() if isinstance(item, str) and item.strip() else None

    present_evidence = [field for field, item in evidence.items() if item]
    if endpoint is None:
        if present_evidence:
            return None, "ORPHAN_ENDPOINT_EVIDENCE_REJECTED", "endpoint evidence supplied without runtime_endpoint_ref", evidence
        return None, "UNBOUND_NO_RUNTIME_ENDPOINT_REF", "no explicit endpoint binding supplied", evidence

    missing = [field for field, item in evidence.items() if not item]
    if missing:
        return (
            None,
            "UNQUALIFIED_ENDPOINT_REJECTED",
            "runtime endpoint lacks required evidence metadata: " + ",".join(missing),
            evidence,
        )
    return endpoint, "EVIDENCE_QUALIFIED_ENDPOINT_BOUND", "endpoint binding includes required evidence metadata", evidence


def build_registry_plan(
    *,
    registry: dict[str, Any],
    manifest_root: Path,
    goal_task_id: str,
    cosv_task_vector: str,
    operation_class: str = "RUNTIME_ROUNDTRIP",
    endpoint_map: dict[str, Any] | None = None,
    counterpart_provenance: str = "UNOBSERVED_CANDIDATE",
) -> dict[str, Any]:
    resolver = _resolver()
    endpoints = endpoint_map or {}
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("registry.entries must be a list")

    plans: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        framework_id = entry.get("framework_id")
        if not isinstance(framework_id, str) or not framework_id:
            plans.append({
                "schema": "stegverse.external-framework-roundtrip-rollout-plan/v1",
                "reusable_task_id": resolver.REUSABLE_TASK_ID,
                "framework_id": None,
                "goal_task_id": goal_task_id,
                "cosv_task_vector": cosv_task_vector,
                "eligibility": "REGISTRY_ENTRY_INVALID",
                "reason": "registry entry missing framework_id",
                "authority_effect": "NONE_COORDINATION_ONLY",
            })
            continue

        manifest_path = entry.get("manifest_path")
        manifest = None
        source_evidence_ref = None
        if isinstance(manifest_path, str) and manifest_path:
            candidate = manifest_root / manifest_path
            source_evidence_ref = manifest_path
            if candidate.is_file():
                manifest = _load(candidate)

        runtime_endpoint_ref, binding_state, binding_reason, endpoint_evidence = _endpoint_binding(endpoints, framework_id)
        plan = resolver.build_plan(
            registry=registry,
            manifest=manifest,
            framework_id=framework_id,
            goal_task_id=goal_task_id,
            cosv_task_vector=cosv_task_vector,
            operation_class=operation_class,
            runtime_endpoint_ref=runtime_endpoint_ref,
            source_evidence_ref=source_evidence_ref,
            counterpart_provenance=counterpart_provenance,
        )
        plan["endpoint_binding_state"] = binding_state
        plan["endpoint_binding_reason"] = binding_reason
        plan.update(endpoint_evidence)
        if manifest is None and plan.get("eligibility") == "REGISTRY_ENTRY_INVALID":
            plan["reason"] = "canonical manifest is missing or unreadable at registry manifest_path"
        plans.append(plan)

    counts = Counter(str(plan.get("eligibility")) for plan in plans)
    binding_counts = Counter(str(plan.get("endpoint_binding_state", "NOT_EVALUATED")) for plan in plans)
    return {
        "schema": "stegverse.external-framework-registry-rollout-plan/v1",
        "reusable_task_id": resolver.REUSABLE_TASK_ID,
        "goal_task_id": goal_task_id,
        "cosv_task_vector": cosv_task_vector,
        "registry_schema_version": registry.get("schema_version"),
        "operation_class": operation_class,
        "counterpart_provenance": counterpart_provenance,
        "framework_count": len(plans),
        "eligibility_counts": dict(sorted(counts.items())),
        "endpoint_binding_counts": dict(sorted(binding_counts.items())),
        "roundtrip_eligible_frameworks": [
            plan.get("framework_id") for plan in plans if plan.get("eligibility") == "ROUNDTRIP_ELIGIBLE"
        ],
        "independent_invocation_semantics": True,
        "endpoint_evidence_qualification_required": True,
        "fail_closed_scope": "PER_FRAMEWORK_INVOCATION",
        "authority_effect": "NONE_COORDINATION_ONLY",
        "transition_effect": "NONE_PLAN_ONLY",
        "plans": plans,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--goal-task-id", required=True)
    parser.add_argument("--cosv-task-vector", required=True)
    parser.add_argument("--operation-class", default="RUNTIME_ROUNDTRIP")
    parser.add_argument("--endpoint-map", type=Path)
    parser.add_argument("--counterpart-provenance", default="UNOBSERVED_CANDIDATE")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_registry_plan(
        registry=_load(args.registry),
        manifest_root=args.manifest_root,
        goal_task_id=args.goal_task_id,
        cosv_task_vector=args.cosv_task_vector,
        operation_class=args.operation_class,
        endpoint_map=_load(args.endpoint_map) if args.endpoint_map else None,
        counterpart_provenance=args.counterpart_provenance,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
