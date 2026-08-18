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

    def append_event(self, value: dict) -> None:
        path = self.root / "events" / "worker-runtime.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, sort_keys=True) + "\n")

    def test_observation_only_worker_releases_carrier_but_not_runtime_goal(self):
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["all_carrier_transition_predicates_pass"], result)
        self.assertTrue(result["all_release_predicates_pass"], result)
        self.assertEqual(result["release_state"], "RELEASE_COMPLETE")
        self.assertTrue(result["predicates"]["worker_runtime_checkpoint_observed_reference_when_worker_runs"], result)
        self.assertFalse(result["predicates"]["worker_task_capable_cycle_observed"], result)
        self.assertFalse(result["all_runtime_goal_predicates_pass"], result)
        self.assertEqual(result["runtime_goal_release_state"], "WORKER_TASK_CAPABLE_CYCLE_PENDING")

    def test_task_capable_worker_event_releases_runtime_goal(self):
        transition = self.read("receipts/heartbeat-transition-continuity/latest.json")
        target_epoch = int(transition["carrier_epoch_after"])
        self.append_event({
            "event_type": "worker_response_observed",
            "carrier_epoch": target_epoch,
            "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
            "authority_effect": False,
        })
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["predicates"]["worker_task_capable_cycle_observed"], result)
        self.assertTrue(result["all_runtime_goal_predicates_pass"], result)
        self.assertEqual(result["runtime_goal_release_state"], "RELEASE_COMPLETE")

    def test_observer_event_is_not_task_capable_evidence(self):
        transition = self.read("receipts/heartbeat-transition-continuity/latest.json")
        target_epoch = int(transition["carrier_epoch_after"])
        self.append_event({
            "event_type": "worker_carrier_reference_observed",
            "carrier_epoch": target_epoch,
            "task_adapters_invoked": 0,
            "authority_effect": False,
        })
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["all_release_predicates_pass"], result)
        self.assertFalse(result["predicates"]["worker_task_capable_cycle_observed"], result)
        self.assertEqual(result["runtime_goal_release_state"], "WORKER_TASK_CAPABLE_CYCLE_PENDING")

    def test_explicit_task_capable_runtime_marker_releases_runtime_goal(self):
        worker = self.read("control/worker-runtime-state.json")
        worker["observation_mode"] = "TASK_CAPABLE_WORKER_COORDINATOR"
        self.write("control/worker-runtime-state.json", worker)
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["predicates"]["worker_task_capable_cycle_observed"], result)
        self.assertTrue(result["all_runtime_goal_predicates_pass"], result)

    def test_missing_oscillator_binding_fails_carrier_release(self):
        carrier = self.read("control/heartbeat-carrier-runtime-state.json")
        carrier.pop("oscillator", None)
        carrier["frequency_rule"] = "GATE_PASSBAND_DERIVED"
        self.write("control/heartbeat-carrier-runtime-state.json", carrier)
        result = refresh_mod.refresh(self.root)
        self.assertFalse(result["predicates"]["oscillator_period_exactly_10ms"])
        self.assertFalse(result["predicates"]["carrier_reference_derived_from_oscillator"])
        self.assertFalse(result["all_release_predicates_pass"])
        self.assertEqual(result["release_state"], "FAIL_CLOSED_CARRIER_INTEGRITY")

    def test_legacy_content_change_fails_carrier_release(self):
        legacy = self.read("control/heartbeat-state.json")
        legacy["last_cycle_at"] = "2099-01-01T00:00:00Z"
        self.write("control/heartbeat-state.json", legacy)
        result = refresh_mod.refresh(self.root)
        self.assertFalse(result["predicates"]["legacy_hb29_unchanged"])
        self.assertFalse(result["predicates"]["state_reconstruction_pass"])
        self.assertEqual(result["release_state"], "FAIL_CLOSED_CARRIER_INTEGRITY")

    def test_stale_consumer_control_plane_does_not_gate_carrier(self):
        control = self.read("control/worker-control-plane-coordination.json")
        control["observed_reference"]["carrier_generation"] = 29
        control["observed_reference"]["reference_frame"] = "heartbeat_epoch:29"
        self.write("control/worker-control-plane-coordination.json", control)
        result = refresh_mod.refresh(self.root)
        self.assertTrue(result["all_release_predicates_pass"], result)
        self.assertTrue(result["predicates"]["worker_control_plane_observed_when_control_plane_runs"], result)
        self.assertFalse(result["all_runtime_goal_predicates_pass"], result)

    def test_cutover_hash_mismatch_fails_reconstruction(self):
        cutover = self.read("receipts/heartbeat-schema-cutover/HB29.json")
        cutover["legacy_state_sha256"] = "0" * 64
        self.write("receipts/heartbeat-schema-cutover/HB29.json", cutover)
        result = refresh_mod.refresh(self.root)
        self.assertFalse(result["predicates"]["state_reconstruction_pass"])
        self.assertFalse(result["all_carrier_transition_predicates_pass"])

    def test_duplicate_fence_blocks_runtime_goal_not_carrier_progression(self):
        control = self.read("control/worker-control-plane-coordination.json")
        leases = control["worker_coordination"]["active_leases"]
        duplicate = dict(leases[0])
        duplicate["task_id"] = "DUPLICATE-FENCE-TEST"
        duplicate["claim_id"] = "DUPLICATE-FENCE-TEST-CLAIM"
        duplicate["worker_instance_id"] = "duplicate-fence-test-instance"
        duplicate["fencing_token"] = leases[1]["fencing_token"]
        leases.append(duplicate)
        self.write("control/worker-control-plane-coordination.json", control)
        result = refresh_mod.refresh(self.root)
        self.assertFalse(result["predicates"]["no_duplicate_claim_or_fence"])
        self.assertTrue(result["all_release_predicates_pass"], result)
        self.assertFalse(result["all_runtime_goal_predicates_pass"], result)


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
