"""G1-R: the Organization ledger on a dedicated Git ref, appended by ref compare-and-swap.

Every repository here is a temporary bare repository; no production ledger ref
is created. Git is transport and custody only: a published commit is not an
ALLOW, and a refused publication is a typed FAIL_CLOSED that commits nothing.

F75-01: an append is authoritative on the node's local ledger ref by local
`update-ref` compare-and-swap; the shared remote is never read or written
inside a transition. A node is seeded by the explicit `materialize` step before
invocation and carries its appends by the explicit `propagate` step after.
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
    """An ephemeral execution's own ledger, materialized from the shared remote before invocation."""
    store = store_module.GitLedgerStore(bare(tmp_path / name), REF, remote=str(origin), custody=custody_class)
    assert store.materialize()["disposition"] == "MATERIALIZED"
    return store


def propagated(store) -> dict:
    """Carry a node's completed local appends to the remote, after the transition."""
    result = store.propagate()
    assert result["disposition"] == "PROPAGATED", result
    return result


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
    # The appends completed locally; the remote was not touched until propagation.
    assert remote_tip(origin) is None
    assert remote_tip(writer.git_dir) is not None
    propagated(writer)

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
    assert remote_tip(origin) is None, "the remote is never awaited or written by the transition"
    row = custody.verified_organization_receipt(
        None, record["receipt_sha256"], state_receipt_sha256=record["source_transition_sha256"])
    assert row == record
    assert not any(tmp_path.rglob("HEAD.json"))
    propagated(org.organization_store())
    assert remote_tip(origin) == remote_tip(tmp_path / "node.git")


def test_concurrent_append_lost_race_is_typed_fail_closed_with_no_partial_write(tmp_path, origin):
    # Two appenders on one node's local ledger: the local update-ref CAS is the
    # serialization, and the configured remote plays no part in it.
    org.aggregate_transition(receipt("GENESIS"), ledger=node(tmp_path, "local.git", origin))
    slow = store_module.GitLedgerStore(tmp_path / "local.git", REF, remote=str(origin), custody="PRIVATE")
    fast = store_module.GitLedgerStore(tmp_path / "local.git", REF, remote=str(origin), custody="PRIVATE")
    local = tmp_path / "local.git"
    with slow.exclusive():
        # Both read the same tip; the fast appender publishes first.
        won = org.aggregate_transition(receipt("FAST"), ledger=fast)
        before = remote_files(local)
        with pytest.raises(store_module.LedgerStoreRefused) as lost:
            org._aggregate_transition_locked(receipt("SLOW"), store=slow)
    refusal = org.store_refusal(lost.value)
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["failed_predicate"] == "ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP"
    assert refusal["retry_entrypoint"] == "resident-runtime/aggregate_repo_transition.py::aggregate_transition"
    assert refusal["consequence_committed"] is False
    # Nothing of the losing append reached the ref: no receipt, no source, no HEAD.
    assert remote_files(local) == before
    assert json.loads(git(local, "cat-file", "blob", REF + ":HEAD.json"))["receipt_sha256"] == won["receipt_sha256"]
    slow_source = store_module.source_key(org.verify_source(receipt("SLOW"))["source_transition_sha256"])
    assert slow_source not in before
    # Its retry re-reads the ref and appends on the winner.
    retried = org.aggregate_transition(receipt("SLOW"), ledger=slow)
    assert retried["previous_receipt_sha256"] == won["receipt_sha256"]
    assert remote_tip(origin) is None, "no append awaited or wrote the remote"


