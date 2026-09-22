from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "mir_tvc_provider_roundtrip_worker.py"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "mir-tvc-provider-roundtrip-001.json"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "mir-tvc-provider-roundtrip-001.json"
REGISTRY = ROOT / "control" / "worker-registry.d" / "mir-tvc-provider-roundtrip-001.json"


def load_worker():
    spec = importlib.util.spec_from_file_location("mir_worker", WORKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invocation(fence=41):
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": "MIR-TVC-PROVIDER-ROUNDTRIP-001",
            "state": "ACTIVE",
            "claim_id": f"CLAIM-MIR-G{fence}",
            "heartbeat_timing": {"fencing_token": fence},
        },
        "scope": {"claim_id": f"CLAIM-MIR-G{fence}", "fencing_token": fence},
    }


def test_exact_mir_request_is_non_secret_and_admitted_shape():
    worker = load_worker()
    request = worker._request()
    assert request["secret_ref"] == "vault://tvc/providers/mir/api-key"
    assert request["export_allowed"] is False
    assert request["return_secret_material"] is False
    operation = request["operation"]
    assert operation["request_id"] == "MIR-RUN2-EVENT-001"
    assert operation["provider_operation"] == "SUBMIT_EVENT"
    assert operation["path"] == "/v1/events"
    assert operation["method"] == "POST"
    assert operation["body"] == {
        "userExternalId": "StegVerse-org/StegVerse-SDK",
        "eventType": "mir.agent.action.completed",
        "occurredAt": "2026-09-12T19:11:41Z",
    }
    assert operation["consumer_credential_access"] is False
    assert operation["github_actions_credential_access"] is False
    assert operation["credential_plaintext_returned"] is False
    assert operation["wallet_contacted"] is False
    assert operation["signed"] is False
    assert operation["broadcast"] is False
    lease = request["lease_receipt"]
    assert lease["secret_values_exported"] is False
    assert lease["protected_values_exposed"] is False
    assert lease["authority_granted"] is False
    intr = worker._intr_request_payload(request)
    assert intr["schema"] == "stegverse.external-provider.operation-request/v1"
    assert intr["provider"] == "mir"
    assert intr["consumer"] == "StegVerse-org/StegVerse-SDK"
    assert intr["request_id"] == "MIR-RUN2-EVENT-001"
    assert intr["request_hash"].startswith("sha256:")
    assert intr["lease_ref"].startswith("sha256:")
    assert "secret_ref" not in intr


def test_workercoordinator_binding_uses_existing_authority_planes_only():
    resident = json.loads(REQUEST.read_text())
    adapter = json.loads(ADAPTER.read_text())
    registry = json.loads(REGISTRY.read_text())
    assert resident["state"] == "REQUESTED"
    assert resident["task_id"] == "MIR-TVC-PROVIDER-ROUNDTRIP-001"
    assert resident["requires_current_workercoordinator_claim_fence"] is True
    assert resident["requires_current_intr_admission"] is True
    assert resident["requires_existing_tvc_vault_broker"] is True
    assert resident["github_token_runtime_authority"] == "NONE"
    assert resident["second_machine_required"] is False
    item = adapter["adapters"][0]
    assert item["command"] == ["python", "workers/mir_tvc_provider_roundtrip_worker.py"]
    for key in (
        "STEGVERSE_TVC_ROOT",
        "STEGVERSE_STEGOS_ROOT",
        "STEGVERSE_REPO_ROOTS_JSON",
        "STEGVERSE_HEARTBEAT_ROOT",
        "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET",
    ):
        assert key in item["env_allowlist"]
    task = registry["tasks"][0]
    assert task["state"] == "HANDOFF_READY"
    assert task["executor_binding"] == "AUTHORIZED"
    assert task["admission"]["fresh_fence_required"] is True
    assert registry["authority_effect"] == "NONE_REGISTRATION_ONLY"


