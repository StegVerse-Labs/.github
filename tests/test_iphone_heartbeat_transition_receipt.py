from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify_iphone_heartbeat_transition_receipt.py"
spec = importlib.util.spec_from_file_location("iphone_hb30", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class IPhoneHeartbeatTransitionReceiptTests(unittest.TestCase):
    def make_root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "management").mkdir(parents=True)
        (root / "control").mkdir(parents=True)
        legacy = {
            "schema": "stegverse.org-heartbeat-state/v1",
            "epoch": 29,
            "generation": 29,
            "issued": [],
            "received": [],
        }
        raw = (json.dumps(legacy, indent=2, sort_keys=True) + "\n").encode()
        (root / "control" / "heartbeat-state.json").write_bytes(raw)
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        contract = {
            "contract_id": "SHWP-IPHONE-HB30-TRANSITION-CAPSULE-001",
            "legacy_state_git_blob_sha": blob,
        }
        (root / "management" / "SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json").write_text(json.dumps(contract))
        return td, root, blob

    def receipt(self, blob):
        value = {
            "schema": "stegverse.iphone-heartbeat-transition-receipt/v1",
            "contract_id": "SHWP-IPHONE-HB30-TRANSITION-CAPSULE-001",
            "physical_execution_surface": "CURRENT_USER_IPHONE",
            "executed_at": "2026-08-17T14:50:00Z",
            "seed": {
                "repository": "StegVerse-Labs/.github",
                "legacy_state_ref": "control/heartbeat-state.json",
                "legacy_state_git_blob_sha": blob,
                "epoch": 29,
                "generation": 29,
            },
            "successor": {
                "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
                "epoch": 30,
                "generation": 30,
                "reference_frame": "heartbeat_epoch:30",
                "activation_state": "ACTIVE",
                "authority_effect": "NONE",
                "legacy_hb29_immutable": True,
            },
            "authority": {
                "credential_authority": "TV/TVC",
                "credential_requirement": "NONE",
                "github_token_runtime_authority": "NONE",
                "non_tv_tvc_secret_or_token_used": False,
                "worker_authority": False,
                "claim_or_fence_mutation": False,
                "route_authority": False,
                "wallet_authority": False,
                "model_output_authority": "NONE",
                "hosted_runtime_production_authority": "NONE",
                "another_physical_machine_required": False,
            },
            "browser": {
                "origin": "https://stegverse.org",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_6 like Mac OS X)",
                "platform": "iPhone",
                "max_touch_points": 5,
                "screen_width_css": 430,
                "screen_height_css": 932,
                "iphone_class_evidence": True,
                "secure_context": True,
                "webcrypto": True,
            },
        }
        value["receipt_sha256"] = hashlib.sha256(mod.canonical_bytes(value)).hexdigest()
        return value

    @staticmethod
    def resign(receipt):
        receipt["receipt_sha256"] = hashlib.sha256(mod.canonical_bytes({k: v for k, v in receipt.items() if k != "receipt_sha256"})).hexdigest()

    def test_valid_receipt_materializes_oscillator_only_hb30_without_mutating_legacy(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        before = (root / "control" / "heartbeat-state.json").read_bytes()
        verification = mod.validate_receipt(receipt, root=root)
        self.assertEqual(verification["state"], "PASS")
        self.assertTrue(verification["iphone_execution_evidence"])
        # This test exercises the sovereign/local path even when the test suite is
        # itself hosted. Hosted fallback behavior is tested separately below.
        with mock.patch.dict(mod.os.environ, {"GITHUB_ACTIONS": ""}, clear=False):
            result = mod.materialize(receipt, verification, root=root)
        self.assertEqual(result["state"], "CARRIER_TRANSITION_COMPLETE")
        carrier = json.loads((root / "control" / "heartbeat-carrier-runtime-state.json").read_text())
        self.assertEqual(carrier["epoch"], 30)
        self.assertEqual(carrier["generation"], 30)
        self.assertEqual(carrier["frequency_rule"], "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL")
        self.assertEqual(carrier["oscillator"]["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertEqual(carrier["oscillator"]["phase_travel_time_ms"], 10)
        self.assertEqual(carrier["oscillator"]["reference_frequency_hz"], 100)
        self.assertFalse(carrier["oscillator"]["downstream_gating"])
        self.assertFalse(carrier["oscillator"]["observation_is_causal"])
        self.assertTrue(carrier["oscillator"]["snapshot_is_observation_only"])
        self.assertEqual((root / "control" / "heartbeat-state.json").read_bytes(), before)
        self.assertTrue(result["all_carrier_transition_predicates_pass"])
        self.assertTrue(result["all_release_predicates_pass"])
        self.assertFalse(result["worker_checkpoint_required"])
        self.assertFalse(result["worker_checkpoint_is_heartbeat_predicate"])
        self.assertEqual(result["downstream_worker_runtime"], "SEPARATE_NON_HEARTBEAT_LANE")

    def test_reduced_desktop_user_agent_passes_with_bounded_iphone_class_evidence(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        receipt["browser"].update({
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/26.0 Safari/605.1.15",
            "platform": "MacIntel",
            "max_touch_points": 5,
            "screen_width_css": 430,
            "screen_height_css": 932,
            "iphone_class_evidence": True,
        })
        self.resign(receipt)
        verification = mod.validate_receipt(receipt, root=root)
        self.assertEqual(verification["state"], "PASS")
        self.assertTrue(verification["iphone_execution_evidence"])

    def test_reduced_user_agent_without_iphone_sized_touch_evidence_fails_closed(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        receipt["browser"].update({
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "platform": "MacIntel",
            "max_touch_points": 0,
            "screen_width_css": 1440,
            "screen_height_css": 900,
            "iphone_class_evidence": False,
        })
        self.resign(receipt)
        verification = mod.validate_receipt(receipt, root=root)
        self.assertEqual(verification["state"], "FAIL_CLOSED")
        self.assertTrue(any("iPhone-class" in error for error in verification["errors"]))

    def test_hosted_materialization_requires_explicit_fallback_marker(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        verification = mod.validate_receipt(receipt, root=root)
        self.assertEqual(verification["state"], "PASS")
        with mock.patch.dict(mod.os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "explicit --allow-third-party-fallback"):
                mod.materialize(receipt, verification, root=root)

    def test_explicit_hosted_fallback_remains_non_authoritative(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        verification = mod.validate_receipt(receipt, root=root)
        with mock.patch.dict(mod.os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            result = mod.materialize(receipt, verification, root=root, fallback_origin="GITHUB_ACTIONS")
        self.assertEqual(result["third_party_fallback"]["provider_role"], "FALLBACK_ONLY")
        self.assertEqual(result["third_party_fallback"]["runtime_authority"], "StegVerse")
        self.assertEqual(result["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")

    def test_wrong_seed_fails_closed(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        receipt["seed"]["epoch"] = 28
        self.resign(receipt)
        verification = mod.validate_receipt(receipt, root=root)
        self.assertEqual(verification["state"], "FAIL_CLOSED")
        self.assertTrue(any("seed.epoch" in error for error in verification["errors"]))

    def test_protected_material_fails_closed(self):
        td, root, blob = self.make_root()
        self.addCleanup(td.cleanup)
        receipt = self.receipt(blob)
        receipt["browser"]["authorization"] = "Bearer x"
        self.resign(receipt)
        verification = mod.validate_receipt(receipt, root=root)
        self.assertEqual(verification["state"], "FAIL_CLOSED")
        self.assertTrue(any("protected material" in error for error in verification["errors"]))


if __name__ == "__main__":
    unittest.main()