"""A manifested append that faults part-way resumes exactly once (B-P36q, W4).

A releasing append writes the batch, BATCH_HEAD, the receipt and HEAD. A fault
after the batch (an unindexed batch) or after BATCH_HEAD (a release whose
carrying receipt never landed) used to refuse every later append; an exact
retry of a successful manifested append also refused, because the release it
carried was compared as caller context. The next attempt now indexes the
batch, carries the committed release, and an exact retry returns the
recorded receipt.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batch  # noqa: E402

MANIFEST = {"schema": "test.parent-manifest/v1",
            "receipt_batch": {"release_condition": {"type": "COUNT", "count": 2}}}


def receipt(name: str) -> dict:
    return {"schema": "stegverse.canonical-state-transition-receipt/v1", "transition_id": name,
            "transition_sequence": 1, "subject_or_correlation_id": "b-p36q", "transition_outcome": "OBSERVED",
            "required_evidence_manifest": []}


@pytest.mark.parametrize("fault_at", [1, 2, 3, 4])
def test_a_releasing_append_faulted_at_any_write_resumes_exactly_once(monkeypatch, tmp_path, fault_at):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id,
        "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY"})
    org.aggregate_transition(receipt("A"), parent_manifest=MANIFEST, hb_epoch=4096)
    org.aggregate_transition(receipt("B"), parent_manifest=MANIFEST, hb_epoch=4096)
    original, writes = org.ledger_store.PosixLedgerStore.put, {"n": 0}

    def put(store, key, value):
        writes["n"] += 1
        if writes["n"] == fault_at:
            raise OSError("simulated fault at write " + str(fault_at) + ": " + key)
        return original(store, key, value)

    with mock.patch.object(org.ledger_store.PosixLedgerStore, "put", put), pytest.raises(OSError):
        org.aggregate_transition(receipt("C"), parent_manifest=MANIFEST, hb_epoch=4096)
    first = org.aggregate_transition(receipt("C"), parent_manifest=MANIFEST, hb_epoch=4096)
    again = org.aggregate_transition(receipt("C"), parent_manifest=MANIFEST, hb_epoch=4096)
    assert again["receipt_sha256"] == first["receipt_sha256"]
    assert first["boundary_evidence"]["parent_manifest_released_batch"]["closure_reason"] == "MANIFEST_RELEASE_CONDITION"
    rows = [org.load(p) for p in (tmp_path / "receipts").glob("*.json")]
    sources = sorted(r["source_transition_id"] for r in rows)
    assert sources == ["A", "B", "C"]
    head = org.load(tmp_path / "BATCH_HEAD.json")
    assert head["batch_id"] == first["boundary_evidence"]["parent_manifest_released_batch"]["batch_id"]
    assert len(list((tmp_path / "batches").glob("*.json"))) == 1


def test_an_exact_retry_of_a_releasing_append_returns_the_recorded_receipt(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id,
        "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY"})
    for name in ("A", "B"):
        org.aggregate_transition(receipt(name), parent_manifest=MANIFEST, hb_epoch=4096)
    first = org.aggregate_transition(receipt("C"), parent_manifest=MANIFEST, hb_epoch=4096)
    assert org.aggregate_transition(receipt("C"), parent_manifest=MANIFEST, hb_epoch=4096) == first
