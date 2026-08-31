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
from scripts import serve_hil_intr_materialization_ingress as hil_ingress


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

    def test_channel_is_payload_deterministic(self):
        payload_hash = "sha256:" + "2" * 64
        a = derive_channel(payload_hash)
        b = derive_channel(payload_hash)
        self.assertEqual(a, b)
        self.assertEqual(a["channel_family"], "H1_PHASE_SLOTS")
        self.assertGreaterEqual(a["phase_slot"], 0)
        self.assertLess(a["phase_slot"], 16)

    def test_binding_channel_matches_exact_carrier_profile(self):
        raw = b"canonical exact carrier bytes"
        import hashlib
        payload_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
        packet = "INTR-" + "9" * 24
        binding = build_carrier_binding(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000,
        )
        from heartbeat_runtime.intr_derived_carrier import derive_intr_carrier_signal
        signal = derive_intr_carrier_signal(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000,
            packet_bytes=raw,
            intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
            boundary_from="DEVICE_SYSTEM",
            boundary_to="STEGOS_ECOSYSTEM",
            packet_receipt_hash="a" * 64,
        )
        self.assertEqual(binding["channel"]["phase_slot"], signal["carrier"]["channel_slot"])
        self.assertEqual(binding["channel"]["channel_id"], signal["carrier"]["channel_id"])

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
        self.assertEqual(p["channel_selection"], "PAYLOAD_SHA256_FIRST64_MOD_16")
        universal = ingress.profile(True)
        self.assertEqual(universal["heartbeat_derived_carrier"], p)

    def test_hil_ingress_uses_same_carrier_validator(self):
        packet = "INTR-" + "4" * 24
        payload_hash = "sha256:" + "5" * 64
        legacy = hil_ingress._carrier_binding_evidence({
            "packet_id": packet,
            "payload_hash": payload_hash,
        })
        self.assertFalse(legacy["carrier_binding_present"])
        binding = build_carrier_binding(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 200,
        )
        evidence = hil_ingress._carrier_binding_evidence({
            "packet_id": packet,
            "payload_hash": payload_hash,
            "carrier_binding": binding,
        })
        self.assertTrue(evidence["carrier_binding_present"])
        self.assertTrue(evidence["carrier_binding_validated"])
        self.assertFalse(evidence["carrier_binding_grants_authority"])

    def test_all_profile_admission_paths_record_carrier_evidence(self):
        root = __import__("pathlib").Path(__file__).resolve().parents[1]
        profiled = (root / "workers/universal_intr_profiled_ingress.py").read_text()
        hil = (root / "scripts/serve_hil_intr_materialization_ingress.py").read_text()
        self.assertGreaterEqual(profiled.count("carrier_binding_evidence(request)"), 4)
        self.assertIn("_carrier_binding_evidence(request)", hil)
        for marker in (
            "carrier_binding_present",
            "carrier_binding_validated",
            "carrier_binding_grants_authority",
        ):
            self.assertIn(marker, profiled)
            self.assertIn(marker, hil)

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
