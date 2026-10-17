"""H34b: the kernel hands an endpoint adapter the carrier frame's heartbeat epoch.

An endpoint adapter whose registry row declares `endpoint_adapter_hb_epoch:
CARRIER_SUPPLIED` (StegVerse-Labs's governance endpoint) is run with
`--hb-epoch <the delivering frame's epoch>`, so the receipts it writes reference
the crossing's own tick instead of one derived from the host clock. The epoch
rule is the shared one TVC's broker applies (StegVerse-Labs/TVC#517): supplied by
the carrier, ASCII digits, value >= 32, and no clock is read on this path.

- no epoch supplied                      -> FAIL_CLOSED HB_EPOCH_NOT_SUPPLIED
- malformed, or derived_from_clock true  -> FAIL_CLOSED HB_EPOCH_INVALID

Each refusal carries the six fields, names StegVerse-org/.github#162 as its
owning goal, and is stored with the disposition it returns. An adapter that does
not declare the epoch input is run exactly as before.

Stdlib only; the governance harness of tests/test_governance_endpoint.py is reused.
"""
from __future__ import annotations

import importlib.util
import hashlib
import inspect
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    "governance_endpoint_harness_h34b", Path(__file__).with_name("test_governance_endpoint.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
K = base.K

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
GOAL = "StegVerse-org/.github#162"
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "test-node", "predecessor": None}
ROUTE = "stegverse.route.ecosystem-diagnostic.v1"
# Records its arguments; touches `ran` beside itself so a test can see it ran at all.
ARGV_ADAPTER = ("import argparse, json, sys\nfrom pathlib import Path\n"
                "ap=argparse.ArgumentParser(); ap.add_argument('--packet'); ap.add_argument('--out')\n"
                "ap.add_argument('--hb-epoch', default=None)\n"
                "a=ap.parse_args(); (Path(__file__).parent/'ran').write_text('1')\n"
                "Path(a.out).write_text(json.dumps({'argv': sys.argv[1:]}))\n")


def scratch(case):
    path = Path(tempfile.mkdtemp())
    case.addCleanup(shutil.rmtree, path, True)
    return path


def supplied(epoch):
    return K.hb_reference(epoch=epoch)


