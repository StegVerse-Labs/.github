"""F66-01: Organization ledger custody passes between materializations by transition.

Custody of a root moves only by ORGANIZATION_LEDGER_CUSTODY_RELEASED on the
predecessor, after which it is read-only for writers, and
ORGANIZATION_LEDGER_CUSTODY_ASSUMED, the first append at the successor. Every
receipt carries its custody_generation. A copy of the root taken before the
release can still be written on another kernel: source detects it where its
receipts meet the release and refuses FAIL_CLOSED; it does not prevent it.
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


def manifest(successor: str, head: str, generation: int = 1) -> dict:
    return {
        "schema": "test.parent-manifest/v1",
        org.CUSTODY_TRANSFER_KEY: {
            "successor_materialization_id": successor,
            "predecessor_head_sha256": head,
            "next_custody_generation": generation,
        },
    }


def head(root: Path) -> str:
    return json.loads((root / "HEAD.json").read_text())["receipt_sha256"]


def receipts(root: Path) -> set[str]:
    return {path.name for path in (root / "receipts").glob("*.json")}


def readback(root: Path, row: dict) -> dict:
    return batch.verified_organization_receipt(root, row["receipt_sha256"],
                                               state_receipt_sha256=row["source_transition_sha256"])


@pytest.fixture
def predecessor(tmp_path):
    root = tmp_path / "node-a" / "org-ledger"
    org.aggregate_transition(receipt("FIRST"), ledger=root)
    second = org.aggregate_transition(receipt("SECOND"), ledger=root)
    return root, second


def handover(tmp_path, root: Path, tip: str, successor: str = "node-b"):
    governing = manifest(successor, tip)
    released = org.release_custody(governing, ledger=root)
    moved = tmp_path / successor / "org-ledger"
    shutil.copytree(root, moved)
    assumed = org.assume_custody(governing, materialization_id=successor, ledger=moved)
    return governing, released, moved, assumed


def attests(successor: str, generation: int, head_sha256: str | None = None, action: str | None = None):
    """A test double standing in for an existing authority; none exists in this repository.

    It attests `successor` at `generation`, extending `head_sha256`, for
    `action` (by default whatever HEAD and action it is asked about).
    """
    def verifier(*, successor_materialization_id, custody_generation, predecessor_head_sha256, action_sha256):
        return {"successor_materialization_id": successor, "custody_generation": generation,
                "predecessor_head_sha256": head_sha256 or predecessor_head_sha256,
                "action_sha256": action or action_sha256, "unique_custody": True}
    return verifier


def refused(predicate: str, call, *args, **kwargs) -> org.CustodyRefused:
    with pytest.raises(org.CustodyRefused) as exc:
        call(*args, **kwargs)
    assert exc.value.failed_predicate == predicate
    refusal = exc.value.refusal()
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["retry_entrypoint"]
    assert refusal["consequence_committed"] is False
    assert refusal["custody_exclusivity"] == "DETECTED_NOT_PREVENTED_ACROSS_KERNELS"
    return exc.value


def test_released_root_append_refused(predecessor):
    root, second = predecessor
    governing = manifest("node-b", second["receipt_sha256"])
    released = org.release_custody(governing, ledger=root)
    assert released["custody_authority_basis"] == org.CUSTODY_AUTHORITY_BASIS_GENERATION_0
    record = released["boundary_evidence"][org.CUSTODY_KEY]
    assert released["org_transition_class"] == "ORGANIZATION_LEDGER_CUSTODY_RELEASED"
    assert released["previous_receipt_sha256"] == second["receipt_sha256"]
    assert released["custody_generation"] == 0
    assert record["successor_materialization_id"] == "node-b"
    assert record["predecessor_head_sha256"] == second["receipt_sha256"]
    assert record["next_custody_generation"] == 1
    assert record["custody_exclusivity"] == "DETECTED_NOT_PREVENTED_ACROSS_KERNELS"
    assert record["governing_manifest_sha256"] == org.sha(governing)
    assert head(root) == released["receipt_sha256"]
    before = receipts(root)

    refused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY", org.aggregate_transition, receipt("THIRD"), ledger=root)
    refused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY", batch.close_batch, "TASK_CLOSURE", root=root)
    refused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY", org.release_custody,
            manifest("node-c", released["receipt_sha256"], 2), ledger=root)
    assert receipts(root) == before and head(root) == released["receipt_sha256"]
    assert not (root / "BATCH_HEAD.json").exists()
    # The exact release retried is the same receipt, not a second one.
    assert org.release_custody(governing, ledger=root) == released
    # Its history still reads back.
    assert readback(root, second)["receipt_sha256"] == second["receipt_sha256"]


def test_assumed_successor_appends(tmp_path, predecessor):
    root, second = predecessor
    governing, released, moved, assumed = handover(tmp_path, root, second["receipt_sha256"])
    record = assumed["boundary_evidence"][org.CUSTODY_KEY]
    assert assumed["org_transition_class"] == "ORGANIZATION_LEDGER_CUSTODY_ASSUMED"
    assert assumed["previous_receipt_sha256"] == released["receipt_sha256"]
    assert assumed["custody_generation"] == 1
    assert record["release_receipt_sha256"] == released["receipt_sha256"]
    assert record["custody_exclusivity"] == "DETECTED_NOT_PREVENTED_ACROSS_KERNELS"
    assert org.assume_custody(governing, materialization_id="node-b", ledger=moved) == assumed

    attested = attests("node-b", 1)
    third = org.aggregate_transition(receipt("THIRD"), ledger=moved, custody_exclusivity_verifier=attested)
    assert third["previous_receipt_sha256"] == assumed["receipt_sha256"]
    assert third["custody_generation"] == 1
    assert third["custody_exclusivity_attestation_sha256"] == org.sha(attested(
        successor_materialization_id="node-b", custody_generation=1,
        predecessor_head_sha256=assumed["receipt_sha256"],
        action_sha256=org.custody_action_sha256("ORGANIZATION_STATE_TRANSITION", third["source_transition_sha256"])))
    # Past the handover nothing claims the generation-0 basis.
    assert "custody_authority_basis" not in third and "custody_authority_basis" not in assumed
    assert readback(moved, third)["receipt_sha256"] == third["receipt_sha256"]
    closed = batch.close_batch("TASK_CLOSURE", root=moved, custody_exclusivity_verifier=attested)
    assert closed["last_org_receipt_sha256"] == third["receipt_sha256"]
    assert len(closed["ordered_receipt_hashes"]) == 5
    # The predecessor stays read-only.
    refused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY", org.aggregate_transition, receipt("FOURTH"), ledger=root)


def test_missing_release_refused(tmp_path, predecessor):
    root, second = predecessor
    governing = manifest("node-b", second["receipt_sha256"])
    before = receipts(root)
    refused("ORGANIZATION_LEDGER_CUSTODY_RELEASE_MISSING", org.assume_custody, governing,
            materialization_id="node-b", ledger=root)
    assert receipts(root) == before and head(root) == second["receipt_sha256"]
    # Assumption never starts a chain, and an empty root cannot be released.
    empty = tmp_path / "empty"
    refused("ORGANIZATION_LEDGER_CUSTODY_RELEASE_MISSING", org.assume_custody, governing,
            materialization_id="node-b", ledger=empty)
    refused("CUSTODY_RELEASE_REQUIRES_EXISTING_HEAD", org.release_custody, governing, ledger=empty)
    assert not (empty / "HEAD.json").exists() and not receipts(empty)
    # The custody classes cannot be appended around the gate.
    refused("ORGANIZATION_LEDGER_CUSTODY_RELEASE_MISSING", org.aggregate_transition, receipt("FORGED"),
            org_transition_class=org.CUSTODY_ASSUMED_CLASS, ledger=root)
    refused("CUSTODY_RELEASE_PREDECESSOR_HEAD_MISMATCH", org.aggregate_transition, receipt("FORGED"),
            org_transition_class=org.CUSTODY_RELEASED_CLASS, ledger=root)
    refused("CUSTODY_TRANSFER_MANIFEST_DECLARATION_REQUIRED", org.release_custody,
            {"schema": "test.parent-manifest/v1"}, ledger=root)
    assert receipts(root) == before


def test_wrong_successor_refused(tmp_path, predecessor):
    root, second = predecessor
    governing = manifest("node-b", second["receipt_sha256"])
    org.release_custody(governing, ledger=root)
    moved = tmp_path / "node-c" / "org-ledger"
    shutil.copytree(root, moved)
    before = receipts(moved)
    refused("CUSTODY_RELEASE_SUCCESSOR_MISMATCH", org.assume_custody, governing,
            materialization_id="node-c", ledger=moved)
    refused("CUSTODY_RELEASE_SUCCESSOR_MISMATCH", org.assume_custody, manifest("node-c", second["receipt_sha256"]),
            materialization_id="node-c", ledger=moved)
    assert receipts(moved) == before


def test_mismatched_head_refused(tmp_path, predecessor):
    root, second = predecessor
    first_digest = second["previous_receipt_sha256"]
    # A manifest naming a HEAD this root no longer holds cannot release it.
    refused("CUSTODY_RELEASE_PREDECESSOR_HEAD_MISMATCH", org.release_custody,
            manifest("node-b", first_digest), ledger=root)
    refused("CUSTODY_GENERATION_MISMATCH", org.release_custody,
            manifest("node-b", second["receipt_sha256"], 2), ledger=root)
    assert head(root) == second["receipt_sha256"]
    governing = manifest("node-b", second["receipt_sha256"])
    org.release_custody(governing, ledger=root)
    moved = tmp_path / "node-b" / "org-ledger"
    shutil.copytree(root, moved)
    before = receipts(moved)
    refused("CUSTODY_RELEASE_PREDECESSOR_HEAD_MISMATCH", org.assume_custody,
            manifest("node-b", first_digest), materialization_id="node-b", ledger=moved)
    refused("CUSTODY_GENERATION_MISMATCH", org.assume_custody,
            manifest("node-b", second["receipt_sha256"], 2), materialization_id="node-b", ledger=moved)
    other = dict(governing, schema="test.other-manifest/v1")
    refused("CUSTODY_TRANSFER_MANIFEST_MISMATCH", org.assume_custody, other,
            materialization_id="node-b", ledger=moved)
    assert receipts(moved) == before


def test_interrupted_handover_fail_closed_with_retry(tmp_path, predecessor):
    root, second = predecessor
    governing = manifest("node-b", second["receipt_sha256"])
    released = org.release_custody(governing, ledger=root)
    # Interrupted: the release receipt is durable but HEAD was never advanced.
    head_path = root / "HEAD.json"
    head_path.write_text(json.dumps(dict(json.loads(head_path.read_text()),
                                         receipt_sha256=second["receipt_sha256"],
                                         receipt_path=str(root / "receipts" / (second["receipt_sha256"][7:] + ".json")))))
    moved = tmp_path / "node-b" / "org-ledger"
    shutil.copytree(root, moved)
    exc = refused("ORGANIZATION_LEDGER_CUSTODY_HANDOVER_INTERRUPTED", org.assume_custody, governing,
                  materialization_id="node-b", ledger=moved)
    assert exc.refusal()["retry_entrypoint"] == "resident-runtime/aggregate_repo_transition.py::release_custody"
    # Nor may the predecessor append past its own half-written release.
    refused("ORGANIZATION_LEDGER_CUSTODY_HANDOVER_INTERRUPTED", org.aggregate_transition,
            receipt("THIRD"), ledger=root)
    assert head(root) == second["receipt_sha256"] and head(moved) == second["receipt_sha256"]

    # The retry entrypoint completes the handover; nothing is appended twice.
    count = len(receipts(root))
    assert org.release_custody(governing, ledger=root) == released
    assert head(root) == released["receipt_sha256"] and len(receipts(root)) == count
    shutil.rmtree(moved)
    shutil.copytree(root, moved)
    assumed = org.assume_custody(governing, materialization_id="node-b", ledger=moved)
    assert assumed["previous_receipt_sha256"] == released["receipt_sha256"]


def other_kernel_at_same_path(tmp_path, root: Path, snapshot: Path, name: str):
    """Write as a second kernel holding a byte copy of `snapshot` at root's identical absolute path.

    This is the case source cannot tell apart: the location HEAD records is the
    location supplied, and the lock is another kernel's. It verifies on its own.
    """
    held = root.with_name(root.name + ".this-kernel")
    root.rename(held)
    shutil.copytree(snapshot, root)
    try:
        written = org.aggregate_transition(receipt(name), ledger=root)
        assert readback(root, written)["receipt_sha256"] == written["receipt_sha256"]
        carried = tmp_path / ("other-kernel-" + name)
        (carried / "receipts").mkdir(parents=True)
        shutil.copy2(root / "receipts" / (written["receipt_sha256"][7:] + ".json"), carried / "receipts")
    finally:
        shutil.rmtree(root)
        held.rename(root)
    return written, carried


def _stale_copy_appends(tmp_path, root: Path, second: dict):
    snapshot = tmp_path / "snapshot-before-release"
    shutil.copytree(root, snapshot)  # taken BEFORE the release
    governing, released, moved, assumed = handover(tmp_path, root, second["receipt_sha256"])
    # Another kernel: the predecessor's lock does not reach it, and nothing in
    # source stops it writing. This is the limit: not prevented.
    written, stale = other_kernel_at_same_path(tmp_path, root, snapshot, "STALE")
    assert written["custody_generation"] == 0
    return stale, written, moved, assumed


def _replay(source: Path, row: dict, destination: Path) -> None:
    name = row["receipt_sha256"][7:] + ".json"
    shutil.copy2(source / "receipts" / name, destination / "receipts" / name)


def test_stale_source_replay_refused(tmp_path, predecessor):
    root, second = predecessor
    stale, written, moved, assumed = _stale_copy_appends(tmp_path, root, second)
    _replay(stale, written, moved)
    exc = refused("CUSTODY_GENERATION_SUPERSEDED", org.aggregate_transition, receipt("FOURTH"), ledger=moved)
    assert written["receipt_sha256"] in exc.detail
    refused("CUSTODY_GENERATION_SUPERSEDED", batch.close_batch, "TASK_CLOSURE", root=moved)
    with pytest.raises(org.CustodyRefused, match="CUSTODY_GENERATION_SUPERSEDED"):
        batch._segment(moved, head(moved), None)
    assert head(moved) == assumed["receipt_sha256"]


def test_superseded_generation_receipt_refused_at_readback(tmp_path, predecessor):
    root, second = predecessor
    stale, written, moved, assumed = _stale_copy_appends(tmp_path, root, second)
    # At the successor's verification and at any readback that sees the release.
    for seen in (moved, root):
        _replay(stale, written, seen)
        with pytest.raises(batch.OrganizationReceiptRefused) as exc:
            readback(seen, written)
        refusal = exc.value.refusal()
        assert refusal["failed_predicate"] == "CUSTODY_GENERATION_SUPERSEDED"
        assert refusal["disposition"] == "FAIL_CLOSED"
        assert refusal["retry_entrypoint"] == batch.RECEIPT_REFUSAL_RETRY_ENTRYPOINT
        assert refusal["consequence_committed"] is False


def test_copied_root_dual_writer_detected_fail_closed(tmp_path, predecessor):
    root, second = predecessor
    snapshot = tmp_path / "snapshot"
    shutil.copytree(root, snapshot)
    ours = org.aggregate_transition(receipt("OURS"), ledger=root)
    # Apart, each copy verifies: two kernels at one path, no shared serializer.
    theirs, copy = other_kernel_at_same_path(tmp_path, root, snapshot, "THEIRS")
    assert readback(root, ours)
    _replay(copy, theirs, root)
    exc = refused("ORGANIZATION_CUSTODY_FORK_DETECTED", org.aggregate_transition, receipt("NEXT"), ledger=root)
    assert second["receipt_sha256"] in exc.detail
    refused("ORGANIZATION_CUSTODY_FORK_DETECTED", batch.close_batch, "TASK_CLOSURE", root=root)
    with pytest.raises(batch.OrganizationReceiptRefused) as readback_refusal:
        readback(root, ours)
    assert readback_refusal.value.refusal()["failed_predicate"] == "ORGANIZATION_CUSTODY_FORK_DETECTED"
    assert readback_refusal.value.refusal()["disposition"] == "FAIL_CLOSED"
    assert head(root) == ours["receipt_sha256"]


def test_two_copies_assuming_one_release_detected_fail_closed(tmp_path, predecessor):
    root, second = predecessor
    governing, released, moved, assumed = handover(tmp_path, root, second["receipt_sha256"])
    twin = tmp_path / "node-b-twin" / "org-ledger"
    shutil.copytree(root, twin)
    # A second copy of the released root, assuming as the same successor on
    # another kernel: both assumptions succeed apart.
    twin_assumed = org.assume_custody(governing, materialization_id="node-b", ledger=twin)
    assert twin_assumed["custody_generation"] == assumed["custody_generation"] == 1
    assert twin_assumed["previous_receipt_sha256"] == assumed["previous_receipt_sha256"]
    # Each copy's own attestation succeeds apart: that is why exclusivity has
    # to come from an authority outside both copies, not from this source.
    twin_written = org.aggregate_transition(receipt("TWIN"), ledger=twin, custody_exclusivity_verifier=attests("node-b", 1))
    ours = org.aggregate_transition(receipt("OURS"), ledger=moved, custody_exclusivity_verifier=attests("node-b", 1))
    for row in (twin_assumed, twin_written):
        _replay(twin, row, moved)
    refused("ORGANIZATION_CUSTODY_FORK_DETECTED", batch.close_batch, "TASK_CLOSURE", root=moved)
    refused("ORGANIZATION_CUSTODY_FORK_DETECTED", org.aggregate_transition, receipt("NEXT"), ledger=moved)
    assert head(moved) == ours["receipt_sha256"]


def _legacy(root: Path) -> list[dict]:
    """Rewrite a chain as it was written before custody_generation existed."""
    rows, cursor = [], head(root)
    while cursor:
        row = json.loads((root / "receipts" / (cursor[7:] + ".json")).read_text())
        rows.append(row)
        cursor = row["previous_receipt_sha256"]
    rows.reverse()
    shutil.rmtree(root / "receipts")
    (root / "receipts").mkdir()
    previous, legacy = None, []
    for row in rows:
        body = {key: value for key, value in row.items() if key not in {"receipt_sha256", "custody_generation"}}
        body["previous_receipt_sha256"] = previous
        if row["previous_receipt_sha256"] is not None:
            body["predecessor_org_state_sha256"] = previous
        record = dict(body, receipt_sha256=org.sha(body))
        (root / "receipts" / (record["receipt_sha256"][7:] + ".json")).write_text(json.dumps(record))
        legacy.append(record)
        previous = record["receipt_sha256"]
    (root / "HEAD.json").write_text(json.dumps({
        "organization": "StegVerse-Labs", "receipt_sha256": previous,
        "receipt_path": str(root / "receipts" / (previous[7:] + ".json")),
    }))
    return legacy


def test_existing_chain_without_custody_generation_verifies(tmp_path, predecessor):
    root, _ = predecessor
    legacy = _legacy(root)
    assert all("custody_generation" not in row for row in legacy)
    assert readback(root, legacy[-1])["receipt_sha256"] == legacy[-1]["receipt_sha256"]
    assert org.custody_generation(legacy[-1]) == 0
    third = org.aggregate_transition(receipt("THIRD"), ledger=root)
    assert third["previous_receipt_sha256"] == legacy[-1]["receipt_sha256"]
    assert third["custody_generation"] == 0
    closed = batch.close_batch("TASK_CLOSURE", root=root)
    assert closed["ordered_receipt_hashes"][:2] == [row["receipt_sha256"] for row in legacy]
    # The legacy chain is generation 0 and its custody moves like any other.
    governing, released, moved, assumed = handover(tmp_path, root, third["receipt_sha256"])
    assert released["custody_generation"] == 0 and assumed["custody_generation"] == 1
    for row in legacy:
        assert readback(moved, row)["receipt_sha256"] == row["receipt_sha256"]


def test_successor_consequential_append_without_exclusivity_attestation_fails_closed(tmp_path, predecessor, monkeypatch):
    root, second = predecessor
    governing, released, moved, assumed = handover(tmp_path, root, second["receipt_sha256"])
    before = receipts(moved)
    exc = refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", org.aggregate_transition, receipt("THIRD"), ledger=moved)
    assert exc.refusal()["retry_entrypoint"] == "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
    assert exc.detail == "node-b@1@" + assumed["receipt_sha256"]
    refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", org.aggregate_transition, receipt("THIRD"),
            ledger=moved, custody_exclusivity_verifier=lambda **_: True)
    # No environment fallback.
    monkeypatch.setenv("STEGVERSE_CUSTODY_EXCLUSIVITY_VERIFIER", "attested")
    refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", org.aggregate_transition, receipt("THIRD"), ledger=moved)
    refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", batch.close_batch, "TASK_CLOSURE", root=moved)
    refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", org.release_custody,
            manifest("node-c", assumed["receipt_sha256"], 2), ledger=moved)
    # A manifest-directed append closes and submits nothing before it is refused.
    submitted = []
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: submitted.append(batch_id))
    refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", org.aggregate_transition, receipt("THIRD"), ledger=moved,
            parent_manifest={"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}})
    assert submitted == [] and not (moved / "BATCH_HEAD.json").exists()
    assert receipts(moved) == before and head(moved) == assumed["receipt_sha256"]
    # The limitation is recorded, never used as a passing predicate.
    assert assumed["boundary_evidence"][org.CUSTODY_KEY]["custody_exclusivity"] == "DETECTED_NOT_PREVENTED_ACROSS_KERNELS"


def test_successor_assumed_record_itself_permitted(tmp_path, predecessor):
    root, second = predecessor
    governing = manifest("node-b", second["receipt_sha256"])
    released = org.release_custody(governing, ledger=root)
    moved = tmp_path / "node-b" / "org-ledger"
    shutil.copytree(root, moved)
    assumed = org.assume_custody(governing, materialization_id="node-b", ledger=moved)
    assert assumed["previous_receipt_sha256"] == released["receipt_sha256"]
    assert assumed["custody_generation"] == 1
    assert "custody_exclusivity_attestation_sha256" not in assumed
    assert head(moved) == assumed["receipt_sha256"]
    assert readback(moved, assumed)["receipt_sha256"] == assumed["receipt_sha256"]
    assert org.assume_custody(governing, materialization_id="node-b", ledger=moved) == assumed


def test_unreleased_root_appends_unchanged(tmp_path, predecessor, monkeypatch):
    root, second = predecessor
    third = org.aggregate_transition(receipt("THIRD"), ledger=root)
    assert third["previous_receipt_sha256"] == second["receipt_sha256"]
    assert third["custody_generation"] == 0
    assert "custody_exclusivity_attestation_sha256" not in third
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: {
        "state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id,
        "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY",
    })
    governing = {"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}}
    fourth = org.aggregate_transition(receipt("FOURTH"), ledger=root, parent_manifest=governing)
    fifth = org.aggregate_transition(receipt("FIFTH"), ledger=root, parent_manifest=governing)
    assert fifth["previous_receipt_sha256"] == fourth["receipt_sha256"] and fifth["custody_generation"] == 0
    released = batch._verified_batch(root, json.loads((root / "BATCH_HEAD.json").read_text())["batch_id"])
    assert released["last_org_receipt_sha256"] == fourth["receipt_sha256"]
    closed = batch.close_batch("TASK_CLOSURE", root=root)
    assert closed["last_org_receipt_sha256"] == fifth["receipt_sha256"]


def _successor(tmp_path, predecessor):
    root, second = predecessor
    return handover(tmp_path, root, second["receipt_sha256"])


def _refused_with(moved, verifier, match=None):
    before = receipts(moved), head(moved)
    exc = refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", org.aggregate_transition, receipt("NEXT"),
                  ledger=moved, custody_exclusivity_verifier=verifier)
    assert (receipts(moved), head(moved)) == before
    if match:
        assert match in exc.detail
    return exc


def test_exclusivity_wrong_generation_refused(tmp_path, predecessor):
    _, _, moved, _ = _successor(tmp_path, predecessor)
    _refused_with(moved, attests("node-b", 2))
    _refused_with(moved, attests("node-b", 0))


def test_exclusivity_wrong_materialization_refused(tmp_path, predecessor):
    _, _, moved, _ = _successor(tmp_path, predecessor)
    _refused_with(moved, attests("node-c", 1))


def test_exclusivity_stale_head_refused(tmp_path, predecessor):
    _, released, moved, assumed = _successor(tmp_path, predecessor)
    _refused_with(moved, attests("node-b", 1, released["receipt_sha256"]))
    third = org.aggregate_transition(receipt("THIRD"), ledger=moved, custody_exclusivity_verifier=attests("node-b", 1))
    # An attestation of the HEAD before THIRD no longer covers a write after it.
    _refused_with(moved, attests("node-b", 1, assumed["receipt_sha256"]))
    assert head(moved) == third["receipt_sha256"]


def test_exclusivity_replayed_attestation_refused(tmp_path, predecessor):
    _, _, moved, assumed = _successor(tmp_path, predecessor)
    recorded = []

    def recording(**asked):
        recorded.append(attests("node-b", 1)(**asked))
        return recorded[-1]

    third = org.aggregate_transition(receipt("THIRD"), ledger=moved, custody_exclusivity_verifier=recording)
    assert third["custody_exclusivity_attestation_sha256"] == org.sha(recorded[0])
    _refused_with(moved, lambda **_: dict(recorded[0]))
    # An attestation already bound in a receipt is a replay even where it names the HEAD it is asked about.
    rows = org.verify_custody_lineage(moved)
    with pytest.raises(org.CustodyRefused, match="attestation replayed"):
        org.require_custody_exclusivity(rows, assumed["receipt_sha256"], "ORGANIZATION_STATE_TRANSITION",
                                        lambda **_: dict(recorded[0]), recorded[0]["action_sha256"])


def test_exclusivity_attestation_for_other_action_refused(tmp_path, predecessor):
    _, _, moved, assumed = _successor(tmp_path, predecessor)
    other = org.custody_action_sha256("ORGANIZATION_STATE_TRANSITION", org.sha(receipt("OTHER")))
    _refused_with(moved, attests("node-b", 1, action=other))
    # Attested for an append, it does not cover a batch closure.
    append_action = org.custody_action_sha256("ORGANIZATION_STATE_TRANSITION", org.sha(receipt("NEXT")))
    before = receipts(moved)
    refused("CUSTODY_EXCLUSIVITY_UNAUTHENTICATED", batch.close_batch, "TASK_CLOSURE", root=moved,
            custody_exclusivity_verifier=attests("node-b", 1, action=append_action))
    assert receipts(moved) == before and not (moved / "BATCH_HEAD.json").exists()
    # The same verifier asked for the exact action is accepted.
    written = org.aggregate_transition(receipt("NEXT"), ledger=moved, custody_exclusivity_verifier=attests("node-b", 1))
    assert written["previous_receipt_sha256"] == assumed["receipt_sha256"]


def test_exclusivity_verifier_unavailable_fail_closed(tmp_path, predecessor):
    _, _, moved, _ = _successor(tmp_path, predecessor)

    def unreachable(**_):
        raise ConnectionError("authority unreachable")

    exc = _refused_with(moved, unreachable, match="verifier unavailable: ConnectionError")
    assert exc.refusal()["retry_entrypoint"] == "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
    _refused_with(moved, lambda **_: None)


def test_generation_zero_relocated_without_handover_consequential_append_refused(tmp_path, predecessor, monkeypatch):
    root, second = predecessor
    copied = tmp_path / "node-c" / "org-ledger"
    shutil.copytree(root, copied)
    moved = tmp_path / "node-b" / "org-ledger"
    shutil.move(str(root), str(moved))
    submitted = []
    monkeypatch.setattr(batch, "submit_released_batch", lambda root, batch_id: submitted.append(batch_id))
    for relocated in (moved, copied):
        before = receipts(relocated)
        exc = refused("UNGOVERNED_RELOCATION_ANOMALY_DETECTED", org.aggregate_transition,
                      receipt("THIRD"), ledger=relocated)
        assert exc.refusal()["retry_entrypoint"] == "resident-runtime/aggregate_repo_transition.py::release_custody"
        refused("UNGOVERNED_RELOCATION_ANOMALY_DETECTED", org.aggregate_transition, receipt("THIRD"),
                ledger=relocated, parent_manifest={"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}})
        refused("UNGOVERNED_RELOCATION_ANOMALY_DETECTED", batch.close_batch, "TASK_CLOSURE", root=relocated)
        # A relocated root cannot release itself either; only one at its recorded location can.
        refused("UNGOVERNED_RELOCATION_ANOMALY_DETECTED", org.release_custody,
                manifest("node-d", second["receipt_sha256"]), ledger=relocated)
        assert receipts(relocated) == before and head(relocated) == second["receipt_sha256"]
        assert not (relocated / "BATCH_HEAD.json").exists()
    assert submitted == []
    # The only governed move is a handover from the recorded location.
    shutil.move(str(moved), str(root))
    governing, released, successor, assumed = handover(tmp_path, root, second["receipt_sha256"], successor="node-e")
    third = org.aggregate_transition(receipt("THIRD"), ledger=successor, custody_exclusivity_verifier=attests("node-e", 1))
    assert third["previous_receipt_sha256"] == assumed["receipt_sha256"]


def test_generation_zero_relocated_readback_still_verifies(tmp_path, predecessor):
    root, second = predecessor
    first = json.loads((root / "receipts" / (second["previous_receipt_sha256"][7:] + ".json")).read_text())
    closed = batch.close_batch("TASK_CLOSURE", root=root)
    moved = tmp_path / "node-b" / "mounted" / "org-ledger"
    moved.parent.mkdir(parents=True)
    shutil.move(str(root), str(moved))
    for row in (first, second):
        assert readback(moved, row)["receipt_sha256"] == row["receipt_sha256"]
    assert [row["receipt_sha256"] for row in batch._segment(moved, head(moved), None)] == [
        first["receipt_sha256"], second["receipt_sha256"]]
    assert batch.verify_batch(moved, closed["batch_id"])["state"] == "PASS"
    assert batch.export_batch_record(moved, closed["batch_id"])["local_verification"]["organization_chain"] == "PASS"


def test_generation_zero_original_location_unchanged(predecessor):
    root, second = predecessor
    third = org.aggregate_transition(receipt("THIRD"), ledger=root)
    assert third["previous_receipt_sha256"] == second["receipt_sha256"] and third["custody_generation"] == 0
    assert "custody_exclusivity_attestation_sha256" not in third
    # A location match is not custody authority, and the receipt says so.
    for row in (second, third):
        assert row["custody_authority_basis"] == (
            "PRE_EXISTING_MATERIALIZATION_UNAUTHENTICATED; LOCATION_CHECK_IS_ANOMALY_DETECTION_ONLY")
    closed = batch.close_batch("TASK_CLOSURE", root=root)
    assert closed["last_org_receipt_sha256"] == third["receipt_sha256"]
    # The same root supplied by a different spelling of the same location is the same location.
    fourth = org.aggregate_transition(receipt("FOURTH"), ledger=root / ".." / root.name)
    assert fourth["previous_receipt_sha256"] == third["receipt_sha256"]
