"""G1-R: the Organization ledger on a dedicated Git ref, appended by ref compare-and-swap.

Every repository here is a temporary bare repository; no production ledger ref
is created. Git is transport and custody only: a published commit is not an
ALLOW, and a refused publication is a typed FAIL_CLOSED that commits nothing.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as custody  # noqa: E402

store_module = org.ledger_store
REF = "refs/heads/organization-ledger/StegVerse-Labs"
IDENTITY = {
    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
}


def receipt(name: str) -> dict:
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": name,
        "transition_sequence": 1,
        "subject_or_correlation_id": "test-worker",
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [],
    }


def git(repo: Path, *args: str, data: bytes | None = None, env: dict | None = None) -> str:
    result = subprocess.run(["git", "--git-dir", str(repo), *args], input=data, capture_output=True,
                            env={**os.environ, **(env or {})}, check=True)
    return result.stdout.decode().strip()


def bare(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-q", str(path)], check=True)
    return path


@pytest.fixture
def origin(tmp_path):
    return bare(tmp_path / "origin.git")


def node(tmp_path: Path, name: str, origin: Path, custody_class: str | None = "PRIVATE"):
    """An ephemeral execution's own object store, appending to the shared remote."""
    return store_module.GitLedgerStore(bare(tmp_path / name), REF, remote=str(origin), custody=custody_class)


def remote_tip(origin: Path) -> str | None:
    found = subprocess.run(["git", "--git-dir", str(origin), "rev-parse", "--verify", "-q", REF],
                           capture_output=True)
    return found.stdout.decode().strip() if found.returncode == 0 else None


def remote_files(origin: Path) -> set[str]:
    return set(git(origin, "ls-tree", "-r", "--name-only", REF).splitlines())


def test_append_then_readback_verifies_from_the_durable_ref(tmp_path, origin):
    writer = node(tmp_path, "writer.git", origin)
    first = org.aggregate_transition(receipt("CLAIM"), ledger=writer)
    second = org.aggregate_transition(receipt("WORK"), ledger=writer)
    assert second["previous_receipt_sha256"] == first["receipt_sha256"]

    # One commit per append holds the receipt, its exact source and HEAD.
    tip = remote_tip(origin)
    changed = set(git(origin, "diff-tree", "--no-commit-id", "--name-only", "-r", tip).splitlines())
    assert changed == {
        "HEAD.json",
        store_module.receipt_key(second["receipt_sha256"]),
        store_module.source_key(second["source_transition_sha256"]),
    }
    assert git(origin, "rev-list", "--count", REF) == "2"
    head = json.loads(git(origin, "cat-file", "blob", REF + ":HEAD.json"))
    assert head["receipt_sha256"] == second["receipt_sha256"]
    assert head["receipt_path"] == REF + ":" + store_module.receipt_key(second["receipt_sha256"])

    # A different ephemeral node, sharing no filesystem, reads it back from the ref.
    reader = node(tmp_path, "reader.git", origin, custody_class=None)
    row = custody.verified_organization_receipt(
        reader, second["receipt_sha256"], state_receipt_sha256=second["source_transition_sha256"],
        expected_transition_id="WORK")
    assert row == second
    retained_row, retained = custody.verified_organization_source_receipt(
        reader, first["receipt_sha256"], state_receipt_sha256=first["source_transition_sha256"])
    assert retained_row == first and retained == receipt("CLAIM")
    result = {"state": "RECORDED", "receipt_sha256": second["source_transition_sha256"],
              "organization_receipt": second}
    assert custody.verified_organization_record(reader, result) == second


def test_materializer_selects_the_git_store_and_readback_uses_it(tmp_path, origin, monkeypatch):
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_ROOT", raising=False)
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_STORE", "git")
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_DIR", str(bare(tmp_path / "node.git")))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_REF", REF)
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_REMOTE", str(origin))
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_CUSTODY", "PRIVATE")
    record = org.aggregate_transition(receipt("CLAIM"))
    assert org.organization_store().kind == "GIT_REF"
    row = custody.verified_organization_receipt(
        None, record["receipt_sha256"], state_receipt_sha256=record["source_transition_sha256"])
    assert row == record
    assert not any(tmp_path.rglob("HEAD.json"))