class CarrierEpochForwardingTests(unittest.TestCase):
    """run_endpoint_adapter, on a synthetic adapter that records what it was handed."""

    def run_adapter(self, reference, *, declared=True):
        root = scratch(self)
        (root / "adapter.py").write_text(ARGV_ADAPTER)
        row = {"service_id": "target.endpoint", "boundary_role": "INTERNAL_ENDPOINT",
               "endpoint_adapter": "adapter.py", "endpoint_adapter_disposition": "ALLOW_DECLARED_ADAPTER",
               "endpoint_adapter_effect": "PURE",
               "admits_processing": [{"capability": "ecosystem_diagnostic", "route_id": ROUTE}]}
        if declared:
            row["endpoint_adapter_hb_epoch"] = "CARRIER_SUPPLIED"
        packet = K.build_packet(origin_org="Origin", origin_service="origin.org-control",
                                destination_org="Target", destination_service="target.endpoint",
                                payload={"processing": {"capability": "ecosystem_diagnostic", "route_id": ROUTE}},
                                standing=GENESIS)
        self.ran = root / "ran"
        return K.run_endpoint_adapter(root, root / "adapter.py", packet, service=row,
                                      heartbeat_reference=reference)

    def refused(self, reference):
        with self.assertRaises(K.CarrierEpochRefusal) as raised:
            self.run_adapter(reference)
        self.assertFalse(self.ran.exists(), "the adapter ran without a supplied epoch")
        record = raised.exception.record
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        for key in SIX:
            self.assertIsInstance(record.get(key), str, key)
            self.assertTrue(record[key].strip(), key)
        self.assertEqual(record["failure_code"], str(raised.exception))
        self.assertEqual(record["owning_existing_goal"], GOAL)
        self.assertEqual(record["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        self.assertIs(record["derived_from_clock"], False)
        return record

    def test_the_carrier_epoch_is_forwarded_to_a_declared_adapter(self):
        argv = self.run_adapter(supplied(1000))["argv"]
        self.assertEqual(argv[argv.index("--hb-epoch") + 1], "1000")

    def test_a_leading_zero_epoch_is_forwarded_as_its_value(self):
        argv = self.run_adapter(dict(supplied(1000), epoch="0033"))["argv"]
        self.assertEqual(argv[argv.index("--hb-epoch") + 1], "33")

    def test_a_digit_string_epoch_is_forwarded_as_supplied(self):
        reference = dict(supplied(417798851), epoch="417798851")
        argv = self.run_adapter(reference)["argv"]
        self.assertEqual(argv[argv.index("--hb-epoch") + 1], "417798851")

    def test_the_hb32_anchor_itself_is_a_valid_epoch(self):
        argv = self.run_adapter(supplied(32))["argv"]
        self.assertEqual(argv[argv.index("--hb-epoch") + 1], "32")

    def test_an_undeclared_adapter_is_run_as_before(self):
        for reference in (supplied(1000), None):
            with self.subTest(reference=reference):
                argv = self.run_adapter(reference, declared=False)["argv"]
                self.assertNotIn("--hb-epoch", argv)

    def test_a_missing_epoch_fails_closed_not_supplied(self):
        for reference in (None, {}, dict(supplied(1000), epoch=None)):
            with self.subTest(reference=reference):
                self.assertEqual(self.refused(reference)["failure_code"], "HB_EPOCH_NOT_SUPPLIED")

    def test_a_malformed_epoch_fails_closed_invalid(self):
        # Only ASCII [0-9]+ is an epoch: nothing coerced to one is accepted.
        for epoch in (31, 0, -40, "-40", "+40", " 40", "40 ", "4e2", "40.0", 40.0, True, False,
                      "+33", " 33", "3_3", "33\n", "", "\uff14\uff10", "\u0663\u0663", "0x40",
                      [40], {"epoch": 40}):
            with self.subTest(epoch=epoch):
                self.assertEqual(self.refused(dict(supplied(1000), epoch=epoch))["failure_code"],
                                 "HB_EPOCH_INVALID")
        self.assertEqual(self.refused("HB:1000")["failure_code"], "HB_EPOCH_INVALID")

    def test_a_clock_derived_epoch_fails_closed_invalid(self):
        derived = K.hb_reference(K.HB_ANCHOR_UNIX_NS + 123 * K.HB_PERIOD_NS)
        self.assertIs(derived["derived_from_clock"], True)
        record = self.refused(derived)
        self.assertEqual(record["failure_code"], "HB_EPOCH_INVALID")
        self.assertIn("clock", record["required_evidence_or_repair"])
        # A carried derived_from_clock must be exactly false; one not carried
        # is not a claim the epoch was derived.
        for value in (True, None, 0, "false", "False"):
            with self.subTest(derived_from_clock=value):
                self.assertEqual(self.refused(dict(supplied(1000), derived_from_clock=value))["failure_code"],
                                 "HB_EPOCH_INVALID")
        unstated = dict(supplied(1000)); unstated.pop("derived_from_clock")
        argv = self.run_adapter(unstated)["argv"]
        self.assertEqual(argv[argv.index("--hb-epoch") + 1], "1000")

    def test_no_clock_is_read_on_this_path(self):
        class NoClock:
            @staticmethod
            def now(*_a, **_k):
                raise AssertionError("the carrier-epoch path read the clock")
        with mock.patch.object(K, "datetime", NoClock):
            argv = self.run_adapter(supplied(1000))["argv"]
            self.assertIn("--hb-epoch", argv)
            self.refused(None)
        for function in (K.carrier_epoch, K.supplied_epoch_failure, K.run_endpoint_adapter,
                         K.adapter_takes_carrier_epoch):
            source = inspect.getsource(function)
            for clock in ("datetime", "time.", "now_ns", "hb_reference("):
                self.assertNotIn(clock, source, function.__name__)


class SharedEpochValidatorTests(unittest.TestCase):
    """`supplied_epoch_failure` is one function, byte-identical across
    StegVerse-org/.github#185 and StegVerse-Labs/.github#3212 / #3213."""

    #: sha256 of the function's source text; the same pin is asserted in each PR.
    SHARED_VALIDATOR_SHA256 = "7f36f0e697cadc91acd27af121eee3fc460b887ec67cfa258727bfccec0ca5f8"

    def test_the_validator_text_is_the_shared_one(self):
        source = inspect.getsource(K.supplied_epoch_failure)
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), self.SHARED_VALIDATOR_SHA256)

    def test_the_rule(self):
        self.assertEqual(K.supplied_epoch_failure(None)[0], "HB_EPOCH_NOT_SUPPLIED")
        # As TVC#517 require_hb_epoch: [0-9]+ fullmatch, then int() >= 32.
        for epoch in (32, 33, "33", "0032", "0033", 10**12):
            with self.subTest(epoch=epoch):
                self.assertIsNone(K.supplied_epoch_failure(epoch))
        for epoch in ("+33", " 33", "3_3", True, False, 33.0, "33.0", "", 31, "31", -33):
            with self.subTest(epoch=epoch):
                self.assertEqual(K.supplied_epoch_failure(epoch)[0], "HB_EPOCH_INVALID")
        self.assertIsNone(K.supplied_epoch_failure(33, {"derived_from_clock": False}))
        self.assertIsNone(K.supplied_epoch_failure(33, {}))
        self.assertEqual(K.supplied_epoch_failure(33, {"derived_from_clock": True})[0], "HB_EPOCH_INVALID")
        self.assertEqual(K.supplied_epoch_failure(33, "HB:33")[0], "HB_EPOCH_INVALID")


