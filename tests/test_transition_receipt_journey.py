import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_transition_receipt_journey import validate

ROOT = Path(__file__).resolve().parents[1]

OUTBOUND = "sha256:" + "a" * 64
RETURN = "sha256:" + "b" * 64


def receipt(leg, direction, endpoint, counterparty, manifest_sha256, **extra):
    evidence = {
        "journey_id": "journey-001",
        "leg": leg,
        "direction": direction,
        "endpoint": endpoint,
        "counterparty": counterparty,
        "manifest_sha256": manifest_sha256,
        # Each endpoint transition records its own outcome.
        "disposition": "ALLOW",
        **extra,
    }
    return {"schema": "stegverse.repo-transition-receipt/v1", "evidence": evidence}


def complete():
    return [
        receipt(1, "EGRESS", "ORG-A", "EPHEMERAL-NODE", OUTBOUND),
        receipt(
            1, "INGRESS", "EPHEMERAL-NODE", "ORG-A", OUTBOUND,
            custody="RETURN_WITH_MANIFEST", manifest_read=True,
            manifest_directed=True, receipt_appended=True,
        ),
        receipt(
            2, "EGRESS", "EPHEMERAL-NODE", "ORG-A", RETURN,
            custody="RETURN_WITH_MANIFEST", manifest_read=True,
            manifest_directed=True, receipt_appended=True,
            next_leg_directed=True, predecessor_manifest_sha256=OUTBOUND,
        ),
        receipt(
            2, "INGRESS", "ORG-A", "EPHEMERAL-NODE", RETURN,
            returned_endpoint_receipts=True,
            predecessor_manifest_sha256=OUTBOUND,
        ),
    ]


