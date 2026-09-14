import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARD = ROOT / "source-bundles/reusable-task-registry.d/RT-EXTERNAL-FRAMEWORK-ROUNDTRIP-ROLLOUT-001.json"
HANDOFF = ROOT / "docs/EXTERNAL_FRAMEWORK_ROUNDTRIP_ROLLOUT_MIRROR_HANDOFF.md"
RESOLVER = ROOT / "scripts/resolve_external_framework_roundtrip_rollout.py"
ELYRIA_PROFILE = ROOT / "data/goal-task-component-profiles/SDK-ELYRIA-INTR-ADAPTER-001.json"


def load_shard():
    return json.loads(SHARD.read_text(encoding="utf-8"))


def load_resolver():
    spec = importlib.util.spec_from_file_location("external_framework_rollout", RESOLVER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def registry_entry(status="SOURCED-CROSSWALK-PROVISIONAL"):
    return {
        "artifact_type": "external_framework_registry",
        "schema_version": "0.4",
        "entries": [
            {
                "framework_id": "open-policy-agent",
                "name": "Open Policy Agent",
                "status": status,
                "manifest_path": "docs/external-frameworks/open-policy-agent.json",
                "source": "https://www.openpolicyagent.org/docs/latest/",
            }
        ],
    }


def manifest(source_version="official documentation recorded", source_reference="https://www.openpolicyagent.org/docs/latest/"):
    return {
        "artifact_type": "external_framework_manifest",
        "schema_version": "0.1",
        "framework_id": "open-policy-agent",
        "name": "Open Policy Agent",
        "source_reference": source_reference,
        "source_version": source_version,
        "allowed_use_boundary": ["policy decision evidence only"],
        "claims": ["structured policy evaluation"],
        "non_claims": ["no execution authority"],
        "transition_table_mapping": {"execution_authority_claim": False},
        "SPE_overlap": {},
        "StegVerse_ecosystem_overlap": {"execution_path": "not authorized"},
        "fail_closed_conditions": ["missing source"],
        "boundary": {
            "execution_authority_claim": False,
            "compatibility_manifest_is_authority": False,
        },
    }


def build(module, **kwargs):
    return module.build_plan(
        registry=kwargs.pop("registry", registry_entry()),
        manifest=kwargs.pop("manifest", manifest()),
        framework_id=kwargs.pop("framework_id", "open-policy-agent"),
        goal_task_id=kwargs.pop("goal_task_id", "MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001"),
        cosv_task_vector=kwargs.pop("cosv_task_vector", "50000000100000"),
        operation_class=kwargs.pop("operation_class", "RUNTIME_ROUNDTRIP"),
        **kwargs,
    )


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


def test_existing_elyria_profile_fits_rollout_without_new_transport_plane():
    rollout = load_shard()
    elyria = json.loads(ELYRIA_PROFILE.read_text(encoding="utf-8"))
    rollout_required = set(rollout["selected_components"])
    rollout_conditional = set(rollout["conditional_components"])
    elyria_selected = {row["component_id"] for row in elyria["selected_components"]}

    assert elyria["task_id"] == "SDK-ELYRIA-INTR-ADAPTER-001"
    assert elyria_selected == rollout_required
    assert "RTC-PUBLISHER-005" not in elyria_selected
    assert "RTC-FARSIDE-FINAL-009" not in elyria_selected
    assert {"RTC-PUBLISHER-005", "RTC-FARSIDE-FINAL-009"} <= rollout_conditional
    assert elyria["new_reusable_component_required"] is False
    assert elyria["new_goal_task_required"] is False
    assert elyria["authority_invariants"]["governed_transition"] == "Interlock/InTr"
    assert elyria["authority_invariants"]["github_runtime_authority"] == "NONE"
    assert any("second Interlock/InTr protocol" in item for item in elyria["duplicate_orchestration_to_retire"])


def test_source_blocked_registry_entry_stops_as_source_only():
    module = load_resolver()
    result = build(
        module,
        registry=registry_entry("OFFICIAL-SOURCE-REQUIRED"),
        manifest=manifest(
            source_version="UNVERIFIED_SOURCE_REQUIRED",
            source_reference="official public source URL required",
        ),
        runtime_endpoint_ref="https://example.invalid/evaluate",
    )
    assert result["eligibility"] == "SOURCE_ONLY"
    assert result["transition_effect"] == "NONE_PLAN_ONLY"


def test_source_crosswalk_is_translation_only_even_with_endpoint_reference():
    module = load_resolver()
    result = build(module, operation_class="SOURCE_CROSSWALK", runtime_endpoint_ref="https://example.invalid/evaluate")
    assert result["eligibility"] == "TRANSLATION_ONLY"
    assert result["foreign_framework_authority_effect"] == "NONE_ON_STEGVERSE"


def test_runtime_roundtrip_requires_current_endpoint_reference():
    module = load_resolver()
    result = build(module)
    assert result["eligibility"] == "RUNTIME_ENDPOINT_UNAVAILABLE"


def test_sourced_framework_with_endpoint_is_roundtrip_eligible_but_non_authorizing():
    module = load_resolver()
    result = build(
        module,
        runtime_endpoint_ref="https://example.invalid/evaluate",
        counterpart_provenance="EXTERNAL_FRAMEWORK_CANDIDATE",
    )
    assert result["eligibility"] == "ROUNDTRIP_ELIGIBLE"
    assert result["transition_effect"] == "NONE_PLAN_ONLY"
    assert result["claim_fence_effect"] == "NONE"
    assert result["credential_effect"] == "NONE"
    assert "executed transitions are runtime truth" in result["runtime_truth_rule"]


def test_duplicate_registry_identity_fails_closed():
    module = load_resolver()
    duplicate = registry_entry()
    duplicate["entries"].append(dict(duplicate["entries"][0]))
    result = build(module, registry=duplicate)
    assert result["eligibility"] == "REGISTRY_ENTRY_INVALID"
    assert "observed=2" in result["reason"]


def test_handoff_preserves_foreign_non_authority_and_transition_truth_boundary():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "foreign verdicts/receipts never become StegVerse authority" in text
    assert "executed transitions are runtime truth at their recorded provenance" in text
    assert "Source, CI, or merge state alone does not prove an unexecuted transition" in text
