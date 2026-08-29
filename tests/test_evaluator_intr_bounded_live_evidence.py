from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/evaluator-intr/bounded-live-observation-20260829.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def receipt_hash(receipt):
    body = dict(receipt)
    claimed = body.pop("receipt_hash")
    actual = "sha256:" + hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()
    return claimed, actual


class EvaluatorInTrBoundedLiveEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_observation_state_is_bounded_not_production(self):
        self.assertEqual(self.evidence["state"], "OBSERVED_BOUNDED_LIVE_EXECUTION")
        self.assertTrue(self.evidence["verification"]["browser_gateway_runtime_round_trip_observed"])
        self.assertFalse(self.evidence["production"]["public_internet_route_observed"])
        self.assertFalse(self.evidence["production"]["public_webpki_hostname_validation_observed"])
        self.assertFalse(self.evidence["production"]["resident_sovereign_production_host_activation_observed"])
        self.assertFalse(self.evidence["production"]["production_activation_claimed"])

    def test_ingress_receipt_hash_and_boundary(self):
        receipt = self.evidence["ingress_receipt"]
        claimed, actual = receipt_hash(receipt)
        self.assertEqual(claimed, actual)
        self.assertEqual(receipt["schema"], "stegverse.intr.hop_receipt/v1")
        self.assertEqual(receipt["from_role"], "DEVICE_SYSTEM")
        self.assertEqual(receipt["to_role"], "STEGOS_ECOSYSTEM")
        self.assertEqual(receipt["transition_state"], "RECEIVED")
        self.assertEqual(receipt["boundary_verification"], "VERIFIED")
        self.assertFalse(receipt["secret_plaintext_present"])
        self.assertFalse(receipt["authority_transfer"])

    def test_egress_receipt_hash_boundary_and_lineage(self):
        ingress = self.evidence["ingress_receipt"]
        receipt = self.evidence["egress_receipt"]
        claimed, actual = receipt_hash(receipt)
        self.assertEqual(claimed, actual)
        self.assertEqual(receipt["schema"], "stegverse.intr.hop_receipt/v1")
        self.assertEqual(receipt["from_role"], "STEGOS_ECOSYSTEM")
        self.assertEqual(receipt["to_role"], "DEVICE_SYSTEM")
        self.assertEqual(receipt["transition_state"], "FORWARDED")
        self.assertEqual(receipt["boundary_verification"], "VERIFIED")
        self.assertEqual(receipt["prior_receipt_hash"], ingress["receipt_hash"])
        self.assertFalse(receipt["secret_plaintext_present"])
        self.assertFalse(receipt["authority_transfer"])

    def test_authority_remains_none(self):
        authority = self.evidence["authority"]
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertEqual(authority["github_token_runtime_authority"], "NONE")
        self.assertEqual(authority["authority_effect"], "NONE")
        self.assertFalse(authority["review_authority"])
        self.assertFalse(authority["freeze_authority"])
        self.assertFalse(authority["test_execution_authority"])
        self.assertFalse(authority["production_activation_authority"])

    def test_proof_harness_origin_exception_cannot_promote_to_production(self):
        browser = self.evidence["browser"]
        self.assertEqual(browser["proof_harness_origin"], "null")
        self.assertTrue(browser["proof_harness_origin_exception_only"])
        self.assertFalse(browser["production_origin_relaxation_authorized"])


if __name__ == "__main__":
    unittest.main()
