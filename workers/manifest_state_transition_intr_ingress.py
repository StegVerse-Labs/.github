#!/usr/bin/env python3
"""Generic SDK manifest state-transition profile for the existing Universal InTr listener.

This module is a non-authorizing ingress/return adapter. It does not create a
listener, scheduler, dispatcher, WorkerCoordinator, credential authority,
transition authority, execution authority, or custody authority. It validates
and retains one SDK manifest-state-transition request, invokes the existing
targeted WorkerCoordinator path in-process, and returns only evidence already
produced by the canonical runtime chain.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Mapping

from heartbeat_runtime.worker_runtime import WorkerCoordinator
from scripts.run_worker_runtime import load_adapters
from workers.canonical_state_transition_custody import build_state_receipt, organization_receipt_gate, submit_state_receipt

REQUEST_SCHEMA = "stegverse.sdk.manifest-state-transition-request/v1"
RESULT_SCHEMA = "stegverse.sdk.manifest-state-transition-result/v1"
PROFILE = "SDK:ManifestStateTransition"
REQUEST_DIR = Path("runtime-state/sdk-manifest-state-transition")
LATEST_SUFFIX = ".latest.json"
ORGANIZATION_RECORD_STATUS_FIELD = "master_records_organization_record_status"
#: Master Records boundary migration: SDK governance results written before the
#: rename carry this legacy field. Readers accept it as a fallback.
LEGACY_ORGANIZATION_RECORD_STATUS_FIELD = "master_records_custody_status"
IMMUTABLE_DIR = "requests"

GOVERNANCE_SOURCE_ROOTS = {
    "sdk": ("STEGVERSE_SDK_SOURCE_ROOT", "StegVerse-org/StegVerse-SDK", "stegverse/governance_ingress_runtime.py"),
    "stegcore": ("STEGVERSE_STEGCORE_SOURCE_ROOT", "StegVerse-Labs/StegCore", "src/stegcore/transaction_lifecycle.py"),
    "core_lite": ("STEGVERSE_CORE_LITE_SOURCE_ROOT", "Data-Continuation/core-lite", "core_lite/transaction_route.py"),
    "master_records": ("STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "master-records/orchestration", "services/manifest_receipt_custody.py"),
}
GOVERNANCE_ROUTE_ID = "stegverse.route.canonical-governed.v1"
ORGANIZATION_BATCH_TASK_ID = "ORGANIZATION-BATCH-CUSTODY-REPLAY-001"
ORGANIZATION_BATCH_POLICY_EXTENSION = "stegverse_organization_receipt_batch"
ORGANIZATION_BATCH_REQUEST_REF = (
    "control/resident-execution-request.d/"
    "canonical-work-organization-batch-custody-replay-001.json"
)

REQUIRED_AUTHORITIES = {
    "credential_authority": "TV/TVC",
    "claim_fence_authority": "WORKERCOORDINATOR",
    "transition_authority": "INTERLOCK_INTR",
    "custody_replay_reconstruction_authority": "ORGANIZATION_LEDGER",
    "request_grants_authority": False,
    "sdk_executes_lifecycle": False,
    "authority_effect": "NONE_MANIFEST_RUNTIME_REQUEST_ONLY",
}

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(raw).hexdigest()

def organization_record_status(governance: Mapping[str, Any]) -> Any:
    """Read the SDK governance organization record status under the current or legacy name."""
    if ORGANIZATION_RECORD_STATUS_FIELD in governance:
        return governance[ORGANIZATION_RECORD_STATUS_FIELD]
    return governance.get(LEGACY_ORGANIZATION_RECORD_STATUS_FIELD)


def _require_organization_receipt(row: Mapping[str, Any], label: str, transition_id: str | None = None,
                                  *, record_refusal: bool = False, with_basis: bool = False):
    """The verified Organization receipt of this exact state receipt closes a transition.

    Master Records reconstruction fields are evidence only and never gate it.
    A refusal raises with its typed DENY or FAIL_CLOSED disposition and
    failed predicate; nothing is committed. `record_refusal` is set where the
    gate sits inside the transition this worker just attempted.
    """
    gate = organization_receipt_gate(row, expected_transition_id=transition_id, record_refusal=record_refusal)
    refusal = gate["refusal"]
    require(gate["verified"], f"{label}_organization_receipt_refused:"
            f"{(refusal or {}).get('disposition')}:{(refusal or {}).get('failed_predicate')}")
    if with_basis:
        return gate["organization_receipt_sha256"], gate["organization_readback_custody_basis"]
    return gate["organization_receipt_sha256"]


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)

def is_manifest_state_transition(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("schema") == REQUEST_SCHEMA

def _validate_manifest_hash(manifest: Mapping[str, Any], claimed: str, request: Mapping[str, Any]) -> None:
    # New SDK contract binds the original immutable ingress manifest separately
    # from its validated normalized projection; neither alters the frozen input.
    if "wire_manifest_sha256" in request or "canonical_manifest_projection" in request:
        wire = request.get("wire_manifest_sha256")
        projection = request.get("canonical_manifest_projection")
        require(isinstance(wire, str) and len(wire) == 64, "wire_manifest_sha256_required")
        require(sha256(manifest) == wire, "wire_manifest_sha256_mismatch")
        require(isinstance(projection, Mapping), "canonical_manifest_projection_required")
        require(sha256(projection) == claimed, "canonical_manifest_projection_sha256_mismatch")
        # The projection retains source fields except explicitly normalized fields.
        normalized = {"processing", "return_projection", "completion", "manifest_labels"}
        for key, value in manifest.items():
            if key not in normalized:
                require(projection.get(key) == value, f"canonical_manifest_projection_source_mismatch:{key}")
        require("canonical_manifest_sha256" not in manifest, "wire_manifest_must_not_embed_derived_digest")
        return
    # Historical self-contained worker fixtures remain accepted on their legacy
    # binding only; production SDK requests emit both new independent bindings.
    body = dict(manifest)
    embedded = body.pop("canonical_manifest_sha256", None)
    require(isinstance(embedded, str) and embedded == claimed, "canonical_manifest_sha256_binding_mismatch")
    require(sha256(body) == claimed, "canonical_manifest_sha256_recompute_mismatch")

def validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    require(request.get("schema") == REQUEST_SCHEMA, "manifest_state_transition_request_schema_mismatch")
    body = dict(request)
    claimed_request_hash = body.pop("request_sha256", None)
    require(isinstance(claimed_request_hash, str) and len(claimed_request_hash) == 64, "request_sha256_required")
    require(sha256(body) == claimed_request_hash, "request_sha256_mismatch")
    for key, expected in REQUIRED_AUTHORITIES.items():
        if key == "custody_replay_reconstruction_authority":
            # Compatibility for SDK manifests pinned to the previous wire value.
            # This input never grants Master Records sovereign authority: the
            # canonical runtime reality locus remains the Organization Ledger.
            require(request.get(key) in ("ORGANIZATION_LEDGER", "MASTER_RECORDS"),
                    "custody_replay_reconstruction_authority_mismatch")
            continue
        require(request.get(key) == expected, f"{key}_mismatch")
    manifest = request.get("canonical_manifest")
    require(isinstance(manifest, Mapping), "canonical_manifest_required")
    manifest_hash = request.get("canonical_manifest_sha256")
    require(isinstance(manifest_hash, str) and len(manifest_hash) == 64, "canonical_manifest_sha256_required")
    _validate_manifest_hash(manifest, manifest_hash, request)
    graph = request.get("state_graph")
    require(isinstance(graph, Mapping), "state_graph_required")
    require(graph.get("schema") == "stegverse.sdk.installed-state-transition-graph/v1", "state_graph_schema_mismatch")
    for key in ("graph_id", "processing_capability", "route_id"):
        require(isinstance(request.get(key), str) and request.get(key), f"{key}_required")
    require(graph.get("graph_id") == request.get("graph_id"), "graph_id_binding_mismatch")
    require(graph.get("processing_capability") == request.get("processing_capability"), "processing_capability_binding_mismatch")
    require(graph.get("route_id") == request.get("route_id"), "route_id_binding_mismatch")
    task_id = request.get("canonical_task_id")
    if request.get("requires_workercoordinator_claim_fence") is True:
        require(isinstance(task_id, str) and task_id, "canonical_task_id_required_for_worker_graph")
    elif task_id is not None:
        require(isinstance(task_id, str) and task_id, "canonical_task_id_invalid")
    require(request.get("predecessor_closure_required") is True, "predecessor_closure_required")
    return dict(request)

def sdk_manifest_binding(validated: Mapping[str, Any]) -> dict[str, str]:
    """Project only authenticated manifest lineage for downstream boundary validation."""
    validated = validate_request(validated)
    return {
        "request_sha256": str(validated["request_sha256"]),
        "canonical_manifest_sha256": str(validated["canonical_manifest_sha256"]),
        "processing_capability": str(validated["processing_capability"]),
        "route_id": str(validated["route_id"]),
    }


def bind_tvc_provider_request(
    validated: Mapping[str, Any], provider_request: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind a TVC credential request to manifest-selected semantics without selecting them.

    Provider/framework identity is provenance only. The four processing-lineage
    fields come exclusively from the already-validated SDK request; caller values
    are neither accepted nor consulted.
    """
    binding = sdk_manifest_binding(validated)
    request = dict(provider_request)
    lease = request.get("lease_receipt")
    require(isinstance(lease, Mapping), "tvc_capability_lease_required")
    request["sdk_manifest_binding"] = dict(binding)
    request["lease_receipt"] = {**dict(lease), "sdk_manifest_binding": dict(binding)}
    return request