class GovernanceCarrierEpochTests(unittest.TestCase):
    """The governance endpoint, through dispatch and through a consumed frame."""
    VARIABLES = base.GovernanceEndpointTests.VARIABLES
    setUp = base.GovernanceEndpointTests.setUp
    with_stegcore = base.GovernanceEndpointTests.with_stegcore
    ledger = base.GovernanceEndpointTests.ledger

    def receipts(self, variable):
        return self.ledger(variable) if (Path(base.os.environ[variable]) / "receipts").is_dir() else []

    def test_the_governance_row_declares_the_carrier_epoch(self):
        row = next(s for s in K.load_registry(base.ROOT)["services"] if s["service_id"] == base.SERVICE)
        self.assertEqual(row["endpoint_adapter_hb_epoch"], "CARRIER_SUPPLIED")

    def test_a_direct_dispatch_without_the_carrier_reference_mints_nothing(self):
        self.with_stegcore()
        with self.assertRaises(K.CarrierEpochRefusal) as raised:
            K.dispatch(base.ROOT, base.packet(base.work_request({"signal": {}})))
        self.assertEqual(str(raised.exception), "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])
        self.assertEqual(self.receipts("STEGVERSE_ORG_LEDGER_ROOT"), [])

    def consume(self, **publish):
        mesh = self.work / "mesh"
        K.publish_packet(base.packet(base.work_request({"signal": {}})), root=mesh, **publish)
        return K.consume_and_respond(base.ROOT, mesh_root=mesh, node_state_root=self.work / "node-state",
                                     seen=set(), repo_ledger_root=self.work / "repo-ledger",
                                     org_ledger_root=self.work / "org-ledger")

    def test_the_frame_epoch_reaches_the_governance_receipts(self):
        self.with_stegcore()
        consumed, = self.consume(epoch=1000)
        self.assertEqual(consumed["result"]["status"], "CONSUMED")
        decision, = [r for r in self.receipts("STEGVERSE_REPO_LEDGER_ROOT")
                     if r["transition_class"] == "ORGANIZATION_GOVERNANCE_DECISION"]
        self.assertEqual(decision["hb_reference"]["epoch"], 1000)
        self.assertIs(decision["hb_reference"]["derived_from_clock"], False)
        organization = [r for r in self.receipts("STEGVERSE_ORG_LEDGER_ROOT")
                        if r.get("repo_receipt_sha256") == decision["receipt_sha256"]]
        self.assertEqual(organization[0]["hb_reference"]["epoch"], 1000)

    def test_a_clock_derived_frame_is_refused_and_stored_as_returned(self):
        self.with_stegcore()
        refused, = self.consume(now_ns=K.HB_ANCHOR_UNIX_NS + 7 * K.HB_PERIOD_NS)
        result = refused["result"]
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "HB_EPOCH_INVALID")
        self.assertEqual(result["owning_existing_goal"], GOAL)
        for key in SIX:
            self.assertTrue(str(result.get(key) or "").strip(), key)
        # FAIL_CLOSED: recorded, not answered, not marked seen.
        self.assertIsNone(refused["response_publication"])
        self.assertIsNone(refused["seen_marker"])
        repository = self.receipts("STEGVERSE_REPO_LEDGER_ROOT")
        self.assertEqual([r["transition_class"] for r in repository], ["ORGANIZATION_FEDERATION_CROSSING_REFUSED"])
        stored = repository[0]["evidence"]
        self.assertEqual(stored["disposition"], result["disposition"])
        organization, = self.receipts("STEGVERSE_ORG_LEDGER_ROOT")
        carried = organization["boundary_evidence"]
        self.assertEqual(carried["disposition"], result["disposition"])
        for key in SIX:
            self.assertEqual(stored[key], result[key], key)
            self.assertEqual(carried[key], result[key], key)


if __name__ == "__main__":
    unittest.main()
