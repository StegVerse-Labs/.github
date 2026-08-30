import copy
import unittest

from scripts import verify_sv_dn1_runtime_observation as verifier


def fixture():
    exchange_id = "sha256:" + "b" * 64
    transform = "sha256:" + "a" * 64
    raw_sha = "sha256:" + "c" * 64
    capture = {
        "raw_sha256": raw_sha,
        "parsed_json": {"modelId": "Qwen/Qwen3-8B"},
    }
    exchange = {
        "exchange_id": exchange_id,
        "raw_evidence": {"preserved_native_fields": capture["parsed_json"]},
        "far_side_receipt": {"transformation_hash": transform},
        "intr": {"previous_receipt_hash": transform},
    }
    resident = {
        "state": "COMPLETE",
        "transition_id": verifier.RESIDENT_TRANSITION,
        "runtime_source_pin_verified": True,
        "raw_response_sha256": raw_sha,
        "semantic_exchange_id": exchange_id,
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
    }
    intr = {
        "state": "COMPLETE",
        "transition_id": verifier.INTR_TRANSITION,
        "route_id": verifier.ROUTE_ID,
        "transport_profile": verifier.TRANSPORT_PROFILE,
        "exchange_id": exchange_id,
        "source_transform_hash": transform,
        "previous_receipt_hash": transform,
        "destination_validation": "PASS",
        "lineage_verified": True,
        "claims": {
            "canonical_protocol_adopted": True,
            "universal_intr_policy_id": verifier.POLICY_ID,
            "boundary_from": "EXTERNAL_SYSTEM",
            "boundary_to": "STEGOS_ECOSYSTEM",
            "interlock_required_per_hop": True,
            "receipt_hash_chain_required": True,
            "runtime_activation_claimed": False,
            "production_interlock_runtime_activated": False,
            "sdk_admitted": False,
            "authority_effect": "NONE",
        },
    }
    intr["receipt_hash"] = verifier.sha256_ref(intr)
    return resident, capture, exchange, intr


class RuntimeObservationVerifierTests(unittest.TestCase):
    def test_complete_authentic_shape_promotes_to_observed(self):
        resident, capture, exchange, intr = fixture()
        result = verifier.verify(resident, capture, exchange, intr)
        self.assertEqual(result["state"], "OBSERVED")
        self.assertEqual(result["resident_source_capture"], "OBSERVED")
        self.assertEqual(result["hf_semantic_exchange"], "OBSERVED")
        self.assertEqual(result["universal_intr_hop"], "OBSERVED")
        self.assertFalse(result["runtime_activation_claimed"])
        self.assertFalse(result["sdk_admitted"])

    def test_tampered_intr_receipt_cannot_promote(self):
        resident, capture, exchange, intr = fixture()
        tampered = copy.deepcopy(intr)
        tampered["destination_validation"] = "FAIL"
        with self.assertRaisesRegex(RuntimeError, "destination validation or lineage failed"):
            verifier.verify(resident, capture, exchange, tampered)

    def test_wrong_boundary_cannot_promote(self):
        resident, capture, exchange, intr = fixture()
        tampered = copy.deepcopy(intr)
        tampered["claims"]["boundary_to"] = "OTHER"
        body = {k: v for k, v in tampered.items() if k != "receipt_hash"}
        tampered["receipt_hash"] = verifier.sha256_ref(body)
        with self.assertRaisesRegex(RuntimeError, "boundary_to"):
            verifier.verify(resident, capture, exchange, tampered)

    def test_missing_resident_receipt_cannot_promote(self):
        resident, capture, exchange, intr = fixture()
        resident["state"] = "HANDOFF_READY"
        with self.assertRaisesRegex(RuntimeError, "resident observation is not complete"):
            verifier.verify(resident, capture, exchange, intr)


if __name__ == "__main__":
    unittest.main()
