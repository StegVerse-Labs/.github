import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
BOOTSTRAP = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"


def current_registry_generation():
    return json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))["generation"]


def run(task_id, context=None, event_ledger=None, observed_generation=None):
    payload = {"task_id": task_id, "observed_registry_generation": current_registry_generation() if observed_generation is None else observed_generation}
    if context is not None:
        payload["checkin_context"] = context
    env = os.environ.copy()
    if event_ledger is not None:
        env["STEGVERSE_TASK_REGISTRY_EVENT_LEDGER"] = str(event_ledger)
    p = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(payload), text=True, capture_output=True, check=True, env=env)
    return json.loads(p.stdout)



def test_stale_registry_generation_fails_closed_before_any_mutation():
    current = current_registry_generation()
    out = run("TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001", observed_generation=current - 1)
    assert out["disposition"] == "STOP_STALE_COORDINATION"
    assert out["session_action"] == "RECONCILE_CANONICAL_GITHUB_STATE_BEFORE_MUTATION"
    assert out["observed_registry_generation"] == current - 1
    assert out["current_registry_generation"] == current
    assert out["write_pr_merge_handoff_claim_admissible"] is False
    assert out["reconciliation_required_before_mutation"] is True
    assert set(out["stale_session_prohibited_mutations"]) == {"SOURCE_WRITE", "PULL_REQUEST_CREATE_OR_UPDATE", "PULL_REQUEST_MERGE", "NEW_HANDOFF_CLAIM"}


def test_current_registry_generation_is_admitted_to_normal_collision_evaluation():
    out = run("TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001")
    assert out["observed_registry_generation"] == current_registry_generation()
    assert out["current_registry_generation"] == current_registry_generation()
    assert out["coordination_generation_current"] is True
    assert out["write_pr_merge_handoff_claim_admissible"] is True

def test_unregistered_stops_before_mutation():
    out = run("THIS-TASK-DOES-NOT-EXIST")
    assert out["disposition"] == "STOP_NOT_REGISTERED"
    assert out["session_action"] == "END_OR_REGISTER_BEFORE_MUTATION"
    assert out["authority_effect"] == "NONE"
    assert out["checkin_context"] == {}
    assert out["checkin_context_sha256"].startswith("sha256:")
    assert out["checkin_disposition_sha256"].startswith("sha256:")


def test_checked_out_runtime_task_without_substrate_review_fails_closed():
    out = run("STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001")
    assert out["task_id"] == "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
    assert out["disposition"] == "STOP_SUBSTRATE_REVIEW_REQUIRED"
    assert out["session_action"] == "END_AND_RECONCILE_EXECUTION_SUBSTRATE_REVIEW"
    assert "requires execution_substrate_resolution" in out["substrate_review_error"]
    assert out["authority_effect"] == "NONE"
    inv = out["registry_global_invariants"]["invariants"]
    assert inv["remote_computer_role"] == "TRANSPORT_DISCOVERY_ONLY"
    assert inv["remote_computer_inventory_semantics"] == "EVIDENCE_REACHABILITY_ONLY"


def test_retired_task_returns_stop_disposition():
    out = run("STEGCORE-UNKNOWN-PROBE-SEMANTICS-001")
    assert out["disposition"] in {"STOP_INACTIVE", "STOP_SUPERSEDED", "STOP_SUBSTRATE_REVIEW_REQUIRED"}


def test_session_branch_pr_and_intended_targets_are_bound_into_disposition():
    context = {
        "session_id": "session-abc",
        "checked_in_at": "2026-09-11T03:30:00Z",
        "repository": "StegVerse-Labs/StegOS",
        "branch": "task-registry-test",
        "pull_request": 999,
        "source_head": "0123456789abcdef",
        "first_unresolved_predicate": "AUTHENTIC_RUNTIME_PROOF",
        "repositories_under_mutation": ["StegVerse-Labs/StegOS", "StegVerse-Labs/.github"],
        "components_under_mutation": ["universal-intr", "task-registry-checkin"],
    }
    out = run("STEGOS-NODE-MANIFOLD-001", context)
    assert out["checkin_context"] == {
        **context,
        "repositories_under_mutation": sorted(context["repositories_under_mutation"]),
        "components_under_mutation": sorted(context["components_under_mutation"]),
    }
    assert out["checkin_context_sha256"].startswith("sha256:")
    assert out["checkin_disposition_sha256"].startswith("sha256:")


def test_substrate_resolution_is_part_of_collision_convergence_contract():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "validate_task_registration_substrate_resolution import validate_resolution" in text
    assert 'if isinstance(r.get("runtime_requirements"), dict):' in text
    assert '"STOP_SUBSTRATE_REVIEW_REQUIRED"' in text
    assert '"execution_substrates":substrates' in text.replace(" ", "")
    assert '"selected_execution_substrate":selected_substrate(r)' in text.replace(" ", "")
    hard_line = next(line for line in text.splitlines() if line.strip().startswith("hard=["))
    assert 'execution_substrates' not in hard_line


def test_canonical_work_bootstrap_requires_registry_preflight_before_route_mutation():
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert 'COLLISION_EVALUATOR_REL = Path("scripts/evaluate_task_registry_collision_checkin.py")' in text
    assert "checkin = collision_preflight(args.task_id)" in text
    checkin_pos = text.index("checkin = collision_preflight(args.task_id)")
    installer_pos = text.index("run([sys.executable, installer])")
    assert checkin_pos < installer_pos
    assert 'if disposition != "CONTINUE":' in text
    assert 'raise RuntimeError("TASK_REGISTRY_CHECKIN:"' in text
    assert 'result.get("authority_effect") != "NONE"' in text


def test_hygiene_repository_only_overlaps_are_visible_but_nonblocking_when_component_scopes_are_disjoint(tmp_path):
    out = run("HYGIENE-CAUSAL-ROOTS-001", event_ledger=tmp_path / "events.jsonl")
    assert out["disposition"] == "CONTINUE"
    expected = {
        "SS-EVIDENCE-COMPARISON-001",
        "AI-GOVERNANCE-OPPORTUNITY-ENGINE-001",
        "STEGVERSE-002-EXPERIMENT-RERUN-001",
        "MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001",
    }
    distinguished = {row["task_id"]: row for row in out["repository_only_scope_distinctions"]}
    assert expected <= set(distinguished)
    collision_ids = {row["task_id"] for row in out["collision_candidates"]}
    assert expected.isdisjoint(collision_ids)
    for task_id in expected:
        row = distinguished[task_id]
        assert row["scope_disposition"] == "DISTINGUISHED_COMPONENT_SCOPE"
        assert row["blocking"] is False
        assert row["overlap"]["repositories"]
        assert row["overlap"]["components"] == []
        assert row["overlap"]["lineage"] is False
        assert row["overlap"]["adjacent"] is False
        assert row["overlap"]["execution_substrates"] == []


def test_repository_only_overlap_remains_blocking_when_component_scope_is_missing():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "and a_components" in text
    assert "and b_components" in text
    assert 'overlap_row["scope_disposition"] = "DISTINGUISHED_COMPONENT_SCOPE"' in text
    assert 'repository_only_scope_distinctions.append(overlap_row)' in text
