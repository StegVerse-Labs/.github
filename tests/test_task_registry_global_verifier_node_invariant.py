from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "task-registry-global-invariants.json"
EVALUATOR = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
SIGNER_RECORD = ROOT / "data" / "canonical-task-records" / "TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001.json"


def run_checkin(task_id: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(EVALUATOR)],
        input=json.dumps({"task_id": task_id, "checkin_context": {}}),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=True,
    )
    return json.loads(proc.stdout)


def test_global_policy_declares_kv_skap_only_user_verifier_and_interchangeable_nodes():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    inv = policy["invariants"]
    assert policy["applies_to"] == "ALL_CANONICAL_TASKS_EXISTING_AND_NEW"
    assert inv["user_verification_authority"] == "KV/SKAP Vault"
    assert inv["user_verification_authority_exclusive"] is True
    assert inv["stegos_device_role"] == "INTERCHANGEABLE_TRANSPORT_NODE"
    assert inv["device_user_verifier_authority"] == "NONE"
    assert inv["node_user_verifier_authority"] == "NONE"
    assert inv["transport_user_verifier_authority"] == "NONE"
    assert inv["secure_enclave_user_verifier_authority"] == "NONE"


def test_existing_registered_task_checkin_receives_global_invariant():
    result = run_checkin("TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001")
    inv = result["registry_global_invariants"]["invariants"]
    assert inv["user_verification_authority"] == "KV/SKAP Vault"
    assert inv["stegos_device_role"] == "INTERCHANGEABLE_TRANSPORT_NODE"


def test_not_yet_registered_task_checkin_receives_same_invariant_before_registration():
    result = run_checkin("FUTURE-TASK-NOT-REGISTERED-TEST")
    assert result["disposition"] == "STOP_NOT_REGISTERED"
    inv = result["registry_global_invariants"]["invariants"]
    assert inv["user_verification_authority"] == "KV/SKAP Vault"
    assert inv["device_user_verifier_authority"] == "NONE"


def test_active_signer_task_no_longer_requires_device_or_channel_user_verifier():
    record = json.loads(SIGNER_RECORD.read_text(encoding="utf-8"))
    truth = record["current_truth"]
    assert truth["user_verification_authority"] == "KV/SKAP Vault"
    assert truth["stegos_device_role"] == "INTERCHANGEABLE_TRANSPORT_NODE"
    assert truth["device_user_verifier_authority"] == "NONE"
    assert truth["node_user_verifier_authority"] == "NONE"
    assert truth["transport_user_verifier_authority"] == "NONE"
    assert truth["signed_intr_transport_is_user_verifier"] is False
    assert truth["signed_intr_transport_required_as_user_verifier"] is False
    blockers = set(record["blockers"])
    assert "IPHONE_AUTHENTICATED_PLATFORM_REQUEST_VERIFIER_NOT_YET_IMPLEMENTED" not in blockers
    assert "PRODUCTION_CHANNEL_IDENTITY_NOT_YET_MATERIALIZED_AND_BOUND" not in blockers
