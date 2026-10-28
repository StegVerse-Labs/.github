"""Sealed-receipt parity for batch custody and custody readback (#3012, ORGANIZATION-BATCH-CUSTODY-REPLAY-001).

organization_ledger_ingest appends a sealed test receipt through the governed writer. These tests put such a row on a
local POSIX ledger the same way (org._append_locked with the sealed binding) and require organization_batch_custody and
organization_custody_readback to accept it, and to refuse a forged or unsealed retained receipt with six fields.
Source-only: no network, no clock-derived epoch."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batches  # noqa: E402
import organization_custody_readback as readback  # noqa: E402
import organization_ledger_ingest as ing  # noqa: E402

CANONICAL = "canonical_transition_results"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def sealed(body):
    body = {k: v for k, v in body.items() if k != "receipt_sha256"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return body | {"receipt_sha256": "sha256:" + hashlib.sha256(canon).hexdigest()}


def receipt(**over):
    return sealed({"schema": batches.SEALED_TEST_RECEIPT_SCHEMA, "receipt_kind": "TVC_LABS_CONFORMANCE_TEST_RECEIPT",
                   "suite": "TVC_LABS_CONFORMANCE", "repository": "StegVerse-Labs/TVC", "head_sha": "c" * 40,
                   "disposition": "ALLOW", "refusals": []} | over)


def append_sealed(store, value):
    context = {"org_transition_class": ing.SEALED_CLASS, "predecessor_org_state_sha256": None,
               "successor_org_state_sha256": None, "boundary_evidence": {"operation": ing.SEALED},
               "authority_effect": "NONE"}
    with store.exclusive():
        return org._append_locked(dict(value), ing.sealed_source(value), store, hb_epoch=4096, **context)


@pytest.fixture
def ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    return tmp_path, org.organization_store(tmp_path)


def assert_six(refused: batches.SealedSourceRefused, code: str):
    out = refused.refusal()
    assert out["disposition"] == "FAIL_CLOSED" and out["failure_code"] == code
    assert all(isinstance(out[k], str) and out[k] for k in SIX)
    assert out["consequence_committed"] is False


def test_the_binding_is_identical_to_the_ingest_route():
    good = receipt()
    assert batches.sealed_source(good) == ing.sealed_source(good)
    assert batches.verify_any_source(good) == ing.verify_any_source(org, good)
    assert (batches.SEALED_TRANSITION_CLASS, batches.SEALED_OPERATION) == (ing.SEALED_CLASS, ing.SEALED)


@pytest.mark.parametrize("value,code", [
    (dict(receipt(), head_sha="e" * 40), "SEALED_SOURCE_SEAL_MISMATCH"),  # forged: body changed after the seal
    ({k: v for k, v in receipt().items() if k != "receipt_sha256"}, "SEALED_SOURCE_SEAL_MISMATCH"),  # unsealed
    (receipt(head_sha=""), "SEALED_SOURCE_IDENTITY_INVALID"),
    (dict(receipt(), schema="stegverse.repo-transition-receipt/v1"), None),  # not sealed: org.verify_source refuses
])
def test_a_forged_or_unsealed_receipt_is_refused_fail_closed(value, code):
    with pytest.raises(ValueError) as caught:
        batches.verify_any_source(value)
    if code:
        assert isinstance(caught.value, batches.SealedSourceRefused)
        assert_six(caught.value, code)
    with pytest.raises(batches.SealedSourceRefused) as direct:
        batches.sealed_source(value)
    assert_six(direct.value, code or "SEALED_SOURCE_SCHEMA_MISMATCH")


def test_a_valid_sealed_receipt_is_accepted_by_batch_custody_and_readback(ledger):
    root, store = ledger
    good = receipt()
    row = append_sealed(store, good)
    assert row["source_receipt_schema"] == batches.SEALED_TEST_RECEIPT_SCHEMA
    got, retained = batches.verified_organization_source_receipt(
        root, row["receipt_sha256"], state_receipt_sha256=good["receipt_sha256"],
        expected_transition_id=batches.sealed_source(good)["source_transition_id"])
    assert got["receipt_sha256"] == row["receipt_sha256"] and retained == good
    ids = (batches.sealed_source(good)["source_transition_id"],)
    result = readback.readback(root, correlation_ids=ids, include_exact=True)
    assert result["state"] == "VERIFIED_LOCAL_READBACK" and result["match_count"] == 1
    # Canonical-only Master Records reconciliation: a sealed source is never queried.
    queried = []
    reconciled = readback.reconcile_master_records(result, get_json=lambda path, params: queried.append(path) or {})
    assert queried == []
    assert [t["state"] for t in reconciled[CANONICAL]] == ["SEALED_SOURCE_NOT_DIRECT_CANONICAL_CUSTODY"]
    closed = batches.close_batch("TASK_CLOSURE", root=root)
    exported = batches.export_batch(root, closed["batch_id"])
    assert exported["source_receipts"] == [good]
    assert readback.readback(root, correlation_ids=ids)["batch_chain"] == "PASS"


def test_a_forged_retained_sealed_receipt_is_refused_by_every_reader(ledger):
    root, store = ledger
    good = receipt()
    row = append_sealed(store, good)
    closed = batches.close_batch("TASK_CLOSURE", root=root)
    # Replace the retained bytes with a forgery that keeps the claimed digest.
    path = root / org.ledger_store.source_key(good["receipt_sha256"])
    path.write_text(json.dumps(dict(good, disposition="DENY")), encoding="utf-8")
    with pytest.raises(batches.OrganizationReceiptRefused) as caught:
        batches.verified_organization_source_receipt(root, row["receipt_sha256"],
                                                     state_receipt_sha256=good["receipt_sha256"])
    assert caught.value.failed_predicate == "ORGANIZATION_SOURCE_RECEIPT_INVALID"
    assert "SEALED_SOURCE_SEAL_MISMATCH" in caught.value.detail
    with pytest.raises(batches.SealedSourceRefused) as exported:
        batches.export_batch(root, closed["batch_id"])
    assert_six(exported.value, "SEALED_SOURCE_SEAL_MISMATCH")
    with pytest.raises(ValueError):
        readback.readback(root, correlation_ids=("X",))


def reseal_row(root, row, **over):
    """Write `row` with `over` applied under its own recomputed digest, so only the binding check can refuse it."""
    body = {k: v for k, v in row.items() if k != "receipt_sha256"} | over
    digest = org.sha(body)
    path = root / org.ledger_store.receipt_key(digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body | {"receipt_sha256": digest}), encoding="utf-8")
    return digest


@pytest.mark.parametrize("over,code", [
    ({"source_repository": "StegVerse-Labs/TVC"}, "SEALED_SOURCE_BINDING_MISMATCH"),  # wrong repository
    ({"repo_receipt_sha256": "sha256:" + "a" * 64}, "SEALED_SOURCE_BINDING_MISMATCH"),  # repository digest
    ({"canonical_state_transition_receipt_sha256": "sha256:" + "a" * 64}, "SEALED_SOURCE_BINDING_MISMATCH"),
    ({"source_transition_sha256": "not-a-digest"}, "SEALED_SOURCE_BINDING_MISMATCH"),  # wrong digest
    ({"source_transition_sha256": None}, "SEALED_SOURCE_BINDING_MISMATCH"),
    ({"source_transition_id": "TVC_LABS_CONFORMANCE_TEST_RECEIPT@" + "c" * 40}, "SEALED_SOURCE_BINDING_MISMATCH"),
    ({"source_transition_id": "@StegVerse-Labs/TVC@" + "c" * 40}, "SEALED_SOURCE_BINDING_MISMATCH"),  # wrong id
    ({"org_transition_class": "TEST"}, "SEALED_SOURCE_CLASS_MISMATCH"),
    ({"boundary_evidence": {"operation": "repo_transition"}}, "SEALED_SOURCE_CLASS_MISMATCH"),
])
def test_a_resealed_sealed_row_with_a_wrong_binding_is_refused(ledger, over, code):
    root, store = ledger
    row = append_sealed(store, receipt())
    assert batches._verified_receipt(root, row["receipt_sha256"]) == row
    assert reseal_row(root, row) == row["receipt_sha256"]  # re-sealing alone changes nothing
    digest = reseal_row(root, row, **over)
    with pytest.raises(batches.SealedSourceRefused) as caught:
        batches._verified_receipt(root, digest)
    assert_six(caught.value, code)
