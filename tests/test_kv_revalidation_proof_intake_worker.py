from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("intake", ROOT / "workers" / "kv_revalidation_proof_intake_worker.py")
assert spec and spec.loader
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)


class FakeTarget:
    TASK_ID = intake.TARGET_TASK_ID
    def __init__(self, state="HANDOFF_READY"):
        self.state = state
        self.received = None
    def execute(self, env):
        self.received = dict(env)
        return {
            "schema": "stegverse.kv.connection-revalidation-worker/v1",
            "state": self.state,
            "transition_id": "TEST_TARGET_RESULT",
            "task_id": intake.TARGET_TASK_ID,
            "provider_operation_authorized": False,
            "credential_material_present": False,
            "provider_network_access_performed": False,
            "proof_manufactured": False,
            "connection_verified": self.state == "COMPLETED",
            "authority_effect": "NONE",
        }


class KVRevalidationProofIntakeTests(unittest.TestCase):
    def _fixture(self, root: Path, **overrides):
        cvk = root / "cvk"; cvk.mkdir()
        kv = root / "kv"; kv.mkdir()
        conf = root / "conformance.json"; conf.write_text("{}", encoding="utf-8")
        read = root / "readback.json"; read.write_text("{}", encoding="utf-8")
        manifest = {
            "schema": intake.MANIFEST_SCHEMA,
            "task_id": intake.TARGET_TASK_ID,
            "assembly_id": "assembly-001",
            "cvk_root": str(cvk),
            "kv_root": str(kv),
            "conformance_proof_path": str(conf),
            "readback_proof_path": str(read),
            "required_after": "2026-08-29T15:00:00-05:00",
            "provider_operation_authorized": False,
            "credential_material_present": False,
            "authority_effect": "NONE",
        }
        manifest.update(overrides)
        path = root / "intake.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_hosted_surface_rejected_before_manifest(self):
        result = intake.execute({"GITHUB_ACTIONS": "true"})
        self.assertEqual(result["transition_id"], "HOSTED_SURFACE_REJECTED")

    def test_credential_environment_rejected(self):
        result = intake.execute({"STEGVERSE_KV_REVALIDATION_INTAKE": "/tmp/x", "GITHUB_TOKEN": "x"})
        self.assertEqual(result["transition_id"], "FORBIDDEN_CREDENTIAL_ENV")

    def test_network_manifest_location_rejected(self):
        result = intake.execute({"STEGVERSE_KV_REVALIDATION_INTAKE": "https://example.test/intake.json"})
        self.assertEqual(result["transition_id"], "INTAKE_MANIFEST_NETWORK_LOCATION_REJECTED")

    def test_manifest_network_proof_location_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root, conformance_proof_path="https://example.test/proof.json")
            result = intake.execute({"STEGVERSE_KV_REVALIDATION_INTAKE": str(manifest)})
            self.assertEqual(result["transition_id"], "INTAKE_VALIDATION_FAILED")
            self.assertIn("NETWORK_LOCATION_REJECTED", result["detail"])

    def test_manifest_cannot_expand_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root, provider_operation_authorized=True)
            result = intake.execute({"STEGVERSE_KV_REVALIDATION_INTAKE": str(manifest)})
            self.assertEqual(result["transition_id"], "INTAKE_VALIDATION_FAILED")
            self.assertIn("PROVIDER_OPERATION_AUTHORITY_PROHIBITED", result["detail"])

    def test_unexpected_credential_like_field_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            payload = json.loads(manifest.read_text())
            payload["api_token"] = "never"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            result = intake.execute({"STEGVERSE_KV_REVALIDATION_INTAKE": str(manifest)})
            self.assertEqual(result["transition_id"], "INTAKE_VALIDATION_FAILED")

    def test_dispatch_forwards_only_exact_nonsecret_revalidation_bindings(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            target = FakeTarget()
            env = {
                "STEGVERSE_KV_REVALIDATION_INTAKE": str(manifest),
                "XDG_STATE_HOME": str(root / "state"),
                "UNRELATED": "do-not-forward",
            }
            result = intake.execute(env, target_module=target)
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "KV_REVALIDATION_PROOF_INTAKE_DISPATCHED")
            self.assertFalse(result["connection_verified_by_intake"])
            self.assertNotIn("UNRELATED", target.received)
            self.assertEqual(target.received["STEGVERSE_KV_CONNECTION_ASSEMBLY_ID"], "assembly-001")
            self.assertEqual(target.received["STEGVERSE_KV_CONNECTION_REQUIRED_AFTER"], "2026-08-29T15:00:00-05:00")
            receipt = json.loads(Path(result["dispatch_receipt_path"]).read_text())
            self.assertTrue(receipt["intake_admitted"])
            self.assertTrue(receipt["target_invoked"])
            self.assertFalse(receipt["connection_verified_by_intake"])
            self.assertEqual(receipt["authority_effect"], "NONE")

    def test_downstream_completion_is_relayed_without_intake_claiming_verification(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._fixture(root)
            target = FakeTarget(state="COMPLETED")
            result = intake.execute({"STEGVERSE_KV_REVALIDATION_INTAKE": str(manifest), "XDG_STATE_HOME": str(root / "state")}, target_module=target)
            self.assertEqual(result["state"], "COMPLETED")
            self.assertTrue(result["downstream"]["connection_verified"])
            self.assertFalse(result["connection_verified_by_intake"])


if __name__ == "__main__":
    unittest.main()
