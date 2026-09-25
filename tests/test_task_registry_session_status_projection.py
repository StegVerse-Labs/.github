"""Regression tests for the existing Task Registry session status projection.

Source fixtures prove deterministic decisions only. They do not attest an
authentic ChatGPT session or establish resident runtime enforcement.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKIN = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
LEDGER = ROOT / "scripts" / "task_registry_checkin_event_history.py"
CLOSE = ROOT / "scripts" / "materialize_task_session_close.py"


def ledger_event(path: Path, *, task: str, session: str, kind: str, moment: str):
    payload = {
        "event_type": kind,
        "task_id": task,
        "session_id": session,
        "event_at": moment,
        "context": {
            "repository": "StegVerse-Labs/.github",
            "branch": "shared-branch",
            "repositories": ["StegVerse-Labs/.github"],
            "components": ["session-close"],
        },
        "registry_disposition": {
            "schema": "stegverse.task-registry-checkin-disposition/v1",
            "task_id": task,
            "disposition": "CONTINUE",
            "authority_effect": "NONE",
        },
    }
    result = subprocess.run(
        [sys.executable, str(LEDGER), "--ledger", str(path)],
        input=json.dumps(payload), text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def checkin(path: Path, *, session: str, observed_generation=None, task="TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001"):
    payload = {
        "task_id": task,
        "checkin_context": {
            "session_id": session,
            "checked_in_at": "2026-09-25T20:00:00Z",
            "repository": "StegVerse-Labs/.github",
            "branch": "shared-branch",
            "repositories_under_mutation": ["StegVerse-Labs/.github"],
            "components_under_mutation": ["session-close"],
        },
    }
    if observed_generation is not None:
        payload["observed_registry_generation"] = observed_generation
    env = dict(os.environ, STEGVERSE_TASK_REGISTRY_EVENT_LEDGER=str(path))
    result = subprocess.run(
        [sys.executable, str(CHECKIN)],
        input=json.dumps(payload), text=True, capture_output=True, env=env,
        check=True,
    )
    return json.loads(result.stdout)


def test_active_same_task_session_is_candidate_not_falsely_attested(tmp_path):
    ledger = tmp_path / "events.jsonl"
    first = ledger_event(
        ledger, task="TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001",
        session="separate-session", kind="CHECK_IN", moment="2026-09-25T19:55:00Z",
    )
    result = checkin(ledger, session="arriving-session")
    status = result["session_status_projection"]
    assert status["duplicate"] == "UNVERIFIED"
    assert status["collision"] == "CONJOIN_REQUIRED"
    assert status["evidence_class"] == "HASH_CHAIN_VALIDATED_SESSION_ORIGIN_UNVERIFIED"
    assert status["same_task_active_session_candidates"][0]["event_sha256"] == first["event_sha256"]
    assert status["same_task_active_session_candidates"][0]["session_origin_attested"] is False
    assert status["authority_effect"] == "NONE"
    # Existing disposition and predecessor-linked original event remain intact.
    assert result["disposition"] in {"CONTINUE", "COORDINATE_CONVERGENCE", "STOP_COLLISION"}
    assert result["checkin_event_sha256"].startswith("sha256:")


def test_returned_session_does_not_become_active_duplicate(tmp_path):
    ledger = tmp_path / "events.jsonl"
    for kind in ("CHECK_IN", "RETURNED"):
        ledger_event(
            ledger, task="TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001",
            session="previous-session", kind=kind, moment="2026-09-25T19:55:00Z",
        )
    result = checkin(ledger, session="arriving-session")
    assert result["session_status_projection"]["same_task_active_session_candidates"] == []
    assert result["session_status_projection"]["duplicate"] == "UNVERIFIED"


def test_foreign_checked_out_collision_requires_owner_conjunction(tmp_path):
    result = checkin(tmp_path / "events.jsonl", session="arriving-session")
    status = result["session_status_projection"]
    if result["hard_collision_task_ids"]:
        assert status["collision"] == "CONJOIN_REQUIRED"
        assert status["colliding_task_ids"] == result["hard_collision_task_ids"]
    else:
        assert status["collision"] != "CONJOIN_REQUIRED"
    assert status["source_disposition"] == result["disposition"]


def test_stale_generation_preserves_existing_stop_and_unknown_status(tmp_path):
    registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text())
    result = checkin(
        tmp_path / "events.jsonl", session="stale-session",
        observed_generation=registry["generation"] - 1,
    )
    assert result["disposition"] == "STOP_STALE_COORDINATION"
    assert result["session_status_projection"]["duplicate"] == "UNVERIFIED"
    assert result["session_status_projection"]["authority_effect"] == "NONE"
    assert result["write_pr_merge_handoff_claim_admissible"] is False


def test_close_carries_exact_status_after_existing_return_receipt(tmp_path):
    ledger = tmp_path / "events.jsonl"
    incoming = {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": "TASK-A", "disposition": "COORDINATE_CONVERGENCE",
        "authority_effect": "NONE",
        "session_status_projection": {
            "schema": "stegverse.task-registry-session-status-projection/v1",
            "duplicate": "UNVERIFIED", "collision": "REVIEW_REQUIRED",
            "source_disposition": "COORDINATE_CONVERGENCE",
            "evidence_class": "REGISTRY_CHECKIN_PROJECTION_NOT_SESSION_ORIGIN_ATTESTATION",
            "authority_effect": "NONE",
        },
    }
    proc = subprocess.run([
        sys.executable, str(CLOSE), "--task-id", "TASK-A",
        "--session-id", "s-a", "--actor-kind", "NON_AI_SYSTEM_COORDINATOR",
        "--ledger", str(ledger),
    ], input=json.dumps(incoming), text=True, capture_output=True, check=True)
    result = json.loads(proc.stdout)
    assert result["session_status_projection"] == incoming["session_status_projection"]
    assert result["footer_handoff_emission_admissible"] is True
    assert result["required_pre_footer_return_event_sha256"] == result["return_receipt"]["event_sha256"]
    assert result["authority_effect"] == "NONE"


def test_invalid_status_cannot_append_session_return(tmp_path):
    ledger = tmp_path / "events.jsonl"
    invalid = {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": "TASK-A", "disposition": "CONTINUE", "authority_effect": "NONE",
        "session_status_projection": {
            "schema": "stegverse.task-registry-session-status-projection/v1",
            "duplicate": "CONFIRMED", "collision": "UNVERIFIED",
            "source_disposition": "DENY", "authority_effect": "NONE",
        },
    }
    proc = subprocess.run([
        sys.executable, str(CLOSE), "--task-id", "TASK-A",
        "--session-id", "s-a", "--actor-kind", "NON_AI_SYSTEM_COORDINATOR",
        "--ledger", str(ledger),
    ], input=json.dumps(invalid), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()

if __name__ == "__main__":
    # Existing stable Cross-Task CI uses stdlib unittest without an external
    # pytest installation. Run these same fixture-style tests directly there.
    from tempfile import TemporaryDirectory

    cases = [
        test_active_same_task_session_is_candidate_not_falsely_attested,
        test_returned_session_does_not_become_active_duplicate,
        test_foreign_checked_out_collision_requires_owner_conjunction,
        test_stale_generation_preserves_existing_stop_and_unknown_status,
        test_close_carries_exact_status_after_existing_return_receipt,
        test_invalid_status_cannot_append_session_return,
    ]
    with TemporaryDirectory(prefix="stegverse-session-status-") as base:
        for case in cases:
            root = Path(base) / case.__name__
            root.mkdir(parents=True)
            case(root)
            print(f"PASS {case.__name__}")
    print(f"PASS session-status focus: {len(cases)} cases")
