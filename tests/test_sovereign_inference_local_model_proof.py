from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ecosystem_chat_sovereign_inference_worker",
    ROOT / "workers" / "ecosystem_chat_sovereign_inference_worker.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def valid_proof(*, live: bool = False) -> dict:
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
    if live:
        proof["endpoint"] = "http://127.0.0.1:31415"
        proof["process_owned_by_verifier"] = False
        proof["predicates"]["live_endpoint_remains_available"] = True
        proof["model_id"] = "stegverse-reference-lm-v1"
        proof["model_hash"] = "abc"
        proof["proof_hash"] = "def"
    return proof


class FakeProcess:
    pid = 4242
    returncode = None

    def poll(self):
        return None


class SovereignInferenceLocalModelProofTests(unittest.TestCase):
    def test_verified_reference_model_proof_is_accepted_as_execution_progress(self) -> None:
        self.assertTrue(mod.reference_model_proof_verified(valid_proof()))

    def test_probe_proof_is_not_mistaken_for_persistent_live_endpoint(self) -> None:
        self.assertFalse(mod.live_reference_model_proof_verified(valid_proof()))
        self.assertTrue(mod.live_reference_model_proof_verified(valid_proof(live=True)))

    def test_reference_proof_cannot_claim_production_llm_equivalence(self) -> None:
        proof = valid_proof()
        proof["qualifies_as_large_production_llm"] = True
        self.assertFalse(mod.reference_model_proof_verified(proof))

    def test_third_party_or_authorizing_proof_is_rejected(self) -> None:
        proof = valid_proof()
        proof["predicates"]["third_party_inference_required"] = True
        self.assertFalse(mod.reference_model_proof_verified(proof))

    def test_find_micro_node_root_discovers_materialized_runtime_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative in (
                "tools/verify_sovereign_model_runtime.py",
                "tools/run_sovereign_model.py",
                "micro_node/local_model_runtime.py",
                "models/stegverse_reference_language_model.v1.json",
                "models/stegverse_reference_corpus.v1.txt",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("present\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"STEGVERSE_MICRO_NODE_RUNTIME_ROOT": str(root)}, clear=False):
                self.assertEqual(mod.find_micro_node_root(), root.resolve())

    def test_worker_launches_local_probe_verifier_without_github_token(self) -> None:
        proof = valid_proof()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            verifier = root / "tools" / "verify_sovereign_model_runtime.py"
            verifier.parent.mkdir(parents=True, exist_ok=True)
            verifier.write_text("import json\n" f"print(json.dumps({proof!r}))\n", encoding="utf-8")
            original = mod.LOCAL_PROOF_RECEIPT
            mod.LOCAL_PROOF_RECEIPT = root / "receipts" / "proof.json"
            try:
                result = mod.run_reference_model_verifier(root)
                self.assertEqual(result["state"], "COMPLETE")
                self.assertFalse(result["github_token_required"])
                persisted = json.loads(mod.LOCAL_PROOF_RECEIPT.read_text(encoding="utf-8"))
                self.assertTrue(mod.reference_model_proof_verified(persisted))
            finally:
                mod.LOCAL_PROOF_RECEIPT = original

    def test_heartbeat_launches_and_leases_live_model_endpoint(self) -> None:
        proof = valid_proof(live=True)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            server = root / "tools" / "run_sovereign_model.py"
            server.parent.mkdir(parents=True, exist_ok=True)
            server.write_text("# present\n", encoding="utf-8")
            original_state = mod.LIVE_MODEL_STATE
            original_proof = mod.LOCAL_PROOF_RECEIPT
            mod.LIVE_MODEL_STATE = root / "receipts" / "live.json"
            mod.LOCAL_PROOF_RECEIPT = root / "receipts" / "proof.json"
            try:
                with mock.patch.object(mod.subprocess, "Popen", return_value=FakeProcess()), mock.patch.object(mod, "_free_port", return_value=31415), mock.patch.object(mod, "_health", return_value={"state": "READY"}), mock.patch.object(mod, "run_reference_model_verifier", return_value={"attempted": True, "state": "COMPLETE", "proof": proof, "proof_path": str(mod.LOCAL_PROOF_RECEIPT), "github_token_required": False}):
                    result = mod.ensure_live_reference_model(root, heartbeat_epoch=31, claim_id="claim-1", fencing_token=9)
                self.assertEqual(result["state"], "COMPLETE")
                self.assertEqual(result["endpoint"], "http://127.0.0.1:31415")
                lifecycle = json.loads(mod.LIVE_MODEL_STATE.read_text(encoding="utf-8"))
                self.assertEqual(lifecycle["state"], "LIVE_VERIFIED")
                self.assertEqual(lifecycle["pid"], 4242)
                self.assertEqual(lifecycle["credential_requirement"], "NONE")
                self.assertFalse(lifecycle["github_token_required"])
            finally:
                mod.LIVE_MODEL_STATE = original_state
                mod.LOCAL_PROOF_RECEIPT = original_proof

    def test_hosted_validation_environment_is_not_production_launch_authority(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            self.assertTrue(mod.third_party_hosted_environment())
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false", "RENDER": "false", "VERCEL": "false", "CF_PAGES": "false", "CLOUDFLARE_WORKERS": "false"}, clear=False):
            self.assertFalse(mod.third_party_hosted_environment())


if __name__ == "__main__":
    unittest.main()
