from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from heartbeat_runtime.runtime_presence_projection import project


class RuntimePresenceProjectionTests(unittest.TestCase):
    def write(self, root: Path, rel: str, value: dict) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def canonical_service_receipt(self) -> dict:
        return {
            "schema": "stegverse.sovereign-heartbeat-service/v4",
            "active": True,
            "carrier_active": True,
            "worker_active": True,
            "native_process_supervision_only": True,
            "separate_carrier_and_worker_processes": True,
            "third_party_process_host_required": False,
            "registration_kind": "systemd-user-separated",
        }

    def ephemeral_service_receipt(self) -> dict:
        return {
            "schema": "stegverse.sovereign-heartbeat-service/v3",
            "registration_kind": "stegverse-ephemeral-console",
            "active": True,
            "carrier_active": True,
            "worker_active": True,
            "separate_carrier_and_worker_processes": True,
            "stegverse_process_supervision": True,
            "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
            "third_party_process_host_required": False,
            "heartbeat_grants_execution_authority": False,
        }

    def self_heal_receipt(self) -> dict:
        return {
            "schema": "stegverse.ephemeral-sovereign-process/v3",
            "active": True,
            "carrier_active": True,
            "worker_active": True,
            "worker_task_capable_cycle_observed": True,
            "separate_carrier_and_worker_processes": True,
            "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
            "third_party_process_host_required": False,
            "heartbeat_grants_execution_authority": False,
            "authority_effect": "NONE_SUPERVISION_ONLY",
        }

    def portable_checkout_receipt(self) -> dict:
        return {
            "schema": "stegverse.workercoordinator-portable-checkout-receipt/v1",
            "portable_authority_epoch": "WC-PORTABLE-IPHONE-20260902",
            "canonical_authority_owner": "StegVerse-Labs/.github WorkerCoordinator",
            "authority_domain": "INDEPENDENT_TASK_CONTROL",
            "task_id": "SHWP-SV002-ORG-RUNTIME-ACTIVATION-001",
            "worker_id": "sv002-org-runtime-activation-worker",
            "claim_id": "SHWP-SHWP-SV002-ORG-RUNTIME-ACTIVATION-001-G25",
            "fencing_token": 25,
            "predecessor_generation": 24,
            "execution_surface": "CURRENT_USER_IPHONE",
            "heartbeat_reference": 123,
            "heartbeat_granted_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "global_workercoordinator_authority": True,
            "stegos_device_task_authority": False,
            "external_non_stegverse_machine_required": False,
            "parallel_workercoordinator_claim_issuance_allowed": False,
            "governed_transfer_required_before_other_surface_claims": True,
            "authority_effect": "CANONICAL_WORKERCOORDINATOR_CLAIM_FENCE",
            "receipt_sha256": "sha256:" + ("a" * 64),
        }

    def fresh_worker(self) -> dict:
        return {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 9,
            "last_cycle_at": "2026-09-04T12:00:00Z",
            "last_observed_carrier_epoch": 42,
            "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
        }

    def test_missing_runtime_evidence_remains_unobserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = project(Path(tmp), {"request": "receipts/request.json"})
            self.assertFalse(result["resident"]["runtime_alive_observed"])
            self.assertFalse(result["resident"]["present_worker_runtime_observed"])
            self.assertFalse(result["resident"]["task_control_runtime_observed"])
            self.assertFalse(result["portable_workercoordinator"]["observed"])
            self.assertFalse(result["governed_progress"]["request_observed"])
            self.assertFalse(result["heartbeat_reference"]["freshness_correlated"])
            self.assertFalse(result["governed_progress"]["runtime_signal_is_execution_receipt"])

    def test_runtime_presence_accepts_canonical_service_activation_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "control/heartbeat-carrier-runtime-state.json", {
                "schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 42, "generation": 42
            })
            self.write(root, "control/worker-runtime-state.json", self.fresh_worker())
            self.write(root, "receipts/sovereign-host/activation.latest.json", self.canonical_service_receipt())
            result = project(root, observed_at=datetime(2026, 9, 4, 12, 0, 10, tzinfo=timezone.utc))
            self.assertTrue(result["resident"]["runtime_alive_observed"])
            self.assertTrue(result["resident"]["task_capable_worker_observed"])
            self.assertTrue(result["resident"]["present_worker_runtime_observed"])
            self.assertTrue(result["resident"]["task_control_runtime_observed"])
            self.assertTrue(result["resident"]["worker_cycle_fresh"])
            self.assertTrue(result["heartbeat_reference"]["freshness_correlated"])
            self.assertEqual(result["resident"]["runtime_evidence_kind"], "CANONICAL_SERVICE_RECEIPT")

    def test_portable_checkout_proves_task_control_surface_without_native_process_presence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "receipts/device/sv002-portable-checkout.json"
            self.write(root, rel, self.portable_checkout_receipt())
            result = project(root, {"portable_checkout": rel})
            self.assertFalse(result["resident"]["runtime_alive_observed"])
            self.assertFalse(result["resident"]["present_worker_runtime_observed"])
            self.assertTrue(result["resident"]["task_control_runtime_observed"])
            self.assertFalse(result["resident"]["native_process_presence_is_universal_runtime_requirement"])
            self.assertTrue(result["portable_workercoordinator"]["observed"])
            self.assertEqual(result["portable_workercoordinator"]["task_id"], "SHWP-SV002-ORG-RUNTIME-ACTIVATION-001")
            self.assertEqual(result["portable_workercoordinator"]["fencing_token"], 25)
            self.assertFalse(result["portable_workercoordinator"]["proves_task_execution"])
            self.assertFalse(result["governed_progress"]["portable_checkout_is_execution_receipt"])
            self.assertFalse(result["heartbeat_reference"]["continuous_process_required_for_progression"])
            self.assertEqual(result["heartbeat_reference"]["progression_dependency"], "OSCILLATOR_ONLY")

    def test_invalid_portable_checkout_cannot_prove_task_control_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "receipts/device/sv002-portable-checkout.json"
            receipt = self.portable_checkout_receipt()
            receipt["global_workercoordinator_authority"] = False
            self.write(root, rel, receipt)
            result = project(root, {"portable_checkout": rel})
            self.assertFalse(result["portable_workercoordinator"]["observed"])
            self.assertFalse(result["resident"]["task_control_runtime_observed"])

    def test_static_portable_package_is_not_portable_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "control/portable-workercoordinator-packages/example.json"
            self.write(root, rel, {
                "schema": "stegverse.workercoordinator-portable-checkout-package/v1",
                "execution_surface": "CURRENT_USER_IPHONE",
            })
            result = project(root, {"portable_checkout": rel})
            self.assertFalse(result["portable_workercoordinator"]["observed"])
            self.assertFalse(result["resident"]["task_control_runtime_observed"])

    def test_ephemeral_v13_service_receipt_can_prove_runtime_alive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "control/worker-runtime-state.json", self.fresh_worker())
            self.write(root, "receipts/sovereign-host/activation.latest.json", self.ephemeral_service_receipt())
            result = project(root, observed_at=datetime(2026, 9, 4, 12, 0, 10, tzinfo=timezone.utc))
            self.assertTrue(result["resident"]["runtime_alive_observed"])
            self.assertTrue(result["resident"]["present_worker_runtime_observed"])
            self.assertEqual(result["resident"]["runtime_evidence_kind"], "EPHEMERAL_CONSOLE_SERVICE_RECEIPT")

    def test_ephemeral_v12_service_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self.ephemeral_service_receipt()
            receipt["canonical_carrier_runtime"] = "heartbeat_runtime.engine_v12.HeartbeatRuntime"
            self.write(root, "control/worker-runtime-state.json", self.fresh_worker())
            self.write(root, "receipts/sovereign-host/activation.latest.json", receipt)
            result = project(root, observed_at=datetime(2026, 9, 4, 12, 0, 10, tzinfo=timezone.utc))
            self.assertFalse(result["resident"]["runtime_alive_observed"])
            self.assertFalse(result["resident"]["present_worker_runtime_observed"])
            self.assertEqual(result["resident"]["runtime_evidence_kind"], "EPHEMERAL_CONSOLE_SERVICE_RECEIPT")

    def test_predicate_activation_proof_remains_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "control/worker-runtime-state.json", self.fresh_worker())
            self.write(root, "receipts/sovereign-host/activation.latest.json", {
                "schema": "stegverse.sovereign-runtime-activation/v1",
                "predicates": {"native_service_active": True, "continuous_runtime_live": True},
                "node_id": "node-7",
            })
            result = project(root, observed_at=datetime(2026, 9, 4, 12, 0, 10, tzinfo=timezone.utc))
            self.assertTrue(result["resident"]["runtime_alive_observed"])
            self.assertEqual(result["resident"]["runtime_evidence_kind"], "PREDICATE_PROOF_COMPATIBILITY")
            self.assertEqual(result["resident"]["node_id"], "node-7")

    def test_self_heal_supervision_can_prove_runtime_alive_with_fresh_worker_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worker = self.fresh_worker()
            worker["runtime_tick"] = 12
            self.write(root, "control/worker-runtime-state.json", worker)
            self.write(root, "receipts/sovereign-host/ephemeral-process.latest.json", self.self_heal_receipt())
            result = project(root, observed_at=datetime(2026, 9, 4, 12, 0, 10, tzinfo=timezone.utc))
            self.assertTrue(result["resident"]["runtime_alive_observed"])
            self.assertTrue(result["resident"]["present_worker_runtime_observed"])
            self.assertEqual(result["resident"]["runtime_evidence_kind"], "CARRIER_SELF_HEAL_SUPERVISION_RECEIPT")
            self.assertTrue(result["resident"]["self_heal_supervision_evidence_observed"])

    def test_self_heal_receipt_with_legacy_carrier_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self.self_heal_receipt()
            receipt["canonical_carrier_runtime"] = "heartbeat_runtime.engine_v12.HeartbeatRuntime"
            self.write(root, "receipts/sovereign-host/ephemeral-process.latest.json", receipt)
            result = project(root)
            self.assertFalse(result["resident"]["runtime_alive_observed"])

    def test_stale_worker_state_cannot_prove_present_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worker = self.fresh_worker()
            worker["last_cycle_at"] = "2026-09-04T11:58:00Z"
            self.write(root, "control/worker-runtime-state.json", worker)
            self.write(root, "receipts/sovereign-host/activation.latest.json", self.canonical_service_receipt())
            result = project(
                root,
                observed_at=datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc),
                worker_freshness_window_seconds=60.0,
            )
            self.assertTrue(result["resident"]["runtime_alive_observed"])
            self.assertTrue(result["resident"]["task_capable_worker_observed"])
            self.assertFalse(result["resident"]["present_worker_runtime_observed"])
            self.assertFalse(result["resident"]["worker_cycle_fresh"])
            self.assertEqual(result["resident"]["worker_cycle_age_seconds"], 120.0)

    def test_partial_or_third_party_service_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self.canonical_service_receipt()
            receipt["third_party_process_host_required"] = True
            self.write(root, "receipts/sovereign-host/activation.latest.json", receipt)
            result = project(root)
            self.assertFalse(result["resident"]["runtime_alive_observed"])
            self.assertEqual(result["resident"]["runtime_evidence_kind"], "CANONICAL_SERVICE_RECEIPT")

    def test_receipt_presence_is_not_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "receipts/request.json", {"schema": "request/v1", "state": "REQUESTED"})
            self.write(root, "receipts/consumption.json", {"schema": "consume/v1", "state": "CONSUMED"})
            result = project(root, {
                "request": "receipts/request.json",
                "consumption": "receipts/consumption.json",
                "execution": "receipts/execution.json",
                "reconstruction": "receipts/reconstruction.json",
            })
            self.assertTrue(result["governed_progress"]["request_observed"])
            self.assertTrue(result["governed_progress"]["consumption_observed"])
            self.assertFalse(result["governed_progress"]["execution_observed"])
            self.assertFalse(result["governed_progress"]["reconstruction_observed"])


if __name__ == "__main__":
    unittest.main()
