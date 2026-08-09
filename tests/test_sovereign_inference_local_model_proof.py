from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ecosystem_chat_sovereign_inference_worker",
    ROOT / "workers" / "ecosystem_chat_sovereign_inference_worker.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class SovereignInferenceLocalModelProofTests(unittest.TestCase):
    def test_verified_reference_model_proof_is_accepted_as_execution_progress(self) -> None:
        proof = {
            "schema": "stegverse.sovereign-local-model-proof/v1",
            "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
            "authority_effect": "NONE",
            "qualifies_as_large_production_llm": False,
            "predicates": {
                "real_model_process_observed": True,
                "private_endpoint_only": True,
                "real_inference_response_observed": True,
                "measured_usage_persistable": True,
                "local_training_observed": True,
                "third_party_inference_required": False,
                "model_output_grants_authority": False,
            },
        }
        self.assertTrue(mod.reference_model_proof_verified(proof))

    def test_reference_proof_cannot_claim_production_llm_equivalence(self) -> None:
        proof = {
            "schema": "stegverse.sovereign-local-model-proof/v1",
            "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
            "authority_effect": "NONE",
            "qualifies_as_large_production_llm": True,
            "predicates": {
                "real_model_process_observed": True,
                "private_endpoint_only": True,
                "real_inference_response_observed": True,
                "measured_usage_persistable": True,
                "local_training_observed": True,
                "third_party_inference_required": False,
                "model_output_grants_authority": False,
            },
        }
        self.assertFalse(mod.reference_model_proof_verified(proof))

    def test_third_party_or_authorizing_proof_is_rejected(self) -> None:
        proof = {
            "schema": "stegverse.sovereign-local-model-proof/v1",
            "state": "VERIFIED_REFERENCE_MODEL_RUNTIME",
            "authority_effect": "NONE",
            "qualifies_as_large_production_llm": False,
            "predicates": {
                "real_model_process_observed": True,
                "private_endpoint_only": True,
                "real_inference_response_observed": True,
                "measured_usage_persistable": True,
                "local_training_observed": True,
                "third_party_inference_required": True,
                "model_output_grants_authority": False,
            },
        }
        self.assertFalse(mod.reference_model_proof_verified(proof))


if __name__ == "__main__":
    unittest.main()
