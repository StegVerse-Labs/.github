from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime.independent_oscillator import (
    FREQUENCY_RULE,
    OSCILLATOR_PERIOD_NS,
    derive_reference,
    normalize_oscillator,
    sample_state,
)

ROOT = Path(__file__).resolve().parents[1]


class IndependentHeartbeatOscillatorTests(unittest.TestCase):
    def base_state(self):
        return {
            "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
            "epoch": 31,
            "generation": 31,
            "last_cycle_at": "2026-08-18T19:47:00.000Z",
            "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
            "reference_frame": "heartbeat_epoch:31",
            "frequency_rule": "GATE_PASSBAND_DERIVED",
            "authority_effect": "NONE",
            "activation_state": "ACTIVE",
            "legacy_cutover": {
                "legacy_schema": "stegverse.org-heartbeat-state/v1",
                "legacy_epoch": 29,
                "legacy_generation": 29,
                "legacy_state_sha256": "0" * 64,
                "source_ref": "control/heartbeat-state.json",
                "closed": True,
            },
        }

    def test_observation_count_does_not_advance_heartbeat(self):
        anchor_ns = 1_000_000_000
        oscillator = {
            "period_ns": OSCILLATOR_PERIOD_NS,
            "anchor_epoch": 31,
            "anchor_unix_ns": anchor_ns,
        }
        first = derive_reference(oscillator, now_ns=anchor_ns + 5_000_000)
        second = derive_reference(oscillator, now_ns=anchor_ns + 5_000_000)
        self.assertEqual(first["epoch"], 31)
        self.assertEqual(second["epoch"], 31)

    def test_exact_10ms_advances_one_reference(self):
        anchor_ns = 2_000_000_000
        oscillator = {
            "period_ns": OSCILLATOR_PERIOD_NS,
            "anchor_epoch": 31,
            "anchor_unix_ns": anchor_ns,
        }
        observed = derive_reference(oscillator, now_ns=anchor_ns + 10_000_000)
        self.assertEqual(observed["epoch"], 32)
        self.assertEqual(observed["phase_offset_ns"], 0)

    def test_delayed_observer_skips_references_without_creating_them(self):
        anchor_ns = 3_000_000_000
        oscillator = {
            "period_ns": OSCILLATOR_PERIOD_NS,
            "anchor_epoch": 31,
            "anchor_unix_ns": anchor_ns,
        }
        observed = derive_reference(oscillator, now_ns=anchor_ns + 95_000_000)
        self.assertEqual(observed["epoch"], 40)
        self.assertEqual(observed["elapsed_quanta"], 9)
        self.assertEqual(observed["phase_offset_ns"], 5_000_000)

    def test_existing_sampling_driven_state_migrates_to_oscillator_anchor(self):
        state = self.base_state()
        sampled_at = 1_660_857_000_000_000_000
        state["last_cycle_at"] = "2022-08-18T19:50:00.000Z"
        oscillator = normalize_oscillator(state, now_ns=sampled_at)
        self.assertEqual(oscillator["anchor_epoch"], 31)
        self.assertEqual(oscillator["period_ns"], 10_000_000)
        self.assertEqual(oscillator["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(oscillator["downstream_gating"])
        self.assertFalse(oscillator["observation_is_causal"])

    def test_sample_state_marks_snapshot_as_observation_only(self):
        state = self.base_state()
        anchor_ns = 1_000_000_000
        state["last_cycle_at"] = "1970-01-01T00:00:01.000Z"
        sampled = sample_state(state, now_ns=anchor_ns + 20_000_000)
        self.assertEqual(sampled["epoch"], 33)
        self.assertEqual(sampled["frequency_rule"], FREQUENCY_RULE)
        self.assertEqual(sampled["oscillator"]["phase_travel_time_ms"], 10)
        self.assertTrue(sampled["oscillator"]["snapshot_is_observation_only"])
        self.assertFalse(sampled["oscillator"]["observation_is_causal"])

    def test_contract_forbids_downstream_gating(self):
        contract = json.loads((ROOT / "control" / "runtime-separation-contract.json").read_text(encoding="utf-8"))
        oscillator = contract["carrier_oscillator"]
        self.assertEqual(contract["schema"], "stegverse.heartbeat-runtime-separation-contract/v2")
        self.assertEqual(oscillator["phase_travel_time_ms"], 10)
        self.assertEqual(oscillator["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(oscillator["worker_or_task_gating"])
        self.assertFalse(oscillator["admission_gating"])
        self.assertFalse(oscillator["claim_or_fence_gating"])
        self.assertFalse(oscillator["route_or_credential_gating"])
        self.assertFalse(oscillator["observation_is_causal"])

    def test_runtime_state_schema_restricts_gate_rule_to_historical_hb31_or_earlier(self):
        schema = json.loads((ROOT / "schemas" / "heartbeat-carrier-runtime-state.schema.json").read_text(encoding="utf-8"))
        branches = schema["oneOf"]
        current = branches[0]
        historical = branches[1]
        self.assertIn("oscillator", current["required"])
        self.assertEqual(current["properties"]["frequency_rule"]["const"], FREQUENCY_RULE)
        self.assertEqual(historical["properties"]["frequency_rule"]["const"], "GATE_PASSBAND_DERIVED")
        self.assertEqual(historical["properties"]["epoch"]["maximum"], 31)
        self.assertEqual(historical["properties"]["generation"]["maximum"], 31)
        self.assertEqual(historical["not"]["required"], ["oscillator"])


if __name__ == "__main__":
    unittest.main()
