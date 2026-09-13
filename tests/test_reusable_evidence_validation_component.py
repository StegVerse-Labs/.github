import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "reusable-task-component-model.json"
CONTRACT = ROOT / "data" / "reusable-evidence-validation-component-contract.json"
HANDOFF = ROOT / "docs" / "REUSABLE_EVIDENCE_VALIDATION_COMPONENTS_MIRROR_HANDOFF.md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_model_materializes_evidence_validation_family():
    model = load(MODEL)
    assert model["component_families"]["evidence_validation"] == "data/reusable-evidence-validation-component-contract.json"


def test_current_selector_exposes_component_interface_and_authority_boundary():
    model = load(MODEL)
    component = load(CONTRACT)["components"][0]
    assert component["component_id"] == "RTC-EVIDENCE-CURRENT-SELECTOR-010"
    for field in model["component_interface_minimum"]:
        assert field in component
    assert component["authority_effect"] == "NONE_EVIDENCE_SELECTION_ONLY"
    invariants = component["invariants"]
    assert invariants["creates_user_verification"] is False
    assert invariants["performs_webauthn"] is False
    assert invariants["selects_latest_by_timestamp"] is False
    assert invariants["device_identity_is_user_verification"] is False
    assert invariants["transport_identity_is_user_verification"] is False
    assert invariants["receipt_selection_mints_authority"] is False
    assert invariants["secret_material_output"] is False


def test_selector_declares_required_failure_semantics():
    component = load(CONTRACT)["components"][0]
    failures = set(component["failure_classes"])
    required = {
        "CURRENT_BINDING_MISSING",
        "CURRENT_BINDING_EXPIRED",
        "CURRENT_BINDING_CONTEXT_MISMATCH",
        "NO_MATCHING_CANDIDATE",
        "AMBIGUOUS_MULTIPLE_MATCHES",
        "DIGEST_MISMATCH",
    }
    assert required <= failures
    assert "never fall back to latest-by-time selection" in component["retry_or_reentry_semantics"]


def test_handoff_preserves_runtime_boundary():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "KV/SKAP Vault remains the sole user-verification authority" in text
    assert "does not synthesize a current binding" in text
    assert "CURRENT_BINDING_MISSING" in text
    assert "Source merge and CI therefore do not satisfy" in text
