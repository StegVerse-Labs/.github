"""OL-1b: the Organization ledger locus is declared by the Organization manifest.

CI evidence only: every append below lands in a temporary bare Git repository
standing in for the declared locus (tests/organization_ledger_standin.py). It
exercises the real expected-head compare-and-swap; it is not Organization
runtime reality and proves no authentic runtime append.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tests.organization_ledger_standin import LOCUS, remote_head, standin_locus

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "resident-runtime" / "aggregate_repo_transition.py"
    spec = importlib.util.spec_from_file_location("aggregate_repo_transition_locus_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source(transition_id="OL1B_TRANSITION"):
    return {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": transition_id,
        "transition_sequence": 1,
        "subject_or_correlation_id": "ol1b-subject",
        "prior_state_ref_or_hash": None,
        "resulting_state_ref_or_hash": "sha256:" + "1" * 64,
        "transition_evidence": {"state": "TEST"},
        "required_evidence_manifest": [],
        "transition_outcome": "COMPLETED",
        "authority_effect": "NONE_STATE_RECEIPT_ONLY",
    }


def git(remote, *args):
    return subprocess.run(["git", "--git-dir", str(remote), *args], capture_output=True, text=True, check=True).stdout


def ref_json(remote, name):
    return json.loads(git(remote, "cat-file", "blob", LOCUS["ref"] + ":" + LOCUS["path"] + "/" + name))


def ref_receipt(remote, digest):
    return ref_json(remote, "receipts/" + digest.split(":", 1)[1] + ".json")


def first_parent_count(remote):
    return int(git(remote, "rev-list", "--count", "--first-parent", LOCUS["ref"]).strip())


class DeclaredLocusTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.scratch = tempfile.TemporaryDirectory()
        self.base = Path(self.scratch.name)
        self.addCleanup(self.scratch.cleanup)

    def test_locus_is_declared_by_the_organization_manifest(self):
        contract = json.loads((ROOT / ".stegverse/transition-ledger/org-contract.json").read_text())
        declared = contract["organization_ledger_locus"]
        self.assertEqual(self.module.declared_locus(),
                         {"repository": declared["repository"], "ref": declared["ref"], "path": declared["path"]})
        self.assertEqual(declared["repository"], contract["organization"] + "/.github")
        self.assertIs(declared["local_checkout_is_authority"], False)
        self.assertIs(declared["forced_update_permitted"], False)
        self.assertEqual(self.module.remote_url(self.module.declared_locus()),
                         "https://github.com/StegVerse-Labs/.github.git")

    def test_an_undeclared_or_malformed_locus_fails_closed(self):
        good = self.module.C
        for change in ({"organization_ledger_locus": None},
                       {"organization_ledger_locus": {**good["organization_ledger_locus"], "repository": "Other/.github"}},
                       {"organization_ledger_locus": {**good["organization_ledger_locus"], "ref": "refs/tags/x"}},
                       {"organization_ledger_locus": {**good["organization_ledger_locus"], "ref": "refs/heads/a..b"}},
                       {"organization_ledger_locus": {**good["organization_ledger_locus"], "path": "../escape"}},
                       {"organization_ledger_locus": {**good["organization_ledger_locus"], "path": "/abs"}}):
            with mock.patch.dict(self.module.C, change):
                with self.assertRaises(self.module.LedgerLocusFailClosed) as caught:
                    self.module.ledger_root()
                self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_LOCUS_DECLARED")

    def test_cache_variable_is_a_cache_of_the_declared_locus(self):
        cache = self.base / "cache"
        with standin_locus(self.base, cache=cache):
            root = self.module.ledger_root()
        self.assertEqual(root, cache.resolve())
        self.assertEqual(self.module.bound_locus(root), self.module.declared_locus())

    def test_cache_bound_to_another_locus_fails_closed(self):
        cache = self.base / "cache"
        other = {**self.module.declared_locus(), "ref": "refs/heads/somewhere-else"}
        self.module.bind_cache(cache, other)
        with standin_locus(self.base, cache=cache) as remote:
            with self.assertRaises(self.module.LedgerLocusFailClosed) as caught:
                self.module.ledger_root()
            self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_CACHE_MATCHES_DECLARED_LOCUS")
            refusal = self.module.location_refusal(caught.exception)
            self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
            self.assertIn("STEGVERSE_ORG_LEDGER_ROOT", refusal["required_evidence_or_repair"])
            with self.assertRaises(self.module.LedgerLocusFailClosed):
                self.module.aggregate_transition(source(), ledger=cache)
            self.assertIsNone(remote_head(remote))

    def test_cache_holding_an_unbound_host_ledger_fails_closed(self):
        cache = self.base / "host-ledger"
        cache.mkdir()
        (cache / "HEAD.json").write_text(json.dumps({"receipt_sha256": "sha256:" + "0" * 64}))
        with standin_locus(self.base, cache=cache) as remote:
            with self.assertRaises(self.module.LedgerLocusFailClosed) as caught:
                self.module.aggregate_transition(source())
            self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_CACHE_MATCHES_DECLARED_LOCUS")
            self.assertIsNone(remote_head(remote))

    def test_append_is_one_commit_on_the_declared_ref_and_reads_back_by_digest(self):
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            record = self.module.aggregate_transition(source())
            self.assertEqual(ref_receipt(remote, record["receipt_sha256"]), record)
            head = ref_json(remote, "HEAD.json")
            self.assertEqual(head["receipt_sha256"], record["receipt_sha256"])
            self.assertEqual(head["receipt_path"], LOCUS["path"] + "/receipts/" + record["receipt_sha256"][7:] + ".json")
            retained = ref_json(remote, "source-receipts/" + record["source_transition_sha256"][7:] + ".json")
            self.assertEqual(retained, source())
            self.assertEqual(first_parent_count(remote), 1)
            names = git(remote, "ls-tree", "-r", "--name-only", LOCUS["ref"]).split()
            self.assertTrue(all(name.startswith(LOCUS["path"] + "/") for name in names))
            self.assertFalse(any("/." in name for name in names))
            second = self.module.aggregate_transition(source("OL1B_SECOND"))
            self.assertEqual(second["previous_receipt_sha256"], record["receipt_sha256"])
            self.assertEqual(first_parent_count(remote), 2)

    def test_unset_cache_variable_appends_to_the_declared_locus(self):
        with standin_locus(self.base) as remote:
            os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT", None)
            record = self.module.aggregate_transition(source())
            self.assertEqual(ref_receipt(remote, record["receipt_sha256"]), record)

    def test_a_fresh_cache_reads_the_chain_from_the_ref_not_the_host(self):
        with standin_locus(self.base, cache=self.base / "first") as remote:
            first = self.module.aggregate_transition(source())
            with mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(self.base / "second")}):
                root = self.module.ledger_root()
                self.assertEqual(json.loads((root / "HEAD.json").read_text())["receipt_sha256"],
                                 first["receipt_sha256"])
                second = self.module.aggregate_transition(source("OL1B_SECOND"))
            self.assertEqual(second["previous_receipt_sha256"], first["receipt_sha256"])
            self.assertEqual(ref_json(remote, "HEAD.json")["receipt_sha256"], second["receipt_sha256"])

    def test_exact_retry_returns_the_same_reachable_receipt(self):
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            record = self.module.aggregate_transition(source())
            head = remote_head(remote)
            with mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(self.base / "retry-cache")}):
                again = self.module.aggregate_transition(source())
            self.assertEqual(again, record)
            self.assertEqual(remote_head(remote), head)

    def test_divergent_identity_fails_closed_and_never_rewrites_the_chain(self):
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            self.module.aggregate_transition(source())
            head = remote_head(remote)
            with self.assertRaisesRegex(ValueError, "context conflict"):
                self.module.aggregate_transition(source(), org_transition_class="DIVERGENT_CLASS")
            self.assertEqual(remote_head(remote), head)

    def test_lost_race_re_reads_and_re_links_without_a_fork(self):
        with standin_locus(self.base, cache=self.base / "a") as remote:
            cache_a = self.module.ledger_root()
            cache_b = self.module.bind_cache(self.base / "b", self.module.declared_locus())
            original = self.module.GitLocus.compare_and_swap
            raced = []

            def racing(git_locus, commit, expected):
                if not raced and git_locus.root == cache_a:
                    raced.append(True)
                    raced.append(self.module.aggregate_transition(source("OL1B_RIVAL"), ledger=cache_b))
                return original(git_locus, commit, expected)

            with mock.patch.object(self.module.GitLocus, "compare_and_swap", racing):
                mine = self.module.aggregate_transition(source(), ledger=cache_a)
            rival = raced[1]
            self.assertIsNone(rival["previous_receipt_sha256"])
            self.assertEqual(mine["previous_receipt_sha256"], rival["receipt_sha256"])
            self.assertEqual(ref_json(remote, "HEAD.json")["receipt_sha256"], mine["receipt_sha256"])
            self.assertEqual(ref_receipt(remote, rival["receipt_sha256"]), rival)
            self.assertEqual(first_parent_count(remote), 2)
            self.assertEqual(git(remote, "rev-list", "--merges", LOCUS["ref"]).strip(), "")

    def test_concurrent_writers_serialize_into_one_linear_chain(self):
        with standin_locus(self.base) as remote:
            results, errors = [], []

            def writer(index):
                try:
                    results.append(self.module.aggregate_transition(
                        source("OL1B_CONCURRENT_%d" % index), ledger=self.module.bind_cache(
                            self.base / ("writer-%d" % index), self.module.declared_locus())))
                except Exception as exc:  # noqa: BLE001 -- surfaced below
                    errors.append(exc)

            threads = [threading.Thread(target=writer, args=(index,)) for index in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(errors, [])
            self.assertEqual(first_parent_count(remote), 4)
            cursor, seen = ref_json(remote, "HEAD.json")["receipt_sha256"], []
            while cursor is not None:
                receipt = ref_receipt(remote, cursor)
                seen.append(receipt["receipt_sha256"])
                cursor = receipt["previous_receipt_sha256"]
            self.assertEqual(sorted(seen), sorted(row["receipt_sha256"] for row in results))

    def test_refused_write_fails_closed_naming_the_predicate(self):
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            hook = remote / "hooks" / "pre-receive"
            hook.write_text("#!/bin/sh\necho 'permission denied to update ref' >&2\nexit 1\n")
            hook.chmod(0o755)
            with self.assertRaises(self.module.LedgerLocusFailClosed) as caught:
                self.module.aggregate_transition(source())
            self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_REF_WRITE_AUTHORIZED")
            self.assertIn("contents write", caught.exception.required_evidence_or_repair)
            self.assertIsNone(remote_head(remote))
            refusal = self.module.location_refusal(caught.exception)
            self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
            self.assertIs(refusal["consequence_committed"], False)

    def test_refused_write_is_reported_by_the_entrypoint(self):
        receipt = self.base / "source.json"
        receipt.write_text(json.dumps(source()))
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            hook = remote / "hooks" / "pre-receive"
            hook.write_text("#!/bin/sh\nexit 1\n")
            hook.chmod(0o755)
            result = subprocess.run(["python", str(ROOT / "resident-runtime/aggregate_repo_transition.py"),
                                     "--transition-receipt", str(receipt)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        refusal = json.loads(result.stdout)
        self.assertEqual(refusal["failed_predicate"], "ORGANIZATION_LEDGER_REF_WRITE_AUTHORIZED")
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")

    def test_unreadable_locus_fails_closed(self):
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            subprocess.run(["rm", "-rf", str(remote)], check=True)
            with self.assertRaises(self.module.LedgerLocusFailClosed) as caught:
                self.module.aggregate_transition(source())
            self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_REF_READABLE")

    def test_protected_fast_forward_only_ref_still_accepts_the_append(self):
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            git(remote, "config", "receive.denyNonFastForwards", "true")
            git(remote, "config", "receive.denyDeletes", "true")
            self.module.aggregate_transition(source())
            self.module.aggregate_transition(source("OL1B_SECOND"))
            self.assertEqual(first_parent_count(remote), 2)

    def test_a_cache_is_never_appended_outside_the_locus_publication(self):
        with standin_locus(self.base) as remote:
            cache = self.module.bind_cache(self.base / "cache", self.module.declared_locus())
            with self.assertRaises(self.module.LedgerLocusFailClosed) as caught:
                self.module._aggregate_transition_locked(source(), root=cache)
            self.assertEqual(caught.exception.failed_predicate, "ORGANIZATION_LEDGER_APPENDED_UNDER_LOCUS_CAS")
            self.assertFalse((cache / "HEAD.json").exists())
            self.assertIsNone(remote_head(remote))

    def test_batch_closure_is_published_under_the_same_compare_and_swap(self):
        sys_path = str(ROOT / "resident-runtime")
        import sys
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        import organization_batch_custody as batches
        with standin_locus(self.base, cache=self.base / "cache") as remote:
            record = batches.org.aggregate_transition(source())
            closed = batches.close_batch("TASK_CLOSURE")
            self.assertEqual(closed["ordered_receipt_hashes"], [record["receipt_sha256"]])
            self.assertEqual(ref_json(remote, "batches/" + closed["batch_id"][7:] + ".json"), closed)
            self.assertEqual(ref_json(remote, "BATCH_HEAD.json")["batch_id"], closed["batch_id"])
            self.assertEqual(first_parent_count(remote), 2)
            # Closing again is the exact retry: the ref does not move.
            self.assertEqual(batches.close_batch("TASK_CLOSURE"), closed)
            self.assertEqual(first_parent_count(remote), 2)

    def test_caller_held_store_is_not_published(self):
        with standin_locus(self.base) as remote:
            store = self.base / "temporary-ledger"
            self.module.aggregate_transition(source(), ledger=store)
            self.assertIsNone(remote_head(remote))
            self.assertIsNone(self.module.bound_locus(store))


if __name__ == "__main__":
    unittest.main()
