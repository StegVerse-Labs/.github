#!/usr/bin/env python3
"""Resolve one external-framework registry entry into a bounded reusable rollout plan.

This resolver is coordination/source logic only. It grants no execution, transition,
credential, custody, publication, claim/fence, or user-verification authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REUSABLE_TASK_ID = "RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001"
REQUIRED_MANIFEST_FIELDS = {
    "artifact_type",
    "schema_version",
    "framework_id",
    "name",
    "source_reference",
    "source_version",
    "allowed_use_boundary",
    "claims",
    "non_claims",
    "transition_table_mapping",
    "SPE_overlap",
    "StegVerse_ecosystem_overlap",
    "fail_closed_conditions",
    "boundary",
}
SOURCE_BLOCKED_STATUSES = {
    "ARTIFACT-PACKAGE-REQUIRED",
    "OFFICIAL-SOURCE-REQUIRED",
    "INTAKE-PROVISIONAL",
}
SOURCE_BLOCKED_MARKERS = {
    "UNVERIFIED_SOURCE_REQUIRED",
    "ARTIFACT_PACKAGE_REQUIRED",
    "OFFICIAL_SOURCE_REQUIRED",
}
RUNTIME_OPERATION_CLASSES = {"RUNTIME_ROUNDTRIP", "GOVERNED_ROUNDTRIP"}
TRANSLATION_OPERATION_CLASSES = {"SOURCE_CROSSWALK", "TRANSLATION_ONLY"}
SUPPORTED_OPERATION_CLASSES = RUNTIME_OPERATION_CLASSES | TRANSLATION_OPERATION_CLASSES

REQUIRED_COMPONENTS = [
    "RT-EXTERNAL-ADAPTER-ESTABLISH-001",
    "RTC-MANIFEST-001",
    "RTC-GOVERNED-PROCESSING-002",
    "RTC-ROUNDTRIP-003",
    "RTC-EVIDENCE-CUSTODY-004",
    "RTC-SDK-RETURN-006",
    "RTC-STEGVERSE-EGRESS-007",
    "RTC-INTERLOCK-INTR-TRANSPORT-008",
]
CONDITIONAL_COMPONENTS = ["RTC-PUBLISHER-005", "RTC-FARSIDE-FINAL-009"]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(rendered).hexdigest()


def _resolve_entry(registry: dict[str, Any], framework_id: str) -> tuple[dict[str, Any] | None, str | None]:
    entries = registry.get("entries")
    if not isinstance(entries, list):
        return None, "registry.entries must be a list"
    matches = [row for row in entries if isinstance(row, dict) and row.get("framework_id") == framework_id]
    if len(matches) != 1:
        return None, f"framework_id must resolve exactly once; observed={len(matches)}"
    return matches[0], None


def _manifest_valid(manifest: Any, framework_id: str) -> tuple[bool, str | None]:
    if not isinstance(manifest, dict):
        return False, "manifest must be an object"
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing:
        return False, "manifest missing required fields: " + ",".join(missing)
    if manifest.get("artifact_type") != "external_framework_manifest":
        return False, "manifest artifact_type mismatch"
    if manifest.get("framework_id") != framework_id:
        return False, "manifest framework_id mismatch"
    boundary = manifest.get("boundary")
    if not isinstance(boundary, dict):
        return False, "manifest boundary must be an object"
    if boundary.get("execution_authority_claim") is True or boundary.get("compatibility_manifest_is_authority") is True:
        return False, "manifest attempts to promote external or compatibility authority"
    return True, None


def classify(
    *,
    entry: dict[str, Any],
    manifest: dict[str, Any],
    operation_class: str,
    runtime_endpoint_ref: str | None,
) -> tuple[str, str]:
    if operation_class not in SUPPORTED_OPERATION_CLASSES:
        return "UNSUPPORTED_OPERATION_CLASS", f"unsupported operation_class={operation_class}"

    status = str(entry.get("status") or "")
    source_version = str(manifest.get("source_version") or "")
    source_reference = str(manifest.get("source_reference") or "")
    if status in SOURCE_BLOCKED_STATUSES or source_version in SOURCE_BLOCKED_MARKERS:
        return "SOURCE_ONLY", "framework remains source/artifact blocked in canonical registry or manifest"
    if "official public source" in source_reference.lower() and "required" in source_reference.lower():
        return "SOURCE_ONLY", "official source is still required"

    if operation_class in TRANSLATION_OPERATION_CLASSES:
        return "TRANSLATION_ONLY", "bounded source/crosswalk translation requested; no runtime transition requested"

    if not runtime_endpoint_ref:
        return "RUNTIME_ENDPOINT_UNAVAILABLE", "runtime round trip requested without an explicit current endpoint reference"

    return "ROUNDTRIP_ELIGIBLE", "source is sufficiently bound and a current endpoint reference was supplied; transition admission remains separate"


def build_plan(
    *,
    registry: dict[str, Any],
    manifest: dict[str, Any] | None,
    framework_id: str,
    goal_task_id: str,
    cosv_task_vector: str,
    operation_class: str,
    runtime_endpoint_ref: str | None = None,
    source_evidence_ref: str | None = None,
    counterpart_provenance: str = "UNOBSERVED_CANDIDATE",
) -> dict[str, Any]:
    entry, error = _resolve_entry(registry, framework_id)
    if error:
        return {
            "schema": "stegverse.external-framework-roundtrip-rollout-plan/v1",
            "reusable_task_id": REUSABLE_TASK_ID,
            "framework_id": framework_id,
            "goal_task_id": goal_task_id,
            "cosv_task_vector": cosv_task_vector,
            "eligibility": "REGISTRY_ENTRY_INVALID",
            "reason": error,
            "authority_effect": "NONE_COORDINATION_ONLY",
        }

    valid, manifest_error = _manifest_valid(manifest, framework_id)
    if not valid:
        return {
            "schema": "stegverse.external-framework-roundtrip-rollout-plan/v1",
            "reusable_task_id": REUSABLE_TASK_ID,
            "framework_id": framework_id,
            "goal_task_id": goal_task_id,
            "cosv_task_vector": cosv_task_vector,
            "eligibility": "REGISTRY_ENTRY_INVALID",
            "reason": manifest_error,
            "entry_digest": _digest(entry),
            "authority_effect": "NONE_COORDINATION_ONLY",
        }

    assert manifest is not None
    eligibility, reason = classify(
        entry=entry,
        manifest=manifest,
        operation_class=operation_class,
        runtime_endpoint_ref=runtime_endpoint_ref,
    )
    return {
        "schema": "stegverse.external-framework-roundtrip-rollout-plan/v1",
        "reusable_task_id": REUSABLE_TASK_ID,
        "goal_task_id": goal_task_id,
        "cosv_task_vector": cosv_task_vector,
        "framework_id": framework_id,
        "framework_name": entry.get("name"),
        "framework_status": entry.get("status"),
        "framework_manifest_path": entry.get("manifest_path"),
        "framework_source_reference": manifest.get("source_reference"),
        "framework_source_version": manifest.get("source_version"),
        "operation_class": operation_class,
        "runtime_endpoint_ref": runtime_endpoint_ref,
        "source_evidence_ref": source_evidence_ref,
        "counterpart_provenance": counterpart_provenance,
        "eligibility": eligibility,
        "reason": reason,
        "entry_digest": _digest(entry),
        "manifest_digest": _digest(manifest),
        "required_components": REQUIRED_COMPONENTS,
        "conditional_components": CONDITIONAL_COMPONENTS,
        "transition_effect": "NONE_PLAN_ONLY",
        "claim_fence_effect": "NONE",
        "credential_effect": "NONE",
        "user_verification_effect": "NONE",
        "foreign_framework_authority_effect": "NONE_ON_STEGVERSE",
        "runtime_truth_rule": "executed transitions are runtime truth at their recorded provenance; source/CI/merge alone does not prove an unexecuted transition",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--framework-id", required=True)
    parser.add_argument("--goal-task-id", required=True)
    parser.add_argument("--cosv-task-vector", required=True)
    parser.add_argument("--operation-class", required=True)
    parser.add_argument("--runtime-endpoint-ref")
    parser.add_argument("--source-evidence-ref")
    parser.add_argument("--counterpart-provenance", default="UNOBSERVED_CANDIDATE")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    plan = build_plan(
        registry=_load(args.registry),
        manifest=_load(args.manifest),
        framework_id=args.framework_id,
        goal_task_id=args.goal_task_id,
        cosv_task_vector=args.cosv_task_vector,
        operation_class=args.operation_class,
        runtime_endpoint_ref=args.runtime_endpoint_ref,
        source_evidence_ref=args.source_evidence_ref,
        counterpart_provenance=args.counterpart_provenance,
    )
    rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
