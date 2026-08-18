import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cosv_state_packet as packet


class CosvStatePacketTests(unittest.TestCase):
    def setUp(self):
        self.base = [
            {"identity":"task:a","profile":"task.v1","level":"task","vector":"51000000110100","evidence_refs":["e:a"],"observed_at":"t0","exact_metrics":{}},
            {"identity":"subsystem:x","profile":"aggregate.v1","level":"subsystem","vector":"57665579810010","evidence_refs":["e:x"],"observed_at":"t0","exact_metrics":{"critical_blockers":1}},
        ]

    def test_full_packet_verifies(self):
        full = packet.build_full("HB29", self.base, "t0")
        self.assertTrue(packet.verify(full))
        self.assertEqual(full["authority"]["heartbeat_authority_effect"], "NONE")
        self.assertEqual(full["authority"]["credential_authority"], "TV/TVC")

    def test_delta_reconstructs_and_emits_gradient_input(self):
        full = packet.build_full("HB29", self.base, "t0")
        current = [dict(item) for item in self.base]
        current[0] = dict(current[0])
        current[0]["vector"] = "71000000100110"
        delta = packet.build_delta("HB30", full, current, "t1")
        self.assertTrue(packet.verify(delta, self.base))
        rebuilt = packet.reconstruct(delta, self.base)
        self.assertEqual(packet.state_root(rebuilt), packet.state_root(current))
        self.assertEqual(len(delta["gradient_inputs"]), 1)
        self.assertEqual(delta["gradient_inputs"][0]["authority_effect"], "NONE")

    def test_delta_rejects_implicit_removal(self):
        full = packet.build_full("HB29", self.base, "t0")
        with self.assertRaises(ValueError):
            packet.build_delta("HB30", full, self.base[:1], "t1")

    def test_digest_tamper_fails(self):
        full = packet.build_full("HB29", self.base, "t0")
        full["carrier_ref"] = "HB999"
        with self.assertRaises(ValueError):
            packet.verify(full)

    def test_non_tvc_authority_fails(self):
        full = packet.build_full("HB29", self.base, "t0")
        full["authority"]["credential_authority"] = "OTHER"
        copy = dict(full)
        copy.pop("packet_sha256", None)
        full["packet_sha256"] = packet.digest(copy)
        with self.assertRaises(ValueError):
            packet.verify(full)


if __name__ == "__main__":
    unittest.main()
