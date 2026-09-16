from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "control/resident-execution-request.d/mir-tvc-provider-roundtrip-001.json"


def test_mir_manifested_request_binds_canonical_resident_workercoordinator_entrypoint():
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert request["schema"] == "stegverse.resident-execution-request/v1"
    assert request["state"] == "REQUESTED"
    assert request["task_id"] == "MIR-TVC-PROVIDER-ROUNDTRIP-001"
    assert request["cosv_profile"] == "task.v1"
    assert request["cosv_task_vector"] == "50000000100000"
    assert request["entrypoint"] == "scripts/refresh_and_execute_resident_task.py"
    assert request["argv"] == ["--task-id", "MIR-TVC-PROVIDER-ROUNDTRIP-001"]
    assert request["provider_request_id"] == "MIR-RUN2-EVENT-001"
    assert request["provider_operation"] == "SUBMIT_EVENT"
    assert request["requires_current_workercoordinator_claim_fence"] is True
    assert request["requires_current_intr_admission"] is True
    assert request["requires_existing_tvc_vault_broker"] is True
    assert request["same_transaction_custody_required"] is True
    assert request["provider_credential_material_allowed"] is False
    assert request["github_token_required"] is False
    assert request["github_token_runtime_authority"] == "NONE"
    assert request["heartbeat_grants_execution_authority"] is False
    assert request["request_granted_authority"] is False
    assert request["second_machine_required"] is False
    assert request["authority_effect"] == "NONE_REQUEST_ONLY"
