from __future__ import annotations

import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refresh_mod = load_script("refresh_heartbeat_transition_receipt", ROOT / "scripts" / "refresh_heartbeat_transition_receipt.py")
worker_mod = load_script("run_worker_runtime_integrity", ROOT / "scripts" / "run_worker_runtime.py")
iphone_mod = load_script("verify_iphone_transition_integrity", ROOT / "scripts" / "verify_iphone_heartbeat_transition_receipt.py")


class TransitionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        for rel in (
            "control/heartbeat-state.json",
            "control/heartbeat-carrier-runtime-state.json",
            "control/worker-runtime-state.json",
            "control/worker-control-plane-coordination.json",
            "receipts/heartbeat-schema-cutover/HB29.json",
            "receipts/heartbeat-transition-continuity/latest.json",
        ):
            src = ROOT / rel
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        self.install_oscillator_carrier()

    def tearDown(self):
        self.tempdir.cleanup()

    def read(self, rel: str) -> dict:
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def write(self, rel: str, value: dict) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def install_oscillator_carrier(self) -> None:
        carrier = self.read("control/heartbeat-carrier-runtime-state.json")
        carrier["frequency_rule"] = "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
        carrier["oscillator"] = {
            "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
            "period_ns": 10_000_000,
            "phase_travel_time_ms": 10,
            "reference_increment_interval_ms": 10,
            "reference_frequency_hz": 100,
            "anchor_epoch": 30,
            "anchor_unix_ns": 1_000_000_000,
            "progression_dependency": "OSCILLATOR_ONLY",
            "downstream_gating": False,
            "observation_is_causal": False,
            "sampled_unix_ns": 1_010_000_000,
            "sampled_reference_epoch": carrier["epoch"],
            "phase_offset_ns": 0,
            "elapsed_quanta_from_anchor": max(0, int(carrier["epoch"]) - 30),
            "snapshot_is_observation_only": True,
        }
        self.write("control/heartbeat-carrier-runtime-state.json", carrier)

    def test_oscillator_observation_releases_without_worker_predicates(self):
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["all_carrier_transition_predicates_pass"], result)
        self.assertTrue(result["all_release_predicates_pass"], result)
        self.assertEqual(result["release_state"], "OSCILLATOR_OBSERVATION_VERIFIED")
        self.assertEqual(result["continuity_model"], "OSCILLATOR_REFERENCE_CONTINUITY")
        self.assertEqual(result["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(result["worker_checkpoint_required"])
        self.assertFalse(result["worker_checkpoint_is_heartbeat_predicate"])
        self.assertNotIn("worker_runtime_checkpoint_observed_at_or_after_carrier_epoch", result["predicates"])
        self.assertNotIn("worker_control_plane_observed", result["predicates"])
        self.assertFalse(result["predicates"]["worker_or_task_state_gates_progression"])
        self.assertFalse(result["downstream_runtime_observation"]["causal_to_heartbeat"])
        self.assertNotIn("runtime_goal_release_state", result)
        self.assertNotIn("all_runtime_goal_predicates_pass", result)

    def test_worker_mode_change_cannot_change_heartbeat_release(self):
        before = refresh_mod.refresh(self.root)
        worker = self.read("control/worker-runtime-state.json")
        worker["observation_mode"] = "TASK_CAPABLE_WORKER_COORDINATOR"
        self.write("control/worker-runtime-state.json", worker)
        after = refresh_mod.refresh(self.root)
        self.assertEqual(after["release_state"], before["release_state"])
        self.assertEqual(after["all_release_predicates_pass"], before["all_release_predicates_pass"])
        self.assertEqual(after["predicates"], before["predicates"])
        self.assertEqual(after["downstream_runtime_observation"]["worker_observation_mode"], "TASK_CAPABLE_WORKER_COORDINATOR")
        self.assertFalse(after["downstream_runtime_observation"]["causal_to_heartbeat"])

    def test_historical_hb31_snapshot_is_pending_observation_not_heartbeat_block(self):
        carrier = self.read("control/heartbeat-carrier-runtime-state.json")
        carrier.pop("oscillator", None)
        carrier["frequency_rule"] = "GATE_PASSBAND_DERIVED"
        self.write("control/heartbeat-carrier-runtime-state.json", carrier)
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["predicates"]["historical_pre_correction_snapshot_only"])
        self.assertFalse(result["predicates"]["oscillator_period_exactly_10ms"])
        self.assertFalse(result["predicates"]["carrier_reference_derived_from_oscillator"])
        self.assertFalse(result["all_release_predicates_pass"])
        self.assertEqual(result["release_state"], "OSCILLATOR_LIVE_OBSERVATION_PENDING")
        self.assertEqual(result["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")

    def test_legacy_content_change_breaks_integrity_without_worker_semantics(self):
        legacy = self.read("control/heartbeat-state.json")
        legacy["last_cycle_at"] = "2099-01-01T00:00:00Z"
        self.write("control/heartbeat-state.json", legacy)
        result = refresh_mod.refresh(self.root)
        self.assertFalse(result["predicates"]["legacy_hb29_unchanged"])
        self.assertFalse(result["predicates"]["state_reconstruction_pass"])
        self.assertFalse(result["all_carrier_transition_predicates_pass"])
        self.assertFalse(result["all_release_predicates_pass"])
        self.assertNotIn("worker_control_plane_observed", result["predicates"])

    def test_control_plane_reference_change_is_downstream_only(self):
        before = refresh_mod.refresh(self.root)
        control = self.read("control/worker-control-plane-coordination.json")
        control["observed_reference"]["carrier_generation"] = 29
        control["observed_reference"]["reference_frame"] = "heartbeat_epoch:29"
        self.write("control/worker-control-plane-coordination.json", control)
        after = refresh_mod.refresh(self.root)
        self.assertEqual(after["release_state"], before["release_state"])
        self.assertEqual(after["all_release_predicates_pass"], before["all_release_predicates_pass"])
        self.assertEqual(after["predicates"], before["predicates"])
        self.assertFalse(after["downstream_runtime_observation"]["causal_to_heartbeat"])

    def test_cutover_hash_mismatch_fails_reconstruction(self):
        cutover = self.read("receipts/heartbeat-schema-cutover/HB29.json")
        cutover["legacy_state_sha256"] = "0" * 64
        self.write("receipts/heartbeat-schema-cutover/HB29.json", cutover)
        result = refresh_mod.refresh(self.root)
        self.assertFalse(result["predicates"]["state_reconstruction_pass"])
        self.assertFalse(result["all_carrier_transition_predicates_pass"])


class PortableFallbackTests(unittest.TestCase):
    def test_hosted_origin_is_detected_without_secret_material(self):
        env = {"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": "must-not-forward"}
        self.assertEqual(worker_mod._fallback_origin(env), "GITHUB_ACTIONS")
        safe = worker_mod._safe_bootstrap_env(env)
        self.assertEqual(safe.get("GITHUB_ACTIONS"), "true")
        self.assertNotIn("GITHUB_TOKEN", safe)

    def test_verifier_requires_explicit_matching_fallback(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaises(RuntimeError):
                iphone_mod._fallback_record(None)
            value = iphone_mod._fallback_record("GITHUB_ACTIONS")
            self.assertEqual(value["provider_role"], "FALLBACK_ONLY")
            self.assertFalse(value["required_dependency"])
            self.assertEqual(value["runtime_authority"], "StegVerse")

    def test_receipt_order_uses_executed_at_and_ignores_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / worker_mod.PORTABLE_RECEIPT_DIR_REL
            directory.mkdir(parents=True)
            (directory / "iphone-portable-bad.json").write_text("not-json", encoding="utf-8")
            (directory / "iphone-portable-old.json").write_text(json.dumps({"executed_at": "2026-08-18T18:00:00Z"}), encoding="utf-8")
            (directory / "iphone-portable-new.json").write_text(json.dumps({"executed_at": "2026-08-18T18:01:00Z"}), encoding="utf-8")
            names = [path.name for path in worker_mod._portable_receipts(root)]
            self.assertEqual(names, ["iphone-portable-new.json", "iphone-portable-old.json"])


if __name__ == "__main__":
    unittest.main()