def test_concurrent_append_lost_race_is_typed_fail_closed_with_no_partial_write(tmp_path, origin):
    org.aggregate_transition(receipt("GENESIS"), ledger=node(tmp_path, "seed.git", origin))
    slow = node(tmp_path, "slow.git", origin)
    fast = node(tmp_path, "fast.git", origin)
    with slow.exclusive():
        # Both read the same tip; the fast node publishes first.
        won = org.aggregate_transition(receipt("FAST"), ledger=fast)
        before = remote_files(origin)
        with pytest.raises(store_module.LedgerStoreRefused) as lost:
            org._aggregate_transition_locked(receipt("SLOW"), store=slow)
    refusal = org.store_refusal(lost.value)
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["failed_predicate"] == "ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP"
    assert refusal["retry_entrypoint"] == "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
    assert refusal["consequence_committed"] is False
    # Nothing of the losing append reached the ref: no receipt, no source, no HEAD.
    assert remote_files(origin) == before
    assert json.loads(git(origin, "cat-file", "blob", REF + ":HEAD.json"))["receipt_sha256"] == won["receipt_sha256"]
    slow_source = store_module.source_key(org.verify_source(receipt("SLOW"))["source_transition_sha256"])
    assert slow_source not in before
    # Its retry re-reads the ref and appends on the winner.
    retried = org.aggregate_transition(receipt("SLOW"), ledger=slow)
    assert retried["previous_receipt_sha256"] == won["receipt_sha256"]


def test_lost_race_on_a_local_ref_and_a_stale_expected_head(tmp_path):
    shared = bare(tmp_path / "ledger.git")
    first = store_module.GitLedgerStore(shared, REF, custody="PRIVATE")
    second = store_module.GitLedgerStore(shared, REF, custody="PRIVATE")
    with first.exclusive():
        org.aggregate_transition(receipt("SECOND"), ledger=second)
        tip = git(shared, "rev-parse", REF)
        with pytest.raises(store_module.LedgerStoreRefused) as lost:
            org._aggregate_transition_locked(receipt("FIRST"), store=first)
    assert lost.value.failed_predicate == "ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP"
    assert git(shared, "rev-parse", REF) == tip
    with pytest.raises(store_module.LedgerStoreRefused) as stale:
        second.append_transaction("receipts/" + "0" * 64 + ".json", {"x": 1}, {"stale": True}, {"head": 1})
    assert stale.value.failed_predicate == "ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP"
    assert git(shared, "rev-parse", REF) == tip


def test_tampered_receipt_on_the_ref_is_refused(tmp_path, origin):
    writer = node(tmp_path, "writer.git", origin)
    record = org.aggregate_transition(receipt("CLAIM"), ledger=writer)
    key = store_module.receipt_key(record["receipt_sha256"])
    forged = dict(record, authority_effect="ALLOW")
    blob = git(origin, "hash-object", "-w", "--stdin",
               data=json.dumps(forged, indent=2, sort_keys=True).encode() + b"\n")
    index = {"GIT_INDEX_FILE": str(tmp_path / "tamper-index")}
    git(origin, "read-tree", REF, env=index)
    git(origin, "update-index", "--cacheinfo", "100644," + blob + "," + key, env=index)
    tree = git(origin, "write-tree", env=index)
    commit = git(origin, "commit-tree", tree, "-p", REF, "-m", "tamper", env=IDENTITY)
    git(origin, "update-ref", REF, commit)

    reader = node(tmp_path, "reader.git", origin, custody_class=None)
    with pytest.raises(custody.OrganizationReceiptRefused) as refused:
        custody.verified_organization_receipt(
            reader, record["receipt_sha256"], state_receipt_sha256=record["source_transition_sha256"])
    assert refused.value.disposition == "DENY"
    assert refused.value.failed_predicate == "ORGANIZATION_RECEIPT_VERIFICATION_FAILED"
    # The tampered key also refuses any further append rather than chaining onto it.
    with pytest.raises(ValueError):
        org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "next.git", origin))


def test_tampered_retained_source_on_the_ref_is_refused(tmp_path, origin):
    record = org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "writer.git", origin))
    key = store_module.source_key(record["source_transition_sha256"])
    blob = git(origin, "hash-object", "-w", "--stdin",
               data=json.dumps(receipt("OTHER"), indent=2, sort_keys=True).encode() + b"\n")
    index = {"GIT_INDEX_FILE": str(tmp_path / "tamper-index")}
    git(origin, "read-tree", REF, env=index)
    git(origin, "update-index", "--cacheinfo", "100644," + blob + "," + key, env=index)
    commit = git(origin, "commit-tree", git(origin, "write-tree", env=index), "-p", REF, "-m", "t", env=IDENTITY)
    git(origin, "update-ref", REF, commit)
    with pytest.raises(custody.OrganizationReceiptRefused) as refused:
        custody.verified_organization_source_receipt(
            node(tmp_path, "reader.git", origin, custody_class=None), record["receipt_sha256"],
            state_receipt_sha256=record["source_transition_sha256"])
    assert refused.value.failed_predicate == "ORGANIZATION_SOURCE_RECEIPT_INVALID"


def test_idempotent_replay_of_the_same_source_receipt(tmp_path, origin):
    first = org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "one.git", origin))
    tip = remote_tip(origin)
    # The same exact source, replayed from another node at a later heartbeat.
    again = org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "two.git", origin), hb_epoch=999)
    assert again == first
    assert remote_tip(origin) == tip
    with pytest.raises(ValueError, match="existing organization source transition context conflict"):
        org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "three.git", origin),
                                 authority_effect="CHANGED")
    assert remote_tip(origin) == tip


