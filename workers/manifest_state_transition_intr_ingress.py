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
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Mapping

from heartbeat_runtime.worker_runtime import WorkerCoordinator
from scripts.run_worker_runtime import load_adapters
from workers.canonical_state_transition_custody import build_state_receipt, submit_state_receipt

REQUEST_SCHEMA = "stegverse.sdk.manifest-state-transition-request/v1"
RESULT_SCHEMA = "stegverse.sdk.manifest-state-transition-result/v1"
PROFILE = "SDK:ManifestStateTransition"
REQUEST_DIR = Path("runtime-state/sdk-manifest-state-transition")
LATEST_SUFFIX = ".latest.json"
IMMUTABLE_DIR = "requests"

GOVERNANCE_SOURCE_ROOTS = {
    "sdk": ("STEGVERSE_SDK_SOURCE_ROOT", "StegVerse-org/StegVerse-SDK", "stegverse/governance_ingress_runtime.py"),
    "stegcore": ("STEGVERSE_STEGCORE_SOURCE_ROOT", "StegVerse-Labs/StegCore", "src/stegcore/transaction_lifecycle.py"),
    "core_lite": ("STEGVERSE_CORE_LITE_SOURCE_ROOT", "Data-Continuation/core-lite", "core_lite/transaction_route.py"),
    "master_records": ("STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "master-records/orchestration", "services/manifest_receipt_custody.py"),
}
GOVERNANCE_ROUTE_ID = "stegverse.route.canonical-governed.v1"

REQUIRED_AUTHORITIES = {
    "credential_authority": "TV/TVC",
    "claim_fence_authority": "WORKERCOORDINATOR",
    "transition_authority": "INTERLOCK_INTR",
    "custody_replay_reconstruction_authority": "MASTER_RECORDS",
    "request_grants_authority": False,
    "sdk_executes_lifecycle": False,
    "authority_effect": "NONE_MANIFEST_RUNTIME_REQUEST_ONLY",
}

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(raw).hexdigest()

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
    require(value.get("reconstruction_status") == "PASS", f"reconstruction_not_pass:{value.get('transition_id')}")
    require(value.get("required_evidence_validation_status") == "PASS", f"required_evidence_not_pass:{value.get('transition_id')}")
    receipt = value.get("receipt_sha256")
    require(isinstance(receipt, str) and receipt == value.get("reconstructed_receipt_sha256"), f"receipt_reconstruction_digest_mismatch:{value.get('transition_id')}")
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
    replay = result.get("master_records_replay")
    require(isinstance(replay, Mapping) and replay.get("status") == "PASS", "MASTER_RECORDS_REPLAY_NOT_OBSERVED")
    reconstruction = result.get("master_records_reconstruction")
    require(isinstance(reconstruction, Mapping), "MASTER_RECORDS_RECONSTRUCTION_NOT_OBSERVED")
    return {
        "schema": RESULT_SCHEMA,
        "state": "COMPLETE",
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "graph_id": request["graph_id"],
        "canonical_task_id": request.get("canonical_task_id"),
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "transition_closures": closures,
        "replay_status": "PASS",
        "reconstruction_status": "PASS",
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
) -> dict[str, Any]:
    """Retain the evaluating profile's correctable DENY, not a forged InTr verdict.

    The current installed worker-only consumer cannot execute a diagnostic graph
    with no task claim. Source/profile evidence is explicitly not sovereign
    organization custody, EVENT_EPHEMERAL materialization or Master Records proof.
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
        "organization_master_records_closure_observed": False,
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
            "ORGANIZATION_PREDECESSOR_LINK_AND_MASTER_RECORDS_CLOSURE",
        ],
        "repair_owner": "EXISTING_SDK_ECOSYSTEM_DIAGNOSTIC_AND_STEGBROWSER_INTR_OWNERS",
        "authority_effect": "NONE_SOURCE_PROFILE_DISPOSITION_ONLY",
    }
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
        "organization_master_records_closure_observed": False,
        "transition_id": "INGRESS_ADMITTED",
        "failed_predicate": "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_BOUND",
        "reason_code": "MANIFEST_SELECTED_CAPABILITY_EXECUTION_OWNER_NOT_BOUND",
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
                        proof_scope: str = "SDK_MANIFEST_SELECTED_STEGBROWSER_LLM_TRANSITION_ONLY") -> dict[str, Any]:
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
    require(custody.get("state") == "RECORDED", f"{transition_id}_master_records_not_recorded")
    require(custody.get("reconstruction_status") == "PASS", f"{transition_id}_reconstruction_not_pass")
    require(custody.get("required_evidence_validation_status") == "PASS", f"{transition_id}_evidence_not_pass")
    org = custody.get("organization_receipt")
    require(isinstance(org, Mapping) and org.get("receipt_sha256"), f"{transition_id}_organization_receipt_missing")
    return {"receipt": receipt, "custody": custody}


def _execute_stegbrowser_llm(runtime_root: Path, validated: Mapping[str, Any]) -> dict[str, Any]:
    graph = validated.get("state_graph") or {}
    op = graph.get("request") if isinstance(graph, Mapping) else None
    require(isinstance(op, Mapping), "stegbrowser_llm_manifest_operation_missing")
    secure_url = op.get("secure_url")
    actions = op.get("browser_actions")
    require(isinstance(secure_url, str) and secure_url.startswith("https://"),
            "stegbrowser_llm_secure_url_required")
    require(isinstance(actions, list) and actions, "stegbrowser_llm_browser_actions_required")
    task_id = str(validated["canonical_task_id"])
    host = (urlsplit(secure_url).hostname or "").lower()
    source = _repo_root("StegVerse-Labs/StegBrowser")
    if source is None:
        failed = _custody_transition(
            transition_id="INGRESS_ADMITTED", sequence=1, task_id=task_id,
            outcome="FAIL_CLOSED", prior=None,
            evidence={
                "request_sha256": validated["request_sha256"],
                "route_id": validated["route_id"],
                "processing_capability": "stegbrowser",
                "profile": graph.get("profile"),
                "failed_predicate": "STEGBROWSER_SOURCE_ROOT_BOUND",
                "required_repo_root": "StegVerse-Labs/StegBrowser",
                "retry_condition": "MATERIALIZE_EXISTING_OWNER_SOURCE_AND_RETRY_SAME_MANIFEST",
            },
        )
        return {
            "schema": RESULT_SCHEMA, "state": "FAIL_CLOSED", "disposition": "FAIL_CLOSED",
            "terminal": False, "canonical_task_id": task_id,
            "processing_capability": "stegbrowser", "route_id": validated["route_id"],
            "request_sha256": validated["request_sha256"],
            "failed_predicate": "STEGBROWSER_SOURCE_ROOT_BOUND",
            "transition_closures": [failed],
            "organization_records_before_master_records": True,
            "authority_effect": "NONE_RETURN_ASSEMBLY_ONLY",
        }
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from src.stegbrowser.llm_browser_execution import execute_manifested_llm_browser_operation

    now = datetime.now(timezone.utc)
    lease = {
        "schema": "stegbrowser.ecosystem-ephemeral-lease.v1",
        "lease_id": "sdk-" + str(validated["request_sha256"])[:20],
        "task_id": task_id,
        "requester": "SDK:ManifestStateTransition",
        "purpose": "manifest-selected credential-free llm.v1 browser operation",
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
        "allowed_origins": [host],
        "allowed_actions": ["navigate", "read_public", "submit_form"],
        "retain_artifacts": ["navigation_receipt", "content_commitment", "governance_receipt"],
        "max_navigations": 4,
        "persistent_profile": False, "persist_cookies": False, "persist_history": False,
    }
    ingress = _custody_transition(
        transition_id="INGRESS_ADMITTED", sequence=1, task_id=task_id, outcome="ALLOW", prior=None,
        evidence={"request_sha256": validated["request_sha256"], "route_id": validated["route_id"],
                  "processing_capability": "stegbrowser", "profile": graph.get("profile"),
                  "secure_url_host": host, "credential_required": False},
    )
    prior = ingress["custody"]["organization_receipt"]["receipt_sha256"]
    try:
        result = execute_manifested_llm_browser_operation(op, lease)
    except Exception as exc:
        failure_evidence = {
            "request_sha256": validated["request_sha256"],
            "route_id": validated["route_id"],
            "processing_capability": "stegbrowser",
            "profile": graph.get("profile"),
            "secure_url_host": host,
            "failed_predicate": "MANIFEST_SELECTED_STEGBROWSER_BROWSER_OPERATION_COMPLETED",
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:1000],
            "credential_required": False,
            "retry_condition": "REPAIR_EXISTING_STEGBROWSER_OWNER_OR_MANIFEST_DATA_THEN_RETRY_SAME_MANIFEST",
        }
        failed = _custody_transition(
            transition_id="LLM_PROFILE_INTERACTION", sequence=2, task_id=task_id,
            outcome="FAIL_CLOSED", prior=prior, evidence=failure_evidence,
        )
        return {
            "schema": RESULT_SCHEMA, "state": "FAIL_CLOSED", "disposition": "FAIL_CLOSED",
            "terminal": False, "canonical_task_id": task_id,
            "processing_capability": "stegbrowser", "route_id": validated["route_id"],
            "request_sha256": validated["request_sha256"],
            "failed_predicate": failure_evidence["failed_predicate"],
            "failure": failure_evidence,
            "transition_closures": [ingress, failed],
            "organization_records_before_master_records": True,
            "authority_effect": "NONE_RETURN_ASSEMBLY_ONLY",
        }
    interaction = _custody_transition(
        transition_id="LLM_PROFILE_INTERACTION", sequence=2, task_id=task_id, outcome="ALLOW", prior=prior,
        evidence={"request_sha256": validated["request_sha256"], "browser_result": result},
    )
    prior = interaction["custody"]["organization_receipt"]["receipt_sha256"]
    egress = _custody_transition(
        transition_id="EGRESS_ADMITTED", sequence=3, task_id=task_id, outcome="ALLOW", prior=prior,
        evidence={"request_sha256": validated["request_sha256"],
                  "result_commitment": sha256(result.get("result") or {}),
                  "endpoint_receipts": result.get("endpoint_receipts")},
    )
    return {
        "schema": RESULT_SCHEMA, "state": "COMPLETE", "disposition": "ALLOW",
        "canonical_task_id": task_id, "processing_capability": "stegbrowser",
        "route_id": validated["route_id"], "request_sha256": validated["request_sha256"],
        "browser_execution": result,
        "transition_closures": [ingress, interaction, egress],
        "organization_records_before_master_records": True,
        "authority_effect": "NONE_RETURN_ASSEMBLY_ONLY",
    }



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
    require(isinstance(custody, Mapping), "master_records_custody_result_required")
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
    for key in ("transition_id", "receipt_sha256", "reconstructed_receipt_sha256",
                "organization_receipt_sha256"):
        require(isinstance(projected.get(key), str) and projected[key], f"governance_closure_{key}_required")
    require(projected["state"] == "RECORDED", "governance_closure_master_records_not_recorded")
    require(projected["reconstruction_status"] == "PASS", "governance_closure_reconstruction_not_pass")
    require(projected["required_evidence_validation_status"] == "PASS", "governance_closure_evidence_not_pass")
    require(projected["receipt_sha256"] == projected["reconstructed_receipt_sha256"],
            "governance_closure_receipt_reconstruction_mismatch")
    return projected


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
        "organization_master_records_closure_observed": True,
        "publisher_executed": False,
        "site_propagation_executed": False,
        "authority_effect": "NONE_GOVERNANCE_DISPOSITION_ONLY",
    }
    if reason_code:
        result["reason_code"] = reason_code
    if failed_predicate:
        result["failed_predicate"] = failed_predicate
    return result


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
    return _governance_disposition(
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
            "sdk_master_records_custody_status": governance.get("master_records_custody_status"),
            "sdk_chain_verified": governance.get("chain_verified"),
            "external_side_effect": governance.get("external_side_effect"),
            "publisher_executed": False,
        },
    )


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
                runtime_root, validated, reason_code=exc.predicate, terminal=True)
    if validated.get("processing_capability") == "governance":
        return _execute_governance(runtime_root, validated, transport)
    require(isinstance(task_id, str) and task_id, "canonical_task_id_required")
    capability = validated.get("processing_capability")
    graph = validated.get("state_graph") or {}
    # Purpose/atomic workers already have a canonical WorkerCoordinator result
    # assembler below. Other installed capabilities must be bound to their
    # existing manifest-selected operation owner before that owner is invoked;
    # never fall through to the Test-1 purpose-worker receipt path.
    if capability == "stegbrowser" and graph.get("profile") == "llm.v1":
        return _execute_stegbrowser_llm(runtime_root, validated)
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
            "organization_master_records_closure_observed": False,
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
    a Master Records closure, or permission to retry a consequential operation.
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
        "organization_master_records_closure_observed": False,
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

__all__ = ["PROFILE", "REQUEST_SCHEMA", "RESULT_SCHEMA", "admit", "execute", "is_manifest_state_transition", "validate_request"]
