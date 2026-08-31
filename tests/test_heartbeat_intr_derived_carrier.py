from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import unittest

from heartbeat_runtime.intr_derived_carrier import (
    DerivedCarrierError,
    derive_intr_carrier_signal,
    recover_intr_packet_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


class HeartbeatIntrDerivedCarrierTests(unittest.TestCase):
    def sample(self, packet: bytes = b'{"schema":"example.intr/v1","payload":"hello"}'):
        return derive_intr_carrier_signal(
            heartbeat_epoch=120,
            heartbeat_reference="HB-0000003C",
            phase_slots=4,
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

    def test_channel_and_phase_are_deterministic(self):
        a = self.sample()
        b = self.sample()
        self.assertEqual(a["signal_id"], b["signal_id"])
        self.assertEqual(a["carrier"]["channel_slot"], b["carrier"]["channel_slot"])
        self.assertEqual(a["carrier"]["phase_offset_deg"], b["carrier"]["phase_offset_deg"])
        self.assertLess(a["carrier"]["channel_slot"], a["carrier"]["phase_slots"])

    def test_different_packet_can_select_different_channel_without_changing_hb(self):
        a = self.sample(b"packet-a")
        b = self.sample(b"packet-b")
        self.assertEqual(a["carrier"]["heartbeat_epoch"], 120)
        self.assertEqual(b["carrier"]["heartbeat_epoch"], 120)
        self.assertEqual(a["carrier"]["reference_rate_hz"], 100.0)
        self.assertEqual(b["carrier"]["reference_rate_hz"], 100.0)
        self.assertFalse(a["carrier"]["phase_plan_changes_reference_interval"])
        self.assertFalse(b["carrier"]["phase_plan_changes_reference_interval"])

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
                heartbeat_epoch=1,
                heartbeat_reference="HB-00000001",
                phase_slots=1,
                packet_bytes=b"x",
                intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
                boundary_from="A",
                boundary_to="B",
                packet_receipt_hash="bad",
            )

    def test_schema_binds_oscillator_and_zero_authority(self):
        schema = json.loads((ROOT / "schemas/heartbeat-intr-derived-carrier.schema.json").read_text())
        carrier = schema["properties"]["carrier"]["properties"]
        self.assertEqual(carrier["reference_rate_hz"]["const"], 100.0)
        self.assertEqual(carrier["reference_period_ms"]["const"], 10.0)
        self.assertEqual(carrier["progression_dependency"]["const"], "OSCILLATOR_ONLY")
        authority = schema["properties"]["authority"]["properties"]
        self.assertFalse(authority["heartbeat_grants_execution_authority"]["const"])
        self.assertFalse(authority["derived_carrier_grants_routing_authority"]["const"])
        self.assertEqual(authority["credential_authority"]["const"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
