"""The disposition invariant applied to a canonical task record's own state."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_task_record_actionable_disposition import (  # noqa: E402
    validate_progression_predicates,
    validate_record,
)

RECORDS = ROOT / "data" / "canonical-task-records"


def actionable(code: str = "CUSTODY_SURFACE_UNAVAILABLE") -> dict:
    return {
        "disposition": "FAIL_CLOSED",
        "evidence_class": "SOURCE_VALIDATION",
        "consequence_committed": False,
        "failure_code": code,
        "failed_predicate": "AUTHORIZED_CUSTODY_CONFIGURATION_PRESENT_AT_INVOCATION",
        "required_evidence_or_repair": "INVOKE_WITH_THE_EXISTING_AUTHORIZED_CONFIGURATION",
        "retry_entrypoint": "module.py::entrypoint",
        "owning_existing_goal": "TEST-GOAL-001",
        "next_attempt": "NEXT_MANIFEST_DIRECTED_APPEND",
        "evidence_refs": ["SOURCE_RECORD_ONLY:data/canonical-task-records/TEST-001.json"],
    }


def test_bare_unobserved_finding_is_rejected():
    errors = validate_record(
        {"current_truth": {"runtime_custody": "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"}},
        "TEST-001",
    )
    assert len(errors) == 1
    assert "STOP_BARE_UNACTIONABLE_FINDING" in errors[0]
    assert "current_truth.runtime_custody" in errors[0]


def test_actionable_disposition_is_accepted():
    assert validate_record({"current_truth": {"runtime_custody": actionable()}}, "TEST-001") == []


def test_non_allow_missing_repair_fields_is_rejected():
    incomplete = actionable()
    del incomplete["retry_entrypoint"]
    errors = validate_record({"current_truth": {"runtime_custody": incomplete}}, "TEST-001")
    assert len(errors) == 1
    assert "NON_ALLOW_REPAIR_REQUIRED" in errors[0]
    assert "retry_entrypoint" in errors[0]


def test_non_allow_without_evidence_refs_is_rejected():
    for refs in (None, [], [""], "SOURCE_RECORD_ONLY:x"):
        incomplete = actionable()
        if refs is None:
            del incomplete["evidence_refs"]
        else:
            incomplete["evidence_refs"] = refs
        errors = validate_record({"current_truth": {"runtime_custody": incomplete}}, "TEST-001")
        assert len(errors) == 1
        assert "NON_ALLOW_REPAIR_REQUIRED" in errors[0]
        assert "evidence_refs" in errors[0]


def test_every_canonical_record_non_allow_carries_evidence_refs():
    for path in sorted(RECORDS.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        assert validate_record(record, record.get("task_id", path.stem)) == [], path


def test_runtime_observation_block_is_judged_by_content_not_name():
    """A binding reference is fine; a value that awaits is not."""
    assert validate_record(
        {"runtime_observation": {"existing_resident_selector": "some_selector",
                                 "intr_admission": actionable()}}, "TEST-001"
    ) == []
    errors = validate_record(
        {"runtime_observation": {"intr_admission": "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"}},
        "TEST-001",
    )
    assert len(errors) == 1
    assert "runtime_observation.intr_admission" in errors[0]


def test_goal_chart_state_is_covered():
    errors = validate_record(
        {"goal_chart": {"A2": {"state": "NOT_AUTHENTICALLY_OBSERVED"}}}, "TEST-001"
    )
    assert len(errors) == 1
    assert "goal_chart.A2.state" in errors[0]


def test_other_vocabularies_are_not_reached():
    """PENDING_EVIDENCE and a dependency PENDING are defined values elsewhere."""
    record = {
        "execution_substrate_resolution": {
            "reviews": [{"substrate_id": "X", "disposition": "PENDING_EVIDENCE"}]
        },
        "dependencies": [{"task_id": "OTHER-001", "state": "PENDING"}],
        "current_truth": {"registration": "MERGED"},
    }
    assert validate_record(record, "TEST-001") == []


def test_this_tasks_record_carries_no_bare_finding():
    record = json.loads(
        (RECORDS / "ORGANIZATION-BATCH-CUSTODY-REPLAY-001.json").read_text(encoding="utf-8")
    )
    assert validate_record(record, record["task_id"]) == []


def test_runtime_resolution_standing_status_is_flagged():
    """#3012 O2: runtime_resolution states standing status like current_truth."""
    errors = validate_record(
        {"runtime_resolution": {"current_observation_state": "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"}},
        "TEST-001",
    )
    assert len(errors) == 1
    assert "STOP_BARE_UNACTIONABLE_FINDING" in errors[0]
    assert "runtime_resolution.current_observation_state" in errors[0]


