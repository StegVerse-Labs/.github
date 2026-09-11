import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "task-registry-sovereign-kv-runtime-intake-contract.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_runtime_intake_reuses_existing_execution_owners():
    contract = load_contract()
    assert contract["schema"] == "stegverse.task-registry-sovereign-kv-runtime-intake/v1"
    assert contract["execution_ownership"]["provider_execution_owner"] == "KV-CONNECTION-REVALIDATION-WORKER-001"
    assert contract["execution_ownership"]["device_kv_skap_intr_evidence_owner"] == "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
    assert contract["execution_ownership"]["new_provider_executor_created"] is False
    assert contract["authority_effect"] == "NONE"


def test_runtime_intake_requires_live_exact_hash_write_and_readback():
    contract = load_contract()
    assert contract["required_provider_operation"] == "WRITE"
    assert contract["required_provider_request_state"] == "PENDING_INTERLOCK_INTR"
    assert contract["required_provider_result_state"] == "ADMITTED"
    binding = contract["event_hash_binding"]
    assert binding["provider_object_ref_equals_event_sha256"] is True
    assert binding["stored_event_sha256_equals_event_sha256"] is True
    assert binding["synthetic_or_fixture_event_eligible"] is False
    assert binding["repository_or_ci_only_evidence_eligible"] is False
    assert "EXACT_STORED_EVENT_SHA256_READBACK" in contract["required_evidence"]


def test_runtime_intake_preserves_authority_boundaries():
    contract = load_contract()
    authority = contract["authority"]
    assert authority["workercoordinator"] == "CLAIM_FENCE"
    assert authority["interlock_intr"] == "TRANSITION_ADMISSION"
    assert authority["credential_authority"] == "TV/TVC"
    assert authority["master_records"] == "OBSERVED_REALITY_RECONSTRUCTION"
    assert authority["heartbeat"] == "OBSERVABILITY_ONLY"
    assert authority["github_runtime_authority"] == "NONE"
    assert contract["credential_material_present"] is False
