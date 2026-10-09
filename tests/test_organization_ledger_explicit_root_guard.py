"""OL-3: an explicit POSIX Organization ledger root never forks the declared chain.

OL-2 routed every production Organization ledger read through
organization_store(), and ledger_root() fails closed under the repository's
declared {store: git}. Two callers still accepted a caller-supplied POSIX root
and appended to and read it directly: the claim consumer
(scripts/consume_org_claim_allocator_request.py --org-ledger-root) and the
federation cycle (resident-runtime/federation_cycle.py org_ledger_root). Under
a declared non-posix store such a root would be a second chain beside the
declared one.

Under the repository's own git declaration (`repository_ledger_locus`), on
temporary bare Git repositories, these tests assert that an explicit POSIX root
is FAIL_CLOSED ORGANIZATION_LEDGER_STORE_KIND_MISMATCH before anything is read
or appended -- the decoy root is never read or written and neither store gains
a receipt -- that without an explicit root the declared store is used, and
that under a declared {store: posix} an explicit root behaves as before. No
real ledger ref is created and no runtime ALLOW is claimed.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "workers"), str(ROOT / "resident-runtime")]

import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batch_custody  # noqa: E402
from tests import test_org_claim_custody as claim  # noqa: E402

REF = "refs/heads/organization-ledger/StegVerse-Labs"
KIND_MISMATCH = "ORGANIZATION_LEDGER_STORE_KIND_MISMATCH"
LOCUS_VARIABLES = ("STEGVERSE_ORG_LEDGER_STORE", "STEGVERSE_ORG_LEDGER_GIT_REF",
                   "STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY")
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "ol3-explicit-root", "predecessor": None}


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cycle = load("ol3_federation_cycle", "resident-runtime/federation_cycle.py")
kernel = cycle.K
ORGANIZATION = kernel.load_registry(ROOT)["organization"]
CONTROL = kernel.organization_slug(ORGANIZATION) + ".org-control"


def bare(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-q", str(path)], check=True)
    return path


def ref_tip(node: Path) -> str | None:
    found = subprocess.run(["git", "--git-dir", str(node), "rev-parse", "-q", "--verify", REF],
                           capture_output=True, text=True)
    return found.stdout.strip() if found.returncode == 0 else None


def decoy(path: Path) -> Path:
    """A POSIX root whose HEAD names a receipt that does not exist: unreadable if read."""
    (path / "receipts").mkdir(parents=True, exist_ok=True)
    (path / "HEAD.json").write_text(json.dumps({"organization": "StegVerse-Labs",
                                                "receipt_sha256": "sha256:" + "0" * 64}))
    return path


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def git_store(node: Path):
    return org.ledger_store.GitLedgerStore(node, REF, custody="PRIVATE")


def receipt(name: str) -> dict:
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": name,
        "transition_sequence": 1,
        "subject_or_correlation_id": "ol3-explicit-root",
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [],
    }


def publish(mesh: Path, communication_id: str) -> None:
    packet = kernel.build_packet(
        origin_org="Origin", origin_service="origin.org-control",
        destination_org=ORGANIZATION, destination_service=CONTROL,
        payload={"communication_id": communication_id, "message_class": "ecosystem.communication",
                 "subject": "s", "body": {}},
        standing=GENESIS, packet_id=communication_id + ":c")
    kernel.publish_packet(packet, root=mesh, epoch=kernel.HB_ANCHOR_EPOCH + 700)


@pytest.fixture
def git_declared(tmp_path, monkeypatch):
    """The repository's own git declaration on a temporary local repository, with a POSIX decoy."""
    for variable in LOCUS_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    node = bare(tmp_path / "node.git")
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_DIR", str(node))
    posix = decoy(tmp_path / "posix-decoy")
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(posix))
    assert org.declared_ledger_locus()["store"] == "git"
    return node, posix, snapshot(posix)


# --- the central guard ------------------------------------------------------

@pytest.mark.repository_ledger_locus
def test_an_explicit_posix_root_is_refused_by_every_organization_store_entry(git_declared):
    node, posix, before = git_declared
    with pytest.raises(org.LedgerStoreKindMismatch) as refused:
        org.organization_store(posix)
    assert refused.value.failed_predicate == KIND_MISMATCH
    refusal = org.location_refusal(refused.value)
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["failed_predicate"] == KIND_MISMATCH
    assert refusal["required_evidence_or_repair"] == org.EXPLICIT_ROOT_REPAIR
    assert refusal["retry_entrypoint"]
    with pytest.raises(org.LedgerStoreKindMismatch):
        org.aggregate_transition(receipt("FORK"), ledger=posix)
    with pytest.raises(org.LedgerStoreKindMismatch):
        batch_custody.current_chain(posix)
    with pytest.raises(batch_custody.OrganizationReceiptRefused) as readback:
        batch_custody.verified_organization_receipt(posix, "sha256:" + "1" * 64,
                                                    state_receipt_sha256="sha256:" + "2" * 64)
    assert readback.value.refusal()["disposition"] == "FAIL_CLOSED"
    assert readback.value.refusal()["failed_predicate"] == KIND_MISMATCH
    # A store the caller holds is still used as is, and nothing reached either store.
    assert org.organization_store(git_store(node)).kind == "GIT_REF"
    assert ref_tip(node) is None
    assert snapshot(posix) == before


