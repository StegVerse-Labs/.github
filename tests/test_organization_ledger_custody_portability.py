"""F63-02: Organization ledger custody is not bound to the host that wrote it.

The root and its lock come only from what the materializer supplies. A root
supplied at another path -- the same ledger on another node -- still reads back
and verifies there. It appends there only once custody has moved to it by
RELEASED/ASSUMED (F66-01, F71-02).
"""
from __future__ import annotations

import json
import shutil
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


def test_host_derived_location_is_refused(monkeypatch, tmp_path):
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_ROOT", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    with pytest.raises(org.LedgerLocationRequired) as refused:
        org.ledger_root()
    assert refused.value.failed_predicate == "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"
    assert str(refused.value) == "ledger_location_required_from_materializer: STEGVERSE_ORG_LEDGER_ROOT"
    assert org.location_refusal(refused.value)["disposition"] == "FAIL_CLOSED"
    with pytest.raises(org.LedgerLocationRequired):
        org.aggregate_transition(receipt("CLAIM"))
    with pytest.raises(org.LedgerLocationRequired):
        batch.close_batch("TASK_CLOSURE")
    assert not any(tmp_path.rglob("HEAD.json"))
    assert not any(tmp_path.rglob(".append.lock"))


def test_supplied_root_is_the_ledger_and_holds_its_lock(monkeypatch, tmp_path):
    supplied = tmp_path / "supplied"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(supplied))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    first = org.aggregate_transition(receipt("CLAIM"))
    assert org.ledger_root() == supplied.resolve()
    assert (supplied / ".append.lock").is_file()
    assert json.loads((supplied / "HEAD.json").read_text())["receipt_sha256"] == first["receipt_sha256"]
    assert not (tmp_path / "home").exists()


def test_root_supplied_at_another_path_reads_but_moves_only_by_handover(monkeypatch, tmp_path):
    written = tmp_path / "node-a" / "org-ledger"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(written))
    parent_manifest = {
        "schema": "test.parent-manifest/v1",
        "receipt_batch": {"release_condition": {"type": "COUNT", "count": 2}},
    }
    first = org.aggregate_transition(receipt("FIRST"), parent_manifest=parent_manifest)
    second = org.aggregate_transition(receipt("SECOND"), parent_manifest=parent_manifest)

    # The one materialization of this root, now supplied at another node's path.
    moved = tmp_path / "node-b" / "mounted" / "org-ledger"
    moved.parent.mkdir(parents=True)
    shutil.move(str(written), str(moved))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(moved))
    submitted = []
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: submitted.append(batch_id) or {
        "state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id,
        "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY",
    })
    # Reads stay portable (F63-02): the chain verifies wherever it is supplied.
    assert [row["receipt_sha256"] for row in batch._segment(moved, second["receipt_sha256"], None)] == [
        first["receipt_sha256"], second["receipt_sha256"]]
    # Writes do not (F71-02): moved without a handover is an anomaly, refused.
    with pytest.raises(org.CustodyRefused, match="UNGOVERNED_RELOCATION_ANOMALY_DETECTED"):
        org.aggregate_transition(receipt("THIRD"), parent_manifest=parent_manifest)
    assert submitted == [] and not (moved / "BATCH_HEAD.json").exists()

    # Moved by RELEASED/ASSUMED from its recorded location, it advances there.
    shutil.move(str(moved), str(written))
    governing = {"schema": "test.parent-manifest/v1", org.CUSTODY_TRANSFER_KEY: {
        "successor_materialization_id": "node-b", "predecessor_head_sha256": second["receipt_sha256"],
        "next_custody_generation": 1}}
    released = org.release_custody(governing, ledger=written)
    shutil.copytree(written, moved)
    assumed = org.assume_custody(governing, materialization_id="node-b", ledger=moved)

    def attested(*, successor_materialization_id, custody_generation, predecessor_head_sha256, action_sha256):
        return {"successor_materialization_id": successor_materialization_id, "custody_generation": custody_generation,
                "predecessor_head_sha256": predecessor_head_sha256, "action_sha256": action_sha256,
                "unique_custody": True}

    third = org.aggregate_transition(receipt("THIRD"), parent_manifest=parent_manifest,
                                     custody_exclusivity_verifier=attested)
    released_batch = batch._verified_batch(moved, json.loads((moved / "BATCH_HEAD.json").read_text())["batch_id"])
    assert released_batch["ordered_receipt_hashes"] == [first["receipt_sha256"], second["receipt_sha256"],
                                                       released["receipt_sha256"], assumed["receipt_sha256"]]
    assert third["previous_receipt_sha256"] == assumed["receipt_sha256"]
    head = json.loads((moved / "HEAD.json").read_text())
    assert head["receipt_sha256"] == third["receipt_sha256"]
    assert Path(head["receipt_path"]).parent == (moved / "receipts").resolve()


def test_head_naming_another_receipt_is_still_refused(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path))
    first = org.aggregate_transition(receipt("CLAIM"))
    head_path = tmp_path / "HEAD.json"
    head = json.loads(head_path.read_text())
    for wrong in (str(tmp_path / "receipts" / ("0" * 64 + ".json")),
                  str(tmp_path / "elsewhere" / (first["receipt_sha256"][7:] + ".json")),
                  ""):
        head_path.write_text(json.dumps(dict(head, receipt_path=wrong)))
        with pytest.raises(ValueError, match="organization ledger HEAD receipt path mismatch"):
            batch.close_batch("TASK_CLOSURE", root=tmp_path)
    assert not (tmp_path / "BATCH_HEAD.json").exists()
