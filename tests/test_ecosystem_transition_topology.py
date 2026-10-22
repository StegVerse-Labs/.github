"""Conformance vectors for topology #3299. Mock readback is not sovereign proof."""
import unittest
from unittest.mock import patch
from scripts.ecosystem_transition_topology import evaluate, verify_organization_readback, canonical_digest, verify_native_organization_transition, verify_published_organization_chain


class TransitionTopologyTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {"manifest_id": "fixture-1", "classification": "SECRET",
                         "minimum_authority_level": "SECRET"}
        self.state = {"authority_level": "SECRET", "classification": "SECRET"}
        self.evidence = {"source_digest_verified": True, "security_exceedance_verified": True}

    def test_native_missing_state_receipt_fails_closed(self):
        result = verify_native_organization_transition({}, expected_transition_id="")
        self.assertEqual(result["disposition"], "FAIL_CLOSED")

    def test_native_readback_missing_fails_closed(self):
        result = verify_native_organization_transition({"receipt_sha256": "fixture"}, expected_transition_id="fixture")
        self.assertEqual(result["disposition"], "FAIL_CLOSED")

    def test_native_gate_rejects_missing_receipt_even_with_expected_id(self):
        result = verify_native_organization_transition(
            {"receipt_sha256": "not-a-real-receipt"},
            expected_transition_id="not-a-real-transition",
        )
        self.assertEqual(result["disposition"], "FAIL_CLOSED")

    def test_native_verified_receipt_uses_existing_gate(self):
        from workers import canonical_state_transition_custody as custody
        receipt = {"receipt_sha256": "sha256:fixture"}
        native = {"verified": True, "organization_receipt_sha256": "sha256:org-fixture",
                  "refusal": None}
        with patch.object(custody, "organization_receipt_gate", return_value=native) as gate:
            result = verify_native_organization_transition(
                receipt, expected_transition_id="transition-1",
                expected_predecessor="sha256:predecessor")
        self.assertEqual(result["predicate"], "NATIVE_ORGANIZATION_READBACK_VERIFIED")
        gate.assert_called_once_with(receipt, root=None,
                                     expected_transition_id="transition-1",
                                     expected_predecessor="sha256:predecessor",
                                     record_refusal=False)

    def test_native_exception_fails_closed(self):
        from workers import canonical_state_transition_custody as custody
        with patch.object(custody, "organization_receipt_gate", side_effect=Exception("readback unavailable")):
            result = verify_native_organization_transition(
                {"receipt_sha256": "sha256:fixture"}, expected_transition_id="transition-1")
        self.assertEqual(result["predicate"], "NATIVE_ORGANIZATION_READBACK_UNAVAILABLE")

    def test_native_refusal_is_not_promoted(self):
        from workers import canonical_state_transition_custody as custody
        with patch.object(custody, "organization_receipt_gate",
                          return_value={"verified": False, "refusal": {"disposition": "DENY"}}):
            result = verify_native_organization_transition(
                {"receipt_sha256": "sha256:fixture"}, expected_transition_id="transition-1")
        self.assertEqual(result["disposition"], "FAIL_CLOSED")

    def test_published_chain_missing_binding_fails_closed(self):
        result = verify_published_organization_chain("", expected_receipt_sha256="")
        self.assertEqual(result["predicate"], "FRESH_REF_OR_RECEIPT_NOT_BOUND")

    def test_published_chain_missing_ref_fails_closed(self):
        result = verify_published_organization_chain(
            "git+/nonexistent/topology.git#refs/stegverse/organization-ledger",
            expected_receipt_sha256="sha256:nonexistent")
        self.assertEqual(result["disposition"], "FAIL_CLOSED")

    def test_published_chain_cannot_accept_wrong_receipt(self):
        result = verify_published_organization_chain(
            "git+/nonexistent/topology.git#refs/stegverse/organization-ledger",
            expected_receipt_sha256="sha256:wrong")
        self.assertNotEqual(result["disposition"], "ALLOW")

    def test_published_chain_binds_transition_and_predecessor_without_granting_authority(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import importlib.util

        observed = {
            "disposition": "ALLOW",
            "every_receipt_verifies_against_its_body": True,
            "every_source_receipt_retained_and_verifies": True,
            "chain": [{"receipt_sha256": "sha256:receipt",
                       "source_transition_id": "transition-1",
                       "previous_receipt_sha256": "sha256:predecessor"}],
            "head_receipt_sha256": "sha256:receipt",
            "chain_length": 1,
        }
        fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))
        with patch.object(importlib.util, "spec_from_file_location", return_value=fake_spec), \
             patch.object(importlib.util, "module_from_spec",
                          return_value=SimpleNamespace(readback=lambda _: observed)):
            kwargs = {"expected_receipt_sha256": "sha256:receipt",
                      "expected_transition_id": "transition-1",
                      "expected_predecessor_sha256": "sha256:predecessor"}
            allowed = verify_published_organization_chain("fixture-ref", **kwargs)
            self.assertEqual(allowed["disposition"], "ALLOW")
            self.assertEqual(allowed["verification_scope"],
                             "ORGANIZATION_RECORDING_ONLY_NOT_GOVERNANCE_ADMISSIBILITY")
            wrong_id = verify_published_organization_chain(
                "fixture-ref", **{**kwargs, "expected_transition_id": "wrong"})
            self.assertEqual(wrong_id["predicate"], "EXPECTED_TRANSITION_ID_MISMATCH")
            wrong_parent = verify_published_organization_chain(
                "fixture-ref", **{**kwargs, "expected_predecessor_sha256": "sha256:wrong"})
            self.assertEqual(wrong_parent["predicate"], "EXPECTED_PREDECESSOR_MISMATCH")
            missing = verify_published_organization_chain(
                "fixture-ref", **{**kwargs, "expected_receipt_sha256": "sha256:absent"})
            self.assertEqual(missing["predicate"], "EXPECTED_SOVEREIGN_RECEIPT_NOT_IN_CHAIN")
            duplicate = {**observed, "chain": observed["chain"] * 2}
            observed.update(duplicate)
            self.assertEqual(verify_published_organization_chain("fixture-ref", **kwargs)["disposition"],
                             "FAIL_CLOSED")

    def test_published_chain_fails_closed_on_native_integrity_rejection(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import importlib.util

        observed = {
            "disposition": "DENY",
            "every_receipt_verifies_against_its_body": True,
            "every_source_receipt_retained_and_verifies": True,
            "chain": [{"receipt_sha256": "sha256:receipt"}],
            "head_receipt_sha256": "sha256:receipt",
            "chain_length": 1,
        }
        fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))
        with patch.object(importlib.util, "spec_from_file_location", return_value=fake_spec), \
             patch.object(importlib.util, "module_from_spec",
                          return_value=SimpleNamespace(readback=lambda _: observed)):
            result = verify_published_organization_chain(
                "fixture-ref", expected_receipt_sha256="sha256:receipt")
            self.assertEqual(result["predicate"], "ORGANIZATION_CHAIN_INTEGRITY_UNVERIFIED")
            observed["disposition"] = "ALLOW"
            observed["every_source_receipt_retained_and_verifies"] = False
            result = verify_published_organization_chain(
                "fixture-ref", expected_receipt_sha256="sha256:receipt")
            self.assertEqual(result["predicate"], "ORGANIZATION_CHAIN_INTEGRITY_UNVERIFIED")

    def test_malformed_native_chain_payload_fails_closed(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        import importlib.util

        fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None))
        with patch.object(importlib.util, "spec_from_file_location", return_value=fake_spec), \
             patch.object(importlib.util, "module_from_spec",
                          return_value=SimpleNamespace(readback=lambda _: None)):
            result = verify_published_organization_chain(
                "fixture-ref", expected_receipt_sha256="sha256:receipt")
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["predicate"], "MALFORMED_NATIVE_ORGANIZATION_READBACK")

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
