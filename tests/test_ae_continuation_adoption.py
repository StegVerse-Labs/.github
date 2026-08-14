from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "verify_ae_continuation_adoption.py"
spec = importlib.util.spec_from_file_location("ae_adoption", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
verify = module.verify


def source():
    return {
        "policy_id": "AE-CONTINUATION-CONFORMANCE-001",
        "source_commit": "78d00ca0e977af3e666c2acec431b111aea0deef",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": False,
        "heartbeat_role": "CARRIER_SYNCHRONIZATION_ONLY",
        "worker_control_plane_separate": True,
        "master_records_custody_separate": True,
    }


def registry():
    return {
        "generation": 21,
        "tasks": [
            {"task_id": "done", "goal_id": "g1", "handoff_ref": "handoffs/done.json", "state": "COMPLETED"},
            {"task_id": "current", "goal_id": "g2", "handoff_ref": "handoffs/current.json", "state": "ACTIVE_WORKER"},
            {"task_id": "future", "goal_id": "g3", "handoff_ref": "handoffs/future.json", "state": "HANDOFF_READY"},
        ],
    }


def projection():
    return {
        "tasks": [
            {
                "task_id": "done",
                "goal_id": "g1",
                "handoff_ref": "handoffs/done.json",
                "temporal_class": "RECENTLY_COMPLETED",
                "ae_impact": "CAPABILITY",
                "capability_id": "cap:done",
                "existence_phase": "ACTIVATED",
                "integration_evidence_refs": ["integration"],
                "activation_proof_ref": "proof",
                "authority_claims": [],
            },
            {
                "task_id": "current",
                "goal_id": "g2",
                "handoff_ref": "handoffs/current.json",
                "temporal_class": "CURRENT",
                "ae_impact": "CAPABILITY",
                "capability_id": "cap:current",
                "existence_phase": "ADMISSIBLE",
                "blockers": ["proof_not_observed"],
                "continuation_owner": "worker:current",
                "authority_claims": [],
            },
            {
                "task_id": "future",
                "goal_id": "g3",
                "handoff_ref": "handoffs/future.json",
                "temporal_class": "FUTURE",
                "ae_impact": "NONE",
                "ae_rationale": "planning-only task",
                "existence_phase": None,
                "authority_claims": [],
            },
        ]
    }


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_valid_projection():
    result = verify(registry(), projection(), source())
    assert result["valid"] is True
    assert result["registry_generation"] == 21
    assert len(result["registry_hash"]) == 64


def test_rejects_activation_without_proof():
    p = projection()
    p["tasks"][0]["activation_proof_ref"] = None
    assert "activation_proof_missing" in codes(verify(registry(), p, source()))


def test_rejects_missing_ae_classification():
    p = projection()
    p["tasks"][1].pop("ae_impact")
    assert "ae_impact_missing" in codes(verify(registry(), p, source()))


def test_rejects_heartbeat_executor_claim():
    p = projection()
    p["tasks"][1]["authority_claims"] = ["HEARTBEAT_WORKER_EXECUTOR_AUTHORITY"]
    assert "forbidden_authority_claim" in codes(verify(registry(), p, source()))


def test_rejects_future_activation():
    p = projection()
    p["tasks"][2]["ae_impact"] = "CAPABILITY"
    p["tasks"][2]["capability_id"] = "cap:future"
    p["tasks"][2]["existence_phase"] = "ACTIVATED"
    p["tasks"][2]["integration_evidence_refs"] = ["fake"]
    p["tasks"][2]["activation_proof_ref"] = "fake"
    assert "future_activation_forbidden" in codes(verify(registry(), p, source()))


def test_rejects_blocked_current_without_continuation_owner():
    p = projection()
    p["tasks"][1]["continuation_owner"] = None
    assert "blocked_current_without_continuation_owner" in codes(verify(registry(), p, source()))


def test_rejects_bad_source_pin():
    s = source()
    s["source_commit"] = "wrong"
    assert "upstream_policy_pin_invalid" in codes(verify(registry(), projection(), s))
