"""Fixture-only negative tests for receive-side warrant + manifest binding.

No real tokens. No Organization Ledger append is performed on refusal.
"""
import unittest
from resident_runtime.intr_destination_ingress import bind_receive_warrant_and_manifest, ReceiveBindingRefusal, sha

class TestReceiveBinding(unittest.TestCase):
    def setUp(self):
        self.manifest = {"schema": "stegverse.canonical-manifest/v1", "payload": "test"}
        self.manifest_sha = sha(self.manifest)
        self.valid_warrant = {
            "operation_class": "DISPATCH_INTR_DESTINATION_PHASE",
            "destination_organization": "StegVerse-Labs",
            "issued_hb_epoch": 100,
            "expires_hb_epoch": 200,
            "consumed": False,
            "canonical_manifest_sha256": self.manifest_sha,
        }

    def test_missing_warrant(self):
        with self.assertRaises(ReceiveBindingRefusal) as cm:
            bind_receive_warrant_and_manifest(None, self.manifest, expected_destination_org="StegVerse-Labs", supplied_hb_epoch=150)
        self.assertEqual(cm.exception.record["failure_code"], "WARRANT_ABSENT")

    def test_manifest_mismatch(self):
        bad = dict(self.valid_warrant)
        bad["canonical_manifest_sha256"] = "sha256:deadbeef"
        with self.assertRaises(ReceiveBindingRefusal) as cm:
            bind_receive_warrant_and_manifest(bad, self.manifest, expected_destination_org="StegVerse-Labs", supplied_hb_epoch=150)
        self.assertEqual(cm.exception.record["failure_code"], "MANIFEST_DIGEST_MISMATCH")

    def test_valid_passes(self):
        # Does not raise
        bind_receive_warrant_and_manifest(self.valid_warrant, self.manifest, expected_destination_org="StegVerse-Labs", supplied_hb_epoch=150)

if __name__ == "__main__":
    unittest.main()
