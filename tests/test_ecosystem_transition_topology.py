"""Conformance vectors for topology #3299. Mock readback is not sovereign proof."""
import unittest
from scripts.ecosystem_transition_topology import evaluate, verify_organization_readback, canonical_digest


class TransitionTopologyTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {"manifest_id": "fixture-1", "classification": "SECRET",
                         "minimum_authority_level": "SECRET"}
        self.state = {"authority_level": "SECRET", "classification": "SECRET"}
        self.evidence = {"source_digest_verified": True, "security_exceedance_verified": True}

    def test_allow(self):
        self.assertEqual(evaluate(self.state, self.manifest, self.evidence)["disposition"], "ALLOW")

    def test_lower_authority_denied(self):
        self.assertEqual(evaluate({**self.state, "authority_level": "INTERNAL"}, self.manifest, self.evidence)["disposition"], "DENY")

    def test_revoked_denied(self):
        self.assertEqual(evaluate({**self.state, "consent_revoked": True}, self.manifest, self.evidence)["disposition"], "DENY")

    def test_missing_security_exceedance_fails_closed(self):
        self.assertEqual(evaluate(self.state, self.manifest, {"source_digest_verified": True})["disposition"], "FAIL_CLOSED")

    def test_unverifiable_authority_fails_closed(self):
        self.assertEqual(evaluate({"classification": "SECRET"}, self.manifest, self.evidence)["disposition"], "FAIL_CLOSED")

    def test_missing_ledger_readback_fails_closed(self):
        self.assertEqual(verify_organization_readback({"id": "x"}, None)["disposition"], "FAIL_CLOSED")

    def test_local_claim_is_not_authentic_readback(self):
        transition = {"id": "x"}
        self.assertEqual(verify_organization_readback(transition, {"transition_digest": canonical_digest(transition)})["disposition"], "FAIL_CLOSED")

    def test_self_attestation_cannot_authenticate_ledger(self):
        transition = {"id": "x"}
        claimed = {"authenticated": True, "recording_confirmed": True,
                   "transition_digest": canonical_digest(transition), "continuity_verified": True}
        result = verify_organization_readback(transition, claimed)
        self.assertEqual(result["predicate"], "AUTHENTIC_SOVEREIGN_VERIFIER_UNAVAILABLE")

    def test_authenticator_rejection_fails_closed(self):
        transition = {"id": "x"}
        claimed = {"authenticated": True, "recording_confirmed": True,
                   "transition_digest": canonical_digest(transition), "continuity_verified": True}
        result = verify_organization_readback(transition, claimed, authenticate=lambda _: False)
        self.assertEqual(result["predicate"], "SOVEREIGN_READBACK_NOT_AUTHENTICATED")

    def test_authenticated_fixture_structural_consistency(self):
        # Fixture proves structural behavior, NOT a production sovereign record.
        transition = {"id": "x"}
        claimed = {"recording_confirmed": True,
                   "transition_digest": canonical_digest(transition), "continuity_verified": True}
        result = verify_organization_readback(transition, claimed, authenticate=lambda _: True)
        self.assertEqual(result["predicate"], "SUPPLIED_SOVEREIGN_READBACK_CONSISTENT")

    def test_digest_mismatch_fails_closed(self):
        transition = {"id": "x"}
        readback = {"authenticated": True, "recording_confirmed": True,
                    "transition_digest": canonical_digest({"id": "y"}), "continuity_verified": True}
        self.assertEqual(verify_organization_readback(transition, readback)["disposition"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
