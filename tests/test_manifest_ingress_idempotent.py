"""One manifest is one transition, however many times it is delivered.

`ORGANIZATION_SDK_MANIFEST_INGRESS` derives its transition id from the request,
but appended a repository receipt and then an organization receipt on every
call. A resubmitted manifest was recorded twice; a run that stopped between the
two appends left a repository receipt the organization never consumed, which
the next delivery then duplicated.

These cases drive `receive` against supplied ledger roots. The SDK, the crossing
and the closure reconstruction are replaced by fixed values, because what is
under test is what `receive` records, not what the SDK derives. They assert: a
replay returns the recorded receipts; a run that stopped between the levels is
completed rather than repeated, at the retained receipt's epoch; the same
transition id over a different manifest refuses; a replayed refusal is recorded
once; and concurrent appenders of one transition commit it once.

The organization ledger is reached through a test adapter onto
`aggregate_transition`, as in `test_organization_manifest_ingress_rule_ref.py`:
`receive` calls `aggregate_repo_transition.append`, which that module does not
define in this repository.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
REVISION = "0123456789abcdef0123456789abcdef01234567"

_fixture_spec = importlib.util.spec_from_file_location(
    "manifest_ingress_rule_ref_fixture", ROOT / "tests/test_organization_manifest_ingress_rule_ref.py")
fixture = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(fixture)
ingress = fixture.ingress
repository_ledger = ingress.repository_ledger
organization_ledger = ingress.organization_ledger


def request(manifest_sha256="a" * 64, request_sha256="b" * 64):
    return {"request_sha256": request_sha256, "wire_manifest_sha256": manifest_sha256,
            "canonical_manifest_sha256": manifest_sha256, "graph_id": "graph-1",
            "canonical_task_id": "task-1", "processing_capability": "ecosystem_diagnostic",
            "route_id": "stegverse.route.ecosystem-diagnostic.v1",
            "destination_resolution_source": "ORGANIZATION_BOUNDARY"}


CROSSING = {"crossing_completed": True, "resolved_service_id": "stegverse-labs.sdk-manifest-ingress",
            "ingress_packet_id": "ingress-1", "egress_packet_id": "egress-1", "application_result": {}}
CLOSURES = [{"transition_id": "t-1", "receipt_sha256": "c" * 64}]


class SimulatedAppendFailure(Exception):
    """A failure of the organization append, injected once."""


class IdempotentReceiveTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo", base / "org"
        self.org_epochs = []
        self.fail_next_org_append = False
        self.request = request()

        def organization_append(repository_receipt, org_transition_class, predecessor, successor,
                                boundary_evidence, authority_effect, hb_epoch=None):
            self.org_epochs.append(hb_epoch)
            if self.fail_next_org_append:
                self.fail_next_org_append = False
                raise SimulatedAppendFailure("FAIL_CLOSED")
            return organization_ledger.aggregate_transition(
                repository_receipt, org_transition_class=org_transition_class,
                predecessor_org_state_sha256=predecessor, successor_org_state_sha256=successor,
                boundary_evidence=boundary_evidence, authority_effect=authority_effect)

        patches = [
            mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                         "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)}),
            mock.patch.object(organization_ledger, "append", organization_append, create=True),
            mock.patch.object(ingress, "derive_execution_request", lambda m, b: dict(self.request)),
            mock.patch.object(ingress, "bound_here", lambda r: {"operation": "receive"}),
            mock.patch.object(ingress.crossing_module, "cross", lambda *a, **k: dict(CROSSING)),
            mock.patch.object(ingress, "reconstruct_closures", lambda c: [dict(x) for x in CLOSURES]),
            mock.patch.object(ingress, "admit_runtime_result", lambda m, r, result: {"admitted": True}),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def receipts(self, root, transition_class=None):
        directory = root / "receipts"
        found = [json.loads(p.read_text()) for p in directory.glob("*.json")] if directory.is_dir() else []
        if transition_class is not None:
            found = [r for r in found if r.get("transition_class") == transition_class]
        return found

    def receive(self, **options):
        return ingress.receive({"manifest": 1}, registry={}, **options)

    def test_replay_of_the_same_delivery_returns_the_recorded_receipts(self):
        first = self.receive()
        second = self.receive()
        self.assertEqual(first["disposition"], "ALLOW", first.get("detail"))
        self.assertEqual(second["disposition"], "ALLOW", second.get("detail"))
        self.assertIs(first["transition_replayed"], False)
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(len(self.receipts(self.org_root)), 1)

    def test_replay_under_another_packet_id_is_the_same_transition(self):
        """The packet is the carrier; the manifest is the transition."""
        first = self.receive()
        second = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(len(self.receipts(self.org_root)), 1)

    def test_replay_after_the_organization_append_failed_completes_the_chain_once(self):
        self.fail_next_org_append = True
        with self.assertRaises(SimulatedAppendFailure):
            self.receive()
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(self.receipts(self.org_root), [])
        completed = self.receive()
        self.assertEqual(completed["disposition"], "ALLOW", completed.get("detail"))
        self.assertIs(completed["transition_replayed"], True)
        repository, = self.receipts(self.repo_root)
        organization, = self.receipts(self.org_root)
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])
        self.assertEqual(completed["organization_receipt_sha256"], organization["receipt_sha256"])

    def test_replay_completion_takes_its_epoch_from_the_retained_receipt(self):
        """A retry carrying a different epoch still rebuilds the first attempt's records."""
        self.fail_next_org_append = True
        with self.assertRaises(SimulatedAppendFailure):
            self.receive(hb_epoch=32)
        self.receive(hb_epoch=99)
        self.assertEqual(self.org_epochs, [32, 32])
        repository, = self.receipts(self.repo_root)
        self.assertEqual(repository["hb_reference"]["epoch"], 32)

    def test_replay_of_one_transition_id_over_another_manifest_refuses(self):
        self.receive()
        repository, = self.receipts(self.repo_root)
        with self.assertRaises(ValueError) as raised:
            repository_ledger.append(repository["transition_id"], repository["transition_class"],
                                     "sha256:" + "2" * 64, repository["successor_state_sha256"],
                                     repository["evidence"], "NONE", hb_epoch=34,
                                     idempotent_on=("request_sha256",))
        self.assertEqual(str(raised.exception), "ledger_receipt_collision")
        self.assertEqual(len(self.receipts(self.repo_root)), 1)

    def test_replay_with_a_colliding_id_is_recorded_as_a_refusal_not_an_admission(self):
        self.receive()
        # The same request digest (so the same transition id) over another manifest.
        self.request = request(manifest_sha256="f" * 64)
        refused = self.receive(packet_id="org-ingress-collision")
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.assertEqual(refused["failed_predicate"], "ONE_TRANSITION_ID_BINDS_ONE_MANIFEST")
        self.assertEqual(len(self.receipts(self.repo_root, ingress.OPERATION_ID)), 1)
        self.assertEqual(len(self.receipts(self.repo_root, ingress.REFUSED_CLASS)), 1)

    def test_replay_of_a_refusal_is_recorded_once(self):
        def refuses(manifest, boundary):
            raise ValueError("NOT_A_MANIFEST")

        with mock.patch.object(ingress, "derive_execution_request", refuses):
            first = self.receive()
            second = self.receive()
        self.assertEqual(first["disposition"], "FAIL_CLOSED")
        self.assertEqual(first["refusal_repository_receipt_sha256"],
                         second["refusal_repository_receipt_sha256"])
        self.assertEqual(first["refusal_organization_receipt_sha256"],
                         second["refusal_organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.repo_root, ingress.REFUSED_CLASS)), 1)
        self.assertEqual(len(self.receipts(self.org_root)), 1)


class ConcurrentAppendTests(unittest.TestCase):
    """Appenders of one transition sharing one kernel commit it once."""

    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        self.store = repository_ledger.ledger_store.PosixLedgerStore(Path(self._work.name) / "repo")

    def test_concurrent_appenders_of_one_transition_commit_once(self):
        results, errors = [], []

        def appender():
            try:
                results.append(repository_ledger.append(
                    "CONCURRENT-1", "TEST_CLASS", "sha256:" + "a" * 64, "sha256:" + "b" * 64,
                    {"request_sha256": "c" * 64}, "NONE", hb_epoch=40,
                    idempotent_on=("request_sha256",), store=self.store))
            except Exception as exc:  # pragma: no cover - reported below
                errors.append(exc)

        threads = [threading.Thread(target=appender) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len({r["receipt_sha256"] for r in results}), 1)
        self.assertEqual(len(self.store.list_prefix(repository_ledger.ledger_store.RECEIPT_PREFIX)), 1)

    def test_without_idempotency_each_append_is_its_own_receipt(self):
        """Callers that did not opt in keep the old behaviour."""
        for epoch in (41, 42):
            repository_ledger.append("PLAIN-1", "TEST_CLASS", "sha256:" + "a" * 64,
                                     "sha256:" + "b" * 64, {}, "NONE", hb_epoch=epoch,
                                     store=self.store)
        self.assertEqual(len(self.store.list_prefix(repository_ledger.ledger_store.RECEIPT_PREFIX)), 2)

    def test_an_organization_receipt_for_an_exact_source_is_returned_not_minted(self):
        """The organization ledger here consumes a source once, at a supplied root."""
        org_root = Path(self._work.name) / "org"
        source = repository_ledger.append("SRC-1", "TEST_CLASS", "sha256:" + "a" * 64,
                                          "sha256:" + "b" * 64, {}, "NONE", hb_epoch=43,
                                          store=self.store)
        options = dict(org_transition_class="REPO_STATE_PROPAGATION",
                       predecessor_org_state_sha256="sha256:" + "a" * 64,
                       successor_org_state_sha256="sha256:" + "b" * 64,
                       boundary_evidence={}, authority_effect="NONE", ledger=org_root)
        first = organization_ledger.aggregate_transition(source, **options)
        again = organization_ledger.aggregate_transition(source, **options)
        self.assertEqual(first["receipt_sha256"], again["receipt_sha256"])
        self.assertEqual(len(list((org_root / "receipts").glob("*.json"))), 1)
        with self.assertRaises(ValueError):
            organization_ledger.aggregate_transition(
                source, **{**options, "org_transition_class": "SOME_OTHER_CLASS"})


if __name__ == "__main__":
    unittest.main()