def _request_path(runtime_root: Path, task_id: str) -> Path:
    return runtime_root / REQUEST_DIR / (task_id + LATEST_SUFFIX)

def persist_request(runtime_root: Path, request: Mapping[str, Any]) -> Path:
    """Retain immutable request bytes and advance only the non-authorizing latest pointer.

    Re-running the same canonical task with a newly manifested input must not collide
    with prior history. Every request remains content-addressed by request_sha256;
    the existing worker reads only the latest pointer for the current invocation.
    """
    task_id = str(request.get("canonical_task_id") or request["graph_id"])
    request_hash = str(request["request_sha256"])
    root = runtime_root / REQUEST_DIR
    immutable = root / IMMUTABLE_DIR / task_id / f"{request_hash}.json"
    latest = _request_path(runtime_root, task_id)
    raw = json.dumps(dict(request), indent=2, sort_keys=True) + "\n"
    immutable.parent.mkdir(parents=True, exist_ok=True)
    if immutable.exists():
        existing = json.loads(immutable.read_text(encoding="utf-8"))
        require(existing == dict(request), "manifest_state_transition_immutable_request_collision")
    else:
        immutable.write_text(raw, encoding="utf-8")
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return latest

def _closed(row: Any, transition_id: str | None = None) -> dict[str, Any]:
    require(isinstance(row, Mapping), "master_records_transition_missing")
    value = dict(row)
    if transition_id is not None:
        require(value.get("transition_id") == transition_id, f"transition_id_mismatch:{transition_id}")
    require(value.get("state") == "RECORDED", f"master_records_state_not_recorded:{value.get('transition_id')}")
    require(isinstance(value.get("receipt_sha256"), str) and value.get("receipt_sha256"), f"receipt_sha256_required:{value.get('transition_id')}")
    value["verified_organization_receipt_sha256"], value["organization_readback_custody_basis"] = (
        _require_organization_receipt(value, f"closure:{value.get('transition_id')}", value.get("transition_id"),
                                      with_basis=True))
    return value

