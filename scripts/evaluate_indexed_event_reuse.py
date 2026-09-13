from __future__ import annotations


def _set(value):
    return {str(item) for item in (value or []) if str(item)}


def evaluate(payload):
    requirements = payload.get("current_requirements") or {}
    node = payload.get("node_context") or {}
    ecosystem = payload.get("ecosystem_state") or {}
    current = payload.get("current_observations") or {}
    if node.get("connectivity_state") != "ESTABLISHED":
        return {"state": "WAITING_FOR_ESTABLISHED_NODE_CONNECTIVITY", "missing_delta": [], "failures": [], "reused_event": False, "user_interaction_required": False, "authority_effect": "NONE_VALIDATION_ONLY"}

    failures = []
    for req_key, eco_key, code in (
        ("task_id", "task_id", "CURRENT_ECOSYSTEM_TASK_ID_MISMATCH"),
        ("required_coordination_state", "coordination_state", "CURRENT_ECOSYSTEM_COORDINATION_STATE_MISMATCH"),
        ("required_worker_claim_ref", "worker_claim_ref", "CURRENT_ECOSYSTEM_WORKER_CLAIM_MISMATCH"),
        ("required_fence_ref", "fence_ref", "CURRENT_ECOSYSTEM_FENCE_MISMATCH"),
    ):
        expected = str(requirements.get(req_key) or "")
        if expected and ecosystem.get(eco_key) != expected:
            failures.append(code)

    events = payload.get("indexed_events")
    if not isinstance(events, list):
        one = payload.get("indexed_event") or {}
        events = [one] if one else []

    historical_allowed = _set(requirements.get("historically_reusable_predicates"))
    current_only = _set(requirements.get("must_be_current_for_this_execution"))
    invalidated_predicates = _set(ecosystem.get("invalidated_predicates"))
    invalidated_refs = _set(ecosystem.get("invalidated_event_refs"))
    accepted_classes = _set(requirements.get("accepted_evidence_classes"))
    accepted_modes = _set(requirements.get("accepted_verification_modes") or ["REPLAY", "RECONSTRUCTION"])
    historical_covered = set()
    accepted_events = []
    rejected_events = []

    for event in events:
        if not isinstance(event, dict):
            continue
        event_failures = []
        ref = str(event.get("event_ref") or "UNNAMED_EVENT")
        if ref in invalidated_refs:
            event_failures.append("EVENT_INVALIDATED_BY_CURRENT_ECOSYSTEM_STATE")
        evidence_class = str(event.get("evidence_class") or "")
        if accepted_classes and evidence_class not in accepted_classes:
            event_failures.append("EVIDENCE_CLASS_NOT_ACCEPTED")
        modes = event.get("verification_modes") or {}
        passed_modes = sorted(mode for mode in accepted_modes if modes.get(mode) == "PASS")
        if not passed_modes:
            event_failures.append("NO_ACCEPTED_REPLAY_OR_RECONSTRUCTION_PASS")
        if requirements.get("require_exact_node_route_match") is True:
            current_node = str(node.get("node_id") or "")
            event_node = str(event.get("node_id") or "")
            if not current_node or not event_node:
                event_failures.append("EXACT_NODE_ROUTE_IDENTITY_MISSING")
            elif current_node != event_node:
                event_failures.append("EXACT_NODE_ROUTE_MISMATCH")
        if requirements.get("require_device_continuity_match_when_observed") is True:
            current_device = str(node.get("device_continuity_id") or "")
            event_device = str(event.get("device_continuity_id") or "")
            if current_device and event_device and current_device != event_device:
                event_failures.append("DEVICE_CONTINUITY_MISMATCH")
        if event_failures:
            rejected_events.append({"event_ref": ref, "failures": event_failures})
            continue
        reusable = (_set(event.get("observed_predicates")) & historical_allowed) - invalidated_predicates
        historical_covered.update(reusable)
        accepted_events.append({"event_ref": ref, "verification_modes_passed": passed_modes, "covered_predicates": sorted(reusable)})

    historical_covered.difference_update(current_only)
    current_covered = _set(current.get("observed_predicates")) - invalidated_predicates
    covered = historical_covered | current_covered
    missing = sorted(_set(requirements.get("required_predicates")) - covered)
    state = "FAIL_CLOSED" if failures else ("DELTA_REQUIRED" if missing else "REUSE_ACCEPTED")
    return {
        "state": state,
        "missing_delta": missing,
        "failures": failures,
        "covered_from_historical_evidence": sorted(historical_covered),
        "covered_from_current_observations": sorted(current_covered),
        "accepted_events": accepted_events,
        "rejected_events": rejected_events,
        "reused_event": bool(accepted_events),
        "user_interaction_required": False,
        "authority_effect": "NONE_VALIDATION_ONLY",
    }