def test_private_custody_surface_is_required_before_anything_is_published(tmp_path, origin):
    for declared in (None, "PUBLIC"):
        with pytest.raises(store_module.LedgerStoreRefused) as refused:
            org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, f"n{declared}.git", origin, declared))
        assert refused.value.failed_predicate == "ORGANIZATION_LEDGER_PRIVATE_CUSTODY_SURFACE_REQUIRED"
        assert refused.value.refusal()["disposition"] == "FAIL_CLOSED"
    assert remote_tip(origin) is None


def test_ledger_ref_must_be_dedicated(tmp_path, origin):
    for ref in ("refs/heads/main", "refs/heads/organization-ledger/", "refs/heads/organization-ledger/bad..ref"):
        with pytest.raises(store_module.LedgerStoreRefused) as refused:
            store_module.GitLedgerStore(origin, ref, custody="PRIVATE")
        assert refused.value.failed_predicate == "ORGANIZATION_LEDGER_REF_INVALID"


def test_unreachable_remote_fails_closed_without_waiting(tmp_path):
    store = store_module.GitLedgerStore(bare(tmp_path / "node.git"), REF,
                                        remote=str(tmp_path / "absent.git"), custody="PRIVATE")
    with pytest.raises(store_module.LedgerStoreRefused) as refused:
        org.aggregate_transition(receipt("CLAIM"), ledger=store)
    assert refused.value.failed_predicate == "ORGANIZATION_LEDGER_REMOTE_UNREACHABLE"
    with pytest.raises(custody.OrganizationReceiptRefused) as readback:
        custody.verified_organization_receipt(store, "sha256:" + "a" * 64, state_receipt_sha256="sha256:" + "b" * 64)
    assert readback.value.disposition == "FAIL_CLOSED"


def test_manifested_packet_on_git_store_is_refused_not_half_committed(tmp_path, origin):
    with pytest.raises(store_module.LedgerStoreRefused) as refused:
        org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "node.git", origin), parent_manifest={})
    assert refused.value.failed_predicate == "ORGANIZATION_BATCH_CUSTODY_NOT_CARRIED_BY_LEDGER_STORE"
    assert remote_tip(origin) is None


def test_prior_posix_receipts_are_not_git_ledger_history(tmp_path, origin):
    posix = org.aggregate_transition(receipt("CLAIM"), ledger=tmp_path / "posix")
    reader = node(tmp_path, "reader.git", origin, custody_class=None)
    with pytest.raises(custody.OrganizationReceiptRefused) as refused:
        custody.verified_organization_receipt(
            reader, posix["receipt_sha256"], state_receipt_sha256=posix["source_transition_sha256"])
    assert refused.value.failed_predicate == "ORGANIZATION_RECEIPT_READBACK_MISSING"
    # The Git ledger starts at its own genesis, not at the POSIX chain's HEAD.
    first = org.aggregate_transition(receipt("WORK"), ledger=node(tmp_path, "writer.git", origin))
    assert first["previous_receipt_sha256"] is None


def test_posix_selection_is_unchanged(tmp_path, monkeypatch):
    for variable in ("STEGVERSE_ORG_LEDGER_STORE", "STEGVERSE_ORG_LEDGER_ROOT"):
        monkeypatch.delenv(variable, raising=False)
    with pytest.raises(org.LedgerLocationRequired) as refused:
        org.organization_store()
    assert refused.value.failed_predicate == "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "root"))
    store = org.organization_store()
    assert store.kind == "POSIX_FILESYSTEM" and store.root == (tmp_path / "root").resolve()
    record = org.aggregate_transition(receipt("CLAIM"))
    head = json.loads((tmp_path / "root" / "HEAD.json").read_text())
    assert head["receipt_path"] == str((tmp_path / "root" / store_module.receipt_key(record["receipt_sha256"])).resolve())
    assert (tmp_path / "root" / store_module.source_key(record["source_transition_sha256"])).is_file()
    assert custody.verified_organization_receipt(
        None, record["receipt_sha256"], state_receipt_sha256=record["source_transition_sha256"]) == record

    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_STORE", "kv")
    with pytest.raises(org.LedgerStoreSelectionInvalid) as invalid:
        org.organization_store()
    assert org.location_refusal(invalid.value)["failed_predicate"] == "ORGANIZATION_LEDGER_STORE_SELECTION_INVALID"
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_STORE", "git")
    with pytest.raises(org.LedgerLocationRequired) as missing:
        org.organization_store()
    assert missing.value.variable == "STEGVERSE_ORG_LEDGER_GIT_DIR"