def test_bare_status_reason_is_flagged():
    errors = validate_record({"status_reason": "TASK_BOUND_EXECUTION_EVIDENCE_NOT_OBSERVED"}, "TEST-001")
    assert len(errors) == 1
    assert "status_reason=" in errors[0]


def test_token_inside_typed_fail_closed_record_is_not_flagged():
    typed = actionable("ORGANIZATION_RECEIPT_NOT_APPENDED")
    typed["replaces_passive_predicate"] = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
    assert validate_record(
        {"runtime_resolution": {"current_observation_state": typed}}, "TEST-001"
    ) == []


def test_typed_fail_closed_in_runtime_resolution_still_needs_repair_fields():
    incomplete = actionable()
    del incomplete["failed_predicate"]
    errors = validate_record(
        {"runtime_resolution": {"current_observation_state": incomplete}}, "TEST-001"
    )
    assert len(errors) == 1
    assert "NON_ALLOW_REPAIR_REQUIRED" in errors[0]
    assert "failed_predicate" in errors[0]


def test_historical_quotation_is_not_flagged():
    """A retained prior value, history list or dated snapshot quotes history."""
    record = {
        "runtime_resolution": {
            "current_observation_state": actionable(),
            "superseded_current_observation_state": {
                "value": "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED",
                "authority_effect": "NONE_HISTORY_ONLY",
            },
            "observation_history": ["UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"],
            "reconstruction_review_20260921": {"interpretation": "UNKNOWN_NOT_FALSE"},
        },
        "status_reason": "SOURCE_CORRELATION_REPAIR_COMPLETE",
    }
    assert validate_record(record, "TEST-001") == []


def test_historical_exclusion_does_not_hide_a_standing_sibling():
    errors = validate_record(
        {"runtime_resolution": {
            "superseded_unresolved_classification": {"value": "X_NOT_OBSERVED"},
            "unresolved_classification": "X_NOT_OBSERVED",
        }},
        "TEST-001",
    )
    assert len(errors) == 1
    assert "runtime_resolution.unresolved_classification=" in errors[0]


def test_yet_and_un_prefixed_suffix_spellings_are_flagged():
    """#3012 K1: the YET and UN-prefixed spellings carry the same passive meaning."""
    for value in (
        "KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED",
        "TERMINAL_RECEIPT_NOT_YET_AUTHENTICALLY_OBSERVED",
        "SHWP-SV002-ORG-RUNTIME-ACTIVATION-001_REQUESTED_TERMINAL_RECEIPT_UNOBSERVED",
        "DURABLE_RUNTIME_ENDPOINT_STILL_UNOBSERVED",
        "CUSTODY_CHAIN_NOT_YET_PROVEN",
        "CUSTODY_CHAIN_UNPROVEN",
    ):
        errors = validate_record({"runtime_resolution": {"current_evidence": value}}, "TEST-001")
        assert len(errors) == 1, value
        assert "STOP_BARE_UNACTIONABLE_FINDING" in errors[0]
        assert f"runtime_resolution.current_evidence={value}" in errors[0]


def test_widened_suffix_does_not_reach_affirmative_or_inner_tokens():
    """Only the suffix is matched: an affirmative state or an inner token is not."""
    for value in (
        "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:INTERLOCK_INTR_INGRESS",
        "ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED",
        "RECEIPT_UNOBSERVED_LABEL_RETAINED",
        "RUNTIME_OBSERVED",
        "PROVEN",
    ):
        assert validate_record({"runtime_resolution": {"state": value}}, "TEST-001") == [], value


