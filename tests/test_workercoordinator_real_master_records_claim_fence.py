from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator
from workers.canonical_state_transition_custody import reconstruct_state_receipt

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"


def test_workercoordinator_claim_fence_closes_through_real_master_records() -> None:
    mr_root_raw = os.environ.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "")
    db_raw = os.environ.get("MASTER_RECORDS_DB", "")
    assert mr_root_raw, "real Master Records orchestration root is required"
    assert db_raw, "durable Master Records test DB is required"
    mr_root = Path(mr_root_raw).resolve()
    db = Path(db_raw).resolve()
    assert (mr_root / "services/master_records_custody_api.py").is_file()
    assert (mr_root / "services/canonical_state_transition_custody.py").is_file()
    assert db.is_absolute()
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()

    env = {
        "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(mr_root),
        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": str(mr_root),
        "MASTER_RECORDS_DB": str(db),
        "MASTER_RECORDS_RECEIPT_KEY": "test-only-workercoordinator-claim-fence-key",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
    }
    runtime = WorkerCoordinator(ROOT, adapters={})
    claim_id = TASK_ID + "-G42"
    record = {
        "schema": "stegverse.worker-assignment-record/v1",
        "task_id": TASK_ID,
        "worker_id": "stegagents-governed-runtime-worker",
        "worker_instance_id": "stegagents-governed-runtime-worker-G42",
        "claim_id": claim_id,
        "fencing_token": 42,
        "assignment_source": "TEST_ONLY_EXISTING_WORKERCOORDINATOR_PATH",
        "authority_effect": "NONE_TEST_EVIDENCE_ONLY",
    }
    task = {
        "task_id": TASK_ID,
        "last_checkpoint_ref": "docs/SDK_TT_PURPOSE_BOUND_WORKER_RUNTIME_PROOF_MIRROR_HANDOFF.md",
    }
    trigger = {
        "packet_id": "TEST-ONLY-WORKERCOORDINATOR-CLAIM-FENCE-001",
        "source": "INDEPENDENT_TASK_CONTROL",
    }

    with mock.patch.dict(os.environ, env, clear=False):
        closed = runtime._custody_assignment_transition(
            task=task,
            trigger=trigger,
            record=record,
            claim_id=claim_id,
            fencing_token=42,
            worker_instance_id="stegagents-governed-runtime-worker-G42",
        )

        assert closed["transition_id"] == "WORKERCOORDINATOR_CLAIM_FENCE_BOUND"
        assert closed["state"] == "RECORDED"
        assert closed["reconstruction_status"] == "PASS"
        assert closed["required_evidence_validation_status"] == "PASS"
        assert isinstance(closed["receipt_sha256"], str) and len(closed["receipt_sha256"]) == 64
        assert closed["receipt_sha256"] == closed["reconstructed_receipt_sha256"]
        assert closed["master_record_ref"] == (
            "master-record:state-transition:sha256:" + closed["receipt_sha256"]
        )

        reconstructed = reconstruct_state_receipt(closed["receipt_sha256"])

    assert reconstructed["state"] == "PASS"
    assert reconstructed["receipt_sha256"] == closed["receipt_sha256"]
    assert reconstructed["reconstructed_receipt_sha256"] == closed["receipt_sha256"]
    assert reconstructed["required_evidence_validation_status"] == "PASS"
    assert reconstructed["master_record_ref"] == closed["master_record_ref"]
    assert reconstructed["receipt"]["transition_id"] == "WORKERCOORDINATOR_CLAIM_FENCE_BOUND"
    assert reconstructed["receipt"]["subject_or_correlation_id"] == TASK_ID
    manifest = reconstructed["receipt"]["required_evidence_manifest"]
    assert len(manifest) == 1
    assert manifest[0]["evidence_type"] == "WORKERCOORDINATOR_CLAIM_FENCE_ASSIGNMENT"
    assert manifest[0]["content"] == record