@pytest.mark.repository_ledger_locus
def test_functional_memory_refuses_an_explicit_posix_root(git_declared):
    from heartbeat_runtime import worker_assignment_functional_memory as memory
    from workers.canonical_state_transition_custody import organization_receipt_custody

    node, posix, before = git_declared
    custody = organization_receipt_custody()
    with pytest.raises(custody.OrganizationReceiptRefused) as refused:
        memory._ledger(custody, posix)
    assert refused.value.refusal()["failed_predicate"] == KIND_MISMATCH
    assert refused.value.refusal()["disposition"] == "FAIL_CLOSED"
    assert ref_tip(node) is None
    assert snapshot(posix) == before


# --- the federation cycle ---------------------------------------------------

@pytest.mark.repository_ledger_locus
def test_federation_cycle_refuses_an_explicit_posix_root_under_git(git_declared, tmp_path):
    node, posix, before = git_declared
    mesh, state, repo = tmp_path / "mesh", tmp_path / "node-state", tmp_path / "repo-ledger"
    publish(mesh, "ol3-explicit")
    report = cycle.cycle(mesh_root=mesh, node_state_root=state, repo_ledger_root=repo, org_ledger_root=posix)
    assert report["disposition"] == "FAIL_CLOSED"
    assert report["failed_predicate"] == KIND_MISMATCH
    assert report["required_evidence_or_repair"] == org.EXPLICIT_ROOT_REPAIR
    assert report["retry_entrypoint"] == "resident-runtime/federation_cycle.py::main"
    assert report["consequence_committed"] is False
    # Nothing consumed, recorded or appended anywhere.
    assert len(kernel.scan_addressed_frames(ORGANIZATION, root=mesh)) == 1
    assert not state.exists() and not repo.exists()
    assert ref_tip(node) is None
    assert snapshot(posix) == before
    with pytest.raises(ValueError) as custody_refused:
        kernel.crossing_custody(ROOT, repo_ledger_root=repo, org_ledger_root=posix)
    assert custody_refused.value.failed_predicate == KIND_MISMATCH


@pytest.mark.repository_ledger_locus
def test_federation_cycle_without_an_explicit_root_appends_to_the_declared_store(git_declared, tmp_path):
    node, posix, before = git_declared
    mesh, state, repo = tmp_path / "mesh", tmp_path / "node-state", tmp_path / "repo-ledger"
    publish(mesh, "ol3-declared")
    report = cycle.cycle(mesh_root=mesh, node_state_root=state, repo_ledger_root=repo)
    assert report["frames_consumed"] == 1
    assert report["organization_receipts_recorded"] == 1
    head = git_store(node).get(org.ledger_store.HEAD_KEY)
    assert head is not None and ref_tip(node) is not None
    rows = git_store(node).list_prefix(org.ledger_store.RECEIPT_PREFIX)
    assert len(rows) == 1
    # The materializer's STEGVERSE_ORG_LEDGER_ROOT is not the declared store and is untouched.
    assert snapshot(posix) == before


@pytest.mark.repository_ledger_locus
def test_federation_cycle_without_a_materialized_store_fails_closed(git_declared, tmp_path, monkeypatch):
    node, posix, before = git_declared
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_GIT_DIR")
    mesh = tmp_path / "mesh"
    publish(mesh, "ol3-unmaterialized")
    report = cycle.cycle(mesh_root=mesh, node_state_root=tmp_path / "node-state",
                         repo_ledger_root=tmp_path / "repo-ledger")
    assert report["disposition"] == "FAIL_CLOSED"
    assert report["failed_predicate"] == "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"
    assert "STEGVERSE_ORG_LEDGER_GIT_DIR" in report["required_evidence_or_repair"]
    assert len(kernel.scan_addressed_frames(ORGANIZATION, root=mesh)) == 1
    assert ref_tip(node) is None
    assert snapshot(posix) == before


def test_federation_cycle_explicit_root_under_posix_is_unchanged(tmp_path):
    mesh, ledgers = tmp_path / "mesh", tmp_path / "ledgers"
    publish(mesh, "ol3-posix")
    report = cycle.cycle(mesh_root=mesh, node_state_root=tmp_path / "node-state",
                         repo_ledger_root=ledgers / "repo", org_ledger_root=ledgers / "org")
    assert report["frames_consumed"] == 1
    assert report["organization_receipts_recorded"] == 1
    assert len(list((ledgers / "org" / "receipts").glob("*.json"))) == 1
    assert json.loads((ledgers / "org" / "HEAD.json").read_text())["organization"] == ORGANIZATION


