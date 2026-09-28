#!/usr/bin/env python3
"""Manifest-bound adapter for the *existing* SHWP G25+ parent task.

This is an ingress/return adapter inside the existing Universal InTr profile.
It never grants authority, creates another WorkerCoordinator or fabricates
organization/Master Records receipts. Source is materialized on invocation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

TASK_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
COSV = "50000000100000"
GRAPH_ID = TASK_ID + ":ORIGINAL-G25"
CAPABILITY = "sovereign_inference"
ROUTE = "stegverse.route.shwp-sovereign-inference.v1"
ORIGINAL = Path("control/resident-execution-request.d/ecosystem-chat-parent-001.json")
REGISTRY = Path("data/canonical-task-registry.json")
INDEX = Path("control/task-vector-index.json")
RESULT_SCHEMA = "stegverse.sdk.shwp-manifest-transition-result/v1"
REPAIR = "EXISTING_SHWP_AND_SDK_MANIFEST_OWNERS_NO_DEVICE_INVENTORY"


def _hash(value: Any) -> str:
    from workers.manifest_state_transition_intr_ingress import sha256
    return sha256(value)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SHWP_JSON_OBJECT_REQUIRED")
    return value


def _check(request: Mapping[str, Any], source: Path) -> dict[str, Any]:
    """Independently resolve the manifested operation against current Registry."""
    original_path = source / ORIGINAL
    if not original_path.is_file():
        raise ValueError("SHWP_CANONICAL_ORIGINAL_SOURCE_NOT_FOUND")
    original = _load(original_path)
    manifest = request.get("canonical_manifest")
    graph = request.get("state_graph")
    if not isinstance(manifest, Mapping) or not isinstance(graph, Mapping):
        raise ValueError("SHWP_SDK_MANIFEST_GRAPH_REQUIRED")
    binding = (manifest.get("extensions") or {}).get("stegverse_canonical_task")
    route = (manifest.get("extensions") or {}).get("stegverse_route")
    if not isinstance(binding, Mapping) or not isinstance(route, Mapping):
        raise ValueError("SHWP_MANIFEST_ROUTE_TASK_BINDING_REQUIRED")
    processing = manifest.get("processing")
    if processing != {"capability": CAPABILITY, "route_id": ROUTE}:
        raise ValueError("SHWP_MANIFEST_PROCESSING_ROUTE_MISMATCH")
    expected_route = {
        "route_id": ROUTE,
        "lane_class": "MANIFEST_BOUND_SOVEREIGN_INFERENCE",
        "routing_surface": "EXISTING_UNIVERSAL_INTR",
        "containment": "EXISTING_SHWP_PARENT_AUTHORITY_ONLY",
        "sandbox_required": False,
        "external_consequence_enabled": False,
    }
    if dict(route) != expected_route:
        raise ValueError("SHWP_MANIFEST_ROUTE_DECLARATION_MISMATCH")
    if request.get("route_declaration_hash") != _hash(expected_route):
        raise ValueError("SHWP_MANIFEST_ROUTE_HASH_MISMATCH")
    if (request.get("processing_capability") != CAPABILITY
            or request.get("route_id") != ROUTE
            or request.get("canonical_task_id") != TASK_ID
            or request.get("requires_workercoordinator_claim_fence") is not True):
        raise ValueError("SHWP_SDK_REQUEST_ROUTE_TASK_MISMATCH")
    expected_binding = {
        "task_id": TASK_ID,
        "correlation_id": TASK_ID,
        "registry_repository": "StegVerse-Labs/.github",
        "observed_registry_generation": None,
        "cosv_task_vector": COSV,
        "authority_effect": "NONE",
    }
    for key, expected in expected_binding.items():
        if key != "observed_registry_generation" and binding.get(key) != expected:
            raise ValueError("SHWP_CANONICAL_TASK_BINDING_MISMATCH:" + key)
    generation = binding.get("observed_registry_generation")
    if type(generation) is not int or generation < 1:
        raise ValueError("SHWP_REGISTRY_GENERATION_REQUIRED")
    registry = _load(source / REGISTRY)
    if registry.get("generation") != generation:
        raise ValueError("SHWP_STALE_CANONICAL_REGISTRY_GENERATION")
    matches = [row for row in registry.get("tasks", [])
               if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    if len(matches) != 1 or matches[0].get("coordination_state") != "ACTIVE":
        raise ValueError("SHWP_CANONICAL_TASK_NOT_UNIQUELY_ACTIVE")
    if (matches[0].get("cosv_tracking") or {}).get("vector") != COSV:
        raise ValueError("SHWP_CANONICAL_REGISTRY_COSV_MISMATCH")
    index = _load(source / INDEX)
    rows = [row for row in index.get("tasks", [])
            if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    if len(rows) != 1 or rows[0].get("vector") != COSV:
        raise ValueError("SHWP_CANONICAL_COSV_INDEX_MISMATCH")
    task_vector_ref = rows[0].get("source_state_vector_ref")
    if not isinstance(task_vector_ref, str) or not task_vector_ref.startswith("control/task-vectors/"):
        raise ValueError("SHWP_COSV_VECTOR_SOURCE_REQUIRED")
    vector = _load(source / task_vector_ref.split("#", 1)[0])
    if vector.get("vector") != COSV:
        raise ValueError("SHWP_COSV_SOURCE_VECTOR_MISMATCH")
    if manifest.get("payload") != original:
        raise ValueError("SHWP_ORIGINAL_IMMUTABLE_REQUEST_MISMATCH")
    graph_request = graph.get("request")
    if (graph.get("schema") != "stegverse.sdk.installed-state-transition-graph/v1"
            or graph.get("graph_id") != GRAPH_ID
            or graph.get("canonical_task_id") != TASK_ID
            or graph.get("processing_capability") != CAPABILITY
            or graph.get("route_id") != ROUTE
            or graph.get("adapter_executes_lifecycle") is not False
            or not isinstance(graph_request, Mapping)):
        raise ValueError("SHWP_SDK_STATE_GRAPH_MISMATCH")
    for key, expected in {
        "original_request_id": original["request_id"],
        "original_request_sha256": _hash(original),
        "observed_registry_generation": generation,
        "cosv_task_vector": COSV,
        "source_request_ref": str(ORIGINAL),
        "authority_effect": "NONE",
    }.items():
        if graph_request.get(key) != expected:
            raise ValueError("SHWP_SDK_GRAPH_REQUEST_BINDING_MISMATCH:" + key)
    return original


def _outcome(request: Mapping[str, Any], *, predicate: str | None,
             attempt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    success = predicate is None
    result = {
        "schema": RESULT_SCHEMA,
        "state": "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED" if success else "FAIL_CLOSED",
        "disposition": "ALLOW" if success else "FAIL_CLOSED",
        "terminal": False,
        "evaluation_boundary": "SDK_SHWP_MANIFEST_BOUND_PARENT_CONSUMER",
        "failed_predicate": predicate,
        "required_evidence_or_repair": (
            "Retrieve and reconstruct the original organization HEAD, predecessor-linked"
            " receipt batches and Master Records for this manifested execution."
            if success else "Repair the named ingress/consumer transition under existing owners."
        ),
        "retry_entrypoint": "EXISTING_MANIFEST_BOUND_SHWP_INTR_ROUTE",
        "owning_existing_goal": TASK_ID,
        "request_sha256": request.get("request_sha256"),
        "wire_manifest_sha256": request.get("wire_manifest_sha256"),
        "canonical_manifest_sha256": request.get("canonical_manifest_sha256"),
        "graph_id": request.get("graph_id"),
        "processing_capability": request.get("processing_capability"),
        "route_id": request.get("route_id"),
        "canonical_task_id": request.get("canonical_task_id"),
        "original_request_sha256": ((request.get("state_graph") or {}).get("request") or {}).get("original_request_sha256"),
        "consequence_committed_by_this_adapter": False,
        "authentic_intr_disposition_observed": False,
        "organization_master_records_closure_observed": False,
        "consumer_disposition": attempt.get("disposition") if isinstance(attempt, Mapping) else None,
        "consumer_failed_predicate": attempt.get("failed_predicate") if isinstance(attempt, Mapping) else None,
        "runtime_execution_attempted": attempt.get("runtime_execution_attempted") if isinstance(attempt, Mapping) else False,
        "authority_effect": "NONE_PROFILE_RETURN_ONLY",
    }
    result["diagnostic_sha256"] = _hash(result)
    return result


def execute(source_root: Path, runtime_root: Path, request: Mapping[str, Any],
            *, refresh_fn: Callable | None = None,
            consumer_fn: Callable | None = None) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    try:
        original = _check(request, source)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return _outcome(request, predicate=str(exc))
    if source == runtime:
        return _outcome(request, predicate="SHWP_DISTINCT_EPHEMERAL_STATE_ROOT_REQUIRED")
    if refresh_fn is None:
        from scripts.refresh_sovereign_worker_runtime_source import refresh
        refresh_fn = refresh
    if consumer_fn is None:
        from scripts.consume_resident_execution_request import consume
        consumer_fn = consume
    try:
        # Materialization is local, on invocation, and preserves mutable
        # original organization claims, receipts and ledger state.
        refresh_fn(source, runtime)
        materialized = runtime / ORIGINAL
        if not materialized.is_file() or _load(materialized) != original:
            return _outcome(request, predicate="SHWP_ORIGINAL_REQUEST_MATERIALIZATION_MISMATCH")
    except Exception as exc:
        return _outcome(request, predicate="SHWP_EVENT_EPHEMERAL_SOURCE_MATERIALIZATION_FAILED:" + str(exc)[:180])
    try:
        attempt = consumer_fn(source, runtime)
    except Exception as exc:
        # A subprocess exception does not establish a downstream InTr verdict.
        return _outcome(request, predicate="SHWP_PARENT_CONSUMER_INVOCATION_FAILED:" + type(exc).__name__)
    if not isinstance(attempt, Mapping):
        return _outcome(request, predicate="SHWP_PARENT_CONSUMER_RESULT_INVALID")
    if attempt.get("request_id") != original["request_id"] or attempt.get("request_sha256") != _hash(original):
        return _outcome(request, predicate="SHWP_PARENT_CONSUMER_ORIGINAL_REQUEST_LINEAGE_MISMATCH", attempt=attempt)
    if attempt.get("disposition") != "ALLOW":
        code = str(attempt.get("failed_predicate") or "SHWP_PARENT_CONSUMER_NON_ALLOW_UNSPECIFIED")
        return _outcome(request, predicate=code, attempt=attempt)
    if attempt.get("runtime_execution_attempted") is not True:
        # A cached verified attempt must progress through its original
        # custody readback, not become an invented second live invocation.
        return _outcome(request, predicate="SHWP_PREVIOUS_SUCCESS_ORIGINAL_READBACK_REQUIRED", attempt=attempt)
    # The existing consumer verifies its own original parent activation chain
    # and evidence projection. Independent organization ledger readback must
    # still be executed by the existing custody interface; no terminal ALLOW
    # can be inferred by this profile from a child process exit or JSON body.
    return _outcome(request, predicate=None, attempt=attempt)


def retain_source_result(runtime_root: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    """Immutable *local source* diagnostic only; never an org custody receipt."""
    root = runtime_root / "runtime-state/sdk-manifest-state-transition/dispositions/shwp"
    root.mkdir(parents=True, exist_ok=True)
    body = dict(value)
    request_hash = str(body.get("request_sha256") or "unbound")
    identity = _hash({key: val for key, val in body.items() if key != "diagnostic_sha256"})
    exact = root / (request_hash + "." + identity + ".json")
    body["source_disposition_ref"] = str(exact)
    body.pop("diagnostic_sha256", None)
    body["diagnostic_sha256"] = _hash(body)
    raw = json.dumps(body, indent=2, sort_keys=True) + "\\n"
    if exact.exists():
        if exact.read_text(encoding="utf-8") != raw:
            raise ValueError("SHWP_IMMUTABLE_SOURCE_DIAGNOSTIC_COLLISION")
    else:
        exact.write_text(raw, encoding="utf-8")
    return body


__all__ = ["execute", "_check", "retain_source_result", "TASK_ID", "ROUTE", "RESULT_SCHEMA"]
