#!/usr/bin/env python3
"""Typed first-failure responses for the persistent-node / ephemeral-execution loop.

Observational only: this classifier grants no execution, claim/fence, InTr,
credential, custody, publication, or completion authority.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

STAGES: tuple[dict[str, Any], ...] = (
    {"index":1,"stage":"RUNTIME_PROFILE_RESOLUTION","code":"RUNTIME_STAGE_01_PROFILE_RESOLUTION_FAILED","next":"resolve the exact runtime/node profile for this task"},
    {"index":2,"stage":"PERSISTENT_NODE_CONTINUITY","code":"RUNTIME_STAGE_02_NODE_CONTINUITY_UNOBSERVED","next":"materialize or reload the profile-derived StegOS node and verify retained identity/HB lineage"},
    {"index":3,"stage":"EPHEMERAL_REQUEST_CONSUMPTION","code":"RUNTIME_STAGE_03_REQUEST_NOT_CONSUMED","next":"bind and consume the exact task/request/COSV against the retained node"},
    {"index":4,"stage":"WORKERCOORDINATOR_CLAIM_FENCE","code":"RUNTIME_STAGE_04_CLAIM_FENCE_NOT_OBSERVED","next":"obtain the exact fresh WorkerCoordinator claim/fence for this task"},
    {"index":5,"stage":"EPHEMERAL_INTERLOCK_INTR_ADMISSION","code":"RUNTIME_STAGE_05_INTR_ADMISSION_NOT_OBSERVED","next":"execute the bounded Interlock/InTr admission for this exact transition"},
    {"index":6,"stage":"EPHEMERAL_TRANSPORT_PROVIDER_LEASE","code":"RUNTIME_STAGE_06_TRANSPORT_PROVIDER_LEASE_NOT_BOUND","next":"bind the bounded transport/provider/lease required by this operation"},
    {"index":7,"stage":"COMPONENT_EXECUTION","code":"RUNTIME_STAGE_07_COMPONENT_EXECUTION_FAILED","next":"execute or re-execute the exact component operation on the admitted node"},
    {"index":8,"stage":"EXACT_RECEIPT_COMMITMENT","code":"RUNTIME_STAGE_08_RECEIPT_COMMITMENT_FAILED","next":"commit the exact execution/result receipt into retained node evidence lineage"},
    {"index":9,"stage":"MASTER_RECORDS_RECONSTRUCTION","code":"RUNTIME_STAGE_09_MASTER_RECORDS_RECONSTRUCTION_FAILED","next":"perform exact same-execution Master Records custody/reconstruction"},
    {"index":10,"stage":"DOWNSTREAM_PROPAGATION","code":"RUNTIME_STAGE_10_PROPAGATION_NOT_VERIFIED","next":"verify required downstream propagation from the reconstructed receipt"},
)
BY_STAGE = {row["stage"]: row for row in STAGES}
BY_INDEX = {row["index"]: row for row in STAGES}

RESUME_STAGE_ALIASES = {
    "AUTHENTIC_REQUEST_CONSUMPTION":3,
    "SUBJECT_BOUND_RESIDENT_REQUEST_EXECUTION":3,
    "AUTHENTIC_MATERIALIZATION_CONSUMPTION":3,
    "RESIDENT_PROCESS_AND_REQUEST_CONSUMPTION":3,
    "CANONICALWORK_INGRESS_ADMITTED":3,
    "WORKERCOORDINATOR_CLAIM_FENCE":4,
    "PER_CHILD_CLAIM_FENCE_AND_FORMALISM_EXECUTION":4,
    "CURRENT_DEVICE_CONTINUATION":5,
    "ESRL_LEASE_OPEN":6,
    "PROVIDER_RUNTIME_CONSUMPTION":6,
    "SDK_FIRST_ROUND_RESIDENT_ANALYSIS":7,
    "EXACT_PARENT_SDK_EXECUTION":7,
    "CANONICAL_ADAPTER_EXECUTION":7,
    "AUTHENTIC_DEVICE_KV_PARENT":7,
    "SUBJECT_BOUND_GLM_EXECUTION":7,
    "SUBJECT_BOUND_PHASE5_EXECUTION":7,
    "AUTHENTIC_BROWSER_INVOCATION":7,
    "EXACT_PARENT_REBINDING_REEXECUTION":7,
}
PASS_STATES = {"PASS","PASSED","SATISFIED","COMPLETED","ALREADY_CONSUMED","OBSERVED","ADMITTED","BOUND","EXECUTED","RECONSTRUCTED","VERIFIED"}
FAIL_STATES = {"FAIL","FAILED","ERROR","UNOBSERVED","MISSING","DENIED","REFUSED","UNAVAILABLE"}
NONFAIL_FLOW_STATES = {"NOT_REACHED","NOT_APPLICABLE","NOT_REQUIRED","SKIPPED_AFTER_EARLIER_FAILURE"}
# Readiness/liveness are intentionally not terminal completion.
TERMINAL_SUCCESS_STATES = {"COMPLETED","ALREADY_CONSUMED"}


def _normalized_state(value: Any) -> str:
    return str(value or "UNKNOWN").strip().upper()


def _observation_failed(value: Any) -> bool:
    state = _normalized_state(value)
    if state in PASS_STATES or state in NONFAIL_FLOW_STATES:
        return False
    if state in FAIL_STATES:
        return True
    return any(token in state for token in ("FAIL","ERROR","MISSING","UNOBSERVED","DENIED","REFUSED","UNAVAILABLE","PENDING"))


def _stage_from_resume(resume_stage: Any) -> int:
    value = str(resume_stage or "").strip().upper()
    if value in RESUME_STAGE_ALIASES:
        return RESUME_STAGE_ALIASES[value]
    if "CLAIM" in value or "FENCE" in value: return 4
    if "INTR" in value or "INTERLOCK" in value: return 5
    if "LEASE" in value or "PROVIDER" in value or "TRANSPORT" in value: return 6
    if "RECONSTRUCTION" in value or "MASTER_RECORD" in value: return 9
    if "PROPAGATION" in value or "PUBLICATION" in value: return 10
    if "RECEIPT" in value or "CUSTODY" in value: return 8
    if "EXECUTION" in value or "ANALYSIS" in value or "INVOCATION" in value or "REEXECUTION" in value: return 7
    if "REQUEST" in value or "CONSUMPTION" in value or "INGRESS" in value: return 3
    return 1


def failure_response(*, task_id: str, lane: str, stage_index: int, raw_state: Any, reason: str | None = None, evidence_ref: str | None = None) -> dict[str, Any]:
    stage = BY_INDEX[stage_index]
    return {
        "schema":"stegverse.runtime-failure-response/v1",
        "task_id":task_id,
        "lane":lane,
        "failure_stage_index":stage_index,
        "failure_stage":stage["stage"],
        "failure_code":stage["code"],
        "raw_state":str(raw_state or "UNKNOWN"),
        "reason":reason or str(raw_state or "UNKNOWN"),
        "evidence_ref":evidence_ref,
        "retryable_after_predicate_change":True,
        "subject_bound":True,
        "next_action":stage["next"],
        "heartbeat_grants_authority":False,
        "authority_effect":"NONE_DIAGNOSTIC_ONLY",
    }


def annotate_lane_outcome(outcome: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(outcome)
    task_id = str(result.get("task_id") or "UNKNOWN_TASK")
    lane = str(result.get("lane") or task_id)
    raw_state = result.get("state")
    explicit = result.get("stage_observations")
    failure_index = None
    reason = None
    evidence_ref = None
    trace: list[dict[str, Any]] = []

    if isinstance(explicit, Mapping):
        # Explicit observations must be contiguous from stage 1 through the first
        # failure or through the highest stage claimed. A missing earlier predicate
        # is itself an unobserved boundary; later observations cannot skip over it.
        highest_reported = max((row["index"] for row in STAGES if row["stage"] in explicit), default=0)
        for stage in STAGES:
            present = stage["stage"] in explicit
            observation = explicit.get(stage["stage"])
            if not present and stage["index"] <= highest_reported:
                observed_state = "UNOBSERVED_REQUIRED_STAGE"
                observed_reason = "explicit stage observations are non-contiguous; earlier predicate not reported"
                observed_ref = None
                failed = True
            elif isinstance(observation, Mapping):
                observed_state = observation.get("state", "UNKNOWN")
                observed_reason = observation.get("reason")
                observed_ref = observation.get("evidence_ref")
                failed = _observation_failed(observed_state)
            else:
                observed_state = observation if present else "NOT_REPORTED"
                observed_reason = None
                observed_ref = None
                failed = _observation_failed(observed_state) if present else False
            trace.append({"stage_index":stage["index"],"stage":stage["stage"],"state":str(observed_state),"failed":failed})
            if failed and failure_index is None:
                failure_index = stage["index"]
                reason = str(observed_reason or observed_state)
                evidence_ref = str(observed_ref) if observed_ref else None
    else:
        resume_index = _stage_from_resume(result.get("resume_stage"))
        success = _normalized_state(raw_state) in TERMINAL_SUCCESS_STATES
        for stage in STAGES:
            if success:
                state, failed = "PASSED_OR_NOT_REQUIRED_BY_EXISTING_EVIDENCE", False
            elif stage["index"] < resume_index:
                state, failed = "PASSED_BY_EXISTING_EVIDENCE", False
            elif stage["index"] == resume_index:
                state, failed = "FIRST_UNRESOLVED:" + str(raw_state or result.get("resume_stage") or "UNKNOWN"), True
                failure_index = resume_index
                reason = str(result.get("reason") or raw_state or result.get("resume_stage") or "UNKNOWN")
            else:
                state, failed = "NOT_REACHED", False
            trace.append({"stage_index":stage["index"],"stage":stage["stage"],"state":state,"failed":failed})

    result["boundary_trace"] = trace
    if failure_index is None:
        result["first_failure"] = None
        result["first_failure_stage_index"] = None
        result["first_failure_code"] = None
    else:
        response = failure_response(task_id=task_id,lane=lane,stage_index=failure_index,raw_state=raw_state,reason=reason,evidence_ref=evidence_ref)
        result["first_failure"] = response
        result["first_failure_stage_index"] = failure_index
        result["first_failure_code"] = response["failure_code"]
    return result


def summarize_failure_boundaries(outcomes: list[Mapping[str, Any]]) -> dict[str, Any]:
    stage_counts, code_counts = Counter(), Counter()
    for row in outcomes:
        failure = row.get("first_failure") if isinstance(row, Mapping) else None
        if not isinstance(failure, Mapping):
            continue
        stage_counts[f"{failure.get('failure_stage_index')}:{failure.get('failure_stage')}"] += 1
        code_counts[str(failure.get("failure_code"))] += 1
    return {
        "schema":"stegverse.runtime-failure-boundary-summary/v1",
        "failed_lane_count":sum(stage_counts.values()),
        "failure_stage_counts":dict(sorted(stage_counts.items())),
        "failure_code_counts":dict(sorted(code_counts.items())),
        "heartbeat_grants_authority":False,
        "authority_effect":"NONE_DIAGNOSTIC_ONLY",
    }
