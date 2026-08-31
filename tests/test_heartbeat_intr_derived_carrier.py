from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import unittest

from heartbeat_runtime.intr_carrier_profile import derive_channel
from heartbeat_runtime.intr_derived_carrier import (
    DerivedCarrierError,
    derive_intr_carrier_signal,
    recover_intr_packet_bytes,
)
from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS

ROOT = Path(__file__).resolve().parents[1]


class HeartbeatIntrDerivedCarrierTests(unittest.TestCase):
    def sample(
        self,
        packet: bytes = b'{"schema":"example.intr/v1","payload":"hello"}',
        packet_id: str = "INTR-" + "2" * 24,
    ):
        return derive_intr_carrier_signal(
            packet_id=packet_id,
            payload_hash="sha256:" + "3" * 64,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 1234,
            packet_bytes=packet,
            intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
            boundary_from="EXTERNAL_SYSTEM",
            boundary_to="STEGOS_ECOSYSTEM",
            packet_receipt_hash="a" * 64,
        )

    def test_exact_packet_bytes_are_preserved(self):
        packet = b'{"schema":"example.intr/v1","payload":"hello"}'
        signal = self.sample(packet)
        self.assertEqual(recover_intr_packet_bytes(signal), packet)
        self.assertEqual(signal["intr"]["packet_sha256"], hashlib.sha256(packet).hexdigest())
        self.assertEqual(base64.b64decode(signal["intr"]["packet_base64"]), packet)
        self.assertFalse(signal["intr"]["packet_semantics_interpreted_by_heartbeat"])
        self.assertTrue(signal["intr"]["packet_governance_external_to_heartbeat"])

    def test_channel_matches_ingress_advertised_payload_hash_formula(self):
        packet_id = "INTR-" + "2" * 24
        signal = self.sample(packet_id=packet_id)
        expected = derive_channel(signal["intr"]["payload_hash"])
        self.assertEqual(signal["carrier"]["channel_id"], expected["channel_id"])
        self.assertEqual(signal["carrier"]["channel_slot"], expected["phase_slot"])
        self.assertEqual(signal["carrier"]["phase_slots"], 16)
        self.assertEqual(
            signal["carrier"]["channel_derivation"],
            "PAYLOAD_SHA256_FIRST64_MOD_16",
        )

    def test_exact_carrier_bytes_do_not_change_channel_when_payload_hash_identity_is_same(self):
        packet_id = "INTR-" + "4" * 24
        a = self.sample(b"packet-a", packet_id=packet_id)
        b = self.sample(b"packet-b", packet_id=packet_id)
        self.assertEqual(a["carrier"]["channel_id"], b["carrier"]["channel_id"])
        self.assertNotEqual(a["intr"]["packet_sha256"], b["intr"]["packet_sha256"])
        self.assertEqual(a["carrier"]["reference_rate_hz"], 100.0)
        self.assertEqual(b["carrier"]["reference_rate_hz"], 100.0)
        self.assertFalse(a["carrier"]["phase_plan_changes_reference_interval"])

    def test_binding_is_embedded_and_revalidated_on_recovery(self):
        signal = self.sample()
        binding = signal["carrier_binding"]
        self.assertEqual(
            signal["carrier"]["carrier_binding_sha256"],
            binding["binding_sha256"],
        )
        signal["carrier"]["channel_slot"] = (
            signal["carrier"]["channel_slot"] + 1
        ) % 16
        with self.assertRaisesRegex(
            DerivedCarrierError,
            "derived_carrier_channel_slot_mismatch",
        ):
            recover_intr_packet_bytes(signal)

    def test_binding_tamper_fails_closed(self):
        signal = self.sample()
        signal["carrier_binding"]["channel"]["phase_slot"] = (
            signal["carrier_binding"]["channel"]["phase_slot"] + 1
        ) % 16
        with self.assertRaisesRegex(
            DerivedCarrierError,
            "carrier_channel_derivation_mismatch",
        ):
            recover_intr_packet_bytes(signal)

    def test_zero_authority_contract(self):
        signal = self.sample()
        authority = signal["authority"]
        for key, value in authority.items():
            if key.endswith("_authority") and key != "credential_authority":
                self.assertFalse(value, key)
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertEqual(authority["authority_effect"], "NONE_CARRIER_ONLY")

    def test_invalid_receipt_hash_fails_closed(self):
        with self.assertRaises(DerivedCarrierError):
            derive_intr_carrier_signal(
                packet_id="INTR-" + "2" * 24,
                payload_hash="sha256:" + "3" * 64,
                sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 100,
                packet_bytes=b"x",
                intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
                boundary_from="A",
                boundary_to="B",
                packet_receipt_hash="bad",
            )

    def test_schema_binds_canonical_channel_and_zero_authority(self):
        schema = json.loads(
            (ROOT / "schemas/heartbeat-intr-derived-carrier.schema.json").read_text()
        )
        carrier = schema["properties"]["carrier"]["properties"]
        self.assertEqual(carrier["reference_rate_hz"]["const"], 100.0)
        self.assertEqual(carrier["reference_period_ms"]["const"], 10.0)
        self.assertEqual(carrier["progression_dependency"]["const"], "OSCILLATOR_ONLY")
        self.assertEqual(carrier["phase_slots"]["const"], 16)
        self.assertEqual(
            carrier["channel_derivation"]["const"],
            "PAYLOAD_SHA256_FIRST64_MOD_16",
        )
        authority = schema["properties"]["authority"]["properties"]
        self.assertFalse(authority["heartbeat_grants_execution_authority"]["const"])
        self.assertFalse(authority["derived_carrier_grants_routing_authority"]["const"])
        self.assertEqual(authority["credential_authority"]["const"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