def test_widened_suffix_keeps_historical_and_typed_exclusions():
    typed = actionable("ORGANIZATION_RECEIPT_NOT_APPENDED")
    typed["replaces_passive_predicate"] = "TERMINAL_RECEIPT_UNOBSERVED"
    record = {
        "runtime_resolution": {
            "current_evidence": typed,
            "superseded_current_evidence": {
                "value": "TERMINAL_RECEIPT_UNOBSERVED",
                "authority_effect": "NONE_HISTORY_ONLY",
            },
            "observation_history": ["READBACK_NOT_YET_OBSERVED"],
            "reconstruction_review_20261009": {"state": "CHAIN_NOT_YET_PROVEN"},
            "evidence_refs": ["LABEL_STILL_UNOBSERVED"],
        },
    }
    assert validate_record(record, "TEST-001") == []


def test_widened_suffix_does_not_hide_a_standing_sibling_beside_history():
    errors = validate_record(
        {"runtime_resolution": {
            "superseded_current_evidence": {"value": "TERMINAL_RECEIPT_UNOBSERVED"},
            "current_evidence": "TERMINAL_RECEIPT_UNOBSERVED",
        }},
        "TEST-001",
    )
    assert len(errors) == 1
    assert "runtime_resolution.current_evidence=" in errors[0]


def test_gadi_runtime_closure_carries_typed_append_disposition():
    """The record the widened rule flagged on main is repaired, prior value kept."""
    record = json.loads(
        (RECORDS / "GADI-RUNTIME-CLOSURE-001.json").read_text(encoding="utf-8")
    )
    assert validate_record(record, record["task_id"]) == []
    resolution = record["runtime_resolution"]
    current = resolution["canonical_carrier_current_evidence"]
    assert current["disposition"] == "FAIL_CLOSED"
    assert current["consequence_committed"] is False
    assert current["failure_code"] == "ORGANIZATION_RECEIPT_NOT_APPENDED"
    assert current["failed_predicate"] == (
        "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:SHWP_SV002_ORG_RUNTIME_ACTIVATION_TERMINAL_RECEIPT"
    )
    assert current["satisfying_edge"] and current["retry_entrypoint"]
    prior = resolution["superseded_canonical_carrier_current_evidence"]
    assert prior["value"] == (
        "SHWP-SV002-ORG-RUNTIME-ACTIVATION-001_REQUESTED_TERMINAL_RECEIPT_UNOBSERVED"
    )
    assert prior["authority_effect"] == "NONE_HISTORY_ONLY"
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "CLAIMED_INTEGRATION"
    assert record["cosv_task_vector"] == "10100000100000"


APPEND = "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK"


def test_affirmative_observer_in_progression_predicate_fields_is_flagged():
    """#3012: a progression gate naming an observer is a post-closure observer gate."""
    record = {
        "coordination_state": "ACTIVE",
        "runtime_resolution": {"first_unresolved_runtime_predicate": "CURRENT_GATEWAY_RUNTIME_OBSERVED"},
        "remaining_predicates": ["SOURCE_MERGED", "AUTHENTIC_LEASE_CLOSURE_OBSERVED"],
        "goal_specific_completion_predicates": ["REQUIRED_RECONSTRUCTION_OBSERVED"],
        "state_transition_graph": {"transitions": [
            {"from": "A", "to": "B_OBSERVED", "predicate": "NEUTRAL_INVOCATION_RECEIPT_OBSERVED"},
        ]},
        "goal_chart": {"A4": {"predicates": ["RECEIPT_VERIFIED AND AUTHENTIC_INGRESS_OBSERVED"]}},
        "dependencies": [{"dependency_id": "DEP-1", "kind": "RUNTIME_PREDICATE",
                          "ref": "AUTHENTIC_RETAINED_RUNTIME_OBSERVED"}],
        "latest_runtime_reconciliation": {"next_required_predicate": "CLAIM_FENCE_OBSERVED"},
        "gates": ["PROVIDER_CALLBACK_OBSERVED"],
    }
    errors = validate_record(record, "TEST-001")
    assert len(errors) == 8, errors
    assert all("STOP_AFFIRMATIVE_OBSERVER_PREDICATE" in error for error in errors)
    for path in (
        "runtime_resolution.first_unresolved_runtime_predicate=",
        "remaining_predicates[1]=",
        "goal_specific_completion_predicates[0]=",
        "state_transition_graph.transitions[0].predicate=",
        "goal_chart.A4.predicates[0]=",
        "dependencies[0].ref=",
        "latest_runtime_reconciliation.next_required_predicate=",
        "gates[0]=",
    ):
        assert any(path in error for error in errors), path