def test_fail_closed_execution_is_retained_on_the_manifested_receipt_ref(tmp_path):
    worker = load_worker()
    receipt = worker._retain_failure(tmp_path, invocation(), RuntimeError("synthetic boundary"))
    retained = json.loads((tmp_path / worker.RECEIPT_REF).read_text())
    assert retained == receipt
    assert retained["state"] == "FAIL_CLOSED_EXECUTION_RECEIPT"
    assert retained["request_id"] == "MIR-RUN2-EVENT-001"
    assert retained["provider_operation"] == "SUBMIT_EVENT"
    assert retained["provider_operation_completed"] is False
    assert retained["provider_operation_outcome_known"] is True
    assert retained["allow_operation_result_observed"] is False
    assert retained["use_receipt_observed"] is False
    assert retained["claim_id"] == "CLAIM-MIR-G41"
    assert retained["fencing_token"] == 41
    assert retained["intr_admission_required"] is True
    assert retained["master_records_custody_required"] is True
    assert retained["credential_material_retained"] is False
    assert retained["secret_values_exported"] is False
    assert retained["protected_values_exposed"] is False
    assert retained["authority_effect"] == "NONE_FAIL_CLOSED_EXECUTION_EVIDENCE_ONLY"


def test_unknown_provider_outcome_forbids_blind_retry(tmp_path):
    worker = load_worker()
    task = worker._validate_invocation(invocation(9))
    lane = {
        "intent": {"protocol": "InTr"},
        "receipts": [{"receipt_hash": "sha256:" + "a" * 64}],
        "transport_result": {"state": "TRANSPORT_COMPLETE", "component_id": worker.INTR_COMPONENT},
    }
    retained = worker._unknown_provider_outcome(tmp_path, task, lane, TimeoutError("provider response unavailable"))
    assert retained["state"] == "FAIL_CLOSED_PROVIDER_OPERATION_OUTCOME_UNKNOWN"
    assert retained["provider_operation_outcome_known"] is False
    assert retained["provider_operation_retry_allowed"] is False
    assert retained["blind_consequence_retry_allowed"] is False
    assert retained["intr_transport"]["component_id"] == "RTC-INTERLOCK-INTR-TRANSPORT-008"


def test_completed_provider_consequence_is_not_overwritten_as_pre_execution_failure(tmp_path):
    worker = load_worker()
    completed = {
        "schema": "stegverse.mir-tvc-provider-roundtrip-receipt/v1",
        "state": "PROVIDER_OPERATION_COMPLETED_INTR_RESPONSE_PENDING",
        "goal_task_id": worker.TASK_ID,
        "request_id": worker.REQUEST_ID,
        "claim_id": "CLAIM-MIR-G12",
        "fencing_token": 12,
        "provider_operation": "SUBMIT_EVENT",
        "provider_operation_completed": True,
        "provider_operation_outcome_known": True,
        "provider_operation_result": {"decision": "ALLOW_OPERATION_RESULT", "use_receipt": {}},
        "allow_operation_result_observed": True,
        "use_receipt_observed": True,
        "credential_material_retained": False,
        "secret_values_exported": False,
        "protected_values_exposed": False,
    }
    worker._write_receipt(tmp_path, completed)
    retained = worker._retain_failure(tmp_path, invocation(13), RuntimeError("local response transport failure"))
    assert retained["provider_operation_completed"] is True
    assert retained["state"] == "FAIL_CLOSED_POST_PROVIDER_OPERATION_RECEIPT"
    assert retained["provider_operation_retry_allowed"] is False


def test_generic_intr_identity_is_sdk_to_tvc_and_reversed_on_return():
    worker = load_worker()

    class FakeTransport:
        @staticmethod
        def sha256_uri(value):
            return worker._sha(value)
        @staticmethod
        def build_transport_intent(**kwargs):
            return {
                "protocol": "InTr",
                "operation_id": kwargs["operation_id"],
                "payload_hash": kwargs["payload_hash"],
                "prior_transport_receipt_hash": kwargs.get("prior_transport_receipt_hash"),
                "source": {"boundary": kwargs["source_boundary"], "subsystem": kwargs["source_subsystem"]},
                "destination": {"boundary": kwargs["destination_boundary"], "subsystem": kwargs["destination_subsystem"]},
            }
        @staticmethod
        def validate_transport_intent(intent):
            return None

    request_intent, _ = worker._prepare_intr_request(FakeTransport, worker._request())
    assert request_intent["source"] == {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegVerse-org/StegVerse-SDK"}
    assert request_intent["destination"] == {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "TVC:ProviderOperationBroker"}