def _assemble_purpose_result(request: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    result = receipt.get("result")
    require(isinstance(result, Mapping), "purpose_runtime_result_missing")
    assignment = _closed(receipt.get("claim_fence_master_records_transition"), "WORKERCOORDINATOR_CLAIM_FENCE_BOUND")
    closures = [
        assignment,
        _closed(result.get("warrant_policy_master_records_transition"), "TV_TVC_WARRANT_POLICY_VERIFIED"),
        _closed(result.get("intr_admission_master_records_transition"), "STEGCORE_INTR_MATERIALIZATION_ADMITTED"),
    ]
    lifecycle = result.get("purpose_bound_worker_result")
    require(isinstance(lifecycle, Mapping), "purpose_bound_worker_result_missing")
    lifecycle_closures = lifecycle.get("canonical_master_records_transitions")
    require(isinstance(lifecycle_closures, list), "purpose_lifecycle_closures_missing")
    for row in lifecycle_closures:
        closures.append(_closed(row))
    previous = None
    for index, row in enumerate(closures):
        if index and row.get("predecessor_receipt_sha256") != previous:
            raise ValueError(f"immediate_predecessor_closure_mismatch:{row.get('transition_id')}")
        previous = row.get("receipt_sha256")
    governance = result.get("governance")
    require(isinstance(governance, Mapping), "governance_result_missing")
    manifest_receipt_id = governance.get("manifest_receipt_id")
    require(isinstance(manifest_receipt_id, str) and manifest_receipt_id, "manifest_receipt_id_missing")
    # Each closure above is gated on its verified Organization receipt. Master
    # Records replay and reconstruction are evidence only and never gate it.
    replay = result.get("master_records_replay")
    reconstruction = result.get("master_records_reconstruction")
    return {
        "schema": RESULT_SCHEMA,
        "state": "COMPLETE",
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "graph_id": request["graph_id"],
        "canonical_task_id": request.get("canonical_task_id"),
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "transition_closures": closures,
        "closure_gate": "VERIFIED_ORGANIZATION_RECEIPT",
        "verified_organization_receipt_sha256s": [row["verified_organization_receipt_sha256"] for row in closures],
        "organization_readback_custody_bases": [row["organization_readback_custody_basis"] for row in closures],
        "replay_status": replay.get("status") if isinstance(replay, Mapping) else None,
        "reconstruction_status": "SUPPLIED" if isinstance(reconstruction, Mapping) else None,
        "master_records_role": "EVIDENCE_ONLY_NOT_A_CLOSURE_GATE",
        "terminal_state": {
            "records_only": result.get("records_only"),
            "continued_authority": result.get("continued_authority_after_retirement"),
            "worker_live_after_close": result.get("worker_live_after_close"),
        },
        "manifest_receipt_id": manifest_receipt_id,
        "authority_effect": "NONE_RETURN_ASSEMBLY_ONLY",
    }

def _nonworker_diagnostic_deny(
    runtime_root: Path, validated: Mapping[str, Any],
    *, reason_code: str = "ECOSYSTEM_DIAGNOSTIC_NONWORKER_DISPATCH_UNWIRED",
    terminal: bool = False,
    organization_receipt_refusal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Retain the evaluating profile's correctable DENY, not a forged InTr verdict.

    The current installed worker-only consumer cannot execute a diagnostic graph
    with no task claim. Source/profile evidence is explicitly not sovereign
    organization custody, EVENT_EPHEMERAL materialization or Master Records proof.
    When the consumer's Organization receipt gate refused, its typed refusal
    (failed predicate, retry entrypoint, recorded refusal receipt) is carried
    as evidence and no consequence is committed.
    """
    request_hash = str(validated["request_sha256"])
    graph_id = str(validated["graph_id"])
    original = validated.get("canonical_manifest") or {}
    payload = original.get("payload") if isinstance(original, Mapping) else None
    goal = payload.get("goal_task_id") if isinstance(payload, Mapping) else None
    cosv = payload.get("cosv") if isinstance(payload, Mapping) else None
    record = {
        "schema": "stegverse.sdk.manifest-profile-disposition/v1",
        "state": "FAIL_CLOSED" if terminal else "DENY",
        "disposition": "FAIL_CLOSED" if terminal else "DENY",
        "terminal": terminal,
        "automatic_retry_permitted": False,
        "retry_condition": ("SEPARATELY_GOVERNED_FUTURE_REENTRY_ONLY" if terminal
                            else "NEW_GOVERNED_ATTEMPT_AFTER_EXISTING_OWNER_REPAIR"),
        "evaluation_boundary": ("SDK_ADMITTED_DIAGNOSTIC_CONSUMER_LOCAL" if terminal
                                else "SDK_MANIFEST_PROFILE_SOURCE_ONLY"),
        "authentic_intr_disposition_observed": False,
        "organization_master_records_organization_record_observed": False,
        "transition_id": "SDK_ECOSYSTEM_DIAGNOSTIC_DISPATCH",
        "failed_predicate": (reason_code if reason_code !=
                             "ECOSYSTEM_DIAGNOSTIC_NONWORKER_DISPATCH_UNWIRED"
                             else "INSTALLED_NONWORKER_EVENT_EPHEMERAL_DIAGNOSTIC_DISPATCH"),
        "reason_code": reason_code,
        "goal_task_id": goal,
        "cosv": cosv,
        "graph_id": graph_id,
        "canonical_task_id": None,
        "processing_capability": "ecosystem_diagnostic",
        "wire_manifest_sha256": validated.get("wire_manifest_sha256"),
        "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
        "request_sha256": request_hash,
        "evidence_refs": [
            "StegVerse-Labs/.github:workers/manifest_state_transition_intr_ingress.py",
            "StegVerse-org/StegVerse-SDK:stegverse/manifest_state_transition_adapters.py",
            "StegVerse-Labs/.github:docs/STEGBROWSER_MANIFEST_INTR_INGRESS_EXECUTION_MIRROR_HANDOFF.md",
        ],
        "required_evidence_refs": [
            "AUTHENTIC_EVENT_EPHEMERAL_STEGOS_INVOCATION_BINDING",
            "EXACT_BOUND_SDK_DIAGNOSTIC_RESULT",
            "ORGANIZATION_PREDECESSOR_LINK_AND_MASTER_RECORDS_ORGANIZATION_RECORD",
        ],
        "repair_owner": "EXISTING_SDK_ECOSYSTEM_DIAGNOSTIC_AND_STEGBROWSER_INTR_OWNERS",
        "authority_effect": "NONE_SOURCE_PROFILE_DISPOSITION_ONLY",
    }
    if organization_receipt_refusal is not None:
        record["organization_receipt_refusal"] = dict(organization_receipt_refusal)
        record["retry_entrypoint"] = organization_receipt_refusal.get("retry_entrypoint")
        record["consequence_committed"] = False
    root = runtime_root / REQUEST_DIR / "dispositions" / graph_id
    root.mkdir(parents=True, exist_ok=True)
    suffix = hashlib.sha256((record["disposition"] + ":" + reason_code).encode("utf-8")).hexdigest()[:16]
    exact = root / f"{request_hash}.{suffix}.json"
    raw = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if exact.exists():
        require(exact.read_text(encoding="utf-8") == raw, "diagnostic_deny_immutable_collision")
    else:
        exact.write_text(raw, encoding="utf-8")
    return {**record, "source_disposition_ref": str(exact)}


#: Capabilities whose execution owner moved out of this worker. A manifest that
#: names one is not silently unhandled: the disposition points at the owner.
RELOCATED_CAPABILITY_OWNERS = {
    "stegbrowser": "stegverse.governed_llm_fan.run_governed_llm_fan",
}


def _capability_dispatch_fail_closed(runtime_root: Path, validated: Mapping[str, Any]) -> dict[str, Any]:
    """Retain a genuine admitted-profile failure when no executable owner is bound.

    This is the evaluating Universal InTr profile's disposition. It does not claim
    that the requested capability itself ran or that Organization/Master Records
    closure occurred.
    """
    capability = str(validated["processing_capability"])
    graph = validated.get("state_graph") or {}
    profile = graph.get("profile") if isinstance(graph, Mapping) else None
    record = {
        "schema": "stegverse.sdk.manifest-profile-disposition/v1",
        "state": "FAIL_CLOSED",
        "disposition": "FAIL_CLOSED",
        "terminal": False,
        "automatic_retry_permitted": False,
        "retry_condition": "BIND_EXISTING_MANIFEST_SELECTED_CAPABILITY_OWNER_THEN_NEW_GOVERNED_ATTEMPT",
        "evaluation_boundary": "UNIVERSAL_INTR_MANIFEST_CAPABILITY_DISPATCH",
        "authentic_intr_disposition_observed": True,
        "organization_master_records_organization_record_observed": False,
        "transition_id": "INGRESS_ADMITTED",
        "failed_predicate": "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND",
        "reason_code": "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_NOT_BOUND",
        # Not bound here, and for a relocated capability that is deliberate: the
        # owner is named so the disposition is actionable rather than a dead end.
        "relocated_owner": RELOCATED_CAPABILITY_OWNERS.get(capability),
        "owner_relocated_out_of_this_worker": capability in RELOCATED_CAPABILITY_OWNERS,
        "canonical_task_id": validated.get("canonical_task_id"),
        "graph_id": validated["graph_id"],
        "processing_capability": capability,
        "profile": profile,
        "route_id": validated["route_id"],
        "wire_manifest_sha256": validated.get("wire_manifest_sha256"),
        "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
        "request_sha256": validated["request_sha256"],
        "evidence_refs": [
            "StegVerse-Labs/.github:workers/manifest_state_transition_intr_ingress.py",
            "StegVerse-Labs/.github:data/ephemeral-external-ai-reusable-component-profile.v1.json",
        ],
        "required_evidence_refs": [
            "EXISTING_MANIFEST_SELECTED_OPERATION_OWNER_ENTRYPOINT",
            "ORGANIZATION_RECORDS_AFTER_CAPABILITY_DISPOSITION",
            "MASTER_RECORDS_RECONSTRUCTION_AFTER_ORGANIZATION_RECORDS",
        ],
        "repair_owner": "EXISTING_MANIFEST_SELECTED_CAPABILITY_OWNER",
        "consequence_committed": False,
        "authority_effect": "NONE_INTR_PROFILE_DISPOSITION_ONLY",
    }
    root = runtime_root / REQUEST_DIR / "dispositions" / "capability-dispatch" / capability
    root.mkdir(parents=True, exist_ok=True)
    exact = root / (validated["request_sha256"] + ".json")
    raw = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if exact.exists():
        require(exact.read_text(encoding="utf-8") == raw, "capability_dispatch_disposition_immutable_collision")
    else:
        exact.write_text(raw, encoding="utf-8")
    return {**record, "source_disposition_ref": str(exact)}



def _repo_root(name: str) -> Path | None:
    try:
        roots = json.loads(os.getenv("STEGVERSE_REPO_ROOTS_JSON", "{}"))
    except Exception:
        roots = {}
    raw = roots.get(name) if isinstance(roots, Mapping) else None
    if not raw:
        return None
    root = Path(str(raw)).expanduser().resolve()
    return root if root.is_dir() else None


def _custody_transition(*, transition_id: str, sequence: int, task_id: str,
                        outcome: str, prior: str | None, evidence: Mapping[str, Any],
                        # Required: the only path that relied on a default was the
                        # StegBrowser fan, and it no longer lives here. A caller that
                        # omitted this would have inherited a proof scope naming a
                        # capability this worker does not own.
                        proof_scope: str) -> dict[str, Any]:
    receipt = build_state_receipt(
        transition_id=transition_id,
        transition_sequence=sequence,
        subject_or_correlation_id=task_id,
        transition_outcome=outcome,
        prior_state_ref_or_hash=prior,
        resulting_state_ref_or_hash=sha256(evidence),
        governance_decision_ref_where_applicable=None,
        transition_evidence=evidence,
        proof_scope=proof_scope,
        proof_ceiling="ORGANIZATION_FIRST_THEN_MASTER_RECORDS_RECONSTRUCTION",
    )
    custody = submit_state_receipt(receipt)
    # Gate first so that any refusal of this attempted transition, including an
    # append that did not record, is appended as its non-ALLOW record.
    _require_organization_receipt(custody, transition_id, transition_id, record_refusal=True)
    require(custody.get("state") == "RECORDED", f"{transition_id}_organization_not_recorded")
    org = custody.get("organization_receipt")
    require(isinstance(org, Mapping) and org.get("receipt_sha256"), f"{transition_id}_organization_receipt_missing")
    return {"receipt": receipt, "custody": custody}


def _manifest_subject(validated: Mapping[str, Any]) -> str:
    task_id = validated.get("canonical_task_id")
    if isinstance(task_id, str) and task_id:
        return task_id
    manifest = validated.get("canonical_manifest")
    payload = manifest.get("payload") if isinstance(manifest, Mapping) else None
    candidate = payload.get("candidate") if isinstance(payload, Mapping) else None
    goal = candidate.get("goal_task_id") if isinstance(candidate, Mapping) else None
    if isinstance(goal, str) and goal:
        return goal
    return "SDK-MANIFEST-" + str(validated["canonical_manifest_sha256"])[:24]


def _governance_roots() -> dict[str, Path]:
    roots: dict[str, Path] = {}
    try:
        repo_roots = json.loads(os.getenv("STEGVERSE_REPO_ROOTS_JSON", "{}"))
    except Exception:
        repo_roots = {}
    if not isinstance(repo_roots, Mapping):
        repo_roots = {}
    for key, (env_name, repo_key, marker) in GOVERNANCE_SOURCE_ROOTS.items():
        raw = str(os.getenv(env_name) or repo_roots.get(repo_key) or "").strip()
        require(bool(raw), f"{env_name}_NOT_BOUND")
        root = Path(raw).expanduser().resolve()
        require((root / marker).is_file(), f"{env_name}_INVALID")
        roots[key] = root
    return roots


def _load_governance_owner():
    roots = _governance_roots()
    for path in (
        roots["sdk"],
        roots["stegcore"] / "src",
        roots["core_lite"],
        roots["master_records"],
    ):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)
    from stegverse.governance_ingress_runtime import external_manifest_to_public_request
    from stegverse.sovereign_validation_runtime import run_sovereign_validation
    return external_manifest_to_public_request, run_sovereign_validation


def _run_governance_owner(runtime_root: Path, validated: Mapping[str, Any]) -> dict[str, Any]:
    external_manifest_to_public_request, run_sovereign_validation = _load_governance_owner()
    manifest = validated.get("canonical_manifest")
    require(isinstance(manifest, Mapping), "canonical_manifest_required")
    public_request = external_manifest_to_public_request(manifest)
    run_root = runtime_root / REQUEST_DIR / "governance-owner" / str(validated["request_sha256"])
    run_root.mkdir(parents=True, exist_ok=True)
    result = run_sovereign_validation(
        public_request,
        custody_db=run_root / "manifest-receipt-custody.db",
        host_identity="universal-intr-manifest-governance",
    )
    require(isinstance(result, Mapping), "CANONICAL_GOVERNANCE_RESULT_OBJECT_REQUIRED")
    return dict(result)


def _closure_projection(row: Mapping[str, Any], *, predecessor_receipt_sha256: str | None = None) -> dict[str, Any]:
    custody = row.get("custody")
    receipt = row.get("receipt")
    require(isinstance(custody, Mapping), "master_records_organization_record_result_required")
    require(isinstance(receipt, Mapping), "canonical_state_transition_receipt_required")
    organization = custody.get("organization_receipt")
    require(isinstance(organization, Mapping), "organization_receipt_required")
    projected = {
        "transition_id": receipt.get("transition_id"),
        "state": custody.get("state"),
        "reconstruction_status": custody.get("reconstruction_status"),
        "required_evidence_validation_status": custody.get("required_evidence_validation_status"),
        "receipt_sha256": custody.get("receipt_sha256"),
        "reconstructed_receipt_sha256": custody.get("reconstructed_receipt_sha256"),
        "organization_receipt_sha256": organization.get("receipt_sha256"),
        "organization_predecessor_receipt_sha256": organization.get("previous_receipt_sha256"),
    }
    if predecessor_receipt_sha256 is not None:
        projected["predecessor_receipt_sha256"] = predecessor_receipt_sha256
    for key in ("transition_id", "receipt_sha256", "organization_receipt_sha256"):
        require(isinstance(projected.get(key), str) and projected[key], f"governance_closure_{key}_required")
    require(projected["state"] == "RECORDED", "governance_closure_organization_not_recorded")
    _require_organization_receipt(custody, "governance_closure", receipt.get("transition_id"))
    return projected


def _governance_disposition_record(
    runtime_root: Path,
    validated: Mapping[str, Any],
    *,
    disposition: str,
    transition_id: str,
    prior_organization_receipt_sha256: str,
    ingress_closure: Mapping[str, Any],
    evidence: Mapping[str, Any],
    reason_code: str | None = None,
    failed_predicate: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record the one parent governance disposition and return its exact custody row."""
    subject = _manifest_subject(validated)
    governed = _custody_transition(
        transition_id=transition_id,
        sequence=2,
        task_id=subject,
        outcome=disposition,
        prior=prior_organization_receipt_sha256,
        evidence=evidence,
        proof_scope="SDK_MANIFEST_SELECTED_GOVERNANCE_TRANSITION_ONLY",
    )
    closure = _closure_projection(
        governed,
        predecessor_receipt_sha256=str(ingress_closure["receipt_sha256"]),
    )
    result = {
        "schema": RESULT_SCHEMA,
        "state": "COMPLETE" if disposition == "ALLOW" else disposition,
        "disposition": disposition,
        "terminal": disposition != "ALLOW",
        "communication_terminal": False,
        "canonical_task_id": validated.get("canonical_task_id"),
        "subject_or_correlation_id": subject,
        "processing_capability": "governance",
        "route_id": validated["route_id"],
        "graph_id": validated["graph_id"],
        "request_sha256": validated["request_sha256"],
        "wire_manifest_sha256": validated.get("wire_manifest_sha256"),
        "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
        "resolved_ordered_transitions": ["INGRESS_ADMITTED", transition_id],
        "transition_closures": [dict(ingress_closure), closure],
        "organization_records_before_master_records": True,
        "organization_master_records_organization_record_observed": True,
        "publisher_executed": False,
        "site_propagation_executed": False,
        "authority_effect": "NONE_GOVERNANCE_DISPOSITION_ONLY",
    }
    if reason_code:
        result["reason_code"] = reason_code
    if failed_predicate:
        result["failed_predicate"] = failed_predicate
    return result, governed


def _governance_disposition(
    runtime_root: Path,
    validated: Mapping[str, Any],
    *,
    disposition: str,
    transition_id: str,
    prior_organization_receipt_sha256: str,
    ingress_closure: Mapping[str, Any],
    evidence: Mapping[str, Any],
    reason_code: str | None = None,
    failed_predicate: str | None = None,
) -> dict[str, Any]:
    return _governance_disposition_record(
        runtime_root,
        validated,
        disposition=disposition,
        transition_id=transition_id,
        prior_organization_receipt_sha256=prior_organization_receipt_sha256,
        ingress_closure=ingress_closure,
        evidence=evidence,
        reason_code=reason_code,
        failed_predicate=failed_predicate,
    )[0]


def _load_organization_append_owner():
    resident = Path(__file__).resolve().parents[1] / "resident-runtime"
    module_path = resident / "aggregate_repo_transition.py"
    require(module_path.is_file(), "ORGANIZATION_APPEND_OWNER_UNAVAILABLE")
    if str(resident) not in sys.path:
        sys.path.insert(0, str(resident))
    spec = importlib.util.spec_from_file_location(
        "stegverse_manifest_directed_organization_append", module_path
    )
    require(spec is not None and spec.loader is not None, "ORGANIZATION_APPEND_OWNER_IMPORT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_organization_batch_custody():
    resident = Path(__file__).resolve().parents[1] / "resident-runtime"
    require((resident / "organization_batch_custody.py").is_file(),
            "ORGANIZATION_BATCH_CUSTODY_OWNER_UNAVAILABLE")
    if str(resident) not in sys.path:
        sys.path.insert(0, str(resident))
    return importlib.import_module("organization_batch_custody")


def _organization_batch_parent_manifest(validated: Mapping[str, Any]) -> dict[str, Any]:
    """The batch parent manifest, validated by its owner in resident-runtime.

    The organization manifest ingress consumes the same SDK request schema, so
    both receivers share one validator and one set of failure codes.
    """
    return _load_organization_batch_custody().organization_batch_parent_manifest(validated)


def _evidence_entry(transition_id: str, evidence_id: str, evidence_type: str,
                    content: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(content)
    return {
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "origin_transition_id": transition_id,
        "encoding": "canonical-json",
        "sha256": sha256(body),
        "content": body,
    }


def _execute_organization_batch_after_allow(
    runtime_root: Path,
    validated: Mapping[str, Any],
    result: Mapping[str, Any],
    governed: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute the declared organization action as a consequence of the parent ALLOW."""
    parent_manifest = _organization_batch_parent_manifest(validated)
    subject = ORGANIZATION_BATCH_TASK_ID
    governance_receipt_sha256 = str((governed.get("custody") or {}).get("receipt_sha256") or "")
    require(len(governance_receipt_sha256) == 64, "ORGANIZATION_BATCH_PARENT_GOVERNANCE_RECEIPT_REQUIRED")
    governance_org = (governed.get("custody") or {}).get("organization_receipt")
    require(isinstance(governance_org, Mapping) and governance_org.get("receipt_sha256"),
            "ORGANIZATION_BATCH_PARENT_GOVERNANCE_ORG_RECEIPT_REQUIRED")
    parent_evidence = {
        "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
        "request_sha256": validated["request_sha256"],
        "parent_governance_disposition": "ALLOW",
        "parent_governance_transition_id": "GOVERNANCE_DISPOSITION",
        "parent_governance_receipt_sha256": governance_receipt_sha256,
        "parent_governance_organization_receipt_sha256": governance_org["receipt_sha256"],
        "manifest_receipt_id": governance.get("manifest_receipt_id"),
        "result_binding_hash": governance.get("result_binding_hash"),
    }

    dispatch = _custody_transition(
        transition_id="MANIFEST_DIRECTED_ORGANIZATION_APPEND_DISPATCHED",
        sequence=3,
        task_id=subject,
        outcome="EXECUTED",
        prior=str(governance_org["receipt_sha256"]),
        evidence=parent_evidence,
        proof_scope="MANIFEST_DIRECTED_ORGANIZATION_ACTION_DISPATCH_ONLY",
    )
    dispatch_closure = _closure_projection(
        dispatch, predecessor_receipt_sha256=governance_receipt_sha256
    )
    dispatch_receipt_sha256 = str((dispatch.get("custody") or {}).get("receipt_sha256") or "")
    dispatch_org = (dispatch.get("custody") or {}).get("organization_receipt")
    require(len(dispatch_receipt_sha256) == 64, "ORGANIZATION_BATCH_DISPATCH_RECEIPT_REQUIRED")
    require(isinstance(dispatch_org, Mapping) and dispatch_org.get("receipt_sha256"),
            "ORGANIZATION_BATCH_DISPATCH_ORG_RECEIPT_REQUIRED")

    completion_id = "MANIFEST_DIRECTED_ORGANIZATION_APPEND_COMPLETED"
    completion_evidence = {
        **parent_evidence,
        "dispatch_receipt_sha256": dispatch_receipt_sha256,
        "dispatch_organization_receipt_sha256": dispatch_org["receipt_sha256"],
    }
    completion_receipt = build_state_receipt(
        transition_id=completion_id,
        transition_sequence=4,
        subject_or_correlation_id=subject,
        transition_outcome="COMPLETED",
        prior_state_ref_or_hash="sha256:" + dispatch_receipt_sha256,
        resulting_state_ref_or_hash=validated["canonical_manifest_sha256"],
        governance_decision_ref_where_applicable="sha256:" + governance_receipt_sha256,
        transition_evidence=completion_evidence,
        required_evidence_manifest=[
            _evidence_entry(
                completion_id,
                "parent-governance-allow",
                "PARENT_GOVERNANCE_ALLOW_CLOSURE",
                parent_evidence,
            ),
            _evidence_entry(
                completion_id,
                "organization-append-dispatch",
                "MANIFEST_DIRECTED_ACTION_DISPATCH_CLOSURE",
                {
                    "receipt_sha256": dispatch_receipt_sha256,
                    "organization_receipt_sha256": dispatch_org["receipt_sha256"],
                    "state": "RECORDED",
                    "reconstruction_status": "PASS",
                    "required_evidence_validation_status": "PASS",
                },
            ),
        ],
        proof_scope="MANIFEST_DIRECTED_ORGANIZATION_ACTION_RESULT_ONLY",
        proof_ceiling="ORGANIZATION_RECEIPT_PACKET_AND_BATCH_CUSTODY_ONLY",
    )
    owner = _load_organization_append_owner()
    try:
        organization_receipt = owner.aggregate_transition(
            completion_receipt,
            org_transition_class="MANIFEST_DIRECTED_ORGANIZATION_ACTION",
            boundary_evidence={
                "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
                "parent_governance_receipt_sha256": governance_receipt_sha256,
                "parent_governance_result_binding_hash": governance.get("result_binding_hash"),
                "parent_governance_disposition": "ALLOW",
                "dispatch_receipt_sha256": dispatch_receipt_sha256,
            },
            authority_effect="NONE",
            parent_manifest=parent_manifest,
        )
    except Exception as exc:
        failure = _custody_transition(
            transition_id="MANIFEST_DIRECTED_ORGANIZATION_APPEND_FAILED",
            sequence=4,
            task_id=subject,
            outcome="FAILED",
            prior=str(dispatch_org["receipt_sha256"]),
            evidence={
                **completion_evidence,
                "error_class": type(exc).__name__,
                "error": str(exc),
                "failed_predicate": "MANIFEST_DIRECTED_ORGANIZATION_APPEND_COMPLETED",
                "retry_entrypoint": (
                    "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
                ),
            },
            proof_scope="MANIFEST_DIRECTED_ORGANIZATION_ACTION_FAILURE_ONLY",
        )
        failure_closure = _closure_projection(
            failure, predecessor_receipt_sha256=dispatch_receipt_sha256
        )
        return {
            **dict(result),
            "manifest_directed_action": {
                "schema": "stegverse.manifest-directed-action-execution/v1",
                "action_id": "ORGANIZATION_APPEND",
                "execution_result": "FAILED",
                "governance_disposition": None,
                "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
                "parent_governance_receipt_sha256": governance_receipt_sha256,
                "dispatch_closure": dispatch_closure,
                "failure_closure": failure_closure,
                "reason": str(exc),
                "failed_predicate": "MANIFEST_DIRECTED_ORGANIZATION_APPEND_COMPLETED",
                "retry_entrypoint": (
                    "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
                ),
                "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
            },
        }

    boundary = organization_receipt.get("boundary_evidence")
    released = boundary.get("parent_manifest_released_batch") if isinstance(boundary, Mapping) else None
    return {
        **dict(result),
        "manifest_directed_action": {
            "schema": "stegverse.manifest-directed-action-execution/v1",
            "action_id": "ORGANIZATION_APPEND",
            "execution_result": "COMPLETED",
            "governance_disposition": None,
            "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
            "parent_governance_receipt_sha256": governance_receipt_sha256,
            "dispatch_closure": dispatch_closure,
            "organization_receipt_sha256": organization_receipt.get("receipt_sha256"),
            "organization_previous_receipt_sha256": organization_receipt.get("previous_receipt_sha256"),
            "source_transition_sha256": organization_receipt.get("source_transition_sha256"),
            "released_batch": released,
            "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
        },
    }


def _execute_governance(
    runtime_root: Path,
    validated: Mapping[str, Any],
    transport: Mapping[str, Any] | None,
) -> dict[str, Any]:
    require(validated.get("route_id") == GOVERNANCE_ROUTE_ID, "CANONICAL_GOVERNANCE_ROUTE_REQUIRED")
    require(isinstance(transport, Mapping), "AUTHENTIC_INTR_TRANSPORT_EVIDENCE_REQUIRED")
    require(transport.get("origin") == "TVC_RELAY_EGRESS", "CANONICAL_GOVERNANCE_REQUIRES_TVC_RELAY_EGRESS")
    authorization_id = transport.get("authorization_id")
    require(isinstance(authorization_id, str) and authorization_id,
            "CANONICAL_GOVERNANCE_TVC_RELAY_AUTHORIZATION_REQUIRED")
    subject = _manifest_subject(validated)
    ingress = _custody_transition(
        transition_id="INGRESS_ADMITTED",
        sequence=1,
        task_id=subject,
        outcome="ALLOW",
        prior=None,
        evidence={
            "request_sha256": validated["request_sha256"],
            "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
            "route_id": validated["route_id"],
            "processing_capability": "governance",
            "transport_origin": transport.get("origin"),
            "transport_authorization_id_sha256": sha256(authorization_id.encode("utf-8")),
            "transport_payload_sha256": transport.get("payload_sha256"),
        },
        proof_scope="SDK_MANIFEST_SELECTED_GOVERNANCE_TRANSITION_ONLY",
    )
    ingress_closure = _closure_projection(ingress)
    prior_org = str((ingress["custody"]["organization_receipt"])["receipt_sha256"])
    try:
        governance = _run_governance_owner(runtime_root, validated)
    except Exception as exc:
        return _governance_disposition(
            runtime_root,
            validated,
            disposition="FAIL_CLOSED",
            transition_id="GOVERNANCE_CAPABILITY_DISPATCH",
            prior_organization_receipt_sha256=prior_org,
            ingress_closure=ingress_closure,
            reason_code="CANONICAL_GOVERNANCE_OWNER_EXECUTION_FAILED",
            failed_predicate="MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND_AND_EXECUTABLE",
            evidence={
                "request_sha256": validated["request_sha256"],
                "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
                "error_class": type(exc).__name__,
                "error": str(exc),
                "repair_owner": "EXISTING_SDK_CANONICAL_GOVERNANCE_OWNER",
                "new_runtime_created": False,
            },
        )
    raw_disposition = str(governance.get("governance_state") or "").upper()
    if raw_disposition not in {"ALLOW", "DENY"}:
        return _governance_disposition(
            runtime_root,
            validated,
            disposition="FAIL_CLOSED",
            transition_id="GOVERNANCE_DISPOSITION",
            prior_organization_receipt_sha256=prior_org,
            ingress_closure=ingress_closure,
            reason_code="CANONICAL_GOVERNANCE_DISPOSITION_INVALID",
            failed_predicate="EXACT_CANONICAL_GOVERNANCE_DISPOSITION_ALLOW_OR_DENY",
            evidence={
                "request_sha256": validated["request_sha256"],
                "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
                "observed_governance_state": governance.get("governance_state"),
                "result_binding_hash": governance.get("result_binding_hash"),
            },
        )
    result, governed = _governance_disposition_record(
        runtime_root,
        validated,
        disposition=raw_disposition,
        transition_id="GOVERNANCE_DISPOSITION",
        prior_organization_receipt_sha256=prior_org,
        ingress_closure=ingress_closure,
        evidence={
            "request_sha256": validated["request_sha256"],
            "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
            "governance_state": raw_disposition,
            "manifest_receipt_id": governance.get("manifest_receipt_id"),
            "transaction_id": governance.get("transaction_id"),
            "result_binding_hash": governance.get("result_binding_hash"),
            "sdk_master_records_organization_record_status": organization_record_status(governance),
            "sdk_chain_verified": governance.get("chain_verified"),
            "external_side_effect": governance.get("external_side_effect"),
            "publisher_executed": False,
        },
    )
    if raw_disposition == "ALLOW" and validated.get("canonical_task_id") == ORGANIZATION_BATCH_TASK_ID:
        return _execute_organization_batch_after_allow(
            runtime_root, validated, result, governed, governance
        )
    return result


def execute(
    runtime_root: Path,
    request: Mapping[str, Any],
    *,
    transport: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validated = validate_request(request)
    task_id = validated.get("canonical_task_id")
    persist_request(runtime_root, validated)
    if validated.get("processing_capability") == "sovereign_inference":
        from workers.shwp_manifest_parent_consumer import (
            execute as execute_shwp, retain_source_result,
        )
        # The installed SDK graph selects this route; task identity alone
        # cannot select it, and the adapter independently verifies the exact
        # unchanged original request and current canonical Registry/COSV.
        require(validated.get("route_id") == "stegverse.route.shwp-sovereign-inference.v1",
                "SHWP_DECLARED_SDK_ROUTE_REQUIRED")
        outcome = execute_shwp(Path(__file__).resolve().parents[1], runtime_root, validated)
        return retain_source_result(runtime_root, outcome)
    if validated.get("processing_capability") == "ecosystem_diagnostic" and task_id is None:
        from workers.sdk_manifest_diagnostic_admitted_consumer import (
            DiagnosticAdmissionError, DiagnosticExecutionFailClosed, consume,
        )
        try:
            return consume(Path(__file__).resolve().parents[1], runtime_root, validated)
        except DiagnosticAdmissionError as exc:
            return _nonworker_diagnostic_deny(runtime_root, validated, reason_code=exc.predicate)
        except DiagnosticExecutionFailClosed as exc:
            return _nonworker_diagnostic_deny(
                runtime_root, validated, reason_code=exc.predicate, terminal=True,
                organization_receipt_refusal=exc.refusal)
    if validated.get("processing_capability") == "governance":
        return _execute_governance(runtime_root, validated, transport)
    require(isinstance(task_id, str) and task_id, "canonical_task_id_required")
    capability = validated.get("processing_capability")
    graph = validated.get("state_graph") or {}
    # Purpose/atomic workers already have a canonical WorkerCoordinator result
    # assembler below. Other installed capabilities must be bound to their
    # existing manifest-selected operation owner before that owner is invoked;
    # never fall through to the Test-1 purpose-worker receipt path.
    # StegBrowser's fan execution no longer lives here. Translating a v2 journey
    # into one round trip per branch, minting each branch's ephemeral lease and
    # calling the browser owner is orchestration, not authority, so it moved to
    # where the capability is offered: stegverse.governed_llm_fan. The SDK's
    # branch requests were verified byte-identical to the ones this worker
    # produced, and that agreement is frozen as an SDK fixture, so a packet
    # replays the same either way. A manifest naming stegbrowser now falls to the
    # capability dispatch below, which fails closed and names the owner it moved
    # to rather than pretending nothing was requested.
    if capability not in {"purpose_bound_worker", "atomic_task_worker"}:
        return _capability_dispatch_fail_closed(runtime_root, validated)
    runtime = WorkerCoordinator(runtime_root, adapters=load_adapters(runtime_root))
    cycle = runtime.cycle(write=True, target_task_id=task_id)
    require(isinstance(cycle, Mapping), "workercoordinator_cycle_result_missing")
    latest = runtime_root / "receipts/sovereign-host/sdk-tt-purpose-bound-worker-runtime-proof.latest.json"
    if not latest.is_file():
        # The targeted worker cycle was invoked, but no original purpose receipt
        # was returned. This is an actionable verdict at THIS profile boundary,
        # never a claim that InTr denied an unobserved downstream transition.
        record = {
            "schema": "stegverse.sdk.manifest-profile-disposition/v1",
            "state": "FAIL_CLOSED",
            "disposition": "FAIL_CLOSED",
            "evaluation_boundary": "SDK_MANIFEST_WORKER_RESULT_ATTACHMENT",
            "reason_code": "AUTHENTIC_PURPOSE_RUNTIME_RECEIPT_NOT_OBSERVED",
            "failed_predicate": "EXACT_REQUEST_BOUND_PURPOSE_RUNTIME_RECEIPT_PRESENT",
            "canonical_task_id": task_id,
            "graph_id": validated["graph_id"],
            "processing_capability": validated["processing_capability"],
            "route_id": validated["route_id"],
            "request_sha256": validated["request_sha256"],
            "canonical_manifest_sha256": validated["canonical_manifest_sha256"],
            "consequence_committed_by_this_profile": False,
            "authentic_intr_disposition_observed": False,
            "organization_master_records_organization_record_observed": False,
            "required_evidence_refs": [
                "EXACT_REQUEST_BOUND_ORIGINAL_INTR_DISPOSITION",
                "ORGANIZATION_LEDGER_RECEIPT_AND_PREDECESSOR",
                "MATCHING_MASTER_RECORDS_RECONSTRUCTION",
            ],
            "repair_owner": "EXISTING_MANIFEST_WORKERCOORDINATOR_INTR_AND_CUSTODY_OWNERS",
            "retry_entrypoint": "EXISTING_SDK_MANIFEST_UNIVERSAL_INTR_INGRESS",
            "automatic_retry_permitted": False,
            "authority_effect": "NONE_PROFILE_BOUNDARY_DISPOSITION_ONLY",
        }
        root = runtime_root / REQUEST_DIR / "dispositions" / "runtime-attachment"
        root.mkdir(parents=True, exist_ok=True)
        exact = root / (validated["request_sha256"] + ".json")
        raw = json.dumps(record, sort_keys=True, indent=2) + "\n"
        if exact.exists():
            require(exact.read_text(encoding="utf-8") == raw,
                    "runtime_attachment_disposition_immutable_collision")
        else:
            exact.write_text(raw, encoding="utf-8")
        return {**record, "source_disposition_ref": str(exact)}
    receipt = json.loads(latest.read_text(encoding="utf-8"))
    require(receipt.get("task_id") == task_id, "purpose_runtime_receipt_task_mismatch")
    return _assemble_purpose_result(validated, receipt)

_REPAIRABLE_MANIFEST_BINDING_CODES = {
    "canonical_manifest_sha256_binding_mismatch",
    "canonical_manifest_sha256_recompute_mismatch",
    "wire_manifest_sha256_required",
    "wire_manifest_sha256_mismatch",
    "canonical_manifest_projection_required",
    "canonical_manifest_projection_sha256_mismatch",
}


def _manifest_binding_deny(
    runtime_root: Path, request: Mapping[str, Any], *, reason_code: str
) -> dict[str, Any]:
    """Record a specific correctable profile DENY without inventing InTr admission.

    Called only after existing transport validation succeeded. This receipt is
    the evaluating SDK manifest profile's verdict, not an organization receipt,
    a Master Records organization record, or permission to retry a consequential operation.
    """
    actual = sha256(request)
    manifest = request.get("canonical_manifest")
    record = {
        "schema": "stegverse.sdk.manifest-profile-disposition/v1",
        "state": "DENY",
        "disposition": "DENY",
        "terminal": False,
        "automatic_retry_permitted": False,
        "retry_condition": "CORRECT_ENVELOPE_IN_EXISTING_MANIFEST_BUILDER_THEN_NEW_GOVERNED_ATTEMPT",
        "evaluation_boundary": "SDK_MANIFEST_PROFILE",
        "transport_validated": True,
        "authentic_intr_admission_observed": False,
        "organization_master_records_organization_record_observed": False,
        "transition_id": "SDK_MANIFEST_BINDING",
        "reason_code": reason_code,
        "failed_predicate": reason_code,
        "repair_owner": "StegVerse-org/StegVerse-SDK:stegverse/manifest_builder.py",
        "original_request_sha256": actual,
        "claimed_request_sha256": request.get("request_sha256"),
        "original_wire_manifest_sha256": sha256(manifest) if isinstance(manifest, Mapping) else None,
        "claimed_wire_manifest_sha256": request.get("wire_manifest_sha256"),
        "claimed_canonical_manifest_sha256": request.get("canonical_manifest_sha256"),
        "canonical_task_id": request.get("canonical_task_id"),
        "graph_id": request.get("graph_id"),
        "processing_capability": request.get("processing_capability"),
        "required_evidence_refs": ["CORRECTED_MANIFEST_BUILDER_ENVELOPE", "NEW_GOVERNED_ATTEMPT"],
        "authority_effect": "NONE_MANIFEST_PROFILE_DENY_ONLY",
    }
    root = runtime_root / REQUEST_DIR / "dispositions" / "manifest-binding"
    root.mkdir(parents=True, exist_ok=True)
    exact = root / f"{actual}.json"
    raw = json.dumps(record, sort_keys=True, indent=2) + "\n"
    if exact.exists():
        require(exact.read_text(encoding="utf-8") == raw, "manifest_binding_deny_immutable_collision")
    else:
        exact.write_text(raw, encoding="utf-8")
    return {**record, "source_disposition_ref": str(exact)}


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str], transport_validator) -> dict[str, Any]:
    transport = transport_validator(headers, body)
    require(transport.get("origin") in {"STEGOS_NODE_OUTBOX", "TVC_RELAY_EGRESS"}, "manifest_state_transition_transport_origin_invalid")
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("manifest_state_transition_request_json_invalid") from exc
    require(isinstance(payload, dict), "manifest_state_transition_request_object_required")
    try:
        return execute(runtime_root, payload, transport=transport)
    except ValueError as exc:
        reason_code = str(exc)
        # Only a concrete, correctable manifest-binding mismatch returns DENY.
        # All unrelated authentication, state or custody errors remain fail closed.
        if reason_code not in _REPAIRABLE_MANIFEST_BINDING_CODES:
            raise
        return _manifest_binding_deny(runtime_root, payload, reason_code=reason_code)

__all__ = ["PROFILE", "REQUEST_SCHEMA", "RESULT_SCHEMA", "admit", "bind_tvc_provider_request", "execute", "is_manifest_state_transition", "sdk_manifest_binding", "validate_request"]
