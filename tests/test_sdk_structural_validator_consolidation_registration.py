import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cosv import encode_task, validate_record  # noqa: E402

TASK_ID = "SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001"
VECTOR = "60200000013002"
RECORD = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"
TASK_VECTOR = ROOT / "control" / "task-vectors" / f"{TASK_ID}.json"
INDEX = ROOT / "control" / "task-vector-index.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "goal-task-allocation-requests" / "sdk-484-structural-validator-2026-10-13.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_identity_and_states():
    record = load(RECORD)
    assert record["schema"] == "stegverse.canonical-task-record/v1"
    assert record["task_id"] == record["correlation_id"] == record["root_correlation_id"] == TASK_ID
    assert record["parent_task_id"] is None
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "UNCLAIMED"
    assert record["repository"] == "StegVerse-org/StegVerse-SDK"
    assert record["issue_ref"] == "StegVerse-org/StegVerse-SDK#484"
    assert "runtime_requirements" not in record
    assert "AUTHENTICATED_TV_TVC_PROVENANCE_FOR_FINAL_SDK_SOURCE_IDENTITY" in record["remaining_predicates"]


def test_vector_is_encoded_from_exact_metrics_and_agrees_everywhere():
    task_vector = load(TASK_VECTOR)
    assert task_vector["identity"] == f"StegVerse-Labs/.github:task:{TASK_ID}"
    assert task_vector["profile"] == "task.v1" and task_vector["level"] == "task"
    assert task_vector["authority_effect"] == "NONE"
    assert encode_task(task_vector["exact_metrics"]) == task_vector["vector"] == VECTOR
    assert validate_record(task_vector)
    assert load(RECORD)["cosv_task_vector"] == VECTOR
    rows = [r for r in load(REGISTRY)["tasks"] if r["task_id"] == TASK_ID]
    assert len(rows) == 1 and rows[0]["cosv_task_vector"] == VECTOR
    entries = [e for e in load(INDEX)["tasks"] if e["task_id"] == TASK_ID]
    assert len(entries) == 1
    assert entries[0]["vector"] == VECTOR and entries[0]["vector_state"] == "EMITTED"
    request = load(REQUEST)
    assert request["state"] == "REGISTERED"
    assert request["cosv_task_vector"] == VECTOR
    assert request["registration"]["authority_effect"] == "NONE_REGISTRATION_ONLY"
    assert request["owner_authorization"]["status"] == "EXPLICITLY_APPROVED_IN_CHAT"


def test_authority_separation_and_no_completion_claim():
    record = load(RECORD)
    authority = record["authority_model"]
    assert authority["task_registry_mints_execution_authority"] is False
    assert authority["worker_claim_authority"] == "WORKERCOORDINATOR"
    assert authority["credential_authority"] == "TV/TVC"
    assert authority["interlock_intr_required_for_governed_ingress_egress"] is True
    assert authority["github_runtime_authority"] == "NONE"
    assert authority["second_user_operated_device_required"] is False
    assert "gateway_owner" not in authority
    assert record["completion"] == {"claimed": False, "validated": False, "runtime_observed": False}


def test_worker_claim_is_workercoordinator_projection_in_record_and_row():
    expected = {
        "authority": "WORKERCOORDINATOR",
        "claim_ref": None,
        "fence_ref": None,
        "projection_only": True,
    }
    assert load(RECORD)["worker_claim"] == expected
    rows = [r for r in load(REGISTRY)["tasks"] if r["task_id"] == TASK_ID]
    assert len(rows) == 1 and rows[0]["worker_claim"] == expected


def test_master_records_reconstruction_is_non_gating_downstream_evidence():
    mr = "APPLICABLE_MASTER_RECORDS_RECONSTRUCTION_EVIDENCE_RETAINED"
    rows = [r for r in load(REGISTRY)["tasks"] if r["task_id"] == TASK_ID]
    for record in (load(RECORD), rows[0]):
        assert mr not in record["remaining_predicates"]
        assert len(record["remaining_predicates"]) == 3
        assert record["cosv_exact_metrics"]["blocker_count"] == 3
        evidence = [e for e in record["non_gating_downstream_evidence"] if e["evidence"] == mr]
        assert len(evidence) == 1
        assert evidence[0]["completion_predicate"] is False and evidence[0]["gating"] is False
        assert record["authority_model"]["master_records_role"] == (
            "ORGANIZATION_RECORDS_AND_RECONSTRUCTION_ONLY_NON_GATING"
        )
        assert record["authority_model"]["master_records_reality_authority"] is False
