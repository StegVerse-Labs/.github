from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_worker():
    path = ROOT / "workers/sv_dn1_resident_observer_worker.py"
    spec = importlib.util.spec_from_file_location("sv_dn1_resident_observer_worker_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


W = load_worker()


class SvDn1ResidentObserverWorkerTests(unittest.TestCase):
    def test_registry_adapter_handoff_and_cost_basis_are_consistent(self) -> None:
        registry = json.loads((ROOT / "control/worker-registry.d/sv-dn1-resident-observer-001.json").read_text())
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/sv-dn1-resident-observer-001.json").read_text())
        handoff = json.loads((ROOT / "handoffs/SV-DN1-RESIDENT-OBSERVER-001.json").read_text())
        cost = json.loads((ROOT / "cost-basis/worker-runtime/sv-dn1-resident-observer.json").read_text())

        task = registry["tasks"][0]
        worker = registry["workers"][0]
        proc = adapter["adapters"][0]

        self.assertEqual(task["task_id"], W.TASK_ID)
        self.assertEqual(worker["worker_id"], W.WORKER_ID)
        self.assertEqual(proc["adapter_ref"], worker["adapter_ref"])
        self.assertEqual(proc["command"], ["python", "workers/sv_dn1_resident_observer_worker.py"])
        self.assertEqual(worker["capability_profile_ref"], "control/worker-capability-profiles.json#public-research-worker-v1")
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertFalse(handoff["authority"]["github_token_required"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])
        self.assertFalse(handoff["authority"]["sdk_admission_authority"])
        self.assertEqual(cost["cost_estimate"]["external_cost_usd"], 0)

    def test_source_missing_returns_handoff_ready_without_remote_checkout(self) -> None:
        with mock.patch.dict(os.environ, {W.ROOT_ENV: "/definitely/missing"}, clear=False):
            self.assertIsNone(W.find_source_root())
        response = W.source_wait_response(W.SourceUnavailable("missing"))
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertFalse(response["github_token_used"])
        self.assertFalse(response["repository_writeback_performed"])

    def test_public_source_unavailable_returns_handoff_ready(self) -> None:
        response = W.public_source_wait_response(W.PublicSourceUnavailable("temporary"))
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertEqual(response["transition_id"], "SV_DN1_PUBLIC_SOURCE_TEMPORARILY_UNAVAILABLE")
        self.assertEqual(response["evidence_refs"], [W.TARGET_URL])

    def test_hosted_and_credentials_are_explicitly_forbidden(self) -> None:
        source = (ROOT / "workers/sv_dn1_resident_observer_worker.py").read_text()
        for token in ("GITHUB_ACTIONS", "GITHUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN"):
            self.assertIn(token, source)
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/sv-dn1-resident-observer-001.json").read_text())
        env = set(adapter["adapters"][0]["env_allowlist"])
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("HF_TOKEN", env)
        self.assertNotIn("HUGGINGFACE_TOKEN", env)

    def test_handoff_public_network_scope_is_narrow_and_unauthenticated(self) -> None:
        handoff = json.loads((ROOT / "handoffs/SV-DN1-RESIDENT-OBSERVER-001.json").read_text())
        net = handoff["execution"]["public_network_access"]
        self.assertTrue(net["enabled"])
        self.assertEqual(net["methods"], ["GET"])
        self.assertEqual(net["allowed_hosts"], ["huggingface.co", "*.huggingface.co"])
        self.assertFalse(net["authenticated"])
        self.assertFalse(net["credential_forwarding"])

    def test_completed_response_stops_before_intr_sdk_and_publication(self) -> None:
        receipt = {
            "source_capture_ref": "observed/source-capture.json",
            "semantic_exchange_ref": "observed/exchange.json",
            "local_receipt_ref": "receipts/latest.json",
        }
        response = W.completed_response(receipt)
        self.assertEqual(response["state"], "COMPLETED")
        self.assertEqual(response["expected_next_transition"], "SV_DN1_INTR_SDK_LIVE_ADMISSION")
        self.assertFalse(response["github_token_used"])
        self.assertFalse(response["repository_writeback_performed"])

    def test_validate_invocation_rejects_sdk_admission_authority(self) -> None:
        invocation = {
            "task": {"task_id": W.TASK_ID, "worker_id": W.WORKER_ID, "claim_id": "claim-1"},
            "handoff": {
                "authority": {
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "non_tv_tvc_secret_or_token_allowed": False,
                    "repository_writeback_authority": False,
                    "sdk_admission_authority": True,
                    "heartbeat_grants_execution_authority": False,
                }
            },
        }
        with self.assertRaises(RuntimeError):
            W.validate_invocation(invocation)

    def test_runtime_source_manifest_is_required_and_pinned(self) -> None:
        source = (ROOT / "workers/sv_dn1_resident_observer_worker.py").read_text()
        self.assertIn("config/sv_dn1_runtime_source_manifest.json", source)
        self.assertIn("validate_pinned_source", source)

    def test_pinned_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            target = root / "scripts" / "example.py"
            target.write_text("print('changed')\n", encoding="utf-8")
            manifest = {
                "schema": "stegverse.sv-dn1.runtime-source-manifest/v1",
                "hash_profile": "git-blob-sha1",
                "source_basis_commit": "test",
                "files": {"scripts/example.py": "0" * 40},
            }
            (root / "config" / "sv_dn1_runtime_source_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with self.assertRaises(W.SourceUnavailable):
                W.validate_pinned_source(root)


if __name__ == "__main__":
    unittest.main()
