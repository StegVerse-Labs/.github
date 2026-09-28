import unittest

from scripts.validate_transition_receipt_journey import validate

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
        self.assertFalse(result["ephemeral_durable_custody_required"])

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
