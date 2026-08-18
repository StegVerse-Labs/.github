from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workers" / "independent_heartbeat_live_proof_worker.py"
spec = importlib.util.spec_from_file_location("heartbeat_live_proof_worker", SCRIPT)
worker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(worker)


class IndependentHeartbeatLiveProofWorkerTests(unittest.TestCase):
    def canonical_values(self):
        result = {
            "progression_dependency": "OSCILLATOR_ONLY",
            "oscillator_period_ms": 10,
            "observation_is_causal": False,
        }
        carrier = {
            "epoch": 42,
            "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
            "authority_effect": "NONE",
            "oscillator": {
                "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
                "period_ns": 10_000_000,
                "phase_travel_time_ms": 10,
                "reference_increment_interval_ms": 10,
                "reference_frequency_hz": 100,
                "progression_dependency": "OSCILLATOR_ONLY",
                "downstream_gating": False,
                "observation_is_causal": False,
                "snapshot_is_observation_only": True,
                "sampled_reference_epoch": 42,
            },
        }
        observation = {
            "carrier": {
                "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
                "phase_travel_time_ms": 10,
                "observation_is_causal": False,
                "authority_effect": "NONE",
            }
        }
        return result, carrier, observation

    def test_canonical_nested_oscillator_shape_passes(self) -> None:
        result, carrier, observation = self.canonical_values()
        worker.verify_live_proof(result, carrier, observation)

    def test_old_top_level_only_shape_is_rejected(self) -> None:
        result, carrier, observation = self.canonical_values()
        carrier["progression_dependency"] = "OSCILLATOR_ONLY"
        carrier["phase_travel_time_ms"] = 10
        carrier["snapshot_is_observation_only"] = True
        carrier.pop("oscillator")
        with self.assertRaises(AssertionError):
            worker.verify_live_proof(result, carrier, observation)

    def test_sample_epoch_must_bind_carrier_epoch(self) -> None:
        result, carrier, observation = self.canonical_values()
        carrier["oscillator"]["sampled_reference_epoch"] = 41
        with self.assertRaises(AssertionError):
            worker.verify_live_proof(result, carrier, observation)

    def test_downstream_gating_or_causality_is_rejected(self) -> None:
        result, carrier, observation = self.canonical_values()
        carrier["oscillator"]["downstream_gating"] = True
        with self.assertRaises(AssertionError):
            worker.verify_live_proof(result, carrier, observation)


if __name__ == "__main__":
    unittest.main()
