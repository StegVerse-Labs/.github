from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_task_registration_substrate_resolution.py"
SPEC = importlib.util.spec_from_file_location("hygiene_substrate_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)

TASK_ID = "HYGIENE-CAUSAL-ROOTS-001"


def hygiene_record() -> dict:
    registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
    matches = [row for row in registry["tasks"] if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]


def test_hygiene_runtime_registration_has_valid_single_device_first_resolution() -> None:
    record = hygiene_record()
    validator.validate_resolution(record)
    resolution = record["execution_substrate_resolution"]
    assert resolution["review_order"] == validator.REVIEW_ORDER
    assert resolution["selected_substrate_id"] is None
    assert resolution["external_device_required"] is False
    assert resolution["second_user_operated_device_allowed"] is False
    assert resolution["authority_effect"] == "NONE"
    assert resolution["reviews"][-1] == {
        "substrate_id": "REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT",
        "disposition": "NOT_APPLICABLE",
        "limitation_class": "NOT_APPLICABLE",
        "evidence_refs": [],
    }


def test_hygiene_resolution_preserves_unobserved_same_device_capacity_as_pending_evidence() -> None:
    reviews = hygiene_record()["execution_substrate_resolution"]["reviews"]
    for review in reviews[:-1]:
        assert review["disposition"] == "PENDING_EVIDENCE"
        assert review["limitation_class"] == "EVIDENCE_REACHABILITY"
        assert review["evidence_refs"]
