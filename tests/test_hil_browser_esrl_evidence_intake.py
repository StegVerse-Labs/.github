import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "intake_hil_browser_esrl_evidence.py"
spec = importlib.util.spec_from_file_location("hil_esrl_intake", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class HILBrowserESRLEvidenceIntakeTests(unittest.TestCase):
    def artifact(self):
        binding = "a" * 64
        return {
            "schema": mod.ARTIFACT_SCHEMA,
            "state": "LEASE_OPEN",
            "lease_state": "LEASE_OPEN",
            "lease_id": "HIL-BROWSER-ESRL-" + binding[:24],
            "hil_esrl_protocol": mod.ESRL_PROTOCOL,
            "source_browser_protocol": mod.SOURCE_PROTOCOL,
            "task_id": mod.TASK_ID,
            "resident_request_id": mod.REQUEST_ID,
            "resident_request_sha256": mod.REQUEST_SHA256,
            "node_id": "stegnode-web-f24e3bfb7f5343cb37323187a88e51f3",
            "browser_context_id": "ctx_d151139d2db1eeecb6512f5844058246",
            "claim_id": "SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25",
            "fencing_token": 25,
            "canonical_checkout_receipt_sha256": "sha256:" + "b" * 64,
            "source_execution_entry_sha256": "8ddd8c6fc08038ce4111b349f47a5f44bd48a7bfbc551fae1bfb59a1a384da69",
            "binding_sha256": "sha256:" + binding,
            "state_machine": mod.EXPECTED_STATES,
            "runtime_class": "EVENT_EPHEMERAL",
            "lease_profile": "INTAKE",
            "runtime_materialized": True,
            "local_identity_verified": True,
            "local_ready_source_observed": True,
            "journal_replay_state": "PASS",
            "public_https_rendezvous_observed": False,
            "public_observation_is_downstream_optional": True,
            "same_device_execution_required": True,
            "execution_surface": "CURRENT_USER_IPHONE",
            "requires_other_machine": False,
            "second_claim_minted": False,
            "request_consumption_claimed": False,
            "custody_observed": False,
            "post_restart_exact_byte_proof_observed": False,
            "tvc_lifecycle_receipt_observed": False,
            "broader_hil_lifecycle_complete": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "heartbeat_granted_authority": False,
            "authority_effect": "NONE_RUNTIME_OBSERVATION_ONLY",
        }

    def test_valid_exact_subject_binding_is_accepted(self):
        canonical = json.loads((ROOT / mod.CANONICAL_RECEIPT_REL).read_text(encoding="utf-8"))
        receipt = mod.validate_artifact(self.artifact(), canonical)
        self.assertEqual(receipt["state"], "ACCEPTED")
        self.assertTrue(receipt["esrl_lease_open_observed"])
        self.assertFalse(receipt["post_restart_exact_byte_proof_observed"])
        self.assertFalse(receipt["tvc_lifecycle_receipt_observed"])

    def test_downstream_claim_fails_closed(self):
        canonical = json.loads((ROOT / mod.CANONICAL_RECEIPT_REL).read_text(encoding="utf-8"))
        artifact = self.artifact()
        artifact["tvc_lifecycle_receipt_observed"] = True
        with self.assertRaises(mod.IntakeError):
            mod.validate_artifact(artifact, canonical)

    def test_context_mismatch_fails_closed(self):
        canonical = json.loads((ROOT / mod.CANONICAL_RECEIPT_REL).read_text(encoding="utf-8"))
        artifact = self.artifact()
        artifact["browser_context_id"] = "ctx_" + "0" * 32
        with self.assertRaises(mod.IntakeError):
            mod.validate_artifact(artifact, canonical)

    def test_exact_artifact_hash_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "evidence.json"
            artifact_path.write_text(json.dumps(self.artifact(), sort_keys=True) + "\n", encoding="utf-8")
            receipt = mod.intake(repo_root=ROOT, artifact_path=artifact_path)
            self.assertRegex(receipt["source_artifact_sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(receipt["canonical_request_consumption_ref"], str(mod.CANONICAL_RECEIPT_REL))


if __name__ == "__main__":
    unittest.main()
