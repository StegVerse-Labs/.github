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
        with org._materialized_repository_ledger(ledger):
            aggregate(receipt, org_root)
    refusal = raised.value.refusal
    assert (refusal["failure_code"], refusal["terminal"]) == ("SOURCE_RECEIPT_NOT_ON_LEDGER", False)
    assert "retry" in refusal["next_attempt"]
    assert not org_root.exists()


# --- Lead ruling 21:13Z: the source ledger is the materializer's, paired with the organization ledger ---

TRACKED = ROOT / "tests" / "fixtures" / "base-state-readback"  # a committed directory: never a ledger


def assert_refused(receipt, org_root, code, **kwargs):
    with pytest.raises(org.OrgLedgerEpochRefused) as raised:
        aggregate(receipt, org_root, **kwargs)
    refusal = raised.value.refusal
    assert refusal["failure_code"] == code, refusal
    for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                  "owning_existing_goal", "next_attempt"):
        assert str(refusal[field]).strip(), field
    assert not org_root.exists(), "nothing is written for a refused source"


def test_a_public_ledger_kwarg_pointing_elsewhere_is_refused(ledgers, tmp_path):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    elsewhere = org.ledger_store.PosixLedgerStore(tmp_path / "elsewhere")
    on_ledger(elsewhere, "own")
    assert_refused(receipt, org_root, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED", repository_ledger=elsewhere)


def test_a_symlink_to_the_designated_ledger_is_the_same_ledger(ledgers, tmp_path):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    link = tmp_path / "link"
    link.symlink_to(ledger.root)
    assert aggregate(receipt, org_root, repository_ledger=org.ledger_store.PosixLedgerStore(link))


def test_a_lone_git_repository_ledger_override_that_does_not_pair_is_refused(ledgers, monkeypatch, tmp_path):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    bare = tmp_path / "foreign.git"
    __import__("subprocess").run(["git", "init", "-q", "--bare", str(bare)], check=True)
    location = org._repository_ledger().C["repository_ledger_location"]
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", "git+%s#%s:%s" % (bare, location["ref"], location["namespace"]))
    # A git repository ledger with a POSIX organization ledger pairs with nothing.
    assert_refused(receipt, org_root, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED")


@pytest.mark.parametrize("via_symlink", [False, True])
def test_a_root_holding_tracked_files_is_not_contract_designated(ledgers, monkeypatch, tmp_path, via_symlink):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    root = TRACKED
    if via_symlink:
        root = tmp_path / "looks-like-a-ledger"
        root.symlink_to(TRACKED)
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", str(root))
    assert_refused(receipt, org_root, "LEDGER_ROOT_NOT_CONTRACT_DESIGNATED")


def test_another_repositorys_receipt_is_a_cross_repo_refusal(ledgers):
    ledger, org_root = ledgers
    on_ledger(ledger, "own")
    body = {**{k: v for k, v in minted("site").items() if k != "receipt_sha256"}, "repository": "StegVerse-Labs/Site"}
    foreign = {**body, "receipt_sha256": org.sha(body)}
    assert_refused(foreign, org_root, "SPPA_CROSS_REPO_OBSERVATION_UNVERIFIED")


# --- Lead conditions 21:23Z: the internal channel is the materializer's only, and forged roots are refused ---

def test_the_internal_channel_is_not_reachable_from_cli_env_or_request(ledgers, monkeypatch, tmp_path):
    import re
    import subprocess
    # Only the kernel's custody and the two materialized consumers pass it, and only their custody's store.
    passers = {}
    for path in ROOT.glob("**/*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith(("tests/", "receipts/")) or relative == "resident-runtime/aggregate_repo_transition.py":
            continue
        for match in re.finditer(r"_materialized_repository_ledger\((custody\[\"repository_store\"\]|[^)\n]+)\)",
                                 path.read_text(encoding="utf-8")):
            passers.setdefault(relative, set()).add(match.group(1).strip())
    # SPPA's CLI never reaches it (coordinator 2026-10-27, R2): only the kernel's crossing custody and the
    # claim consumer bind it.
    assert passers == {"org-kernel/kernel.py": {'custody["repository_store"]'},
                       "scripts/consume_org_claim_allocator_request.py": {'custody["repository_store"]'}}, passers
    # It is not a keyword of either append entry point: passing one is a TypeError, never a binding.
    import inspect
    for entry in (org.aggregate_transition, org._aggregate_transition_locked):
        assert "_materialized_repository_ledger" not in inspect.signature(entry).parameters
    with pytest.raises(TypeError):
        aggregate(minted("x"), tmp_path / "org-never", _materialized_repository_ledger=ledgers[0])
    # No CLI option reaches it.
    helped = subprocess.run([sys.executable, "-B", str(ROOT / "resident-runtime/aggregate_repo_transition.py"), "--help"],
                            capture_output=True, text=True, timeout=60).stdout
    assert "materialized" not in helped and "repository-ledger" not in helped and "source-ledger" not in helped
    # No environment variable reaches it: a decoy pointing at a ledger that holds the receipt changes nothing.
    ledger, org_root = ledgers
    on_ledger(ledger, "own")
    decoy = org.ledger_store.PosixLedgerStore(tmp_path / "decoy")
    forged = on_ledger(decoy, "forged-only-in-decoy")
    for name in ("STEGVERSE_MATERIALIZED_REPOSITORY_LEDGER", "STEGVERSE_REPO_LEDGER_HOME", "STEGVERSE_SOURCE_LEDGER"):
        monkeypatch.setenv(name, str(decoy.root))
    assert_refused(forged, org_root, "SOURCE_RECEIPT_NOT_ON_LEDGER")
    # A committed request naming a ledger is refused before the cycle runs (tests/test_federation_cycle_epoch.py).


def _bare_store(path, location):
    import subprocess
    subprocess.run(["git", "init", "-q", "--bare", str(path)], check=True)
    return org.ledger_store.GitLedgerStore(path, location["ref"], namespace=location["namespace"])


def test_a_forged_materializer_root_with_a_foreign_realpath_is_refused(tmp_path):
    location = org._repository_ledger().C["repository_ledger_location"]
    organization = _bare_store(tmp_path / "organization.git", location)
    foreign = _bare_store(tmp_path / "foreign.git", location)
    receipt = minted("own")
    refusal = org.source_ledger_refusal(receipt, organization=organization, materialized=foreign)
    assert refusal["failure_code"] == "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED", refusal
    # The paired one passes the pair check and is then held to the chain like any other.
    paired = org.ledger_store.GitLedgerStore(tmp_path / "organization.git", location["ref"],
                                             namespace=location["namespace"])
    refusal = org.source_ledger_refusal(receipt, organization=organization, materialized=paired)
    assert refusal["failure_code"] == "SOURCE_RECEIPT_NOT_ON_LEDGER", refusal


def test_a_forged_materializer_root_holding_tracked_files_is_refused(ledgers, monkeypatch):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    monkeypatch.delenv("STEGVERSE_REPO_LEDGER_ROOT")  # the channel alone carries the forged root
    with org._materialized_repository_ledger(org.ledger_store.PosixLedgerStore(TRACKED)):
        assert_refused(receipt, org_root, "LEDGER_ROOT_NOT_CONTRACT_DESIGNATED")


# --- Lead ruling 21:42Z: a mixed pair is refused in both directions ---

def test_a_posix_repository_ledger_with_a_git_organization_ledger_is_a_mixed_pair(tmp_path):
    location = org._repository_ledger().C["repository_ledger_location"]
    organization = _bare_store(tmp_path / "organization.git", location)
    repository = org.ledger_store.PosixLedgerStore(tmp_path / "repo")
    refusal = org.source_ledger_refusal(minted("own"), organization=organization, materialized=repository)
    assert refusal["failure_code"] == "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED", refusal
    assert "MIXED_LEDGER_KIND_PAIR" in refusal["detail"]


def test_a_git_repository_ledger_with_a_posix_organization_ledger_is_a_mixed_pair(tmp_path):
    location = org._repository_ledger().C["repository_ledger_location"]
    repository = _bare_store(tmp_path / "repository.git", location)
    organization = org.ledger_store.PosixLedgerStore(tmp_path / "org")
    refusal = org.source_ledger_refusal(minted("own"), organization=organization, materialized=repository)
    assert refusal["failure_code"] == "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED", refusal
    assert "MIXED_LEDGER_KIND_PAIR" in refusal["detail"]


def test_a_posix_organization_root_holding_tracked_files_is_not_contract_designated(tmp_path):
    repository = org.ledger_store.PosixLedgerStore(tmp_path / "repo")
    organization = org.ledger_store.PosixLedgerStore(TRACKED)
    refusal = org.source_ledger_refusal(minted("own"), organization=organization, materialized=repository)
    assert refusal["failure_code"] == "LEDGER_ROOT_NOT_CONTRACT_DESIGNATED", refusal


# --- Coordinator 2026-10-27 (R2): lone roots, an unexpanded ~, symlinks, the materializer's two channels ---

def test_an_unexpanded_home_root_is_refused(ledgers, monkeypatch):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    monkeypatch.setenv("STEGVERSE_REPO_LEDGER_ROOT", "~/repo-ledger")
    assert_refused(receipt, org_root, "LEDGER_ROOT_NOT_CONTRACT_DESIGNATED")
    import importlib.util
    spec = importlib.util.spec_from_file_location("kernel_home_probe", ROOT / "org-kernel/kernel.py")
    kernel = importlib.util.module_from_spec(spec); spec.loader.exec_module(kernel)
    for repo_root, org_root_arg in (("~/repo", str(org_root)), (str(ledger.root), "~/org")):
        with pytest.raises(ValueError, match="LEDGER_ROOT_NOT_CONTRACT_DESIGNATED"):
            kernel.crossing_custody(ROOT, repo_ledger_root=repo_root, org_ledger_root=org_root_arg)


def test_a_lone_repository_ledger_with_no_organization_ledger_is_refused():
    refusal = org.source_ledger_refusal(minted("own"), organization=None,
                                        materialized=org.ledger_store.PosixLedgerStore("/nonexistent-lone-root"))
    assert refusal["failure_code"] == "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED", refusal
    assert "LONE_REPOSITORY_LEDGER" in refusal["detail"]


def test_the_custody_root_and_the_materializers_variable_must_name_one_ledger(ledgers, tmp_path):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    other = org.ledger_store.PosixLedgerStore(tmp_path / "other")
    on_ledger(other, "own")
    with org._materialized_repository_ledger(other):
        assert_refused(receipt, org_root, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED")


def test_a_symlink_is_accepted_only_when_its_realpath_is_the_designated_ledger(ledgers, tmp_path):
    ledger, org_root = ledgers
    receipt = on_ledger(ledger, "own")
    foreign = org.ledger_store.PosixLedgerStore(tmp_path / "foreign")
    on_ledger(foreign, "own")
    to_foreign = tmp_path / "to-foreign"
    to_foreign.symlink_to(foreign.root)
    assert_refused(receipt, org_root, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED",
                   repository_ledger=org.ledger_store.PosixLedgerStore(to_foreign))
    with org._materialized_repository_ledger(org.ledger_store.PosixLedgerStore(to_foreign)):
        assert_refused(receipt, org_root, "CALLER_CHOSEN_SOURCE_LEDGER_REJECTED")
    to_designated = tmp_path / "to-designated"
    to_designated.symlink_to(ledger.root)
    with org._materialized_repository_ledger(org.ledger_store.PosixLedgerStore(to_designated)):
        assert aggregate(receipt, org_root)["repo_receipt_sha256"] == receipt["receipt_sha256"]


def test_federation_cycles_root_is_admitted_only_as_half_of_a_same_kind_pair(tmp_path):
    location = org._repository_ledger().C["repository_ledger_location"]
    organization = _bare_store(tmp_path / "organization.git", location)
    # federation_cycle --repo-ledger-root as a POSIX directory beside the git organization ledger: refused.
    refusal = org.source_ledger_refusal(minted("own"), organization=organization,
                                        materialized=org.ledger_store.PosixLedgerStore(tmp_path / "repo"))
    assert "MIXED_LEDGER_KIND_PAIR" in refusal["detail"], refusal
    # As the subtree of that same ref, it pairs and is then held to the chain like any other.
    subtree = org.ledger_store.open_store("git+%s#%s:%s" % (tmp_path / "organization.git", location["ref"],
                                                            location["namespace"]))
    refusal = org.source_ledger_refusal(minted("own"), organization=organization, materialized=subtree)
    assert refusal["failure_code"] == "SOURCE_RECEIPT_NOT_ON_LEDGER", refusal
