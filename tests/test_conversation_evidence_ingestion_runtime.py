import importlib.util
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "workers"))
SPEC = importlib.util.spec_from_file_location(
    "conversation_evidence_ingestion_runtime_worker",
    ROOT / "workers" / "conversation_evidence_ingestion_runtime_worker.py",
)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(worker)


def invocation():
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 121,
        "task": {
            "task_id": worker.TASK_ID,
            "claim_id": "CLAIM-SYNTH-001",
            "worker_id": "conversation-evidence-ingestion-custody-worker",
            "worker_instance_id": "worker-instance-synth-001",
            "heartbeat_timing": {"fencing_token": 122},
        },
        "handoff": {
            "execution": {
                "required_capabilities": [worker.CAPABILITY],
                "allowed_paths": ["receipts/conversation-evidence-ingestion/**"],
            }
        },
    }


def test_runtime_worker_requires_fresh_claim_and_fence(monkeypatch):
    value = invocation()
    value["task"]["claim_id"] = None
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(value)))
    assert worker.main() == 6


def test_runtime_worker_completes_only_after_exact_master_records_closure(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    monkeypatch.setattr(worker, "RECEIPT_ROOT", tmp_path / "receipts" / "conversation-evidence-ingestion")
    monkeypatch.setattr(worker, "custody_ingestion", lambda package: {
        "state": "RECORDED",
        "master_records": {
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": "a" * 64,
            "reconstructed_receipt_sha256": "a" * 64,
        },
    })
    stdin = io.StringIO(json.dumps(invocation()))
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    assert worker.main() == 0
    response = json.loads(stdout.getvalue())
    assert response["state"] == "COMPLETED"
    assert response["transition_id"] == "CONVERSATION_EVIDENCE_INGESTED"
    assert response["synthetic_fixture_only"] is True
    assert response["publication_performed"] is False
    assert response["adjudication_performed"] is False
    assert response["master_records"]["state"] == "RECORDED"
    assert response["master_records"]["reconstruction_status"] == "PASS"
    assert response["master_records"]["required_evidence_validation_status"] == "PASS"
    assert response["master_records"]["receipt_sha256"] == response["master_records"]["reconstructed_receipt_sha256"]


def test_runtime_worker_blocks_when_master_records_not_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    monkeypatch.setattr(worker, "RECEIPT_ROOT", tmp_path / "receipts" / "conversation-evidence-ingestion")
    monkeypatch.setattr(worker, "custody_ingestion", lambda package: {
        "state": "BOUNDARY",
        "reason": "MASTER_RECORDS_INGESTION_CUSTODY_NOT_CLOSED",
        "master_records": {"state": "BOUNDARY"},
    })
    stdin = io.StringIO(json.dumps(invocation()))
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    assert worker.main() == 0
    response = json.loads(stdout.getvalue())
    assert response["state"] == "BLOCKED"
    assert response["expected_next_transition"] == "CONVERSATION_EVIDENCE_INGESTED"


def test_canonical_work_request_and_workercoordinator_bindings_exist():
    request = json.loads((ROOT / "control/resident-execution-request.d/canonical-work-conversation-evidence-ingestion-custody-001.json").read_text())
    handoff = json.loads((ROOT / "handoffs/CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001.json").read_text())
    registry = json.loads((ROOT / "control/worker-registry.d/conversation-evidence-ingestion-custody-001.json").read_text())
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/conversation-evidence-ingestion-custody-001.json").read_text())
    assert request["mode"] == "CANONICAL_WORK_EVENT_BOOTSTRAP"
    assert request["task_id"] == worker.TASK_ID
    assert request["second_machine_required"] is False
    assert handoff["activation"]["targeted_execution"]["argv"][-1] == worker.TASK_ID
    assert handoff["activation"]["targeted_execution"]["requires_existing_separated_carrier_reference"] is False
    assert handoff["activation"]["targeted_execution"]["state_triggered_after_canonical_work_ingress"] is True
    assert handoff["continuity"]["master_records_required"] is True
    assert registry["tasks"][0]["state"] == "HANDOFF_READY"
    assert registry["tasks"][0]["admission"]["fresh_fence_required"] is True
    assert adapter["adapters"][0]["command"][-1] == "workers/conversation_evidence_ingestion_runtime_worker.py"


def test_generic_canonical_work_consumer_registers_request_spec():
    source = (ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.legacy.py").read_text()
    assert "CONVERSATION_EVIDENCE_INGESTION_CUSTODY_SPEC" in source
    assert "canonical-work-conversation-evidence-ingestion-custody-001.json" in source
    assert '"task_id": "CONVERSATION-EVIDENCE-INGESTION-CUSTODY-001"' in source
