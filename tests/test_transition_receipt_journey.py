import copy
import unittest

from scripts.validate_transition_receipt_journey import validate

MANIFEST="sha256:"+"a"*64
def receipt(leg,direction,endpoint,counterparty,**extra):
    e={"journey_id":"journey-001","leg":leg,"direction":direction,"endpoint":endpoint,
       "counterparty":counterparty,"manifest_sha256":MANIFEST,**extra}
    return {"schema":"stegverse.repo-transition-receipt/v1","evidence":e}

def complete():
    return [
      receipt(1,"EGRESS","ORG-A","EPHEMERAL-NODE"),
      receipt(1,"INGRESS","EPHEMERAL-NODE","ORG-A",custody="RETURN_WITH_MANIFEST"),
      receipt(2,"EGRESS","EPHEMERAL-NODE","ORG-A",custody="RETURN_WITH_MANIFEST"),
      receipt(2,"INGRESS","ORG-A","EPHEMERAL-NODE",returned_endpoint_receipts=True),
    ]

class TransitionReceiptJourneyTests(unittest.TestCase):
    def test_complete_roundtrip_allows_without_ephemeral_durable_custody(self):
        out=validate(complete())
        self.assertEqual(out["disposition"],"ALLOW")
        self.assertFalse(out["ephemeral_durable_custody_required"])

    def test_missing_endpoint_receipt_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"JOURNEY_INCOMPLETE"):
            validate(complete()[:-1])

    def test_manifest_change_fails_closed(self):
        rows=complete()
        rows[2]["evidence"]["manifest_sha256"]="sha256:"+"b"*64
        with self.assertRaisesRegex(ValueError,"MANIFEST_HANDOFF_MISMATCH"):
            validate(rows)

    def test_unrelated_receipts_cannot_be_joined(self):
        rows=complete()
        rows[1]["evidence"]["journey_id"]="other"
        with self.assertRaisesRegex(ValueError,"JOURNEY_ID_MISMATCH"):
            validate(rows)

    def test_wrong_counterparty_fails_closed(self):
        rows=complete()
        rows[1]["evidence"]["counterparty"]="ORG-X"
        with self.assertRaisesRegex(ValueError,"OUTBOUND_HANDOFF_MISMATCH"):
            validate(rows)

    def test_ephemeral_receipt_must_return_with_manifest(self):
        rows=complete()
        rows[1]["evidence"]["custody"]="LOCAL_DISK"
        with self.assertRaisesRegex(ValueError,"EPHEMERAL_CUSTODY_INVALID"):
            validate(rows)

    def test_initiator_must_attest_returned_endpoint_receipts(self):
        rows=complete()
        rows[-1]["evidence"]["returned_endpoint_receipts"]=False
        with self.assertRaisesRegex(ValueError,"RETURN_EVIDENCE_MISSING"):
            validate(rows)

if __name__=="__main__":
    unittest.main()
