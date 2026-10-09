"""OL-2: every production Organization ledger read addresses the store the append uses.

The repository's Organization manifest declares the Git store
(org-contract.json organization_ledger). Before OL-2, appends went to that
store while the resident dispatcher, the manifest ingress and the diagnostic
consumer still read a POSIX ledger_root(): two runtime realities, and a
readback that could not verify its own append. These tests run the production
readers against the repository's own declaration (`repository_ledger_locus`)
on temporary bare Git repositories, with a decoy POSIX root that must never be
read or written. No real ledger ref is created and no runtime ALLOW is claimed.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "workers"), str(ROOT / "resident-runtime")]

import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as custody  # noqa: E402

REF = "refs/heads/organization-ledger/StegVerse-Labs"
LOCUS_VARIABLES = ("STEGVERSE_ORG_LEDGER_STORE", "STEGVERSE_ORG_LEDGER_GIT_REF",
                   "STEGVERSE_ORG_LEDGER_GIT_REMOTE", "STEGVERSE_ORG_LEDGER_GIT_CUSTODY")
KIND_MISMATCH = "ORGANIZATION_LEDGER_STORE_KIND_MISMATCH"


def receipt(name: str) -> dict:
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": name,
        "transition_sequence": 1,
        "subject_or_correlation_id": "ol2-same-store",
        "transition_outcome": "OBSERVED",
        "required_evidence_manifest": [],
    }


def bare(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-q", str(path)], check=True)
    return path


def decoy(tmp_path: Path) -> Path:
    """A POSIX root whose HEAD names a receipt that does not exist: unreadable if read."""
    root = tmp_path / "posix-decoy"
    (root / "receipts").mkdir(parents=True)
    (root / "HEAD.json").write_text(json.dumps({"organization": "StegVerse-Labs",
                                                "receipt_sha256": "sha256:" + "0" * 64}))
    return root


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.fixture
def git_declared(tmp_path, monkeypatch):
    """The repository's own git declaration, materialized on a temporary local repository."""
    for variable in LOCUS_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    node = bare(tmp_path / "node.git")
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_GIT_DIR", str(node))
    posix = decoy(tmp_path)
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(posix))
    assert org.declared_ledger_locus()["store"] == "git"
    return node, posix, snapshot(posix)


def git_store(node: Path):
    return org.ledger_store.GitLedgerStore(node, REF, custody="PRIVATE")


@pytest.mark.repository_ledger_locus
def test_ledger_root_under_the_git_declaration_fails_closed(git_declared):
    with pytest.raises(org.LedgerStoreKindMismatch) as refused:
        org.ledger_root()
    assert refused.value.failed_predicate == KIND_MISMATCH
    assert isinstance(refused.value, org.LedgerLocationRequired)
    refusal = org.location_refusal(refused.value)
    assert refusal["disposition"] == "FAIL_CLOSED"
    assert refusal["failed_predicate"] == KIND_MISMATCH
    assert refusal["consequence_committed"] is False
    assert "organization_store()" in refusal["required_evidence_or_repair"]
    # The declared store is still selected; only the raw POSIX read is refused.
    assert org.organization_store().kind == "GIT_REF"


def test_ledger_root_under_the_posix_declaration_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "root"))
    assert org.declared_ledger_locus() == {"store": "posix"}
    assert org.ledger_root() == (tmp_path / "root").resolve()
    store = org.organization_store()
    assert store.kind == "POSIX_FILESYSTEM" and store.root == org.ledger_root()


def test_ledger_root_without_a_declaration_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "root"))
    monkeypatch.delitem(org.C, "organization_ledger")
    with pytest.raises(org.LedgerLocusNotDeclared):
        org.ledger_root()


@pytest.mark.repository_ledger_locus
def test_current_chain_reads_the_declared_git_store(git_declared):
    node, posix, before = git_declared
    assert custody.current_chain() == (None, [])
    first = org.aggregate_transition(receipt("CLAIM"))
    second = org.aggregate_transition(receipt("WORK"))
    head, rows = custody.current_chain()
    assert head["receipt_sha256"] == second["receipt_sha256"]
    assert [row["receipt_sha256"] for row in rows] == [first["receipt_sha256"], second["receipt_sha256"]]
    assert git_store(node).get(org.ledger_store.HEAD_KEY) == head
    assert snapshot(posix) == before


def test_current_chain_on_posix_is_unchanged_and_refuses_receipts_without_head(tmp_path, monkeypatch):
    monkeypatch.setenv("STEGVERSE_ORG_LEDGER_ROOT", str(tmp_path / "org"))
    record = org.aggregate_transition(receipt("CLAIM"))
    head, rows = custody.current_chain()
    assert head == json.loads((tmp_path / "org" / "HEAD.json").read_text())
    assert rows == [record]
    (tmp_path / "org" / "HEAD.json").unlink()
    with pytest.raises(ValueError, match="receipts exist without HEAD"):
        custody.current_chain()


def _dispatch():
    from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator  # noqa: F401  (import order)
    from scripts import dispatch_resident_execution_requests as dispatch
    return dispatch


def _outcome(dispatch, state="ATTEMPT_RECORDED"):
    return [{"consumer": dispatch.COMPONENT011_SELECTOR,
             "consumer_ref": "scripts/consume_ungoverned_ai_defensive_envelope_request.py",
             "attempted": True, "state": state, "returncode": 0, "result": {"state": state}}]


