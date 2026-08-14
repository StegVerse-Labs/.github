from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "local_source_generation_executor",
    ROOT / "workers" / "local_source_generation_executor.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class LocalSourceGenerationExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads((ROOT / "control" / "local-source-generation-executor.json").read_text(encoding="utf-8"))
        self.manifest = {
            "schema": "stegverse.owner-implementation-work-manifest/v0.1",
            "claim_state": "READY_FOR_SEPARATE_OWNER_ADMISSION",
            "delta_id": "delta-test-001",
            "owner_repository": "StegVerse-Labs/example-owner",
            "proposed_paths": ["EXAMPLE_MIRROR_HANDOFF.md", "src/example.py"],
        }
        self.source_evidence = {
            "capability_id": "stegverse:capability:formalism-source-generation:v1",
            "capability_version": "1.0.0",
            "phase": "ACTIVATED",
            "existence_hash": "a" * 64,
            "activation_proof_ref": "receipts/source-generation/activation.json",
            "integration_evidence_refs": ["receipts/source-generation/integration.json"],
            "authority_ref": "handoffs/SHWP-ADMISSIBLE-SOURCE-GENERATION-CAPABILITY-001.json",
            "profile_ref": "control/admissible-source-generation-capability.json",
        }
        self.model_evidence = {
            "capability_id": "stegverse:capability:sovereign-local-model:v1",
            "capability_version": "1.0.0",
            "phase": "ACTIVATED",
            "activation_proof_ref": "receipts/local-model/activation.json",
            "integration_evidence_refs": ["receipts/local-model/integration.json"],
        }
        self.payload = {
            "source_generation_capability_evidence": self.source_evidence,
            "local_model_capability_evidence": self.model_evidence,
            "owner_manifest": self.manifest,
            "source_hashes": {"EXAMPLE_MIRROR_HANDOFF.md": None, "src/example.py": "b" * 64},
            "base_ref": "main",
            "expected_base_sha": "c" * 40,
            "runtime_endpoint": "http://127.0.0.1:11435",
            "lifetime_class": "ONE_SHOT_OPERATION",
            "execution_identity": "test-execution-001",
        }
        self.generated = {
            "files": [
                {"path": "EXAMPLE_MIRROR_HANDOFF.md", "content_utf8": "# Example\n"},
                {"path": "src/example.py", "content_utf8": "VALUE = 1\n"},
            ],
            "new_branch": "feat/generated-example",
            "commit_message": "Implement admitted example",
        }
        self.telemetry = {
            "model": "stegverse-reference-lm-v1",
            "model_hash": "d" * 64,
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

    def run_payload(self, payload=None, generated=None):
        with patch.object(mod, "request_completion", return_value=(generated or self.generated, self.telemetry, None)):
            return mod.execute(self.config, payload or self.payload)

    def test_source_generation_below_activated_fails_closed(self):
        payload = dict(self.payload)
        payload["source_generation_capability_evidence"] = dict(self.source_evidence, phase="ADMISSIBLE")
        result, code = self.run_payload(payload)
        self.assertEqual(code, 0)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("NOT_ACTIVATED", result["reason"])

    def test_local_model_below_activated_fails_closed(self):
        payload = dict(self.payload)
        payload["local_model_capability_evidence"] = dict(self.model_evidence, phase="ADMISSIBLE")
        result, _ = self.run_payload(payload)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("NOT_ACTIVATED", result["reason"])

    def test_missing_activation_proof_fails_closed(self):
        payload = dict(self.payload)
        evidence = dict(self.source_evidence)
        evidence["activation_proof_ref"] = None
        payload["source_generation_capability_evidence"] = evidence
        result, _ = self.run_payload(payload)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("ACTIVATION_PROOF_MISSING", result["reason"])

    def test_non_loopback_endpoint_is_not_accepted(self):
        endpoint, error = mod.loopback_endpoint("https://example.com/v1", set(self.config["allowed_hosts"]))
        self.assertIsNone(endpoint)
        self.assertEqual(error, "RUNTIME_ENDPOINT_NOT_LOOPBACK_HTTP")

    def test_secret_bearing_environment_is_not_forwarded(self):
        source = {
            "PATH": "/usr/bin",
            "LANG": "C.UTF-8",
            "GITHUB_TOKEN": "forbidden",
            "PROVIDER_API_KEY": "forbidden",
            "WALLET_PRIVATE_KEY": "forbidden",
        }
        child = mod.safe_runtime_env(self.config, source)
        self.assertEqual(child, {"PATH": "/usr/bin", "LANG": "C.UTF-8"})
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertNotIn("PROVIDER_API_KEY", child)
        self.assertNotIn("WALLET_PRIVATE_KEY", child)

    def test_deterministic_prompt_binds_manifest_base_and_source_hashes(self):
        bindings, error = mod.manifest_source_bindings(self.manifest, self.payload)
        self.assertIsNone(error)
        prompt1 = mod.generation_prompt(bindings)
        prompt2 = mod.generation_prompt(bindings)
        self.assertEqual(prompt1, prompt2)
        parsed = json.loads(prompt1)
        self.assertEqual(parsed["owner_manifest_sha256"], mod.canonical_hash(self.manifest))
        self.assertEqual(parsed["expected_base_sha"], "c" * 40)
        self.assertEqual(parsed["expected_source_sha256"]["src/example.py"], "b" * 64)

    def test_malformed_model_output_fails_closed(self):
        with patch.object(mod.urllib.request, "urlopen") as opened:
            response = opened.return_value.__enter__.return_value
            response.read.return_value = json.dumps({"choices": [{"message": {"content": "not json"}}]}).encode("utf-8")
            generated, telemetry, error = mod.request_completion("http://127.0.0.1:11435", "{}", 1, 1024)
        self.assertIsNone(generated)
        self.assertEqual(telemetry, {})
        self.assertEqual(error, "MODEL_OUTPUT_NOT_STRICT_JSON")

    def test_out_of_scope_path_fails_closed(self):
        generated = dict(self.generated)
        generated["files"] = [{"path": "EXAMPLE_MIRROR_HANDOFF.md", "content_utf8": "# H\n"}, {"path": "src/not-admitted.py", "content_utf8": "x=1\n"}]
        result, _ = self.run_payload(generated=generated)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("GENERATED_PATH_NOT_ADMITTED", result["reason"])

    def test_file_count_and_byte_limits_are_enforced(self):
        config = dict(self.config)
        config["maximum_file_count"] = 1
        bindings, error = mod.manifest_source_bindings(self.manifest, self.payload)
        self.assertIsNone(error)
        files, error = mod.validate_generated(config, bindings, self.generated)
        self.assertIsNone(files)
        self.assertEqual(error, "GENERATED_FILE_COUNT_EXCEEDED")
        config = dict(self.config)
        config["maximum_total_bytes"] = 2
        files, error = mod.validate_generated(config, bindings, self.generated)
        self.assertIsNone(files)
        self.assertEqual(error, "GENERATED_TOTAL_BYTES_EXCEEDED")

    def test_valid_bounded_flow_emits_exact_result_and_proofs(self):
        result, code = self.run_payload()
        self.assertEqual(code, 0)
        self.assertEqual(result["state"], "COMPLETED")
        body = result["result"]
        self.assertEqual(body["schema"], "stegverse.local-source-generation-result/v0.1")
        self.assertEqual(body["generator_phase"], "ACTIVATED")
        self.assertEqual(body["local_model_phase"], "ACTIVATED")
        self.assertFalse(body["persistent_execution_used"])
        self.assertEqual(body["credential_authority"], "TV/TVC")
        self.assertFalse(body["github_token_runtime_authority"])
        self.assertFalse(body["non_tv_tvc_secret_or_token_used"])
        self.assertFalse(body["consumer_credential_present"])
        proof = body["_runtime_proof"]
        self.assertEqual(proof["endpoint_class"], "LOOPBACK_ONLY")
        self.assertFalse(proof["non_tv_tvc_secret_or_token_used"])
        self.assertFalse(proof["provider_secret_used"])
        self.assertFalse(proof["wallet_contacted"])
        self.assertFalse(proof["signed"])
        self.assertFalse(proof["broadcast"])
        teardown = body["_teardown_proof"]
        self.assertFalse(teardown["persistent_execution_used"])


if __name__ == "__main__":
    unittest.main()
