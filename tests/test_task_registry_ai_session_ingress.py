import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_task_registry_ai_session_checkin.py"
POLICY = ROOT / "data" / "task-registry-ai-ingress-policy.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"


def current_generation():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["generation"]


def run(payload):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_session_without_actor_kind_fails_closed():
    out = run({
        "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "checkin_context": {"session_id": "session-test"},
    })
    assert out["disposition"] == "STOP_ACTOR_IDENTITY_REQUIRED"
    assert out["authority_effect"] == "NONE"
    assert out["runtime_identity_attestation_proven"] is False


def test_non_chatgpt_ai_is_denied_before_registry_checkin():
    out = run({
        "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "checkin_context": {
            "session_id": "session-test",
            "actor_kind": "NON_CHATGPT_AI",
        },
    })
    assert out["disposition"] == "STOP_AI_BOUNDARY_DENIED"
    assert out["session_action"] == "END_SESSION"
    assert out["reason"] == "non_chatgpt_ai_task_registry_ingress_forbidden"


def test_unknown_actor_kind_fails_closed():
    out = run({
        "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "checkin_context": {
            "session_id": "session-test",
            "actor_kind": "SOME_NEW_AI",
        },
    })
    assert out["disposition"] == "STOP_ACTOR_KIND_UNRECOGNIZED"


def test_chatgpt_session_reaches_canonical_checkin_without_execution_authority():
    out = run({
        "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "observed_registry_generation": current_generation(),
        "checkin_context": {
            "session_id": "session-test",
            "actor_kind": "CHATGPT_SESSION",
        },
    })
    assert out["task_id"] == "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
    assert out["disposition"] in {"CONTINUE", "COORDINATE_CONVERGENCE", "STOP_COLLISION"}
    assert out["authority_effect"] == "NONE"
    assert out["ai_session_ingress"]["actor_kind"] == "CHATGPT_SESSION"
    assert out["ai_session_ingress"]["chatgpt_is_only_permitted_ai_kind"] is True
    assert out["ai_session_ingress"]["runtime_identity_attestation_proven"] is False


def test_policy_explicitly_separates_source_gate_from_runtime_attestation():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["invariants"]["chatgpt_is_only_ai_actor_kind_permitted"] is True
    assert policy["invariants"]["runtime_identity_attestation_proven"] is False
    assert "NON_CHATGPT_AI" in policy["denied_ai_actor_kinds"]
    assert "CHATGPT_SESSION" in policy["allowed_actor_kinds"]


def chatgpt_payload(observed_marker="CURRENT"):
    payload = {
        "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "checkin_context": {
            "session_id": "session-generation-test",
            "actor_kind": "CHATGPT_SESSION",
        },
    }
    if observed_marker == "CURRENT":
        payload["observed_registry_generation"] = current_generation()
    elif observed_marker == "STALE":
        payload["observed_registry_generation"] = current_generation() - 1
    elif observed_marker == "DIVERGENT":
        payload["observed_registry_generation"] = current_generation() + 1
    return payload


def test_chatgpt_ai_session_missing_generation_stops_before_mutation():
    out = run(chatgpt_payload("MISSING"))
    assert out["disposition"] == "STOP_COORDINATION_GENERATION_REQUIRED"
    assert out["write_pr_merge_handoff_claim_admissible"] is False


def test_chatgpt_ai_session_stale_generation_stops_before_mutation():
    out = run(chatgpt_payload("STALE"))
    assert out["disposition"] == "STOP_STALE_COORDINATION"
    assert out["write_pr_merge_handoff_claim_admissible"] is False
    assert out["reconciliation_required_before_mutation"] is True


def test_chatgpt_ai_session_divergent_generation_stops_before_mutation():
    out = run(chatgpt_payload("DIVERGENT"))
    assert out["disposition"] == "STOP_COORDINATION_GENERATION_MISMATCH"
    assert out["write_pr_merge_handoff_claim_admissible"] is False
