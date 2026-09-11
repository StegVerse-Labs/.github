import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "data" / "canonical-task-records" / "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003.json"


def test_sdk_generic_manifest_goal_is_canonically_registered():
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert record["schema"] == "stegverse.canonical-task-record/v1"
    assert record["task_id"] == "SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003"
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "UNCLAIMED"
    assert record["cosv_task_vector"] == "71000000100110"
    assert record["worker_claim"]["authority"] == "NONE_TASK_REGISTRY_PROJECTION_ONLY"
    assert record["worker_claim"]["projection_only"] is True
    assert record["authority_model"]["task_registry_mints_execution_authority"] is False
    assert record["authority_model"]["worker_claim_authority"] == "WORKERCOORDINATOR"
    assert record["authority_model"]["credential_authority"] == "TV/TVC"
    assert record["authority_model"]["interlock_intr_required_for_governed_ingress_egress"] is True
    assert record["authority_model"]["heartbeat_execution_authority"] is False
    assert record["authority_model"]["github_runtime_authority"] == "NONE"
    assert record["authority_model"]["hosted_execution_fallback"] is False
    assert record["authority_model"]["second_user_operated_device_required"] is False
    assert "StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md" in record["handoff_projection_refs"]
    assert "resident-refresh-dispatch" in record["targets"]["components"]
    assert "RESIDENT_RESEAL_CONSUMPTION_RECEIPT_OBSERVED" in record["remaining_predicates"]
    assert record["completion"] == {
        "claimed": False,
        "validated": False,
        "activation_proof_complete": False,
    }