def test_divergent_nodes_complete_locally_and_propagation_detects_the_fork(tmp_path, origin):
    seed = node(tmp_path, "seed.git", origin)
    org.aggregate_transition(receipt("GENESIS"), ledger=seed)
    propagated(seed)
    slow = node(tmp_path, "slow.git", origin)
    fast = node(tmp_path, "fast.git", origin)
    org.aggregate_transition(receipt("FAST"), ledger=fast)
    propagated(fast)
    published = remote_tip(origin)
    # The slow node's append completes on its own ledger; the remote is not a predicate.
    local = org.aggregate_transition(receipt("SLOW"), ledger=slow)
    assert slow.get(store_module.HEAD_KEY)["receipt_sha256"] == local["receipt_sha256"]
    fork = slow.propagate()
    assert fork["disposition"] == "FAIL_CLOSED"
    assert fork["failed_predicate"] == "ORGANIZATION_LEDGER_FORK_DETECTED"
    assert fork["retry_entrypoint"] == "resident-runtime/ledger_store.py::GitLedgerStore.propagate"
    assert fork["remote_tip"] == published and fork["local_tip"] == remote_tip(slow.git_dir)
    # Detected, not prevented or repaired: neither side is rewritten.
    assert remote_tip(origin) == published
    assert slow.get(store_module.HEAD_KEY)["receipt_sha256"] == local["receipt_sha256"]
    assert slow.propagate() == fork, "an exact retry reports the same fork"
    # Seeding the diverged node from the remote is refused the same way.
    assert slow.materialize()["failed_predicate"] == "ORGANIZATION_LEDGER_FORK_DETECTED"
    assert slow.get(store_module.HEAD_KEY)["receipt_sha256"] == local["receipt_sha256"]


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
    propagated(writer)
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
    writer = node(tmp_path, "writer.git", origin)
    record = org.aggregate_transition(receipt("CLAIM"), ledger=writer)
    propagated(writer)
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
    one = node(tmp_path, "one.git", origin)
    first = org.aggregate_transition(receipt("CLAIM"), ledger=one)
    propagated(one)
    tip = remote_tip(origin)
    # The same exact source, replayed from another node at a later heartbeat.
    two = node(tmp_path, "two.git", origin)
    again = org.aggregate_transition(receipt("CLAIM"), ledger=two, hb_epoch=999)
    assert again == first
    assert remote_tip(two.git_dir) == tip
    assert propagated(two)["remote_tip"] == tip
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


def test_unreachable_remote_does_not_block_the_local_append_and_propagation_fails_closed(tmp_path):
    absent = tmp_path / "absent.git"
    store = store_module.GitLedgerStore(bare(tmp_path / "node.git"), REF, remote=str(absent), custody="PRIVATE")
    # Seeding is an explicit step before invocation; an unreachable remote is a typed refusal there.
    seeded = store.materialize()
    assert seeded["disposition"] == "FAIL_CLOSED"
    assert seeded["failed_predicate"] == "ORGANIZATION_LEDGER_REMOTE_UNREACHABLE"
    assert seeded["retry_entrypoint"] == "resident-runtime/ledger_store.py::GitLedgerStore.materialize"
    # The transition never awaits the remote: the append completes on the local ledger.
    record = org.aggregate_transition(receipt("CLAIM"), ledger=store)
    tip = remote_tip(store.git_dir)
    assert custody.verified_organization_receipt(
        store, record["receipt_sha256"], state_receipt_sha256=record["source_transition_sha256"]) == record
    failed = store.propagate()
    assert failed["disposition"] == "FAIL_CLOSED"
    assert failed["failed_predicate"] == "ORGANIZATION_LEDGER_REMOTE_UNREACHABLE"
    assert failed["retry_entrypoint"] == "resident-runtime/ledger_store.py::GitLedgerStore.propagate"
    assert failed["local_tip"] == tip and failed["authority_effect"] == "NONE_CUSTODY_TRANSPORT_ONLY"
    # The failed propagation neither undid nor blocked the local ledger.
    assert remote_tip(store.git_dir) == tip
    second = org.aggregate_transition(receipt("WORK"), ledger=store)
    assert second["previous_receipt_sha256"] == record["receipt_sha256"]
    # Once the remote is reachable, the retry entrypoint carries the whole local chain.
    bare(absent)
    assert propagated(store)["remote_tip"] == remote_tip(store.git_dir)
    assert remote_tip(absent) == remote_tip(store.git_dir)
    # An exact retry of propagation is idempotent.
    assert propagated(store)["remote_tip"] == remote_tip(absent)
    assert git(absent, "rev-list", "--count", REF) == "2"


