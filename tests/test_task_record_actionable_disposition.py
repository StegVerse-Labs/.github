"""The disposition invariant applied to a canonical task record's own state."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_task_record_actionable_disposition import validate_record  # noqa: E402

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