class TransitionReceiptJourneyTests(unittest.TestCase):
    def test_complete_roundtrip_allows_without_ephemeral_durable_custody(self):
        result = validate(complete())
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertIsNone(result["failed_predicate"])
        self.assertEqual(result["failed_endpoints"], [])
        self.assertFalse(result["ephemeral_durable_custody_required"])

    def test_a_journey_over_a_refused_endpoint_is_not_reported_as_allowed(self):
        # The leg-1 ingress endpoint recorded its own refusal, as a refused
        # ingress records it in its receipt evidence. The journey is otherwise
        # well formed; it must say the leg did not produce ALLOW.
        rows = complete()
        rows[1]["evidence"].update(disposition="DENY",
                                   failed_predicate="CAPABILITY_IS_BOUND_TO_THIS_RECEIVING_OPERATION",
                                   retry_entrypoint="resident-runtime/organization_manifest_ingress.py::receive")
        result = validate(rows)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"], "JOURNEY_ENDPOINT_TRANSITION_NOT_ALLOWED")
        self.assertEqual(result["failed_endpoints"], [{
            "leg": 1, "direction": "INGRESS", "endpoint": "EPHEMERAL-NODE", "disposition": "DENY",
            "failed_predicate": "CAPABILITY_IS_BOUND_TO_THIS_RECEIVING_OPERATION",
            "retry_entrypoint": "resident-runtime/organization_manifest_ingress.py::receive"}])
        self.assertEqual(result["retry_entrypoint"], "resident-runtime/organization_manifest_ingress.py::receive")

    def test_a_receipt_level_fail_closed_fails_the_journey_and_the_command(self):
        rows = complete()
        rows[2]["disposition"] = "FAIL_CLOSED"
        rows[2]["failed_predicate"] = "EPHEMERAL_EGRESS_NOT_EMITTED"
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "journey.json"
            path.write_text(json.dumps({"receipts": rows}))
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_transition_receipt_journey.py"), str(path)],
                capture_output=True, text=True, cwd=work, timeout=60)
        self.assertEqual(completed.returncode, 1, completed.stderr[-400:])
        record = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        self.assertEqual([(row["leg"], row["direction"], row["failed_predicate"]) for row in record["failed_endpoints"]],
                         [(2, "EGRESS", "EPHEMERAL_EGRESS_NOT_EMITTED")])
        self.assertEqual(record["retry_entrypoint"], "scripts/validate_transition_receipt_journey.py")

    def test_receipts_appended_by_the_repository_emitter_carry_their_refusal_to_the_journey(self):
        spec = importlib.util.spec_from_file_location(
            "journey_emit", ROOT / ".stegverse/transition-ledger/emit.py")
        emit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emit)
        rows = complete()
        rows[1]["evidence"].update(disposition="FAIL_CLOSED", failed_predicate="LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER")
        with tempfile.TemporaryDirectory() as work:
            store = emit.ledger_store.PosixLedgerStore(Path(work) / "repo-ledger")
            receipts = [emit.append(f"JOURNEY-001-{index}", "ENDPOINT_TRANSITION", OUTBOUND, RETURN,
                                    row["evidence"], store=store) for index, row in enumerate(rows)]
        self.assertEqual(receipts[1]["evidence"]["disposition"], "FAIL_CLOSED")
        result = validate(receipts)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual([row["failed_predicate"] for row in result["failed_endpoints"]],
                         ["LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER"])

    def test_missing_endpoint_receipt_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "JOURNEY_INCOMPLETE"):
            validate(complete()[:-1])

    def test_manifest_mismatch_within_leg_fails_closed(self):
        rows = complete()
        rows[1]["evidence"]["manifest_sha256"] = "sha256:" + "c" * 64
        with self.assertRaisesRegex(ValueError, "OUTBOUND_MANIFEST_MISMATCH"):
            validate(rows)

    def test_return_manifest_must_link_outbound_predecessor(self):
        rows = complete()
        rows[2]["evidence"]["predecessor_manifest_sha256"] = "sha256:" + "c" * 64
        with self.assertRaisesRegex(ValueError, "RETURN_MANIFEST_PREDECESSOR_MISSING"):
            validate(rows)

    def test_unrelated_receipts_cannot_be_joined(self):
        rows = complete()
        rows[1]["evidence"]["journey_id"] = "other"
        with self.assertRaisesRegex(ValueError, "JOURNEY_ID_MISMATCH"):
            validate(rows)

    def test_wrong_counterparty_fails_closed(self):
        rows = complete()
        rows[1]["evidence"]["counterparty"] = "ORG-X"
        with self.assertRaisesRegex(ValueError, "OUTBOUND_HANDOFF_MISMATCH"):
            validate(rows)

    def test_ephemeral_node_must_read_manifest(self):
        rows = complete()
        rows[1]["evidence"]["manifest_read"] = False
        with self.assertRaisesRegex(ValueError, "EPHEMERAL_MANIFEST_NOT_READ"):
            validate(rows)

    def test_ephemeral_node_action_must_be_manifest_directed(self):
        rows = complete()
        rows[2]["evidence"]["manifest_directed"] = False
        with self.assertRaisesRegex(ValueError, "EPHEMERAL_ACTION_NOT_MANIFEST_DIRECTED"):
            validate(rows)

    def test_ephemeral_node_must_append_receipt(self):
        rows = complete()
        rows[2]["evidence"]["receipt_appended"] = False
        with self.assertRaisesRegex(ValueError, "EPHEMERAL_RECEIPT_NOT_APPENDED"):
            validate(rows)

    def test_ephemeral_node_must_direct_next_manifested_leg(self):
        rows = complete()
        rows[2]["evidence"]["next_leg_directed"] = False
        with self.assertRaisesRegex(ValueError, "EPHEMERAL_NEXT_LEG_NOT_DIRECTED"):
            validate(rows)

    def test_ephemeral_receipt_must_return_with_manifest(self):
        rows = complete()
        rows[1]["evidence"]["custody"] = "LOCAL_DISK"
        with self.assertRaisesRegex(ValueError, "EPHEMERAL_CUSTODY_INVALID"):
            validate(rows)

    def test_initiator_must_attest_returned_endpoint_receipts(self):
        rows = complete()
        rows[-1]["evidence"]["returned_endpoint_receipts"] = False
        with self.assertRaisesRegex(ValueError, "RETURN_EVIDENCE_MISSING"):
            validate(rows)


if __name__ == "__main__":
    unittest.main()