def test_propagation_requires_private_custody_and_a_supplied_remote(tmp_path, origin):
    writer = node(tmp_path, "writer.git", origin)
    org.aggregate_transition(receipt("CLAIM"), ledger=writer)
    public = store_module.GitLedgerStore(writer.git_dir, REF, remote=str(origin), custody="PUBLIC")
    with pytest.raises(store_module.LedgerStoreRefused) as refused:
        public.propagate()
    assert refused.value.failed_predicate == "ORGANIZATION_LEDGER_PRIVATE_CUSTODY_SURFACE_REQUIRED"
    assert remote_tip(origin) is None
    unconfigured = store_module.GitLedgerStore(writer.git_dir, REF, custody="PRIVATE")
    assert unconfigured.propagate()["failed_predicate"] == "ORGANIZATION_LEDGER_REMOTE_NOT_SUPPLIED"
    assert remote_tip(origin) is None


def test_invalid_manifested_packet_on_git_store_commits_nothing(tmp_path, origin):
    with pytest.raises(ValueError, match="receipt_batch policy required"):
        org.aggregate_transition(receipt("CLAIM"), ledger=node(tmp_path, "node.git", origin), parent_manifest={})
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


# --- G1-R2: packet release and batch custody carried by the Git ledger store ---

sys.path.insert(0, str(ROOT))
from heartbeat_runtime import independent_oscillator as osc  # noqa: E402
import organization_custody_readback as readback_module  # noqa: E402

T0_EPOCH = osc.PROTOCOL_ANCHOR_EPOCH + 1_000


def hb_now_ns(epoch: int) -> int:
    return osc.PROTOCOL_ANCHOR_UNIX_NS + (epoch - osc.PROTOCOL_ANCHOR_EPOCH) * osc.OSCILLATOR_PERIOD_NS


def manifest(count: int = 2) -> dict:
    return {
        "schema": "test.parent-manifest/v1",
        "receipt_batch": {
            "release_condition": {"type": "COUNT", "count": count},
            "establishment": {"heartbeat_id": osc.encode_heartbeat_id(T0_EPOCH), "expiry_delta_heartbeats": 500},
        },
    }


@pytest.fixture
def carried(monkeypatch):
    """The released batch's custody carriage, recorded rather than transported."""
    calls = []

    def submit(root, batch_id):
        calls.append(batch_id)
        return {"state": "COMPLETED", "execution_result": "COMPLETED", "batch_id": batch_id,
                "governance_disposition": None, "authority_effect": "NONE_ORGANIZATION_RECORD_ONLY"}

    monkeypatch.setattr(custody, "submit_released_batch", submit)
    return calls


def open_packet(writer, parent, count=2):
    """Establish a packet at t(0) and fill it to its COUNT, one commit per append."""
    t0 = org.aggregate_transition(receipt("FOUR-PART-ASSIGNMENT"), ledger=writer, parent_manifest=parent,
                                  establishes_packet=True, now_ns=hb_now_ns(T0_EPOCH))
    work = [org.aggregate_transition(receipt("WORK-1" + "b" * index), ledger=writer, parent_manifest=parent,
                                     now_ns=hb_now_ns(T0_EPOCH + 1)) for index in range(count - 1)]
    return (t0, *work)


def tamper(tmp_path, origin, key, value):
    blob = git(origin, "hash-object", "-w", "--stdin", data=json.dumps(value, indent=2, sort_keys=True).encode() + b"\n")
    index = {"GIT_INDEX_FILE": str(tmp_path / ("tamper-index-" + key.replace("/", "-")))}
    git(origin, "read-tree", REF, env=index)
    git(origin, "update-index", "--add", "--cacheinfo", "100644," + blob + "," + key, env=index)
    commit = git(origin, "commit-tree", git(origin, "write-tree", env=index), "-p", REF, "-m", "tamper", env=IDENTITY)
    git(origin, "update-ref", REF, commit)


