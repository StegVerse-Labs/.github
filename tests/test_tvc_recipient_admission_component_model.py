import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001"
PROFILE = ROOT / "data" / "goal-task-transport-profiles" / f"{TASK_ID}.json"
MODEL = ROOT / "data" / "reusable-task-component-model.json"
POLICY = ROOT / "data" / "reusable-task-component-decomposition-policy.json"
CONTRACT = ROOT / "data" / "reusable-transport-component-contract.json"
HANDOFF = ROOT / "docs" / "TVC_RECIPIENT_ADMISSION_OPAQUE_SIGNER_COMPONENT_MODEL_MIRROR_HANDOFF.md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_profile_selects_only_required_transport_components():
    profile = load(PROFILE)
    contract = load(CONTRACT)
    assert profile["task_id"] == TASK_ID
    assert profile["cosv_task_vector"] == "50000000102000"
    known = {row["id"] for row in contract["components"]}
    selected = set(profile["selected_components"])
    assert selected <= known
    assert selected == {
        "RTC-MANIFEST-001",
        "RTC-GOVERNED-PROCESSING-002",
        "RTC-ROUNDTRIP-003",
        "RTC-EVIDENCE-CUSTODY-004",
        "RTC-INTERLOCK-INTR-TRANSPORT-008",
    }
    assert profile["transport_requirements"]["required_round_trips"] == [
        "recipient_admission_signature_round_trip"
    ]
    assert profile["transport_requirements"]["publisher_projection"] is False
    assert profile["transport_requirements"]["sdk_return_assembly"] is False
    assert profile["transport_requirements"]["stegverse_final_egress_transition"] is False
    assert profile["transport_requirements"]["far_side_final_transition"] is False


def test_profile_preserves_authority_separation():
    profile = load(PROFILE)
    authority = profile["authority_invariants"]
    assert authority["task_registry"] == "COORDINATION_ONLY"
    assert authority["claim_fence"] == "WorkerCoordinator"
    assert authority["user_verification"] == "KV/SKAP Vault"
    assert authority["device_role"] == "INTERCHANGEABLE_STEGOS_TRANSPORT_NODE"
    assert authority["credential_signing"] == "TV/TVC"
    assert authority["transition"] == "Interlock/InTr"
    assert authority["reality_reconstruction"] == "Master Records"
    assert authority["heartbeat"] == "OBSERVABILITY_ONLY"
    assert authority["github_runtime_authority"] == "NONE"


def test_component_model_and_policy_are_canonical_inputs():
    model = load(MODEL)
    policy = load(POLICY)
    assert model["schema"] == "stegverse.reusable-task-component-model/v1"
    assert policy["schema"] == "stegverse.reusable-task-component-decomposition-policy/v1"
    assert policy["decision"]["score_13_plus"].startswith("STOP_SCOPE_GROWTH_AND_DECOMPOSE")


def test_component_handoff_preserves_runtime_evidence_boundary():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "score = 27" in text
    assert "GOAL IDENTITY PRESERVED" in text
    assert "No second user-operated device is required" in text
    assert "No device-local user verification is authorized" in text
    assert "Source construction, CI, merge, and component compatibility do not satisfy these runtime predicates" in text
    assert "public deep-link/loopback signing-service idea         -> rejected/obsolete" in text
