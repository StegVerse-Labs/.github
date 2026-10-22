import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cosv import encode_task, validate_record  # noqa: E402

TASK_ID = "SDK-COST-DERIVED-TIER-PRICING-001"
VECTOR = "10300000011002"
RECORD = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"
TASK_VECTOR = ROOT / "control" / "task-vectors" / f"{TASK_ID}.json"
INDEX = ROOT / "control" / "task-vector-index.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "goal-task-allocation-requests" / "sdk-484-cost-derived-tier-pricing-2026-10-17.json"
OWNER_COMMENT = "https://github.com/StegVerse-org/StegVerse-SDK/issues/484#issuecomment-6235730818"


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
    assert "stegverse/tier_pricing.py" in record["targets"]["paths"]
    assert record["adjacent_task_refs"] == [
        "SDK-STRUCTURAL-VALIDATOR-CONSOLIDATION-001",
        "WORKER-TASK-RESOURCE-COST-LINKAGE-001",
        "ORGANIZATION-BATCH-CUSTODY-REPLAY-001",
    ]


def test_pricing_invariant_grants_nothing():
    invariant = load(RECORD)["pricing_invariant"]
    assert invariant["formula"] == "C_pricing = max(C_estimated, C_authentically_observed)"
    assert invariant["unknown_is_zero"] is False
    assert invariant["incomplete_evidence_disposition"] == "PROVISIONAL_SCENARIO_ONLY"
    assert invariant["foundation_ref"] == "SV-COST-FIVE-LANE-RESULTS-001"
    assert invariant["expansion_ref"] == "SV-COST-ELEVEN-LANE-RESULTS-001"
    assert invariant["execution_preference"] == "INTERNAL_FIRST"
    assert invariant["issues_tv_tvc_entitlement"] is False
    assert invariant["issues_intr_allow"] is False


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
    assert request["registration"]["registry_generation"] == request["observed_registry_generation"] + 1
    assert request["owner_authorization"]["source_ref"] == OWNER_COMMENT
    assert request["owner_authorization"]["authority_limit"] == "OWNER_INTENT_ONLY"


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
    assert record["worker_claim"] == {
        "authority": "WORKERCOORDINATOR",
        "claim_ref": None,
        "fence_ref": None,
        "projection_only": True,
    }
    assert record["completion"] == {"claimed": False, "validated": False, "runtime_observed": False}
