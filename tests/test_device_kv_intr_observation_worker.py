from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import device_kv_intr_observation_worker as worker


ROOT = Path(__file__).resolve().parents[1]


def invocation():
    handoff = json.loads((ROOT / "handoffs/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json").read_text())
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 44,
        "task": {
            "task_id": worker.TASK_ID,
            "claim_id": "claim-device-kv-44",
            "heartbeat_timing": {"fencing_token": 44},
        },
        "handoff": handoff,
    }


class DeviceKVInTrObservationWorkerTests(unittest.TestCase):
    def test_registration_is_independent_non_authorizing_successor(self):
        registry = json.loads((ROOT / "control/worker-registry.d/device-kv-intr-observation-001.json").read_text())
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/device-kv-intr-observation-001.json").read_text())
        handoff = json.loads((ROOT / "handoffs/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json").read_text())
        task = registry["tasks"][0]
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertEqual(task["admission"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertTrue(task["admission"]["fresh_fence_required"])
        self.assertFalse(task["admission"]["heartbeat_grants_execution_authority"])
        self.assertNotIn("parent_terminal_transition_required", task["admission"])
        self.assertEqual(task["admission"]["admitted_predecessor_rule"], "AUTHENTIC_RELAY_CONTINUITY_OR_VERIFIED_DEVICE_KV_EVENT_MATERIALIZATION")
        self.assertFalse(task["admission"]["event_materialization_grants_authority"])
        self.assertEqual(registry["credential_authority"], "TV/TVC")
        self.assertFalse(registry["github_token_required"])
        self.assertFalse(registry["non_tv_tvc_secret_or_token_required"])
        row = adapter["adapters"][0]
        self.assertEqual(row["adapter_ref"], "process:device-kv-intr-observation-v1")
        self.assertEqual(row["env_allowlist"], ["STEGVERSE_STEGOS_ROOT", "STEGVERSE_KV_SOURCE_ROOT", "STEGVERSE_DEVICE_KV_INTR_MATERIALIZATION_ID"])
        self.assertFalse(handoff["authority"]["physical_additional_machine_required"])
        self.assertFalse(handoff["authority"]["third_party_runtime_required"])
        self.assertFalse(handoff["activation"]["targeted_execution"]["g18_bootstrap_allowed"])

    def test_missing_parent_fails_closed_without_human_action(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parent = root / "receipts/stegos-sovereign-relay/parent.json"
            receipt = root / "receipts/device-kv-intr/result.json"
            with mock.patch.object(worker, "ROOT", root), \
                 mock.patch.object(worker, "PARENT_RECEIPT", parent), \
                 mock.patch.object(worker, "RECEIPT", receipt), \
                 mock.patch.object(sys, "stdin", io.StringIO(json.dumps(invocation()))), \
                 mock.patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(worker.main(), 0)
            result = json.loads(receipt.read_text())
            self.assertEqual(result["state"], "ACTIVE")
            self.assertEqual(result["transition_id"], "DEVICE_KV_ADMITTED_PREDECESSOR_REQUIRED")
            self.assertFalse(result["blocker"]["human_action_required"])
            self.assertFalse(result["blocker"]["physical_additional_machine_required"])
            self.assertFalse(result["blocker"]["third_party_runtime_required"])

    def test_canonical_connector_owns_transport_intents_and_receipts(self):
        source = (ROOT / "workers/device_kv_intr_observation_worker.py").read_text()
        self.assertIn('connector = load_canonical_device_kv_connector(stegos_root)', source)
        self.assertIn('connector.prepare(', source)
        self.assertIn('connector.accept_hop(', source)
        self.assertIn('connector.validate_complete(', source)
        self.assertIn('connector.prepare_response(', source)
        self.assertIn('connector.profile.profile_id', source)
        self.assertIn('"canonical_connector_profile"', source)
        self.assertIn('"compatibility_envelope_only": True', source)
        self.assertNotIn("def build_transport_receipt(", source)
        self.assertNotIn("def validate_transport_receipt(", source)


    def test_hb_carrier_binds_exact_precommitted_receipt_and_recovers_bytes(self):
        receipt = {
            "packet_id": "p-carrier",
            "payload_hash": "sha256:" + "2" * 64,
            "receipt_hash": "sha256:" + "3" * 64,
        }
        payload = b'{"request":"exact"}'
        now_ns = 1_787_511_600_000_000_000 + (250 * 10_000_000)
        signal, reference = worker.build_hb_carrier_signal(
            packet_id=receipt["packet_id"],
            payload_hash=receipt["payload_hash"],
            packet_bytes=payload,
            receipt_hash=receipt["receipt_hash"],
            boundary_from="DEVICE_SYSTEM",
            boundary_to="KV",
            now_ns=now_ns,
        )
        self.assertEqual(reference["epoch"], 282)
        self.assertEqual(signal["intr"]["packet_receipt_hash"], receipt["receipt_hash"][7:])
        self.assertEqual(worker.recover_intr_packet_bytes(signal), payload)
        self.assertEqual(signal["carrier"]["reference_rate_hz"], 100.0)
        self.assertEqual(signal["carrier"]["phase_slots"], 16)
        self.assertEqual(signal["carrier"]["channel_derivation"], "PAYLOAD_SHA256_FIRST64_MOD_16")
        self.assertEqual(signal["carrier"]["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(signal["authority"]["derived_carrier_grants_receiving_authority"])
        self.assertEqual(signal["authority"]["authority_effect"], "NONE_CARRIER_ONLY")

    def test_worker_transports_request_and_response_as_hb_carrier_frames(self):
        source = (ROOT / "workers/device_kv_intr_observation_worker.py").read_text()
        self.assertIn("send_frame(client, request_carrier_wire)", source)
        self.assertIn("recovered = recover_intr_packet_bytes(received_signal)", source)
        self.assertIn("send_frame(self.request, response_carrier_wire)", source)
        self.assertIn("response_wire = recover_intr_packet_bytes(response_carrier_signal)", source)
        self.assertIn("persist_local_intr_subsignal(", source)
        self.assertIn('"request_shared_hb_signal_ref"', source)
        self.assertIn('"response_shared_hb_signal_ref"', source)
        self.assertIn('"hb_derived_carrier_transport_observed": True', source)


    def test_controlled_request_contains_no_personal_record_scope(self):
        handoff = json.loads((ROOT / "handoffs/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json").read_text())
        controlled = handoff["execution"]["controlled_operation"]
        self.assertEqual(controlled["operation"], "DISCOVER")
        self.assertEqual(controlled["record_class"], "transport-capability-observation")
        self.assertEqual(controlled["requested_scope"], ["capability_status"])
        text = json.dumps(controlled).lower()
        for token in ("password", "private_key", "credential_value", "health", "financial", "biometric"):
            self.assertNotIn(token, text)

    def test_worker_captures_receipt_store_return_directly(self):
        source = (ROOT / "workers/device_kv_intr_observation_worker.py").read_text()
        self.assertIn('endpoint_ref_box["ref"] = ref', source)
        self.assertIn('endpoint_ref = endpoint_ref_box.get("ref")', source)
        self.assertIn('"endpoint_receipt_ref": endpoint_ref', source)
        self.assertNotIn('.get("receipt", {}).get("receipt_ref")', source)


if __name__ == "__main__":
    unittest.main()
