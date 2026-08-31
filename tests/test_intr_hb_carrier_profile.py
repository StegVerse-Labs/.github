from __future__ import annotations

import unittest

from heartbeat_runtime.intr_carrier_profile import (
    BINDING_SCHEMA,
    PROFILE_SCHEMA,
    build_carrier_binding,
    carrier_profile,
    derive_channel,
    derive_reference_from_unix_ms,
    validate_carrier_binding,
)
from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS
from workers import universal_intr_profiled_ingress as ingress


class HBDerivedInTrCarrierTests(unittest.TestCase):
    def test_reference_derives_from_hb32_anchor(self):
        anchor_ms = PROTOCOL_ANCHOR_UNIX_NS // 1_000_000
        ref = derive_reference_from_unix_ms(anchor_ms)
        self.assertEqual(ref["heartbeat_epoch"], 32)
        self.assertEqual(ref["heartbeat_id"], "HB-0000000W")
        self.assertEqual(ref["phase_offset_ms"], 0)
        later = derive_reference_from_unix_ms(anchor_ms + 27)
        self.assertEqual(later["heartbeat_epoch"], 34)
        self.assertEqual(later["phase_offset_ms"], 7)

    def test_channel_is_packet_deterministic(self):
        a = derive_channel("INTR-" + "2" * 24)
        b = derive_channel("INTR-" + "2" * 24)
        self.assertEqual(a, b)
        self.assertEqual(a["channel_family"], "H1_PHASE_SLOTS")
        self.assertGreaterEqual(a["phase_slot"], 0)
        self.assertLess(a["phase_slot"], 16)

    def test_binding_round_trip_and_authority_separation(self):
        sample_ms = PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 1234
        packet = "INTR-" + "2" * 24
        payload_hash = "sha256:" + "3" * 64
        binding = build_carrier_binding(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=sample_ms,
        )
        self.assertEqual(binding["schema"], BINDING_SCHEMA)
        validated = validate_carrier_binding(
            binding,
            packet_id=packet,
            payload_hash=payload_hash,
        )
        self.assertEqual(validated, binding)
        for key, value in binding.items():
            if key.startswith("carrier_grants_"):
                self.assertFalse(value)

    def test_binding_tamper_fails_closed(self):
        sample_ms = PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 1234
        packet = "INTR-" + "2" * 24
        payload_hash = "sha256:" + "3" * 64
        binding = build_carrier_binding(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=sample_ms,
        )
        binding["channel"]["phase_slot"] = (binding["channel"]["phase_slot"] + 1) % 16
        with self.assertRaisesRegex(ValueError, "carrier_channel_derivation_mismatch"):
            validate_carrier_binding(binding, packet_id=packet, payload_hash=payload_hash)

    def test_profile_advertises_carrier_without_authority(self):
        p = carrier_profile()
        self.assertEqual(p["schema"], PROFILE_SCHEMA)
        self.assertEqual(p["reference_frequency_hz"], 100)
        self.assertEqual(p["heartbeat_period_ms"], 10)
        self.assertEqual(p["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(p["carrier_binding_required"])
        self.assertTrue(p["legacy_unbound_packets_temporarily_accepted"])
        self.assertFalse(p["carrier_presence_grants_admission_authority"])
        self.assertFalse(p["carrier_presence_grants_execution_authority"])
        universal = ingress.profile(True)
        self.assertEqual(universal["heartbeat_derived_carrier"], p)

    def test_ingress_evidence_distinguishes_bound_and_legacy(self):
        packet = "INTR-" + "2" * 24
        payload_hash = "sha256:" + "3" * 64
        legacy = ingress.carrier_binding_evidence({
            "packet_id": packet,
            "payload_hash": payload_hash,
        })
        self.assertFalse(legacy["carrier_binding_present"])
        self.assertFalse(legacy["carrier_binding_validated"])

        binding = build_carrier_binding(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 100,
        )
        evidence = ingress.carrier_binding_evidence({
            "packet_id": packet,
            "payload_hash": payload_hash,
            "carrier_binding": binding,
        })
        self.assertTrue(evidence["carrier_binding_present"])
        self.assertTrue(evidence["carrier_binding_validated"])
        self.assertEqual(evidence["carrier_binding_sha256"], binding["binding_sha256"])
        self.assertFalse(evidence["carrier_binding_grants_authority"])


if __name__ == "__main__":
    unittest.main()
