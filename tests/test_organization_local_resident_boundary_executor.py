from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from heartbeat_runtime.intr_carrier_profile import build_carrier_binding

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "workers/organization_local_resident_boundary_executor.py"


def load_module():
    spec = importlib.util.spec_from_file_location("org_boundary_worker", PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class OrganizationLocalResidentBoundaryExecutorTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()

    def packet(self):
        payload = {"operation":"OBSERVE_ONLY","value":"x"}
        payload_hash = self.m.sha256_uri(payload)
        return {
            "schema": self.m.PACKET_SCHEMA,
            "profile_id": self.m.PROFILE_ID,
            "direction": "INGRESS",
            "packet_id": "ORG-BOUNDARY-TEST-001",
            "payload": payload,
            "payload_hash": payload_hash,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "request_grants_execution_authority": False,
            "carrier_grants_execution_authority": False,
            "canonical_state_change_authorized": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }

    def test_valid_packet_without_carrier(self):
        packet_id, payload_hash, carrier = self.m.validate_packet(self.packet())
        self.assertEqual(packet_id, "ORG-BOUNDARY-TEST-001")
        self.assertEqual(payload_hash, self.packet()["payload_hash"])
        self.assertIsNone(carrier)

    def test_valid_packet_with_canonical_carrier(self):
        packet = self.packet()
        packet["carrier_binding"] = build_carrier_binding(
            packet_id=packet["packet_id"],
            payload_hash=packet["payload_hash"],
            sampled_unix_ms=1788368400000,
        )
        _, _, carrier = self.m.validate_packet(packet)
        self.assertEqual(carrier["authority_effect"], "NONE_CARRIER_ONLY")

    def test_profile_drift_fails_closed(self):
        packet = self.packet()
        packet["profile_id"] = "wrong"
        with self.assertRaisesRegex(ValueError, "profile_id"):
            self.m.validate_packet(packet)

    def test_request_authority_confusion_fails_closed(self):
        packet = self.packet()
        packet["request_grants_execution_authority"] = True
        with self.assertRaisesRegex(ValueError, "request_grants_execution_authority"):
            self.m.validate_packet(packet)

    def test_carrier_authority_confusion_fails_closed(self):
        packet = self.packet()
        packet["carrier_binding"] = build_carrier_binding(
            packet_id=packet["packet_id"],
            payload_hash=packet["payload_hash"],
            sampled_unix_ms=1788368400000,
        )
        packet["carrier_binding"]["carrier_grants_execution_authority"] = True
        with self.assertRaises(ValueError):
            self.m.validate_packet(packet)

    def test_forbidden_credential_field_fails_closed(self):
        packet = self.packet()
        packet["payload"]["access_token"] = "x"
        packet["payload_hash"] = self.m.sha256_uri(packet["payload"])
        with self.assertRaisesRegex(ValueError, "forbidden_field"):
            self.m.validate_packet(packet)

    def test_payload_hash_drift_fails_closed(self):
        packet = self.packet()
        packet["payload_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "payload_hash"):
            self.m.validate_packet(packet)

    def test_transition_basis_cannot_escalate(self):
        packet = self.packet()
        packet["transition_basis"] = {"authority_effect":"EXECUTE"}
        with self.assertRaisesRegex(ValueError, "transition_basis"):
            self.m.validate_packet(packet)

    def test_stale_fence_shape_is_rejected_by_main(self):
        invocation = {
            "schema":"stegverse.worker-invocation/v0.1",
            "heartbeat_epoch":50,
            "task":{"task_id":self.m.TASK_ID,"claim_id":"CLAIM-G3","heartbeat_timing":{"fencing_token":4}},
        }
        with mock.patch("sys.stdin", new=__import__("io").StringIO(json.dumps(invocation))):
            self.assertEqual(self.m.main(), 4)

    def test_receipt_and_egress_hashes_reconstruct_exactly(self):
        packet = self.packet()
        ingress_hash = self.m.sha256_uri(packet)
        egress_payload = {
            "disposition":"ACCEPTED_LOCAL_BOUNDARY",
            "ingress_packet_id":packet["packet_id"],
            "ingress_packet_sha256":ingress_hash,
            "payload_hash":packet["payload_hash"],
            "canonical_state_changed":False,
            "external_side_effect_performed":False,
        }
        egress = {
            "schema":self.m.PACKET_SCHEMA,
            "profile_id":self.m.PROFILE_ID,
            "direction":"EGRESS",
            "packet_id":packet["packet_id"],
            "payload":egress_payload,
            "payload_hash":self.m.sha256_uri(egress_payload),
            "credential_authority":"TV/TVC",
            "github_token_runtime_authority":"NONE",
            "request_grants_execution_authority":False,
            "carrier_grants_execution_authority":False,
            "canonical_state_change_authorized":False,
            "authority_effect":"NONE_EGRESS_ONLY",
        }
        self.assertEqual(self.m.sha256_uri(egress), self.m.sha256_uri(json.loads(json.dumps(egress))))


if __name__ == "__main__":
    unittest.main()