def test_append_predicate_and_evidence_labels_are_not_flagged():
    record = {
        "coordination_state": "ACTIVE",
        "runtime_resolution": {"first_unresolved_runtime_predicate": f"{APPEND}:GATEWAY_RUNTIME"},
        "remaining_predicates": [f"{APPEND}:LEASE_CLOSURE"],
        # Evidence labels the Master Records reconciliation matches, and state
        # names, are not progression predicates.
        "expected_evidence_predicates": ["AUTHENTIC_INGRESS_OBSERVED"],
        "allowed_next_transitions": ["REUSABLE_INVOCATION_OBSERVED"],
        "state_transition_graph": {"transitions": [
            {"from": "A_OBSERVED", "to": "B_OBSERVED", "predicate": f"{APPEND}:B"},
        ]},
        "verification_evidence": ["FIRST_EXIT_TRANSITION_OBSERVED"],
        # A plain `ref` outside a dependency entry is a reference, not a gate.
        "source": {"ref": "SOURCE_AUDIT_OBSERVED"},
    }
    assert validate_record(record, "TEST-001") == []


def test_affirmative_rule_keeps_historical_and_typed_exclusions():
    typed = actionable("ORGANIZATION_RECEIPT_NOT_APPENDED")
    typed["failed_predicate"] = "CURRENT_CLAIM_FENCE_OBSERVED"
    record = {
        "coordination_state": "ACTIVE",
        "goal_chart": {"A3": {"predicate": f"{APPEND}:CLAIM_FENCE", "state": typed,
                              "superseded_predicate": {"value": "CURRENT_CLAIM_FENCE_OBSERVED",
                                                       "authority_effect": "NONE_HISTORY_ONLY"}}},
        "superseded_remaining_predicates": {"value": ["AUTHENTIC_LEASE_CLOSURE_OBSERVED"]},
        "predicate_history": ["AUTHENTIC_LEASE_CLOSURE_OBSERVED"],
        "review_20261009": {"remaining_predicates": ["AUTHENTIC_LEASE_CLOSURE_OBSERVED"]},
    }
    assert validate_record(record, "TEST-001") == []
    # The exclusion does not hide a standing sibling beside the history.
    record["goal_chart"]["A3"]["predicate"] = "CURRENT_CLAIM_FENCE_OBSERVED"
    errors = validate_record(record, "TEST-001")
    assert len(errors) == 1 and "goal_chart.A3.predicate=" in errors[0]


def test_retired_record_gates_nothing():
    record = {"coordination_state": "RETIRED",
              "decomposition": {"first_unresolved_successor_predicate": "AUTHENTIC_RUNTIME_OBSERVED"}}
    assert validate_progression_predicates(record, "TEST-001") == []
    record["coordination_state"] = "ACTIVE"
    assert len(validate_progression_predicates(record, "TEST-001")) == 1


def test_gadi_first_unresolved_runtime_predicate_is_the_append_predicate():
    record = json.loads((RECORDS / "GADI-RUNTIME-CLOSURE-001.json").read_text(encoding="utf-8"))
    resolution = record["runtime_resolution"]
    assert resolution["first_unresolved_runtime_predicate"] == (
        f"{APPEND}:DURABLE_SERVICE_GATEWAY_RESIDENT_RENDEZVOUS_RUNTIME"
    )
    prior = resolution["superseded_first_unresolved_runtime_predicate"]
    assert prior["value"] == "CURRENT_DURABLE_SERVICE_GATEWAY_RESIDENT_RENDEZVOUS_RUNTIME_OBSERVED"
    assert prior["superseded_at_generation"] == 301
    assert prior["authority_effect"] == "NONE_HISTORY_ONLY"
    # The evidence label of the same name is kept for Master Records matching.
    assert prior["value"] in record["expected_evidence_predicates"]
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "CLAIMED_INTEGRATION"
    assert record["cosv_task_vector"] == "10100000100000"


def test_aggregate_registry_carries_no_affirmative_observer_gate():
    registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
    assert registry["generation"] >= 301
    for task in registry["tasks"]:
        assert validate_progression_predicates(task, task.get("task_id")) == [], task.get("task_id")