@pytest.mark.repository_ledger_locus
def test_dispatcher_append_and_readback_use_the_same_declared_git_store(git_declared, tmp_path):
    node, posix, before = git_declared
    dispatch = _dispatch()
    first = dispatch.retain_component011_dispatch_in_organization(ROOT, tmp_path / "runtime", _outcome(dispatch))
    assert first["state"] == "RECORDED", first
    assert first["exact_receipt_readback"] == "PASS"
    second = dispatch.retain_component011_dispatch_in_organization(
        ROOT, tmp_path / "runtime", _outcome(dispatch, "FAIL_CLOSED"))
    assert second["state"] == "RECORDED", second
    assert second["immediate_predecessor_sha256"] == first["organization_receipt_sha256"]
    assert second["immediate_predecessor_readback"] == "PASS"
    store = git_store(node)
    assert store.get(org.ledger_store.HEAD_KEY)["receipt_sha256"] == second["organization_receipt_sha256"]
    row = store.get(org.ledger_store.receipt_key(second["organization_receipt_sha256"]))
    assert row["previous_receipt_sha256"] == first["organization_receipt_sha256"]
    # The decoy POSIX root, whose HEAD does not verify, was never read or written.
    assert snapshot(posix) == before


@pytest.mark.repository_ledger_locus
def test_dispatcher_without_the_git_materialization_path_appends_nothing(git_declared, tmp_path, monkeypatch):
    _, posix, before = git_declared
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_GIT_DIR")
    dispatch = _dispatch()
    result = dispatch.retain_component011_dispatch_in_organization(ROOT, tmp_path / "runtime", _outcome(dispatch))
    assert result["state"] == "BOUNDARY"
    assert result["reason"] == "COMPONENT011_ORGANIZATION_DISPATCH_CUSTODY_FAILED"
    assert result["error_type"] == "LedgerLocationRequired"
    assert snapshot(posix) == before


FORWARDERS = ("scripts/dispatch_resident_execution_requests.py",
              "scripts/refresh_and_execute_resident_task.py",
              "scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py")


def _parse(path: Path) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(path.read_text(encoding="utf-8"))


def test_dispatchers_forward_the_git_materialization_path_beside_the_root():
    for relative in FORWARDERS:
        tree = _parse(ROOT / relative)
        forwarded = next(ast.literal_eval(node.value) for node in tree.body
                         if isinstance(node, ast.Assign)
                         and any(getattr(t, "id", None) in {"NONSECRET_ENV", "NONSECRET_FORWARD"} for t in node.targets))
        assert "STEGVERSE_ORG_LEDGER_ROOT" in forwarded and "STEGVERSE_ORG_LEDGER_GIT_DIR" in forwarded, relative


@pytest.mark.repository_ledger_locus
def test_ingress_readback_reads_the_declared_git_store(git_declared):
    from tests.test_organization_manifest_ingress_rule_ref import ingress

    _, posix, before = git_declared
    ledger = ingress.organization_ledger
    record = ledger.aggregate_transition(receipt("INGRESS"))
    assert ingress._organization_receipt_read_back(record["source_transition_sha256"]) == (
        True, record["receipt_sha256"])
    assert ingress._organization_receipt_read_back("sha256:" + "f" * 64) == (False, None)
    assert snapshot(posix) == before


@pytest.mark.repository_ledger_locus
def test_diagnostic_consumer_reads_retained_sources_from_the_declared_git_store(git_declared, monkeypatch):
    node, posix, before = git_declared
    from tests.test_organization_record_gates_not_master_records import _diagnostic_chain

    # _diagnostic_chain supplies a POSIX root; the git declaration must ignore it.
    consumer, ingress, ingress_hash, binding, binding_hash = _diagnostic_chain(monkeypatch, posix.parent)
    read = consumer._organization_source_receipts(ROOT)
    assert consumer._prove_ancestry(read, binding_hash, ingress_hash) == (binding, ingress)
    assert git_store(node).get(org.ledger_store.source_key("sha256:" + binding_hash)) == binding
    assert not (posix.parent / "org").exists()
    monkeypatch.delenv("STEGVERSE_ORG_LEDGER_GIT_DIR")
    with pytest.raises(consumer.DiagnosticAdmissionError, match="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"):
        consumer._organization_source_receipts(ROOT)
    assert snapshot(posix) == before


@pytest.mark.repository_ledger_locus
def test_refusal_record_is_appended_and_found_again_on_the_declared_git_store(git_declared):
    from workers.canonical_state_transition_custody import record_organization_receipt_refusal

    node, posix, before = git_declared
    refusal = {"disposition": "FAIL_CLOSED", "failed_predicate": "OL2_FIXTURE", "retry_entrypoint": "r",
               "consequence_committed": False}
    first = record_organization_receipt_refusal(refusal, gated_transition_id="OL2", state_receipt_sha256="e" * 64)
    assert first["refusal_recorded"] is True, first
    head = git_store(node).get(org.ledger_store.HEAD_KEY)
    again = record_organization_receipt_refusal(refusal, gated_transition_id="OL2", state_receipt_sha256="e" * 64)
    assert again["refusal_organization_receipt_sha256"] == first["refusal_organization_receipt_sha256"]
    assert git_store(node).get(org.ledger_store.HEAD_KEY) == head
    assert snapshot(posix) == before


PRODUCTION_DIRECTORIES = ("scripts", "workers", "resident-runtime")


def test_no_production_reader_calls_ledger_root_outside_the_posix_store_selection():
    """ledger_root() is called only where organization_store() builds the declared POSIX store."""
    callers = []
    for directory in PRODUCTION_DIRECTORIES:
        for path in sorted((ROOT / directory).rglob("*.py")):
            tree = _parse(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if name == "ledger_root":
                    callers.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert len(callers) == 1 and callers[0].startswith("resident-runtime/aggregate_repo_transition.py:"), callers
