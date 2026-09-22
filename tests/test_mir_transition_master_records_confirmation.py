import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workers" / "reusable_task_master_records_roundtrip.py"
spec = importlib.util.spec_from_file_location("mir_mr_probe", MODULE_PATH)
assert spec and spec.loader
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)


def sample_one_way():
    return {
        "schema": MOD.MIR_ONE_WAY_SCHEMA,
        "goal_task_id": "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001",
        "root_goal_task_id": "MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001",
        "cosv_task_vector": "50000000100000",
        "claim_id": "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001-G7",
        "fencing_token": 7,
        "destination_profile": "MIR",
        "destination": "STEGVERSE_OWNED_MIR_MIRROR",
        "provenance": "MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME",
        "request_ingress_receipt": {"receipt_id": "INGRESS"},
        "response_egress_receipt": {"receipt_id": "EGRESS"},
        "receipt_chain_linked": True,
        "mir_external_ingress_receipt": {"receipt_id": "MIR-FARSIDE"},
        "return_queue_receipt": {"queue_id": "RETURN-Q"},
        "response_packet_sha256": "sha256:" + "a" * 64,
    }


def test_transition_packets_cover_route_state_transitions_in_order():
    packets = MOD._mir_transition_packets(sample_one_way())
    assert [item["transition_id"] for item in packets] == [
        "CURRENT_GOAL_COSV_BOUND",
        "CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED",
        "RTC-STEGVERSE-EGRESS-007",
        "RTC-INTERLOCK-INTR-TRANSPORT-008",
        "RTC-FARSIDE-FINAL-009",
        "MIR_DESTINATION_EVIDENCE_RETAINED",
        "EXACT_GOVERNED_RETURN_PACKET_RETAINED",
    ]
    assert all(item["transition_observed"] is True for item in packets)
    assert all(item["authority_effect"] == "NONE_CONFIRMATION_EVIDENCE_ONLY" for item in packets)


def test_first_non_return_transition_is_reported_without_authority_promotion():
    value = sample_one_way()
    with tempfile.TemporaryDirectory() as td:
        request_path = Path(td) / "one-way-transition.latest.json"
        request_path.write_text(json.dumps(value), encoding="utf-8")

        def fake_roundtrip(path, *, binding=None):
            if "04-RTC-INTERLOCK-INTR-TRANSPORT-008" in path.name:
                return {"state": "BOUNDARY", "reason": "TEST_NON_RETURN", "authority_effect": "NONE"}
            return {"state": "RETURNED", "custody_ref": str(path) + ".custody", "reconstructed_ref": str(path) + ".reconstructed", "authority_effect": "NONE"}

        with mock.patch.object(MOD, "_roundtrip_one", side_effect=fake_roundtrip):
            result = MOD._execute_mir_transition_confirmations(request_path, value, binding=(Path(td), Path(td)))

    assert result["state"] == "FIRST_NON_RETURN_IDENTIFIED"
    assert result["first_non_return_transition_id"] == "RTC-INTERLOCK-INTR-TRANSPORT-008"
    assert result["authority_effect"] == "NONE_DIAGNOSTIC_ONLY"


def test_unobserved_transition_is_first_non_return_without_fabricating_receipt():
    value = sample_one_way()
    value["mir_external_ingress_receipt"] = None
    packets = MOD._mir_transition_packets(value)
    row = next(item for item in packets if item["transition_id"] == "RTC-FARSIDE-FINAL-009")
    assert row["transition_observed"] is False
    assert row["state"] == "TRANSITION_NOT_OBSERVED"
