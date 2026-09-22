#!/usr/bin/env python3
"""Dispatch bounded resident execution requests independently.

This dispatcher is transport-free and non-authorizing. It does not mint claims,
fences, credentials, heartbeat authority, publication authority, or runtime
authority. Each request-specific consumer remains responsible for validating its
own request and invoking only its already-admitted execution path.

A failed or blocked request never prevents later independent requests from being
visited. Consumers retain their own exactly-once semantics. Callers may select an
exact subset of registered consumers; unknown selectors fail before any consumer
is invoked.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_REL = Path("receipts/sovereign-host/resident-request-dispatch.latest.json")
SDK_EVALUATOR_SELECTOR = "sdk_evaluator_governance_posture"
SDK_EVALUATOR_REQUEST_REL = Path("control/resident-execution-request.d/sdk-evaluator-governance-posture-runtime-proof-001.json")
AWARENESS_AGGREGATE_REL = Path("receipts/sovereign-host/astra-class-resilience-awareness.latest.json")
AWARENESS_STATE_DIR = Path("runtime-state/entity-awareness")
AWARENESS_PROTECTED = {
    "stegverse001_bounded_autonomy",
    "sv002_org_runtime_activation",
    "sv011_phase5_source_materialization",
    "sv011_phase5",
}
AWARENESS_STATE_FILES = ("stegverse-001.json", "stegverse-002.json", "sv-011.json")
QUANTUM_AWARENESS_AGGREGATE_REL = Path("receipts/sovereign-host/quantum-resilience-awareness.latest.json")
QUANTUM_AWARENESS_STATE_DIR = Path("runtime-state/entity-quantum-awareness")
QUANTUM_AWARENESS_PROTECTED = set(AWARENESS_PROTECTED)
QUANTUM_AWARENESS_STATE_FILES = AWARENESS_STATE_FILES
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT",
    "STEGVERSE_STEGOPS_ORCHESTRATOR_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "STEGVERSE_MASTER_RECORDS_ENDPOINT",
    "STEGVERSE_MASTER_RECORDS_TOKEN", "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
    "MASTER_RECORDS_DB", "MASTER_RECORDS_RECEIPT_KEY", "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
    "STEGVERSE_ORG_FEDERATION_GATEWAY_URL", "STEGVERSE_ORG_FEDERATION_ROOT",
    "STEGVERSE_HIL_STATE_ROOT", "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_VAULT_AGENT_SOCKET", "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET",
    "STEGVERSE_ARA_MAIL_RECIPIENT", "STEGVERSE_ARA_MAIL_SENDER", "STEGVERSE_SV_DN1_SOURCE_ROOT",
    "STEGVERSE_SOURCE_MATERIALIZATION_ROOT", "STEGVERSE_SOURCE_PACKAGE_ROOT",
    "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT", "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT",
    "STEGVERSE_SV_DN1_INTR_STATE_ROOT", "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT", "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_INTR_ROUTE_CONFIG", "STEGVERSE_STEGOS_ROOT", "STEGVERSE_NODE_GENESIS_RECEIPT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_KV_ROOT",
    "STEGVERSE_SITE_ROOT", "STEGVERSE_STEGINDEX_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_HEALER_ROOT",
    "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_EVALUATOR_INTR_PORT",
    "STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
    "STEGVERSE_SV002_OBSERVE_PORT", "STEGVERSE_RELAY_RUNTIME_BASE", "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT", "STEGVERSE_GTG_ROOT", "STEGVERSE_AE_ROOT",
    "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT", "STEGVERSE_SELF_CHAR_MODEL_ID",
    "STEGVERSE_OLLAMA_MODEL", "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT",
    "STEGVERSE_RESIDENT_SOURCE_MANIFEST", "STEGVERSE_MASTER_RECORDS_ROOT",
    "STEGVERSE_ORG_CONTROL_ROOT", "STEGVERSE_SV002_ORG_ROOT",
    "STEGVERSE_SV001_AUTONOMY_LEASE",
    "STEGVERSE_SV011_ORG_ROOT",
    "STEGVERSE_SV011_MATERIALIZED_ROOT",
    "STEGVERSE_GLM53_ENDPOINT", "STEGVERSE_GLM53_MODEL_PATH", "STEGVERSE_GLM53_RUNTIME_IDENTITY",
    "STEGVERSE_GLM53_ENERGY_KWH", "STEGVERSE_GLM53_HARDWARE_AMORTIZATION_USD",
    "STEGVERSE_GLM53_ENERGY_COST_USD", "STEGVERSE_GLM53_STORAGE_NETWORK_RUNTIME_OVERHEAD_USD",
    "STEGVERSE_RELAY_EGRESS_BINDING", "STEGVERSE_RELAY_EGRESS_AUTHORIZATION", "STEGVERSE_RELAY_EGRESS_PAYLOAD",
    "STEGVERSE_GOOGLE_DRIVE_CLIENT_ID", "STEGVERSE_OWNER_BINDING_DIGEST", "STEGVERSE_STEGFIN_SOURCE_ROOT",
    "STEGVERSE_WARRANT_JSON", "TV_POLICY_BUNDLE_SHA256", "TV_WARRANT_ISSUER_PUBKEY_B64", "TV_WARRANT_MAX_TTL_SECONDS",
)
CONSUMERS = (
    ("ecosystem_chat", "scripts/consume_resident_execution_request.py"),
    ("kv_ai_memory", "scripts/consume_kv_ai_memory_resident_request.py"),
    ("g18", "scripts/consume_g18_resident_execution_request.py"),
    ("hil", "scripts/consume_hil_resident_execution_request.py"),
    ("evaluator_intr", "scripts/consume_evaluator_intr_resident_execution_request.py"),
    ("sdk_evaluator_governance_posture", "scripts/consume_sdk_evaluator_governance_posture_request.py"),
    ("sv002_public_observation", "scripts/consume_sv002_public_observation_request.py"),
    ("ara_graph", "scripts/consume_ara_graph_resident_execution_request.py"),
    ("cmc028_root_custody", "scripts/consume_cmc028_resident_execution_request.py"),
    ("sv_dn1", "scripts/consume_sv_dn1_resident_execution_request.py"),
    ("sv_dn1_publication", "scripts/consume_sv_dn1_publication_resident_request.py"),
    ("stegos_kv_intr_chain", "scripts/consume_stegos_kv_intr_chain_request.py"),
    ("kv_bound_ephemeral_evidence_reconcile", "control/resident-execution-request.d/consume-kv-evidence-reconcile.py"),
    ("gadi_runtime_observation", "workers/gadi_runtime_observation_request_consumer.py"),
    ("stegos_sovereign_relay_return_path", "workers/stegos_sovereign_relay_return_path_request_consumer.py"),
    ("bootstrap_v1_release_prep", "scripts/consume_bootstrap_v1_release_prep_request.py"),
    ("bootstrap_v1_intr_bundle_delivery", "scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py"),
    ("tvc_broker_validation", "scripts/consume_tvc_broker_validation_request.py"),
    ("mir_tvc_provider_roundtrip", "workers/mir_tvc_provider_roundtrip_request_consumer.py"),
    ("stegbrowser_tvc_source_promotion", "control/resident-execution-request.d/consume-stegbrowser-tvc-source-promotion.py"),
    ("stegbrowser_runtime_connection_ingress", "scripts/consume_stegbrowser_runtime_connection_ingress_request.py"),
    ("sv002_self_characterization", "scripts/consume_sv002_self_characterization_request.py"),
    ("astra_class_resilience_awareness", "scripts/consume_astra_class_resilience_awareness_request.py"),
    ("quantum_resilience_awareness", "scripts/consume_quantum_resilience_awareness_request.py"),
    ("sv002_org_runtime_activation", "scripts/consume_sv002_org_runtime_activation_request.py"),
    ("healer_sovereign_scheduler", "scripts/consume_healer_sovereign_scheduler_request.py"),
    ("universal_governance_enforced_reference", "scripts/consume_universal_governance_enforced_reference_request.py"),
    ("cross_framework_current_basis_v04", "scripts/consume_cross_framework_current_basis_v04_request.py"),
    ("stegverse001_bounded_autonomy", "scripts/consume_stegverse001_bounded_autonomy_request.py"),
    ("one_shot_resident_stack_activation", "scripts/consume_one_shot_resident_stack_activation_request.py"),
    ("sv011_phase5_source_materialization", "scripts/consume_sv011_phase5_source_materialization_request.py"),
    ("sv011_phase5", "scripts/consume_sv011_phase5_resident_execution_request.py"),
    ("glm53_sovereign_lane", "scripts/consume_glm53_sovereign_lane_request.py"),
    ("stegagents_governed_runtime_targeted", "scripts/consume_stegagents_governed_runtime_targeted_request.py"),
    ("sdk_tt_richard_seam_authentic_runtime", "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py"),
    ("ecosystem_receipt_hb_checkpoint", "scripts/consume_ecosystem_receipt_hb_checkpoint.py"),
    ("deepseek_intr_runtime", "control/resident-execution-request.d/consume-deepseek-intr-runtime.py"),
    ("ungoverned_ai_defensive_envelope", "scripts/consume_ungoverned_ai_defensive_envelope_request.py"),
    ("erl_ai_economic_transparency_review", "scripts/consume_erl_ai_economic_transparency_review_request.py"),
    ("org_claim_allocator", "scripts/consume_org_claim_allocator_request.py"),
    ("native_email_action_monitor", "scripts/consume_native_email_action_monitor_request.py"),
    ("governed_multilane_manifold_activation", "control/resident-execution-request.d/consume-governed-multilane-manifold-activation.py"),
    ("canonical_work_coordination", "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py"),
    ("runtime_profile_map", "control/resident-execution-request.d/consume-runtime-profile-map-build.py"),
    ("runtime_profile_map_custody", "control/resident-execution-request.d/consume-runtime-profile-map-custody.py"),
    ("runtime_profile_map_reconciliation", "control/resident-execution-request.d/consume-runtime-profile-map-reconciliation.py"),
    ("runtime_profile_map_transition_readiness", "control/resident-execution-request.d/consume-runtime-profile-map-transition-readiness.py"),
    ("runtime_profile_map_governance_review", "control/resident-execution-request.d/consume-runtime-profile-map-governance-review.py"),
    ("cosv_task_pointer_runtime_enforcement", "scripts/consume_cosv_task_pointer_runtime_enforcement_request.py"),
    ("ibc_verified_intr_ack", "scripts/consume_ibc_intr_resident_request.py"),
    ("sdk_workspace_external_collab_client_secret_reseal", "control/resident-execution-request.d/consume-sdk-workspace-external-collab-client-secret-reseal.py"),
    ("sdk_workspace_external_collab_consent_listener", "control/resident-execution-request.d/consume-sdk-workspace-external-collab-consent-listener.py"),
    ("stegsocials_bounded_intr_admission", "scripts/consume_stegsocials_bounded_intr_admission_request.py"),
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not dispatch sovereign resident requests: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def standing_awareness_ready(runtime: Path) -> bool:
    aggregate = load_json(runtime / AWARENESS_AGGREGATE_REL)
    if not aggregate:
        return False
    if aggregate.get("state") != "COMPLETED" or aggregate.get("runtime_awareness_materialized") is not True or aggregate.get("standing_directive_active") is not True or aggregate.get("entity_count") != 3:
        return False
    contract_sha = aggregate.get("contract_sha256")
    if not isinstance(contract_sha, str) or not contract_sha:
        return False
    for filename in AWARENESS_STATE_FILES:
        state = load_json(runtime / AWARENESS_STATE_DIR / filename)
        if not state or state.get("state") != "ACTIVE" or state.get("standing_directive_active") is not True:
            return False
        if state.get("contract_sha256") != contract_sha or state.get("credential_authority") != "TV/TVC":
            return False
        if state.get("capability_confers_authority") is not False or state.get("heartbeat_grants_execution_authority") is not False:
            return False
        if state.get("intr_interlock_remains_transition_boundary") is not True or state.get("second_machine_required") is not False:
            return False
    return True


def quantum_awareness_ready(runtime: Path) -> bool:
    aggregate = load_json(runtime / QUANTUM_AWARENESS_AGGREGATE_REL)
    if not aggregate or aggregate.get("state") != "COMPLETED" or aggregate.get("runtime_awareness_materialized") is not True or aggregate.get("standing_directive_active") is not True or aggregate.get("entity_count") != 3:
        return False
    contract_sha, census_sha = aggregate.get("contract_sha256"), aggregate.get("census_sha256")
    if not isinstance(contract_sha, str) or not contract_sha or not isinstance(census_sha, str) or not census_sha:
        return False
    for filename in QUANTUM_AWARENESS_STATE_FILES:
        state = load_json(runtime / QUANTUM_AWARENESS_STATE_DIR / filename)
        if not state or state.get("state") != "ACTIVE" or state.get("standing_directive_active") is not True:
            return False
        if state.get("contract_sha256") != contract_sha or state.get("census_sha256") != census_sha:
            return False
        if state.get("credential_authority") != "TV/TVC" or state.get("quantum_capability_confers_authority") is not False:
            return False
        if state.get("pqc_validity_confers_transition_authority") is not False or state.get("heartbeat_grants_execution_authority") is not False:
            return False
        if state.get("intr_interlock_remains_transition_boundary") is not True or state.get("second_machine_required") is not False:
            return False
    return True


def select_consumers(only_consumers: tuple[str, ...] | None) -> tuple[tuple[str, str], ...]:
    if not only_consumers:
        return CONSUMERS
    by_name = {name: rel for name, rel in CONSUMERS}
    unknown = sorted(set(only_consumers) - set(by_name))
    if unknown:
        raise RuntimeError("unknown resident consumer selector(s): " + ",".join(unknown))
    requested = set(only_consumers)
    return tuple((name, rel) for name, rel in CONSUMERS if name in requested)


def retain_sdk_evaluator_dispatch_visit_in_master_records(source: Path, runtime: Path, outcomes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Retain the existing SDK evaluator selector visit through canonical Master Records custody."""
    row = next((item for item in outcomes if item.get("consumer") == SDK_EVALUATOR_SELECTOR), None)
    if not isinstance(row, dict) or row.get("attempted") is not True:
        return None
    request = load_json(runtime / SDK_EVALUATOR_REQUEST_REL)
    if not request:
        return {"state": "BOUNDARY", "reason": "SDK_EVALUATOR_DISPATCH_REQUEST_IDENTITY_UNAVAILABLE", "authority_effect": "NONE"}
    task_id = request.get("task_id")
    request_id = request.get("request_id")
    if not isinstance(task_id, str) or not task_id or not isinstance(request_id, str) or not request_id:
        return {"state": "BOUNDARY", "reason": "SDK_EVALUATOR_DISPATCH_REQUEST_IDENTITY_INVALID", "authority_effect": "NONE"}
    workers_root = source / "workers"
    if str(workers_root) not in sys.path:
        sys.path.insert(0, str(workers_root))
    from canonical_state_transition_custody import build_state_receipt, sha256_uri, submit_state_receipt
    machine_result = row.get("result")
    evidence_content = {
        "selector": SDK_EVALUATOR_SELECTOR,
        "consumer_ref": row.get("consumer_ref"),
        "attempted": True,
        "state": row.get("state"),
        "returncode": row.get("returncode"),
        "task_id": task_id,
        "request_id": request_id,
        "machine_result_sha256": sha256_uri(machine_result),
        "machine_result": machine_result,
    }
    transition_id = f"{task_id}:RESIDENT_REQUEST_DISPATCH_VISIT:{request_id}"
    required_evidence = [{
        "evidence_id": f"{transition_id}:selector-visit",
        "evidence_type": "RESIDENT_REQUEST_DISPATCH_SELECTOR_VISIT",
        "origin_transition_id": transition_id,
        "encoding": "canonical-json",
        "sha256": sha256_uri(evidence_content).split(":", 1)[1],
        "content": evidence_content,
    }]
    state_receipt = build_state_receipt(
        transition_id=transition_id,
        transition_sequence=1,
        subject_or_correlation_id=task_id,
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=None,
        resulting_state_ref_or_hash=sha256_uri(evidence_content),
        governance_decision_ref_where_applicable=None,
        transition_evidence={
            "transition": "RESIDENT_REQUEST_DISPATCH_VISIT",
            "selector": SDK_EVALUATOR_SELECTOR,
            "consumer_ref": row.get("consumer_ref"),
            "attempted": True,
            "task_id": task_id,
            "request_id": request_id,
            "machine_result_sha256": sha256_uri(machine_result),
            "dispatch_grants_authority": False,
        },
        required_evidence_manifest=required_evidence,
        proof_scope="SDK_EVALUATOR_GOVERNANCE_POSTURE_DISPATCH_VISIT_ONLY",
        proof_ceiling="MASTER_RECORDS_VALIDATED_DISPATCH_VISIT_EVIDENCE_ONLY",
    )
    result = submit_state_receipt(state_receipt)
    return {
        "transition_id": transition_id,
        "selector": SDK_EVALUATOR_SELECTOR,
        "task_id": task_id,
        "request_id": request_id,
        "attempted": True,
        "machine_result_sha256": sha256_uri(machine_result),
        "state": result.get("state"),
        "reconstruction_status": result.get("reconstruction_status"),
        "required_evidence_validation_status": result.get("required_evidence_validation_status"),
        "receipt_sha256": result.get("receipt_sha256"),
        "reconstructed_receipt_sha256": result.get("reconstructed_receipt_sha256"),
        "reason": result.get("reason"),
        "authority_effect": result.get("authority_effect", "NONE"),
    }