def test_manifested_release_and_establishment_publish_as_one_commit_and_read_back(tmp_path, origin, carried):
    parent = manifest()
    writer = node(tmp_path, "writer.git", origin)
    t0, work1 = open_packet(writer, parent)
    assert t0["boundary_evidence"][custody.ESTABLISHMENT_KEY]["establishment_kind"] == "MANIFEST_ASSIGNMENT_T0"
    propagated(writer)
    before = remote_tip(origin)

    # The next transition releases the satisfied packet, from a node sharing no filesystem.
    following = node(tmp_path, "next.git", origin)
    work2 = org.aggregate_transition(receipt("WORK-2"), ledger=following,
                                     parent_manifest=parent, now_ns=hb_now_ns(T0_EPOCH + 2))
    assert len(carried) == 1
    assert remote_tip(origin) == before, "the release completed locally without awaiting the remote"
    propagated(following)
    tip = remote_tip(origin)
    assert git(origin, "rev-parse", tip + "^") == before, "the release is exactly one commit on the prior tip"
    reader = node(tmp_path, "reader.git", origin, custody_class=None)
    batch_head = reader.get(custody.BATCH_HEAD_KEY)
    released = custody._verified_batch(reader, batch_head["batch_id"])
    assert released["batch_id"] == carried[0]
    assert released["ordered_receipt_hashes"] == [t0["receipt_sha256"], work1["receipt_sha256"]]
    assert released["closure_reason"] == "MANIFEST_RELEASE_CONDITION"
    establishment = reader.get(store_module.receipt_key(work2["previous_receipt_sha256"]))
    assert establishment["org_transition_class"] == "ORGANIZATION_RECEIPT_PACKET_ESTABLISHMENT"
    record = establishment["boundary_evidence"][custody.ESTABLISHMENT_KEY]
    assert record["establishment_kind"] == "PRIOR_PACKET_RELEASE"
    assert record["released_batch"]["batch_id"] == released["batch_id"]
    changed = set(git(origin, "diff-tree", "--no-commit-id", "--name-only", "-r", tip).splitlines())
    assert changed == {
        "HEAD.json", custody.BATCH_HEAD_KEY, custody._batch_key(released["batch_id"]),
        store_module.receipt_key(establishment["receipt_sha256"]),
        store_module.source_key(establishment["source_transition_sha256"]),
        store_module.receipt_key(work2["receipt_sha256"]),
        store_module.source_key(work2["source_transition_sha256"]),
    }

    # Every read comes back from the committed ref.
    assert custody.verify_batch(reader, released["batch_id"])["organization_chain"] == "PASS"
    exported = custody.export_batch_record(reader, released["batch_id"])
    assert exported["local_verification"]["source_reconstruction"] == "SOURCE_DIGESTS_AND_REQUIRED_EVIDENCE_BYTES_PASS"
    state = custody.open_packet_state(parent, root=reader, now_ns=hb_now_ns(T0_EPOCH + 2))
    assert state["receipt_count"] == 2 and state["release_condition_satisfied"] is True
    snapshot = readback_module.readback(reader, correlation_ids=("WORK-2",))
    assert snapshot["state"] == "VERIFIED_LOCAL_READBACK"
    assert snapshot["receipt_count"] == 4 and snapshot["batch_count"] == 1
    assert snapshot["last_batch_id"] == released["batch_id"]
    assert snapshot["head_receipt_sha256"] == work2["receipt_sha256"]
    assert [m["source_transition_id"] for m in snapshot["matching_transitions"]] == ["WORK-2"]
    assert custody.verified_organization_receipt(
        reader, work2["receipt_sha256"], state_receipt_sha256=work2["source_transition_sha256"],
        expected_transition_id="WORK-2") == work2


