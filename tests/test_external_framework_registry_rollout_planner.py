import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "scripts/plan_external_framework_registry_rollout.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("registry_rollout_planner", PLANNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_manifest(root: Path, framework_id: str, *, source_version="official docs"):
    path = root / "docs/external-frameworks" / f"{framework_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "artifact_type": "external_framework_manifest",
        "schema_version": "0.1",
        "framework_id": framework_id,
        "name": framework_id,
        "source_reference": f"https://example.test/{framework_id}",
        "source_version": source_version,
        "allowed_use_boundary": ["bounded test"],
        "claims": ["test claim"],
        "non_claims": ["no execution authority"],
        "transition_table_mapping": {"execution_authority_claim": False},
        "SPE_overlap": {},
        "StegVerse_ecosystem_overlap": {},
        "fail_closed_conditions": ["missing source"],
        "boundary": {
            "execution_authority_claim": False,
            "compatibility_manifest_is_authority": False,
        },
    }), encoding="utf-8")


def registry():
    return {
        "artifact_type": "external_framework_registry",
        "schema_version": "0.4",
        "entries": [
            {"framework_id": "alpha", "name": "Alpha", "status": "SOURCED-CROSSWALK-PROVISIONAL", "manifest_path": "docs/external-frameworks/alpha.json"},
            {"framework_id": "beta", "name": "Beta", "status": "SOURCED-CROSSWALK-PROVISIONAL", "manifest_path": "docs/external-frameworks/beta.json"},
            {"framework_id": "blocked", "name": "Blocked", "status": "OFFICIAL-SOURCE-REQUIRED", "manifest_path": "docs/external-frameworks/blocked.json"},
        ],
    }


def qualified_endpoint(url="https://alpha.test/evaluate"):
    return {
        "runtime_endpoint_ref": url,
        "endpoint_evidence_ref": "evidence/alpha-endpoint-observation.json",
        "endpoint_observed_at": "2026-09-13T22:30:00-05:00",
        "endpoint_evidence_class": "PUBLIC_ENDPOINT_OBSERVATION",
    }


def test_registry_sweep_classifies_each_framework_independently(tmp_path):
    module = load_planner()
    write_manifest(tmp_path, "alpha")
    write_manifest(tmp_path, "beta")
    write_manifest(tmp_path, "blocked", source_version="OFFICIAL_SOURCE_REQUIRED")
    result = module.build_registry_plan(
        registry=registry(),
        manifest_root=tmp_path,
        goal_task_id="MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001",
        cosv_task_vector="50000000100000",
        endpoint_map={"bindings": {"alpha": qualified_endpoint()}},
    )
    assert result["framework_count"] == 3
    assert result["eligibility_counts"] == {
        "ROUNDTRIP_ELIGIBLE": 1,
        "RUNTIME_ENDPOINT_UNAVAILABLE": 1,
        "SOURCE_ONLY": 1,
    }
    assert result["roundtrip_eligible_frameworks"] == ["alpha"]
    assert result["endpoint_binding_counts"] == {
        "EVIDENCE_QUALIFIED_ENDPOINT_BOUND": 1,
        "UNBOUND_NO_RUNTIME_ENDPOINT_REF": 2,
    }
    assert result["endpoint_evidence_qualification_required"] is True
    assert result["fail_closed_scope"] == "PER_FRAMEWORK_INVOCATION"
    assert result["authority_effect"] == "NONE_COORDINATION_ONLY"
    assert result["transition_effect"] == "NONE_PLAN_ONLY"


def test_bare_or_unqualified_endpoint_fails_closed(tmp_path):
    module = load_planner()
    for framework_id in ("alpha", "beta", "blocked"):
        write_manifest(tmp_path, framework_id, source_version="official docs")
    result = module.build_registry_plan(
        registry=registry(),
        manifest_root=tmp_path,
        goal_task_id="MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001",
        cosv_task_vector="50000000100000",
        endpoint_map={
            "alpha": "https://alpha.test/evaluate",
            "beta": {"runtime_endpoint_ref": "https://beta.test/evaluate"},
        },
    )
    rows = {row.get("framework_id"): row for row in result["plans"]}
    assert rows["alpha"]["eligibility"] == "RUNTIME_ENDPOINT_UNAVAILABLE"
    assert rows["alpha"]["endpoint_binding_state"] == "UNQUALIFIED_ENDPOINT_REJECTED"
    assert rows["beta"]["eligibility"] == "RUNTIME_ENDPOINT_UNAVAILABLE"
    assert rows["beta"]["endpoint_binding_state"] == "UNQUALIFIED_ENDPOINT_REJECTED"
    assert result["roundtrip_eligible_frameworks"] == []


def test_missing_manifest_fails_only_that_framework(tmp_path):
    module = load_planner()
    write_manifest(tmp_path, "alpha")
    write_manifest(tmp_path, "blocked", source_version="OFFICIAL_SOURCE_REQUIRED")
    result = module.build_registry_plan(
        registry=registry(),
        manifest_root=tmp_path,
        goal_task_id="MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001",
        cosv_task_vector="50000000100000",
        endpoint_map={
            "bindings": {
                "alpha": qualified_endpoint(),
                "beta": qualified_endpoint("https://beta.test/evaluate"),
            }
        },
    )
    rows = {row.get("framework_id"): row for row in result["plans"]}
    assert rows["alpha"]["eligibility"] == "ROUNDTRIP_ELIGIBLE"
    assert rows["beta"]["eligibility"] == "REGISTRY_ENTRY_INVALID"
    assert "manifest" in rows["beta"]["reason"]
    assert rows["blocked"]["eligibility"] == "SOURCE_ONLY"


def test_orphan_endpoint_evidence_fails_closed(tmp_path):
    module = load_planner()
    for framework_id in ("alpha", "beta", "blocked"):
        write_manifest(tmp_path, framework_id, source_version="official docs")
    result = module.build_registry_plan(
        registry=registry(),
        manifest_root=tmp_path,
        goal_task_id="MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001",
        cosv_task_vector="50000000100000",
        endpoint_map={
            "bindings": {
                "alpha": {
                    "endpoint_evidence_ref": "evidence/alpha.json",
                    "endpoint_observed_at": "2026-09-13T22:30:00-05:00",
                    "endpoint_evidence_class": "PUBLIC_ENDPOINT_OBSERVATION",
                }
            }
        },
    )
    row = next(item for item in result["plans"] if item.get("framework_id") == "alpha")
    assert row["eligibility"] == "RUNTIME_ENDPOINT_UNAVAILABLE"
    assert row["endpoint_binding_state"] == "ORPHAN_ENDPOINT_EVIDENCE_REJECTED"


def test_source_crosswalk_sweep_never_requires_runtime_endpoint(tmp_path):
    module = load_planner()
    for framework_id in ("alpha", "beta", "blocked"):
        write_manifest(tmp_path, framework_id, source_version="official docs")
    result = module.build_registry_plan(
        registry=registry(),
        manifest_root=tmp_path,
        goal_task_id="MIR-CONNECTION-ROUNDTRIP-TECHNICAL-GUIDE-001",
        cosv_task_vector="50000000100000",
        operation_class="SOURCE_CROSSWALK",
    )
    rows = {row.get("framework_id"): row for row in result["plans"]}
    assert rows["alpha"]["eligibility"] == "TRANSLATION_ONLY"
    assert rows["beta"]["eligibility"] == "TRANSLATION_ONLY"
    assert rows["blocked"]["eligibility"] == "SOURCE_ONLY"
