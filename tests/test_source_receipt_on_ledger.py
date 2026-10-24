"""A repository source receipt is consumed only as the repository ledger's own (VALIDATOR row 8).

verify_source checked the schema, the repository prefix and the receipt's own
hash, so a self-consistent receipt minted anywhere was aggregated. Before any
organization store opens, aggregate_transition now requires the receipt to be,
byte-for-byte, the one the repository ledger holds at its address and
reachable from that ledger's HEAD (emit.chain verifies every node). No
repository ledger supplied is the location refusal, never a pass.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402

SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64


def minted(transition_id, previous=None):
    body = {"schema": "stegverse.repo-transition-receipt/v1", "repository": "StegVerse-Labs/.github",
            "transition_id": transition_id, "transition_class": "TEST",
            "predecessor_state_sha256": SHA_A, "successor_state_sha256": SHA_B,
            "hb_reference": org.kernel.hb_reference(epoch=4096), "previous_receipt_sha256": previous}
    return {**body, "receipt_sha256": org.sha(body)}


def on_ledger(ledger, transition_id):
    """Append a receipt as the next chained node of `ledger` and publish it as HEAD."""
    head = ledger.get(org.ledger_store.HEAD_KEY)
    receipt = minted(transition_id, head["receipt_sha256"] if head else None)
    ledger.put(org.ledger_store.receipt_key(receipt["receipt_sha256"]), receipt)
    ledger.put(org.ledger_store.HEAD_KEY, {"receipt_sha256": receipt["receipt_sha256"]})
    return receipt


@pytest.fixture
def ledgers(monkeypatch, tmp_path):
    repo, org_root = tmp_path / "repo", tmp_path / "org"
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", str(repo))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(org_root))
    return org.ledger_store.PosixLedgerStore(repo), org_root


def aggregate(receipt, org_root, **kwargs):
    return org.aggregate_transition(receipt, predecessor_org_state_sha256=SHA_A, successor_org_state_sha256=SHA_B,
                                    hb_epoch=4096, ledger=org_root, **kwargs)


def assert_refused_before_any_write(receipt, org_root, detail, **kwargs):
    with pytest.raises(org.OrgLedgerEpochRefused) as raised:
        aggregate(receipt, org_root, **kwargs)
    refusal = raised.value.refusal
    assert (refusal["failure_code"], refusal["failed_predicate"]) == (
        "SOURCE_RECEIPT_NOT_ON_LEDGER", "SOURCE_RECEIPT_IS_THE_REPOSITORY_LEDGERS_OWN")
    for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                  "owning_existing_goal", "next_attempt"):
        assert str(refusal[field]).strip(), field
    assert detail in refusal["detail"]
    assert refusal["consequence_committed"] is False
    assert not org_root.exists(), "no organization store is opened for a refused source"


def test_the_repository_ledgers_own_receipt_is_aggregated(ledgers):
    ledger, org_root = ledgers
    on_ledger(ledger, "earlier")
    receipt = on_ledger(ledger, "own")
    assert aggregate(receipt, org_root)["repo_receipt_sha256"] == receipt["receipt_sha256"]


def test_a_self_consistent_receipt_minted_off_the_ledger_is_refused(ledgers):
    ledger, org_root = ledgers
    on_ledger(ledger, "own")
    forged = minted("forged")
    assert org.verify_source(forged)  # passes every check verify_source makes
    assert_refused_before_any_write(forged, org_root, "not reachable from the repository ledger's HEAD")


def test_a_ledger_receipt_altered_by_one_field_is_refused(ledgers):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    altered = dict(receipt, transition_class="OTHER")
    altered["receipt_sha256"] = org.sha({k: v for k, v in altered.items() if k != "receipt_sha256"})
    assert_refused_before_any_write(altered, org_root, "not reachable")
    # The same address, different bytes, as a caller holding the store sees it.
    stored_elsewhere = dict(receipt, evidence={"x": 1})
    assert_refused_before_any_write(stored_elsewhere, org_root, "differs from the receipt", repository_ledger=ledger)


def test_an_orphan_receipt_head_does_not_reach_is_refused(ledgers):
    ledger, org_root = ledgers
    on_ledger(ledger, "own")
    orphan = minted("orphan")
    ledger.put(org.ledger_store.receipt_key(orphan["receipt_sha256"]), orphan)  # stored, never chained
    assert_refused_before_any_write(orphan, org_root, "not reachable")


def test_no_repository_ledger_supplied_is_the_location_refusal(ledgers, monkeypatch):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    monkeypatch.delenv("STEGVERSE_REPO_LEDGER_ROOT")
    with pytest.raises(org.LedgerLocationRequired):
        aggregate(receipt, org_root)
    assert not org_root.exists()


def test_a_broken_repository_chain_is_refused(ledgers):
    ledger, org_root = ledgers
    first = on_ledger(ledger, "first")
    receipt = on_ledger(ledger, "own")
    (ledger.root / org.ledger_store.receipt_key(first["receipt_sha256"])).unlink()
    assert_refused_before_any_write(receipt, org_root, "REPO_LEDGER_CHAIN_BREAK")


# --- Row 9: a corrupt or unreadable repository ledger never crashes the walk ---

@pytest.mark.parametrize("corruption", ["{not json", '{"a":' + "[" * 200000 + "]" * 200000 + "}"])
def test_a_corrupt_stored_receipt_is_a_terminal_refusal_not_a_traceback(ledgers, corruption):
    ledger, org_root = ledgers
    first = on_ledger(ledger, "first")
    receipt = on_ledger(ledger, "own")
    (ledger.root / org.ledger_store.receipt_key(first["receipt_sha256"])).write_text(corruption)
    with pytest.raises(org.OrgLedgerEpochRefused) as raised:
        aggregate(receipt, org_root)
    assert raised.value.refusal["failure_code"] == "SOURCE_RECEIPT_NOT_ON_LEDGER"
    assert raised.value.refusal["terminal"] is True
    assert not org_root.exists()


def test_an_unreadable_repository_ledger_is_a_non_terminal_refusal(ledgers, monkeypatch):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")

    def unreadable(self, key):
        raise OSError("simulated EIO reading " + key)

    monkeypatch.setattr(org.ledger_store.PosixLedgerStore, "get", unreadable)
    with pytest.raises(org.OrgLedgerEpochRefused) as raised:
        aggregate(receipt, org_root, repository_ledger=ledger)
    refusal = raised.value.refusal
    assert (refusal["failure_code"], refusal["terminal"]) == ("SOURCE_RECEIPT_NOT_ON_LEDGER", False)
    assert "retry" in refusal["next_attempt"]
    assert not org_root.exists()
