"""One manifest is one transition, however many times it is delivered.

`ORGANIZATION_SDK_MANIFEST_INGRESS` derives its transition id from the request,
but appended a repository receipt and then an organization receipt on every
call. A resubmitted manifest was recorded twice; a run that stopped between the
two appends left a repository receipt the organization never consumed, which
the next delivery then duplicated.

These cases drive `receive` against supplied ledger roots. The SDK, the crossing
and the closure reconstruction are replaced by stubs, because what is under test
is what `receive` records, not what the SDK derives. The crossing stub honours
`packet_id` as the real crossing does -- each delivery names its own ingress and
egress packet and closes on its own boundary receipt -- so a redelivery under
another packet id is exercised as it occurs (I-10), and only the carrier may
vary under one transition id. They assert: a
replay returns the recorded receipts; a run that stopped between the levels is
completed rather than repeated, at the retained receipt's epoch; the same
transition id over a different manifest refuses; a replayed refusal is recorded
once; and concurrent appenders of one transition commit it once.

The organization ledger is its own append owner, `aggregate_transition`;
a failure of it is injected by wrapping that owner, and `receive` returns its
typed partial-commit record rather than raising.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import hashlib
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


def crossing(manifest, *, registry, standing=None, packet_id):
    """The crossing as the boundary drives it: each delivery is its own packet.

    The packet id is the carrier's, so a redelivery under another packet id
    names another ingress and egress packet, exactly as the real crossing does.
    """
    return {"crossing_completed": True, "resolved_service_id": "stegverse-labs.sdk-manifest-ingress",
            "ingress_packet_id": packet_id, "egress_packet_id": packet_id + ":egress",
            "application_result": {}}


def closures(crossing):
    """One closure per crossing, derived from the packet that carried it."""
    digest = hashlib.sha256(crossing["ingress_packet_id"].encode()).hexdigest()
    return [{"transition_id": "t-1", "receipt_sha256": digest}]


class SimulatedAppendFailure(Exception):
    """A failure of the organization append, injected once."""


class IngressLedgerCase(unittest.TestCase):
    """`receive` against temporary ledger roots, with the SDK and crossing stubbed."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo", base / "org"
        self.org_epochs = []
        self.fail_next_org_append = False
        self.request = request()

        aggregate_transition = organization_ledger.aggregate_transition

        def organization_append(*args, **kwargs):
            self.org_epochs.append(kwargs.get("hb_epoch"))
            if self.fail_next_org_append:
                self.fail_next_org_append = False
                raise SimulatedAppendFailure("FAIL_CLOSED")
            return aggregate_transition(*args, **kwargs)

        patches = [
            mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                         "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)}),
            mock.patch.object(organization_ledger, "aggregate_transition", organization_append),
            mock.patch.object(ingress, "derive_execution_request", lambda m, b: dict(self.request)),
            mock.patch.object(ingress, "bound_here", lambda r: {"operation": "receive"}),
            mock.patch.object(ingress.crossing_module, "cross", crossing),
            mock.patch.object(ingress, "reconstruct_closures", closures),
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

    def receipt_bytes(self, root):
        directory = root / "receipts"
        return {p.name: p.read_bytes() for p in directory.glob("*.json")} if directory.is_dir() else {}


class IdempotentReceiveTests(IngressLedgerCase):
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
        """The packet is the carrier; the manifest is the transition (I-10).

        The redelivery is carried by other packets, so its crossing names other
        packet ids and closes on another boundary receipt. It reuses the
        original receipts at both levels, byte for byte, with no second state
        effect, and reports its own packets as non-identity delivery evidence.
        """
        first = self.receive(packet_id="org-ingress-delivery-1")
        repository_bytes = self.receipt_bytes(self.repo_root)
        organization_bytes = self.receipt_bytes(self.org_root)
        organization_head = (self.org_root / "HEAD.json").read_bytes()
        second = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(first["disposition"], "ALLOW", first.get("detail"))
        self.assertEqual(second["disposition"], "ALLOW", second.get("detail"))
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(first["organization_transition_id"], second["organization_transition_id"])
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(self.receipt_bytes(self.repo_root), repository_bytes)
        self.assertEqual(self.receipt_bytes(self.org_root), organization_bytes)
        self.assertEqual((self.org_root / "HEAD.json").read_bytes(), organization_head)
        organization, = self.receipts(self.org_root)
        # The receipt keeps the packets that committed it.
        self.assertEqual(organization["boundary_evidence"]["ingress_packet_id"], "org-ingress-delivery-1")
        self.assertEqual(organization["boundary_evidence"]["egress_packet_id"],
                         "org-ingress-delivery-1:egress")
        # The redelivery's own packets are reported, not dropped and not recorded as identity.
        attempt = second["delivery_attempt"]
        self.assertEqual((attempt["ingress_packet_id"], attempt["egress_packet_id"]),
                         ("org-ingress-redelivered", "org-ingress-redelivered:egress"))
        self.assertEqual(attempt["transition_identity_role"], "NON_IDENTITY_DELIVERY_EVIDENCE")
        self.assertIs(attempt["is_the_recorded_delivery"], False)
        self.assertEqual(attempt["recorded_delivery"],
                         {"ingress_packet_id": "org-ingress-delivery-1",
                          "egress_packet_id": "org-ingress-delivery-1:egress"})
        self.assertIs(first["delivery_attempt"]["is_the_recorded_delivery"], True)

    def test_redelivery_completing_a_partial_commit_names_the_recorded_delivery(self):
        """The organization level is completed under the packets the repository recorded."""
        self.fail_next_org_append = True
        partial = self.receive(packet_id="org-ingress-delivery-1")
        self.assertEqual(partial["failure_code"], "ORGANIZATION_APPEND_NOT_COMMITTED")
        repository_bytes = self.receipt_bytes(self.repo_root)
        completed = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(completed["disposition"], "ALLOW", completed.get("detail"))
        self.assertEqual(self.receipt_bytes(self.repo_root), repository_bytes)
        repository, = self.receipts(self.repo_root)
        organization, = self.receipts(self.org_root)
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])
        self.assertEqual(organization["boundary_evidence"]["ingress_packet_id"], "org-ingress-delivery-1")

    def test_a_recorded_delivery_that_does_not_reconstruct_is_refused(self):
        """The recorded packets are re-derived, not taken on the record's word."""
        self.receive(packet_id="org-ingress-delivery-1")
        organization_bytes = self.receipt_bytes(self.org_root)
        with mock.patch.object(ingress, "reconstruct_closures",
                               lambda c: [{"transition_id": "t-1", "receipt_sha256": "9" * 64}]):
            refused = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.assertEqual(refused["failed_predicate"], "RECORDED_DELIVERY_RECONSTRUCTS_INDEPENDENTLY")
        self.assertEqual(refused["detail"], "RECORDED_DELIVERY_EVIDENCE_DOES_NOT_RECONSTRUCT")
        self.assertEqual(len(self.receipts(self.repo_root, ingress.OPERATION_ID)), 1)
        self.assertTrue(set(organization_bytes.items()) <= set(self.receipt_bytes(self.org_root).items()))

    def test_replay_that_misses_a_concurrent_record_still_returns_it(self):
        """The lookup before the append can run before a racing delivery lands.

        The repository ledger compares the successor on an exact retry, and a
        redelivery's successor is its own carrier's closure, so the append
        collides; the operation reads the chain again, resolves the recorded
        successor, and returns the recorded receipts rather than a refusal.
        """
        first = self.receive()
        original = repository_ledger.recorded
        calls = {"n": 0}

        def misses_once(*args, **kwargs):
            calls["n"] += 1
            return None if calls["n"] == 1 else original(*args, **kwargs)

        repository_ledger.recorded = misses_once
        self.addCleanup(setattr, repository_ledger, "recorded", original)
        second = self.receive(packet_id="org-ingress-raced")
        self.assertEqual(second["disposition"], "ALLOW", second.get("detail"))
        self.assertEqual(first["repository_receipt_sha256"], second["repository_receipt_sha256"])
        self.assertEqual(first["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(len(self.receipts(self.org_root)), 1)

    def test_replay_after_the_organization_append_failed_completes_the_chain_once(self):
        self.fail_next_org_append = True
        partial = self.receive()
        self.assertEqual(partial["failure_code"], "ORGANIZATION_APPEND_NOT_COMMITTED")
        self.assertIs(partial["repository_receipt_committed"], True)
        self.assertIs(partial["organization_receipt_committed"], False)
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
        partial = self.receive(hb_epoch=32)
        self.assertEqual(partial["failure_code"], "ORGANIZATION_APPEND_NOT_COMMITTED")
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


class DeliveryIdentityCollisionTests(IngressLedgerCase):
    """Only the carrier may vary under one transition id; anything consequential collides.

    The recorded transition is redelivered under another packet id with one
    consequence-defining fact changed. Each fails closed and leaves the
    recorded receipts byte for byte as they were.
    """

    def recorded(self):
        first = self.receive(packet_id="org-ingress-delivery-1")
        self.assertEqual(first["disposition"], "ALLOW", first.get("detail"))
        return self.receipt_bytes(self.repo_root), self.receipt_bytes(self.org_root)

    def assert_recorded_unchanged(self, repository_bytes, organization_bytes):
        self.assertEqual({k: v for k, v in self.receipt_bytes(self.repo_root).items()
                          if k in repository_bytes}, repository_bytes)
        self.assertEqual(len(self.receipts(self.repo_root, ingress.OPERATION_ID)), 1)
        self.assertTrue(set(organization_bytes.items()) <= set(self.receipt_bytes(self.org_root).items()))
        org_rows = [r for r in self.receipts(self.org_root)
                    if r["source_transition_id"].startswith("ORGANIZATION-SDK-MANIFEST-INGRESS-")
                    and "-REFUSED-" not in r["source_transition_id"]]
        self.assertEqual(len(org_rows), 1)

    def test_identity_changed_manifest_binding_collides(self):
        recorded = self.recorded()
        self.request = request(manifest_sha256="f" * 64)
        refused = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(refused["failed_predicate"], "ONE_TRANSITION_ID_BINDS_ONE_MANIFEST")
        self.assert_recorded_unchanged(*recorded)

    def test_identity_changed_request_under_the_same_id_collides(self):
        """Issuer and destination are bound by the request digest; another request collides."""
        recorded = self.recorded()
        self.request = request(request_sha256="b" * 16 + "e" * 48)
        refused = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(refused["failed_predicate"], "ONE_TRANSITION_ID_BINDS_ONE_MANIFEST")
        self.assert_recorded_unchanged(*recorded)

    def test_identity_changed_destination_service_collides(self):
        recorded = self.recorded()
        original = ingress.crossing_module.cross

        def elsewhere(*args, **kwargs):
            return {**original(*args, **kwargs), "resolved_service_id": "stegverse-labs.another-service"}

        with mock.patch.object(ingress.crossing_module, "cross", elsewhere):
            refused = self.receive(packet_id="org-ingress-redelivered")
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.assertEqual(refused["failure_code"], "ORGANIZATION_APPEND_NOT_COMMITTED")
        self.assertIn("context conflict", refused["detail"])
        self.assert_recorded_unchanged(*recorded)

    def organization_retry(self, **change):
        """The organization append owner, retried over the recorded source with one change."""
        repository, = self.receipts(self.repo_root)
        organization, = self.receipts(self.org_root)
        options = dict(org_transition_class=organization["org_transition_class"],
                       predecessor_org_state_sha256=organization["predecessor_org_state_sha256"],
                       successor_org_state_sha256=organization["successor_org_state_sha256"],
                       boundary_evidence=organization["boundary_evidence"],
                       authority_effect=organization["authority_effect"])
        self.assertEqual(organization_ledger.aggregate_transition(repository, **options)["receipt_sha256"],
                         organization["receipt_sha256"])
        with self.assertRaises(ValueError) as raised:
            organization_ledger.aggregate_transition(repository, **{**options, **change})
        return str(raised.exception)

    def test_identity_changed_successor_collides_at_both_levels(self):
        recorded = self.recorded()
        repository, = self.receipts(self.repo_root)
        with self.assertRaises(ValueError) as raised:
            repository_ledger.append(repository["transition_id"], repository["transition_class"],
                                     repository["predecessor_state_sha256"], "sha256:" + "3" * 64,
                                     repository["evidence"], "NONE", hb_epoch=35,
                                     idempotent_on=("request_sha256",))
        self.assertEqual(str(raised.exception), "ledger_receipt_collision")
        self.assertIn("context conflict",
                      self.organization_retry(successor_org_state_sha256="sha256:" + "3" * 64))
        self.assert_recorded_unchanged(*recorded)

    def test_identity_changed_authority_collides_at_both_levels(self):
        recorded = self.recorded()
        repository, = self.receipts(self.repo_root)
        with self.assertRaises(ValueError) as raised:
            repository_ledger.append(repository["transition_id"], repository["transition_class"],
                                     repository["predecessor_state_sha256"],
                                     repository["successor_state_sha256"],
                                     repository["evidence"], "GRANTS_AUTHORITY", hb_epoch=35,
                                     idempotent_on=("request_sha256",))
        self.assertEqual(str(raised.exception), "ledger_receipt_collision")
        self.assertIn("context conflict", self.organization_retry(authority_effect="GRANTS_AUTHORITY"))
        self.assert_recorded_unchanged(*recorded)

    def test_identity_changed_packet_ids_in_the_receipt_itself_collide(self):
        """The receipt's own packets are immutable: only the reported attempt varies."""
        recorded = self.recorded()
        organization, = self.receipts(self.org_root)
        forged = {**organization["boundary_evidence"], "ingress_packet_id": "org-ingress-redelivered"}
        self.assertIn("context conflict", self.organization_retry(boundary_evidence=forged))
        self.assert_recorded_unchanged(*recorded)


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
