from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batch  # noqa: E402


def receipt(name: str) -> dict:
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": name,
        "transition_sequence": 1,
        "subject_or_correlation_id": "test-worker",
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [],
    }


def append(monkeypatch, root: Path, name: str) -> tuple[dict, dict]:
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(root))
    source = receipt(name)
    return source, org.aggregate_transition(source)


def test_close_and_verify_two_contiguous_batches(monkeypatch, tmp_path):
    source1, first = append(monkeypatch, tmp_path, "CLAIM")
    source2, second = append(monkeypatch, tmp_path, "WORK")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    assert closed["contiguous_receipt_range"] == [1, 2]
    assert closed["ordered_receipt_hashes"] == [first["receipt_sha256"], second["receipt_sha256"]]
    assert closed["acknowledgement_state"] == batch.ACK
    assert closed["required_evidence_scope"] == "ORGANIZATION_BOUNDARY_REFERENCES_ONLY"
    assert batch.verify_batch(tmp_path, closed["batch_id"])["organization_chain"] == "PASS"
    assert batch.verify_batch(
        tmp_path, closed["batch_id"],
        source_receipts={org.sha(source1): source1, org.sha(source2): source2},
    )["source_reconstruction"] == "SOURCE_DIGESTS_PASS_REQUIRED_EVIDENCE_BYTES_NOT_EVALUATED"
    assert batch.close_batch("TASK_CLOSURE", root=tmp_path) == closed
    _, third = append(monkeypatch, tmp_path, "EXPIRE")
    after = batch.close_batch("WORKER_EXPIRY", root=tmp_path)
    assert after["contiguous_receipt_range"] == [3, 3]
    assert after["previous_batch_commitment"] == closed["batch_id"]
    assert after["cross_boundary_predecessor_refs"] == [second["receipt_sha256"]]
    assert after["ordered_receipt_hashes"] == [third["receipt_sha256"]]
    assert batch.verify_batch(tmp_path, after["batch_id"])["state"] == "PASS"
    assert len(list((tmp_path / "batches").glob("*.json"))) == 2


def test_missing_or_tampered_individual_receipt_fails_closed(monkeypatch, tmp_path):
    _, first = append(monkeypatch, tmp_path, "CLAIM")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    path = tmp_path / "receipts" / (first["receipt_sha256"][7:] + ".json")
    saved = path.read_text()
    path.write_text(saved.replace("CLAIM", "ALTERED"))
    with pytest.raises(ValueError, match="hash mismatch"):
        batch.verify_batch(tmp_path, closed["batch_id"])
    with pytest.raises(ValueError, match="hash mismatch"):
        batch.close_batch("TASK_CLOSURE", root=tmp_path)
    path.unlink()
    with pytest.raises(ValueError, match="missing"):
        batch.verify_batch(tmp_path, closed["batch_id"])


def test_broken_predecessor_chain_cannot_close(monkeypatch, tmp_path):
    _, first = append(monkeypatch, tmp_path, "CLAIM")
    _, second = append(monkeypatch, tmp_path, "EXECUTION")
    second_path = tmp_path / "receipts" / (second["receipt_sha256"][7:] + ".json")
    altered = json.loads(second_path.read_text())
    altered["previous_receipt_sha256"] = None
    altered_body = dict(altered)
    altered_body.pop("receipt_sha256")
    # An otherwise internally well-hashed forged immutable receipt is still
    # rejected because HEAD and predecessor linkage disagree.
    altered["receipt_sha256"] = org.sha(altered_body)
    forged = tmp_path / "receipts" / (altered["receipt_sha256"][7:] + ".json")
    second_path.unlink()
    forged.write_text(json.dumps(altered))
    head_path = tmp_path / "HEAD.json"
    head = json.loads(head_path.read_text())
    head["receipt_sha256"] = altered["receipt_sha256"]
    head["receipt_path"] = str(forged)
    head_path.write_text(json.dumps(head))
    with pytest.raises(ValueError, match="orphaned or omitted"):
        batch.close_batch("TASK_CLOSURE", root=tmp_path)


def test_invalid_source_or_changed_closure_refused(monkeypatch, tmp_path):
    source, _ = append(monkeypatch, tmp_path, "CLAIM")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    with pytest.raises(ValueError, match="conflicting batch closure"):
        batch.close_batch("WORKER_EXPIRY", root=tmp_path)
    with pytest.raises(ValueError, match="source transition receipt missing or invalid"):
        batch.verify_batch(tmp_path, closed["batch_id"], source_receipts={})
    altered = dict(source, transition_id="OTHER")
    with pytest.raises(ValueError, match="source transition receipt missing or invalid"):
        batch.verify_batch(
            tmp_path, closed["batch_id"],
            source_receipts={org.sha(source): altered},
        )


def test_batch_commitment_tamper_and_head_tamper_fail_closed(monkeypatch, tmp_path):
    append(monkeypatch, tmp_path, "CLAIM")
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    path = tmp_path / "batches" / (closed["batch_id"][7:] + ".json")
    tampered = dict(closed, closure_reason="WORKER_EXPIRY")
    path.write_text(json.dumps(tampered))
    with pytest.raises(ValueError, match="organization batch hash mismatch"):
        batch.verify_batch(tmp_path, closed["batch_id"])
    path.write_text(json.dumps(closed))
    head_path = tmp_path / "BATCH_HEAD.json"
    head = json.loads(head_path.read_text())
    head["last_org_receipt_sha256"] = "sha256:" + "0" * 64
    head_path.write_text(json.dumps(head))
    with pytest.raises(ValueError, match="organization batch HEAD mismatch"):
        batch.close_batch("TASK_CLOSURE", root=tmp_path)


def test_empty_close_invalid_reason_and_missing_custody_proof(monkeypatch, tmp_path):
    append(monkeypatch, tmp_path, "CLAIM")
    with pytest.raises(ValueError, match="unsupported"):
        batch.close_batch("UNREVIEWED", root=tmp_path)
    closed = batch.close_batch("TASK_CLOSURE", root=tmp_path)
    assert batch.verify_batch(tmp_path, closed["batch_id"])["master_records_acknowledgement"] == "NOT_ESTABLISHED"
    assert "master_record_ref" not in closed
    assert closed["authority_effect"] == "NONE_BATCH_CUSTODY_PROPOSAL_ONLY"
