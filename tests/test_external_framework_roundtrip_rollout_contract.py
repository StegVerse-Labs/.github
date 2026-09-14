import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARD = ROOT / "source-bundles/reusable-task-registry.d/RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001.json"
HANDOFF = ROOT / "docs/EXTERNAL_FRAMEWORK_ROUNDTRIP_ROLLOUT_MIRROR_HANDOFF.md"


def load_shard():
    return json.loads(SHARD.read_text(encoding="utf-8"))


def test_reusable_task_identity_and_authority_are_bounded():
    task = load_shard()
    assert task["reusable_task_id"] == "RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001"
    assert task["authority_effect"] == "NONE_ORCHESTRATION_COMPOSITION_ONLY"
    assert "RT-EXTERNAL-ADAPTER-ESTABLISH-001" in task["selected_components"]
    assert "RTC-INTERLOCK-INTR-TRANSPORT-008" in task["selected_components"]
    assert "RTC-EVIDENCE-CUSTODY-004" in task["selected_components"]


def test_runtime_ineligible_frameworks_fail_closed_without_blocking_other_invocations():
    task = load_shard()
    states = set(task["framework_eligibility_states"])
    assert {
        "ROUNDTRIP_ELIGIBLE",
        "SOURCE_ONLY",
        "TRANSLATION_ONLY",
        "RUNTIME_ENDPOINT_UNAVAILABLE",
        "UNSUPPORTED_OPERATION_CLASS",
        "REGISTRY_ENTRY_INVALID",
    } <= states
    instructions = task["reuse_instructions"]
    assert "stop that invocation" in instructions
    assert "without creating substitute transport" in instructions
    assert "without blocking unrelated framework invocations" in instructions


def test_reference_profiles_cover_mir_and_non_mir_existing_consumer():
    task = load_shard()
    assert task["reference_profiles"] == [
        "MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001",
        "SDK-ELYRIA-INTR-ADAPTER-001",
    ]


def test_handoff_preserves_foreign_non_authority_and_runtime_evidence_boundary():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "foreign verdicts/receipts never become StegVerse authority" in text
    assert "Source/CI/merge does not satisfy runtime predicates" in text