def test_release_lost_race_is_typed_fail_closed_with_no_orphan_batch(tmp_path, origin, carried, monkeypatch):
    # Two appenders on one node's local ledger: the release's staged commit
    # loses the local update-ref CAS (a cross-node divergence is a fork at
    # propagation instead; see the divergent-nodes test).
    parent = manifest(count=3)
    slow = node(tmp_path, "local.git", origin)
    open_packet(slow, parent, count=3)
    fast = store_module.GitLedgerStore(slow.git_dir, REF, remote=str(origin), custody="PRIVATE")
    local = slow.git_dir
    raced = {}
    submit = custody.submit_released_batch

    def race(root, batch_id):
        # The slow node has pinned its tip and staged its release; the fast node
        # releases the same packet and publishes first.
        if not raced:
            raced["started"] = True
            raced["won"] = org.aggregate_transition(receipt("FAST"), ledger=fast, parent_manifest=parent,
                                                    now_ns=hb_now_ns(T0_EPOCH + 2))
            raced["files"] = remote_files(local)
            raced["tip"] = remote_tip(local)
        return submit(root, batch_id)

    monkeypatch.setattr(custody, "submit_released_batch", race)
    with pytest.raises(store_module.LedgerStoreRefused) as lost:
        org.aggregate_transition(receipt("SLOW"), ledger=slow, parent_manifest=parent, now_ns=hb_now_ns(T0_EPOCH + 2))
    refusal = org.store_refusal(lost.value)
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["failed_predicate"] == "ORGANIZATION_LEDGER_REF_COMPARE_AND_SWAP"
    assert refusal["consequence_committed"] is False
    # Nothing of the losing transition reached the ref: no second batch, no
    # BATCH_HEAD move, no establishment or work receipt.
    assert remote_tip(local) == raced["tip"]
    assert remote_files(local) == raced["files"]
    assert len([name for name in raced["files"] if name.startswith(custody.BATCH_PREFIX)]) == 1
    slow_source = store_module.source_key(org.verify_source(receipt("SLOW"))["source_transition_sha256"])
    assert slow_source not in raced["files"]
    # The retry re-reads the ref: the packet is already released, so it appends on the winner.
    retried = org.aggregate_transition(receipt("SLOW"), ledger=slow, parent_manifest=parent,
                                       now_ns=hb_now_ns(T0_EPOCH + 2))
    assert retried["previous_receipt_sha256"] == raced["won"]["receipt_sha256"]
    assert "parent_manifest_released_batch" not in retried["boundary_evidence"]
    assert remote_tip(origin) is None, "no transition awaited or wrote the remote"


def test_release_replay_is_idempotent_on_the_git_store(tmp_path, origin, carried):
    # COUNT 3, so the successor packet (establishment + WORK-2) is still open at the replay.
    parent = manifest(count=3)
    writer = node(tmp_path, "writer.git", origin)
    open_packet(writer, parent, count=3)
    work2 = org.aggregate_transition(receipt("WORK-2"), ledger=writer, parent_manifest=parent,
                                     now_ns=hb_now_ns(T0_EPOCH + 2))
    propagated(writer)
    tip = remote_tip(origin)
    two = node(tmp_path, "two.git", origin)
    again = org.aggregate_transition(receipt("WORK-2"), ledger=two,
                                     parent_manifest=parent, now_ns=hb_now_ns(T0_EPOCH + 3), hb_epoch=999)
    assert again == work2
    assert remote_tip(two.git_dir) == tip
    assert remote_tip(origin) == tip
    assert len(carried) == 1, "an exact replay does not release or carry the batch again"
    # Closing the already-closed batch for the same reason is the same batch, not a second one.
    batch_id = writer.get(custody.BATCH_HEAD_KEY)["batch_id"]
    released = custody._verified_batch(writer, batch_id)
    head = writer.get(store_module.HEAD_KEY)
    assert head["receipt_sha256"] == work2["receipt_sha256"]
    assert released["last_org_receipt_sha256"] != head["receipt_sha256"]


def test_close_batch_on_the_git_store_is_one_commit_and_needs_private_custody(tmp_path, origin):
    writer = node(tmp_path, "writer.git", origin)
    first = org.aggregate_transition(receipt("CLAIM"), ledger=writer)
    propagated(writer)
    tip = remote_tip(origin)
    public = node(tmp_path, "public.git", origin, "PUBLIC")
    with pytest.raises(store_module.LedgerStoreRefused) as refused:
        custody.close_batch("TASK_CLOSURE", root=public)
    assert refused.value.failed_predicate == "ORGANIZATION_LEDGER_PRIVATE_CUSTODY_SURFACE_REQUIRED"
    assert remote_tip(public.git_dir) == tip
    assert remote_tip(origin) == tip

    closed = custody.close_batch("TASK_CLOSURE", root=writer)
    assert remote_tip(origin) == tip, "the close completed locally without awaiting the remote"
    propagated(writer)
    assert git(origin, "rev-parse", remote_tip(origin) + "^") == tip
    changed = set(git(origin, "diff-tree", "--no-commit-id", "--name-only", "-r", remote_tip(origin)).splitlines())
    assert changed == {custody.BATCH_HEAD_KEY, custody._batch_key(closed["batch_id"])}
    assert closed["ordered_receipt_hashes"] == [first["receipt_sha256"]]
    after = remote_tip(origin)
    again = node(tmp_path, "again.git", origin)
    assert custody.close_batch("TASK_CLOSURE", root=again) == closed
    assert remote_tip(again.git_dir) == after, "an idempotent close publishes nothing"
    assert remote_tip(origin) == after
    with pytest.raises(ValueError, match="conflicting batch closure"):
        custody.close_batch("WORKER_EXPIRY", root=writer)


