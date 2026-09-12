from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load():
    path = ROOT / "workers/erl_device_kv_terminal.py"
    spec = importlib.util.spec_from_file_location("erl_device_kv_terminal_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTransport:
    def __init__(self, mod):
        self.mod = mod

    def sha256_uri(self, value):
        return self.mod.sha_uri(value)

    def validate_transport_intent(self, intent):
        if intent.get("boundary_path") != self.mod.FULL_PATH:
            raise ValueError("path")

    def build_hop_receipt(self, intent, *, hop_index, receipt_id, boundary_identity_ref, recorded_at, prior_receipt_hash, transition_state):
        path = intent["boundary_path"]
        body = {
            "schema": "stegverse.intr.hop_receipt/v1",
            "receipt_id": receipt_id,
            "packet_id": intent["packet_id"],
            "hop_index": hop_index,
            "direction": "FORWARD",
            "from_role": path[hop_index - 1],
            "to_role": path[hop_index],
            "operation_hash": self.mod.sha_uri({"operation_id": intent["operation_id"], "packet_id": intent["packet_id"], "payload_hash": intent["payload_hash"]}),
            "payload_hash": intent["payload_hash"],
            "prior_receipt_hash": prior_receipt_hash,
            "boundary_identity_ref": boundary_identity_ref,
            "boundary_verification": "VERIFIED",
            "transition_state": transition_state,
            "secret_plaintext_present": False,
            "authority_transfer": False,
            "recorded_at": recorded_at,
        }
        return {**body, "receipt_hash": self.mod.sha_uri(body)}

    def validate_receipt_chain(self, intent, receipts):
        prior = None
        for index, receipt in enumerate(receipts, start=1):
            if receipt["packet_id"] != intent["packet_id"] or receipt["payload_hash"] != intent["payload_hash"] or receipt["hop_index"] != index:
                raise ValueError("identity")
            if receipt["prior_receipt_hash"] != prior:
                raise ValueError("lineage")
            prior = receipt["receipt_hash"]


def make_hop(mod, intent, index, prior):
    return FakeTransport(mod).build_hop_receipt(
        intent,
        hop_index=index,
        receipt_id=f"ERL-{index}",
        boundary_identity_ref=f"resident://{index}",
        recorded_at="2026-09-12T23:00:00Z",
        prior_receipt_hash=prior,
        transition_state="FORWARDED",
    )


class ERLDeviceKVTerminalIdentityTests(unittest.TestCase):
    def test_terminal_hop_preserves_original_identity_and_exact_bytes(self):
        mod = load()
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            envelope = {
                "schema": "stegverse.erl.active-research-acquisition-envelope/v1",
                "group_id": "ERL-RC-CYBER-SABOTAGE-LINEAGE-2026",
                "source_id": "ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET",
                "source_url": "https://www.cisa.gov/news-events/cybersecurity-advisories/aa25-176a",
                "required_storage_lane": "02_Research/ERL",
                "finding_authorized": False,
                "publication_authorized": False,
            }
            payload_hash = mod.sha_uri(envelope)
            intent = {
                "schema": "stegverse.universal-intr-transport/v1",
                "protocol": "InTr",
                "operation_id": "ERL-ACTIVE-RESEARCH-abc",
                "packet_id": "INTR-0123456789abcdef01234567",
                "payload_hash": payload_hash,
                "prior_transport_receipt_hash": None,
                "source": {"boundary": "EXTERNAL_SYSTEM", "subsystem": "ERL:ActiveResearchExternalSource"},
                "destination": {"boundary": "KV", "subsystem": "KnowledgeVault:ERL"},
                "boundary_path": mod.FULL_PATH,
                "interlock_required": True,
            }
            hop1 = make_hop(mod, intent, 1, None)
            hop2 = make_hop(mod, intent, 2, hop1["receipt_hash"])
            mid = "INTR-MAT-0123456789abcdef01234567"
            payload_path = runtime / "intr-payloads/erl-active-research/envelope.json"
            payload_path.parent.mkdir(parents=True)
            payload_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            profile_path = runtime / mod.PROFILE_DIR / f"{mid}.json"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(json.dumps({"hop_receipts": [hop1, hop2]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            request = {
                "materialization_id": mid,
                "transport_intent_hash": mod.sha_uri(intent),
                "operation_id": intent["operation_id"],
                "packet_id": intent["packet_id"],
                "payload_hash": intent["payload_hash"],
                "payload_ref": "runtime-local:intr-payloads/erl-active-research/envelope.json",
                "boundary_path": mod.TERMINAL_PATH,
                "prior_transport_receipt_hash": hop2["receipt_hash"],
                "erl_full_path": mod.FULL_PATH,
                "erl_upstream_receipt_hashes": [hop1["receipt_hash"], hop2["receipt_hash"]],
                "erl_transport_intent": intent,
            }
            ingress = {"operation_id": intent["operation_id"], "packet_id": intent["packet_id"], "payload_hash": intent["payload_hash"]}
            fake = FakeTransport(mod)
            with mock.patch.object(mod, "_load_transport", return_value=fake):
                result = mod.execute(runtime_root=runtime, stegos_root=runtime, request=request, ingress=ingress, boundary_identity_ref="kv-event://proof")
            receipt = result["terminal_receipt"]
            self.assertEqual(receipt["hop_index"], 3)
            self.assertEqual(receipt["from_role"], "DEVICE_SYSTEM")
            self.assertEqual(receipt["to_role"], "KV")
            self.assertEqual(receipt["packet_id"], intent["packet_id"])
            self.assertEqual(receipt["payload_hash"], intent["payload_hash"])
            self.assertEqual(receipt["prior_receipt_hash"], hop2["receipt_hash"])
            self.assertTrue(result["complete_three_hop_chain_verified"])
            self.assertTrue(result["exact_payload_bytes_transported"])
            self.assertTrue(result["durable_payload_readback_verified"])
            readback = runtime / result["kv_payload_readback_ref"]
            self.assertEqual(readback.read_bytes(), mod.canonical(envelope))
            self.assertEqual(result["kv_payload_readback_sha256"], payload_hash)
            self.assertFalse(result["provider_operation_attempted"])

    def test_rejects_reminted_terminal_packet(self):
        mod = load()
        request = {
            "erl_full_path": mod.FULL_PATH,
            "erl_transport_intent": {"packet_id": "INTR-original"},
            "erl_upstream_receipt_hashes": ["a", "b"],
        }
        self.assertTrue(mod.is_erl_terminal_request(request))


if __name__ == "__main__":
    unittest.main()
