from __future__ import annotations


def evaluate(payload):
    event = payload.get("indexed_event") or {}
    requirements = payload.get("current_requirements") or {}
    node = payload.get("node_context") or {}
    if node.get("connectivity_state") != "ESTABLISHED":
        return {"state": "WAITING_FOR_ESTABLISHED_NODE_CONNECTIVITY", "authority_effect": "NONE_VALIDATION_ONLY"}
    failures = []
    if event.get("replay_state") != "PASS":
        failures.append("INDEXED_EVENT_REPLAY_NOT_PASS")
    if event.get("reconstruction_state") != "PASS":
        failures.append("INDEXED_EVENT_RECONSTRUCTION_NOT_PASS")
    required = set(requirements.get("required_predicates", []))
    observed = set(event.get("observed_predicates", []))
    missing = sorted(required - observed)
    state = "FAIL_CLOSED" if failures else ("DELTA_REQUIRED" if missing else "REUSE_ACCEPTED")
    return {
        "state": state,
        "missing_delta": missing,
        "failures": failures,
        "reused_event": state == "REUSE_ACCEPTED",
        "user_interaction_required": False,
        "authority_effect": "NONE_VALIDATION_ONLY",
    }
