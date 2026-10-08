#!/usr/bin/env python3
"""Manifest the unchanged canonical SHWP request and invoke installed SDK/InTr.

Runs on the already-authorized event-ephemeral invocation surface. It neither
finds a machine nor schedules another task. The manifest selects semantics;
source/task identity only binds the original request and current Registry.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST = Path("control/resident-execution-request.d/ecosystem-chat-parent-001.json")
REGISTRY = Path("data/canonical-task-registry.json")
TASK_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
COSV = "50000000100000"
ROUTE = "stegverse.route.shwp-sovereign-inference.v1"
RESULT_SCHEMA = "stegverse.shwp-manifest-invocation/v1"
ORGANIZATION_RECORD_OBSERVED_FIELD = "organization_master_records_organization_record_observed"
#: Master Records boundary migration: results written before the rename carry
#: this legacy flag. Readers accept it as a fallback.
LEGACY_ORGANIZATION_RECORD_OBSERVED_FIELD = "organization_master_records_closure_observed"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SHWP_MANIFEST_SOURCE_OBJECT_REQUIRED")
    return value


def organization_record_observed(result: Mapping[str, Any]) -> Any:
    """Read the organization-record-observed flag under the current or legacy name."""
    if ORGANIZATION_RECORD_OBSERVED_FIELD in result:
        return result[ORGANIZATION_RECORD_OBSERVED_FIELD]
    return result.get(LEGACY_ORGANIZATION_RECORD_OBSERVED_FIELD)


def _nonallow(reason: str, *, request_id: str | None = None,
              manifest_sha256: str | None = None) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "state": "FAIL_CLOSED",
        "disposition": "FAIL_CLOSED",
        "evaluation_boundary": "SDK_SHWP_EVENT_EPHEMERAL_MANIFEST_INVOCATION",
        "failed_predicate": reason,
        "required_evidence_or_repair": "Repair exact manifested ingress at its first failed predicate.",
        "retry_entrypoint": "EXISTING_SHWP_MANIFEST_ROUTE",
        "owning_existing_goal": TASK_ID,
        "cosv_task_vector": COSV,
        "request_id": request_id,
        "manifest_sha256": manifest_sha256,
        "runtime_execution_attempted": False,
        "consequence_committed": False,
        "downstream_intr_disposition_inferred": False,
        "organization_receipt_inferred": False,
        "second_machine_required": False,
        "authority_effect": "NONE_ATTACHMENT_EVALUATION_ONLY",
    }


def build_manifest(source_root: Path, *, digest: Callable[[Any], str]) -> dict[str, Any]:
    source = source_root.resolve()
    original = _read(source / REQUEST)
    if original.get("request_id") != "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002":
        raise ValueError("SHWP_ORIGINAL_REQUEST_ID_MISMATCH")
    if original.get("task_id") != TASK_ID or original.get("fresh_fence_minimum_exclusive") != 24:
        raise ValueError("SHWP_ORIGINAL_G25_TASK_BINDING_MISMATCH")
    registry = _read(source / REGISTRY)
    generation = registry.get("generation")
    matches = [x for x in registry.get("tasks", [])
               if isinstance(x, dict) and x.get("task_id") == TASK_ID]
    if (type(generation) is not int or len(matches) != 1
            or matches[0].get("coordination_state") != "ACTIVE"
            or (matches[0].get("cosv_tracking") or {}).get("vector") != COSV):
        raise ValueError("SHWP_CURRENT_CANONICAL_TASK_COSV_NOT_ADMITTED")
    return {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "manifest_profile_version": "1",
        "source_framework": "StegVerse-Labs/.github",
        "source_output_id": original["request_id"],
        "created_at": original["requested_at"],
        "declared_intent": "Consume unchanged original authorized SHWP G25+ request",
        "requested_consequence": "EXISTING_SHWP_PARENT_ONLY",
        "payload": original,
        "hashes": {"payload_sha256": digest(original)},
        "processing": {"capability": "sovereign_inference", "route_id": ROUTE},
        "extensions": {
            "stegverse_route": {
                "route_id": ROUTE,
                "lane_class": "MANIFEST_BOUND_SOVEREIGN_INFERENCE",
                "routing_surface": "EXISTING_UNIVERSAL_INTR",
                "containment": "EXISTING_SHWP_PARENT_AUTHORITY_ONLY",
                "sandbox_required": False,
                "external_consequence_enabled": False,
            },
            "stegverse_canonical_task": {
                "task_id": TASK_ID,
                "correlation_id": TASK_ID,
                "registry_repository": "StegVerse-Labs/.github",
                "observed_registry_generation": generation,
                "cosv_task_vector": COSV,
                "authority_effect": "NONE",
            },
        },
    }


def invoke(source_root: Path, runtime_root: Path,
           *, sdk_execute: Callable | None = None,
           digest: Callable[[Any], str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if sdk_execute is None or digest is None:
        sdk_root = str(os.environ.get("STEGVERSE_SDK_SOURCE_ROOT") or "").strip()
        if sdk_root:
            local = Path(sdk_root).expanduser().resolve()
            if (local / "stegverse/manifest_state_transition_runtime.py").is_file():
                sys.path.insert(0, str(local))
        try:
            sdk = importlib.import_module("stegverse.manifest_state_transition_runtime")
            hashing = importlib.import_module("stegverse.governance_navigation")
        except (ImportError, AttributeError) as exc:
            return _nonallow("INSTALLED_STEGVERSE_SDK_MANIFEST_RUNTIME_REQUIRED:" + type(exc).__name__)
        if sdk_execute is None:
            sdk_execute = sdk.execute_manifest
        if digest is None:
            digest = hashing.canonical_sha256
    try:
        manifest = build_manifest(source, digest=digest)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        return _nonallow(str(exc))
    request_id = manifest["source_output_id"]
    manifest_hash = digest(manifest)
    try:
        response = sdk_execute(manifest)
    except (ValueError, RuntimeError, OSError, TypeError) as exc:
        # The attempted SDK/transport attachment is the only verified boundary.
        return _nonallow("SHWP_SDK_MANIFEST_INVOCATION_FAILED:" + str(exc)[:180],
                         request_id=request_id, manifest_sha256=manifest_hash)
    if not isinstance(response, Mapping):
        return _nonallow("SHWP_SDK_RETURN_NOT_OBJECT",
                         request_id=request_id, manifest_sha256=manifest_hash)
    # Only lineage-bound SDK results can advance the original request. A
    # structurally plausible response with no exact manifest/request binding
    # is not evidence of native ingress or authorized execution.
    profile = response.get("schema")
    if profile not in {
        "stegverse.sdk.shwp-manifest-transition-result/v1",
        "stegverse.sdk.manifest-attachment-disposition/v1",
    }:
        return _nonallow("SHWP_SDK_PROFILE_RESULT_SCHEMA_MISMATCH",
                         request_id=request_id, manifest_sha256=manifest_hash)
    for key, expected in {
        "canonical_task_id": TASK_ID,
        "processing_capability": "sovereign_inference",
        "route_id": ROUTE,
        "wire_manifest_sha256": manifest_hash,
    }.items():
        if response.get(key) != expected:
            return _nonallow("SHWP_SDK_RETURN_LINEAGE_MISMATCH:" + key,
                             request_id=request_id, manifest_sha256=manifest_hash)
    if profile == "stegverse.sdk.shwp-manifest-transition-result/v1":
        if response.get("original_request_sha256") != digest(manifest["payload"]):
            return _nonallow("SHWP_SDK_RETURN_ORIGINAL_REQUEST_MISMATCH",
                             request_id=request_id, manifest_sha256=manifest_hash)
        if (organization_record_observed(response) is not False
                or response.get("terminal") is not False):
            return _nonallow("SHWP_SDK_RETURN_CUSTODY_ESCALATION",
                             request_id=request_id, manifest_sha256=manifest_hash)
    state = str(response.get("state") or "")
    if state == "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED" and profile == (
            "stegverse.sdk.shwp-manifest-transition-result/v1"):
        # A verified original child projection is nonterminal until the source
        # manifest is independently bound to original org HEAD and Master Records.
        return {
            "schema": RESULT_SCHEMA,
            "state": state,
            "disposition": "ALLOW",
            "terminal": False,
            "owning_existing_goal": TASK_ID,
            "cosv_task_vector": COSV,
            "request_id": request_id,
            "manifest_sha256": manifest_hash,
            "sdk_profile_result_sha256": digest(dict(response)),
            "runtime_execution_attempted": response.get("runtime_execution_attempted") is True,
            "organization_master_records_organization_record_observed": False,
            "next_transition": "EXISTING_ORIGINAL_ORGANIZATION_HEAD_AND_MASTER_RECORDS_READBACK",
            "second_machine_required": False,
            "authority_effect": "NONE_NONTERMINAL_PROFILE_RETURN",
        }
    if state != "FAIL_CLOSED":
        return _nonallow("SHWP_UNEXPECTED_SDK_PROFILE_RETURN:" + state,
                         request_id=request_id, manifest_sha256=manifest_hash)
    failed = str(response.get("failed_predicate") or "SHWP_SDK_NON_ALLOW_UNSPECIFIED")
    outcome = _nonallow(failed, request_id=request_id, manifest_sha256=manifest_hash)
    outcome["evaluation_boundary"] = str(response.get("evaluation_boundary")
                                          or outcome["evaluation_boundary"])
    outcome["sdk_profile_result_sha256"] = digest(dict(response))
    outcome["runtime_execution_attempted"] = response.get("runtime_execution_attempted") is True
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description="Admit original SHWP via existing SDK manifest and InTr.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = invoke(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