def test_tampered_batch_or_batch_head_on_the_ref_is_refused(tmp_path, origin, carried):
    parent = manifest()
    writer = node(tmp_path, "writer.git", origin)
    open_packet(writer, parent)
    org.aggregate_transition(receipt("WORK-2"), ledger=writer, parent_manifest=parent, now_ns=hb_now_ns(T0_EPOCH + 2))
    propagated(writer)
    reader = node(tmp_path, "reader.git", origin, custody_class=None)
    batch_id = reader.get(custody.BATCH_HEAD_KEY)["batch_id"]
    released = custody._verified_batch(reader, batch_id)

    tamper(tmp_path, origin, custody._batch_key(batch_id), dict(released, acknowledgement_state="ACCEPTED"))
    reader.materialize()
    with pytest.raises(ValueError, match="organization batch hash mismatch"):
        custody.verify_batch(reader, batch_id)
    with pytest.raises(ValueError, match="organization batch hash mismatch"):
        custody.open_packet_state(parent, root=reader, now_ns=hb_now_ns(T0_EPOCH + 3))
    with pytest.raises(ValueError):
        readback_module.readback(reader, correlation_ids=("WORK-2",))
    tip = remote_tip(origin)
    with pytest.raises(ValueError):
        org.aggregate_transition(receipt("WORK-3"), ledger=node(tmp_path, "next.git", origin),
                                 parent_manifest=parent, now_ns=hb_now_ns(T0_EPOCH + 3))
    assert remote_tip(origin) == tip

    tamper(tmp_path, origin, custody._batch_key(batch_id), released)
    tamper(tmp_path, origin, custody.BATCH_HEAD_KEY,
           {"organization": org.C["organization"], "batch_id": batch_id,
            "last_org_receipt_sha256": "sha256:" + "0" * 64})
    reader.materialize()
    with pytest.raises(ValueError, match="organization batch HEAD mismatch"):
        custody.open_packet_state(parent, root=reader, now_ns=hb_now_ns(T0_EPOCH + 3))

    # An unindexed batch on the ref is an orphan, not history.
    tamper(tmp_path, origin, custody.BATCH_HEAD_KEY,
           {"organization": org.C["organization"], "batch_id": batch_id,
            "last_org_receipt_sha256": released["last_org_receipt_sha256"]})
    tamper(tmp_path, origin, custody._batch_key("sha256:" + "1" * 64), released)
    reader.materialize()
    with pytest.raises(ValueError, match="ORGANIZATION_BATCH_ORPHAN_DETECTED"):
        readback_module.readback(reader, correlation_ids=("WORK-2",))


def test_manifested_packet_on_a_non_private_surface_is_refused_before_carriage(tmp_path, origin, carried):
    parent = manifest()
    writer = node(tmp_path, "writer.git", origin)
    open_packet(writer, parent)
    propagated(writer)
    tip = remote_tip(origin)
    for declared in (None, "PUBLIC"):
        with pytest.raises(store_module.LedgerStoreRefused) as refused:
            org.aggregate_transition(receipt("WORK-2"), ledger=node(tmp_path, f"n{declared}.git", origin, declared),
                                     parent_manifest=parent, now_ns=hb_now_ns(T0_EPOCH + 2))
        assert refused.value.failed_predicate == "ORGANIZATION_LEDGER_PRIVATE_CUSTODY_SURFACE_REQUIRED"
    assert carried == [], "the released batch is not carried from a surface not declared private"
    assert remote_tip(origin) == tip
