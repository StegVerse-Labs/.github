import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDICATE_ID = "PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002"
RECEIPT_REF = "receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json"


def test_retained_hil_browser_receipt_satisfies_cross_task_predicate():
    receipt = json.loads((ROOT / RECEIPT_REF).read_text(encoding="utf-8"))
    cross = json.loads((ROOT / "control/cross-task-coordination.json").read_text(encoding="utf-8"))
    predicate = next(p for p in cross["predicates"] if p["predicate_id"] == PREDICATE_ID)

    assert receipt["schema"] == "stegverse.hil-resident-execution-request-consumption/v1"
    assert receipt["state"] == "COMPLETED"
    assert receipt["request_id"] == "RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002"
    assert receipt["task_id"] == "SHWP-HIL-SOVEREIGN-RECEIVER-001"
    assert receipt["terminal_hil_transition_observed"] is True
    assert receipt["runtime_execution_surface"] == "CURRENT_USER_IPHONE_BROWSER"
    assert receipt["second_machine_required"] is False
    assert receipt["claim_id"] == "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25"
    assert receipt["fencing_token"] == 25

    assert predicate["state"] == "SATISFIED"
    assert predicate["satisfied_by_evidence_ref"] == RECEIPT_REF
    assert not any(g["predicate_id"] == PREDICATE_ID for g in cross.get("gaps", []))


def test_hil_handoff_reuses_same_device_receipt_without_connected_device_gate():
    handoff = json.loads((ROOT / "handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json").read_text(encoding="utf-8"))
    targeted = handoff["activation"]["targeted_execution"]
    resident = handoff["activation"]["resident_execution_request"]

    assert targeted["requires_existing_separated_carrier_reference"] is False
    assert resident["runtime_execution_observed"] is True
    assert resident["runtime_execution_surface"] == "CURRENT_USER_IPHONE_BROWSER"
    assert resident["evidence_ref"] == RECEIPT_REF
    assert resident["broader_hil_lifecycle_complete"] is False
    assert resident["second_machine_required"] is False
