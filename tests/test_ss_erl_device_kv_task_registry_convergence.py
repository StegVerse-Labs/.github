from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER_ID = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
ERL_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
ROUNDTRIP_ID = "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
EVALUATOR = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"


def test_existing_device_kv_owner_is_registered_without_runtime_upgrade():
    record = json.loads((ROOT / f"data/canonical-task-records/{OWNER_ID}.json").read_text())
    assert record["schema"] == "stegverse.canonical-task-record/v1"
    assert record["task_id"] == OWNER_ID
    assert record["cosv_task_vector"] == "50000000101000"
    assert record["coordination_state"] == "ACTIVE"
    assert record["checkout_state"] == "HANDOFF_READY_RUNTIME_PROOF_PENDING"
    assert record["completion"]["claimed"] is False
    assert record["completion"]["validated"] is False
    assert record["completion"]["activation_proof_complete"] is False
    assert record["authority_model"]["task_registry_mints_execution_authority"] is False
    assert record["authority_model"]["worker_claim_authority"] == "WORKERCOORDINATOR"
    assert record["authority_model"]["device_user_verification_authority"] == "NONE"
    assert record["authority_model"]["github_runtime_authority"] == "NONE"


def test_task_registry_exposes_current_convergence_instead_of_minting_continue(tmp_path):
    env = dict(os.environ)
    env["STEGVERSE_TASK_REGISTRY_EVENT_LEDGER"] = str(tmp_path / "events.jsonl")
    payload = {
        "task_id": OWNER_ID,
        "checkin_context": {
            "checked_in_at": "2026-09-13T16:15:00Z",
            "first_unresolved_predicate": "CURRENT_USER_IPHONE_PORTABLE_WORKERCOORDINATOR_CHECKOUT_OBSERVED",
            "components_under_mutation": ["runtime_observation:SHWP-DEVICE-KV-INTR-OBSERVATION-001"],
        },
    }
    proc = subprocess.run(
        [sys.executable, str(EVALUATOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    out = json.loads(proc.stdout)
    assert out["schema"] == "stegverse.task-registry-checkin-disposition/v1"
    assert out["task_id"] == OWNER_ID
    assert out["authority_effect"] == "NONE"
    assert out["disposition"] == "COORDINATE_CONVERGENCE"
    collision_ids = {row["task_id"] for row in out["collision_candidates"]}
    assert ERL_ID in collision_ids
    assert ROUNDTRIP_ID in collision_ids
    assert out["hard_collision_task_ids"] == []


def test_roundtrip_collision_is_adjacency_not_evidence_equivalence():
    owner = json.loads((ROOT / f"data/canonical-task-records/{OWNER_ID}.json").read_text())
    roundtrip = json.loads((ROOT / f"data/canonical-task-records/{ROUNDTRIP_ID}.json").read_text())
    erl = json.loads((ROOT / f"data/canonical-task-records/{ERL_ID}.json").read_text())
    assert OWNER_ID in roundtrip["adjacent_task_refs"]
    assert ROUNDTRIP_ID not in owner.get("parent_task_id", "")
    assert erl["completion"]["activation_proof_complete"] is False
    assert "AUTHENTIC_THREE_HOP_RECEIPT_CHAIN_OBSERVED" in erl["expected_evidence_predicates"]
    assert roundtrip["completion"]["activation_proof_complete"] is False or roundtrip["completion"].get("claimed") is False