# --- the claim consumer -----------------------------------------------------

def claim_env(tmp_path: Path, posix: Path):
    """A claim consumer source and runtime whose supplied POSIX root is the decoy."""
    return claim.Env(tmp_path / "claim", org_ledger=posix)


@pytest.mark.repository_ledger_locus
def test_claim_consumer_refuses_an_explicit_posix_root_under_git(git_declared, tmp_path):
    node, posix, _ = git_declared
    env = claim_env(tmp_path, posix)
    before = snapshot(posix)
    result = env.consume()
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == KIND_MISMATCH
    assert result["required_evidence_or_repair"] == org.EXPLICIT_ROOT_REPAIR
    assert result["retry_entrypoint"] == claim.consumer.RETRY_ENTRYPOINT
    assert result["fence_issued"] is False and result["consequence_committed"] is False
    # Refused before anything is read or appended: no repository receipt, no
    # organization receipt, no runtime materialization, the decoy untouched.
    assert not env.repo.exists()
    assert not (env.runtime / "tasks").exists()
    assert ref_tip(node) is None
    assert snapshot(posix) == before
    with pytest.raises(claim.consumer.OrganizationLedgerNotAdmitted):
        claim.consumer.ledger_custody(env.source, env.repo, posix)


@pytest.mark.repository_ledger_locus
def test_claim_consumer_without_an_explicit_root_grants_on_the_declared_store(git_declared, tmp_path):
    node, posix, _ = git_declared
    env = claim_env(tmp_path, posix)
    before = snapshot(posix)
    # Root the declared chain through the existing emitters, as the POSIX tests do.
    claim.seed_rooted_chain(env.source, None, tmp_path / "seed-repo-ledger")
    seeded = ref_tip(node)
    assert seeded is not None
    result = env.consume(org=None)
    assert result["disposition"] == "ALLOW", result
    assert result["fence_issued"] is True and result["fencing_token"] == 8
    assert result["organization_readback"] == "VERIFIED"
    store = git_store(node)
    granted = store.get(org.ledger_store.receipt_key(result["organization_receipt_sha256"]))
    assert granted["boundary_evidence"]["fencing_token"] == 8
    assert store.get(org.ledger_store.HEAD_KEY)["receipt_sha256"] == result["organization_receipt_sha256"]
    assert ref_tip(node) != seeded
    # The chain the next attempt verifies is the declared store's.
    custody = claim.consumer.ledger_custody(env.source, env.repo, None)
    assert custody["organization_root"] is None and custody["organization_store"].kind == "GIT_REF"
    assert [row["boundary_evidence"]["fencing_token"] for row in claim.consumer.chain_grants(
        claim.consumer.verify_organization_chain(custody))] == [8]
    # Consuming the same request again returns the retained grant; no fence is reissued.
    tip = ref_tip(node)
    again = env.consume(org=None)
    assert again["fencing_token"] == 8
    assert again["organization_receipt_sha256"] == result["organization_receipt_sha256"]
    assert ref_tip(node) == tip
    assert snapshot(posix) == before


@pytest.mark.repository_ledger_locus
def test_claim_consumer_on_an_empty_declared_store_fails_closed_unextended(git_declared, tmp_path):
    node, posix, _ = git_declared
    env = claim_env(tmp_path, posix)
    before = snapshot(posix)
    result = env.consume(org=None)
    assert result["disposition"] == "FAIL_CLOSED"
    assert result["failed_predicate"] == "LEDGER_HEAD_OR_FENCE_HISTORY_UNVERIFIED"
    assert "organization chain empty" in result["detail"]
    assert result["organization_receipt_appended"] is False
    assert ref_tip(node) is None
    assert snapshot(posix) == before


def test_claim_consumer_explicit_root_under_posix_is_unchanged(tmp_path):
    env = claim.Env(tmp_path / "claim")
    custody = env.custody()
    assert custody["organization_root"] == env.org.resolve() and custody["organization_store"] is None
    result = env.consume()
    assert result["disposition"] == "ALLOW"
    assert result["fencing_token"] == 8
    assert (env.org / "HEAD.json").is_file()
    # Without the explicit root a posix declaration still refuses, as before.
    bare_env = claim.Env(tmp_path / "unsupplied", seed=False)
    refused = claim.consumer.consume(bare_env.source, bare_env.runtime, repo_ledger_root=bare_env.repo,
                                     env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")})
    assert refused["failed_predicate"] == "LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"
    assert refused["required_evidence_or_repair"] == "supply --repo-ledger-root and --org-ledger-root"