def dispatch(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
    only_consumers: tuple[str, ...] | None = None,
    goal_task_id: str | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    safe_env = clean_exec_env(env)
    selected = select_consumers(only_consumers)
    current_goal_task_id = None
    if goal_task_id is not None:
        current_goal_task_id = str(goal_task_id).strip()
        if not current_goal_task_id:
            raise RuntimeError("goal task id must be non-empty")
        selected_names = tuple(name for name, _ in selected)
        if selected_names != ("canonical_work_coordination",):
            raise RuntimeError("goal task context requires exact canonical_work_coordination selector")
    outcomes: list[dict[str, Any]] = []

    for name, rel in selected:
        if name in AWARENESS_PROTECTED and not standing_awareness_ready(runtime):
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": "STANDING_AWARENESS_REQUIRED", "returncode": None, "result": None, "attempted": False, "authority_effect": "NONE_FAIL_CLOSED"})
            continue
        if name in QUANTUM_AWARENESS_PROTECTED and not quantum_awareness_ready(runtime):
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": "QUANTUM_STANDING_AWARENESS_REQUIRED", "returncode": None, "result": None, "attempted": False, "authority_effect": "NONE_FAIL_CLOSED"})
            continue
        consumer = runtime / rel
        if not consumer.is_file():
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": "CONSUMER_NOT_MATERIALIZED", "returncode": None, "result": None, "attempted": False})
            continue
        command = [sys.executable, str(consumer), "--source-root", str(source), "--runtime-root", str(runtime)]
        if name == "canonical_work_coordination" and current_goal_task_id:
            command.extend(["--goal-task-id", current_goal_task_id])
        try:
            completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=safe_env, timeout=1200)
            result = parse_last_json(completed.stdout)
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": result.get("state") if isinstance(result, dict) else "NO_MACHINE_RESULT", "returncode": completed.returncode, "result": result, "attempted": True})
        except Exception as exc:
            outcomes.append({"consumer": name, "consumer_ref": rel, "state": "DISPATCH_EXCEPTION", "returncode": None, "result": None, "attempted": True, "error_type": type(exc).__name__})

    missing = [row["consumer"] for row in outcomes if row["state"] == "CONSUMER_NOT_MATERIALIZED"]
    exceptions = [row["consumer"] for row in outcomes if row["state"] == "DISPATCH_EXCEPTION"]
    accepted_wait_states = {
        "NO_REQUEST", "ALREADY_CONSUMED", "ALREADY_TERMINAL", "WAITING_FOR_CUSTODY_PACKAGE", "WAITING_FOR_MASTER_RECORDS_CUSTODY", "WAITING_FOR_RECONCILIATION", "WAITING_FOR_TRANSITION_READINESS",
        "MASTER_RECORDS_LOCAL_ROOT_NOT_MATERIALIZED", "MASTER_RECORDS_CUSTODY_CONSUMER_NOT_MATERIALIZED", "MASTER_RECORDS_PROJECTOR_NOT_MATERIALIZED", "ATTEMPT_RECORDED", "COMPLETED", "CYCLE_COMPLETED", "MANIFOLD_VISIT_RECORDED",
        "SOVEREIGN_NODE_MARKER_REQUIRED", "RESIDENT_INTR_ACK_CONSUMED", "RETURN_PATH_VERIFIED", "SERVICE_ALREADY_HEALTHY", "INPUT_NOT_MATERIALIZED", "OBSERVATION_ATTEMPT_RECORDED",
        "WAITING_FOR_MASTER_RECORDS_HB_SUCCESSOR", "AUTHENTIC_FIRST_SUCCESSOR_CHECKPOINT_COMMITTED",
        "WAITING_FOR_ESTABLISHED_NODE_CONNECTIVITY", "REUSE_ACCEPTED", "DELTA_REQUIRED", "BOUND_STATE_INPUT_NOT_READY",
        "A1_A2_A3_A4_OBSERVED", "A1_A2_OBSERVED_A3_A4_PENDING", "A1_OBSERVED_NOT_MATERIALIZED",
        "A1_A2_A2_1_A2_2_A3_A4_OBSERVED", "A1_OBSERVED_CANONICAL_INVOCATION_PENDING_OR_BOUNDARY",
        "A1_NOT_OBSERVED_REGISTERED_NODE_RECEIPT_UNAVAILABLE", "A1_NOT_OBSERVED_CANONICAL_INVOCATION_NOT_RETAINED", "A1_NOT_OBSERVED_NOT_CALLABLE",
    }
    request_failures = [row["consumer"] for row in outcomes if row["state"] not in accepted_wait_states]
    exact_selector_failure = only_consumers is not None and bool(request_failures)
    sdk_evaluator_dispatch_master_records = retain_sdk_evaluator_dispatch_visit_in_master_records(source, runtime, outcomes)
    receipt = {
        "schema": "stegverse.resident-request-dispatch/v1", "state": "DISPATCH_COMPLETE" if not missing and not exceptions and not exact_selector_failure else "DISPATCH_INCOMPLETE",
        "source_root": str(source), "runtime_root": str(runtime), "registered_consumer_count": len(CONSUMERS), "consumer_count": len(selected),
        "selected_consumers": [name for name, _ in selected], "selection_scope": "ALL_REGISTERED" if only_consumers is None else "EXACT_SELECTOR",
        "current_goal_task_id": current_goal_task_id,
        "goal_context_forwarded_to": "canonical_work_coordination" if current_goal_task_id else None,
        "consumers_visited": len(outcomes), "missing_consumers": missing, "dispatch_exceptions": exceptions, "request_failures": request_failures,
        "exact_selector_failure": exact_selector_failure,
        "sdk_evaluator_dispatch_master_records": sdk_evaluator_dispatch_master_records,
        "outcomes": outcomes, "request_failure_blocks_later_requests": False, "astra_class_standing_awareness_ready": standing_awareness_ready(runtime),
        "quantum_resilience_standing_awareness_ready": quantum_awareness_ready(runtime),
        "network_source_fetch_performed": False, "credential_authority": "TV/TVC", "github_token_required": False, "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False, "request_dispatch_grants_authority": False, "second_machine_required": False, "authority_effect": "NONE_DISPATCH_ONLY",
    }
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch bounded resident execution requests.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--only-consumer", action="append", default=None)
    parser.add_argument("--goal-task-id")
    args = parser.parse_args()
    receipt = dispatch(
        args.source_root,
        args.runtime_root,
        only_consumers=tuple(args.only_consumer) if args.only_consumer else None,
        goal_task_id=args.goal_task_id,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "DISPATCH_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
