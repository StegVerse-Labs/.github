from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts import verify_hil_post_restart_reconstruction as mod


def observation() -> dict:
    return {
        "schema": mod.OBSERVATION_SCHEMA,
        "state": "OBSERVED",
        "receiver_schema": "HIL-RECEIVER-RECEIPT-v2",
        "receiver_receipt_id": "HIL-RECEIPT-ABC",
        "submission_id": "HIL-INTAKE-TEST-001",
        "controlled_pdf_sha256": "sha256:" + "a" * 64,
        "retrieved_pdf_sha256": "sha256:" + "a" * 64,
        "exact_byte_reconstruction": "PASS",
        "custody_state": "EXACT_BYTES_PERSISTED",
        "registry_state": "RECORDED",
        "tvc_lifecycle_intent_observed": True,
        "tvc_receiving_receipt_observed": False,
        "receiver_restart_reconstruction_observed": False,
        "runtime_activation_claimed": False,
        "credential_used": False,
    }


def worker(adapter: Path, durable: Path) -> dict:
    return {
        "schema": mod.WORKER_SCHEMA,
        "task_id": mod.TASK_ID,
        "receiver_ready": True,
        "base_url": "http://127.0.0.1:8765",
        "adapter_root": str(adapter),
        "durable_state_root": str(durable),
        "receiver_pid": 1234,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "third_party_runtime_required": False,
    }


def status() -> dict:
    return {
        "schema_version": "HIL-SUBMISSION-STATUS-v1",
        "submission_id": "HIL-INTAKE-TEST-001",
        "submitted_file_sha256": "a" * 64,
        "custody_state": "EXACT_BYTES_PERSISTED",
        "registry_state": "RECORDED",
        "authority": {"execution": False, "acceptance": False, "publication": False, "master_record_append": False},
    }


class Proc:
    pid = 5678


class PostRestartTests(unittest.TestCase):
    def prepare(self, root: Path):
        runtime = root / "runtime"; runtime.mkdir()
        adapter = root / "adapter"; adapter.mkdir()
        durable = root / "durable"; durable.mkdir()
        obs = root / "obs.json"; obs.write_text(json.dumps(observation()))
        wp = runtime / mod.WORKER_RECEIPT_REL; wp.parent.mkdir(parents=True)
        wp.write_text(json.dumps(worker(adapter, durable)))
        return runtime, obs

    def test_missing_tvc_auth_is_retryable_predicate(self):
        with tempfile.TemporaryDirectory() as td:
            runtime, obs = self.prepare(Path(td))
            with self.assertRaisesRegex(mod.PredicatePending, "TVC_RECONSTRUCTION_AUTH_NOT_OBSERVED"):
                mod.verify_post_restart(runtime_root=runtime, observation_path=obs, env={})

    def test_same_submission_survives_controlled_restart(self):
        with tempfile.TemporaryDirectory() as td:
            runtime, obs = self.prepare(Path(td))
            killed = []
            launched = []
            def reader(url, timeout):
                return status()
            def bytes_reader(url, token, timeout):
                self.assertEqual(token, "secret-not-emitted")
                return b"x", {
                    "x-stegverse-hil-submission-id": "HIL-INTAKE-TEST-001",
                    "x-stegverse-hil-submitted-sha256": "a" * 64,
                    "x-stegverse-hil-reconstruction-state": "EXACT_BYTES_HASH_VERIFIED",
                }
            old_digest = mod._digest_hex
            mod._digest_hex = lambda value: "a" * 64
            try:
                result = mod.verify_post_restart(
                    runtime_root=runtime,
                    observation_path=obs,
                    env={"STEGVERSE_HIL_REVIEW_TOKEN": "secret-not-emitted"},
                    json_reader=reader,
                    bytes_reader=bytes_reader,
                    killer=lambda pid: killed.append(pid),
                    launcher=lambda *a, **k: (launched.append((a,k)) or Proc()),
                    ready_verifier=lambda url: {"state":"READY","credential_authority":"TV/TVC","github_token_runtime_authority":"NONE"},
                )
            finally:
                mod._digest_hex = old_digest
            self.assertEqual(result["state"], "PASS")
            self.assertEqual(killed, [1234])
            self.assertEqual(result["replacement_receiver_pid"], 5678)
            self.assertEqual(result["submission_id"], "HIL-INTAKE-TEST-001")
            self.assertFalse(result["credential_value_exposed"])
            self.assertFalse(result["tvc_receiving_receipt_observed"])
            self.assertTrue((runtime / mod.OUTPUT_REL).is_file())

    def test_observation_cannot_preclaim_restart(self):
        value = observation(); value["receiver_restart_reconstruction_observed"] = True
        with self.assertRaisesRegex(mod.ReconstructionFailure, "restart_already_claimed"):
            mod._validate_observation(value)


if __name__ == "__main__":
    unittest.main()
