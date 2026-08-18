from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.cosv_state_packet import build_full, verify
from scripts.materialize_live_cosv_packet import materialize


class COSVLivePacketAutomationTests(unittest.TestCase):
    def write(self, root: Path, rel: str, value: dict) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def base_records(self):
        return [
            {
                "identity": "task:HEARTBEAT-WORKER-REFERENCE-OBSERVATION",
                "profile": "task.v1",
                "level": "task",
                "vector": "70000000100111",
                "evidence_refs": ["control/worker-runtime-state.json"],
                "observed_at": "2026-08-18T19:47:00Z",
                "exact_metrics": {"carrier_epoch": 31, "runtime_tick": 2},
                "admissibility_ref": "docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md",
                "coherency_group_ref": "coherency:heartbeat-runtime",
            },
            {
                "identity": "task:SHWP-DURABLE-RUNTIME-ACTIVATION",
                "profile": "task.v1",
                "level": "task",
                "vector": "70000000100111",
                "evidence_refs": ["receipts/heartbeat-transition-continuity/latest.json"],
                "observed_at": "2026-08-18T19:47:00Z",
                "exact_metrics": {"carrier_epoch": 31, "release_predicates_pass": 7},
                "admissibility_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
                "coherency_group_ref": "coherency:heartbeat-runtime",
            },
        ]

    def fixture(self, root: Path, epoch: int = 32, worker_epoch: int = 32) -> None:
        self.write(root, "control/heartbeat-carrier-runtime-state.json", {
            "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
            "epoch": epoch,
            "generation": epoch,
            "last_cycle_at": "2026-08-18T20:14:00Z",
            "activation_state": "ACTIVE",
            "authority_effect": "NONE",
        })
        self.write(root, "control/worker-runtime-state.json", {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 3,
            "last_observed_carrier_epoch": worker_epoch,
            "last_observed_carrier_generation": worker_epoch,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
        })
        self.write(root, "receipts/heartbeat-transition-continuity/latest.json", {
            "state": "CARRIER_TRANSITION_COMPLETE",
            "release_state": "RELEASE_COMPLETE",
            "all_release_predicates_pass": True,
            "predicates": {
                "legacy_hb29_unchanged": True,
                "carrier_epoch_at_least_30": True,
                "carrier_generation_non_regressing": True,
                "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": True,
                "worker_control_plane_observed": True,
                "no_duplicate_claim_or_fence": True,
                "state_reconstruction_pass": True,
            },
        })
        self.write(root, "control/worker-registry.json", {
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 22,
            "tasks": [
                {
                    "task_id": "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28",
                    "state": "ACTIVE",
                    "claim_id": "SHWP-RECOVER-G23",
                    "worker_id": "ecosystem-chat-orphan-recovery-worker",
                    "evidence_refs": ["handoffs/generated/RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28.json"],
                },
                {
                    "task_id": "SHWP-ECOSYSTEM-CHAT-INFERENCE-001",
                    "state": "BLOCKED",
                    "claim_id": None,
                    "worker_id": None,
                    "evidence_refs": ["handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"],
                },
            ],
        })
        baseline = build_full("heartbeat_epoch:31", self.base_records(), "2026-08-18T19:47:00Z")
        self.write(root, "receipts/cosv/live/HB31.json", baseline)

    def test_materializes_delta_and_reconstructable_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            result = materialize(root)
            self.assertEqual(result["state"], "PACKET_MATERIALIZED")
            self.assertEqual(result["mode"], "DELTA")
            packet = json.loads((root / "receipts/cosv/live/HB32.json").read_text())
            cache = json.loads((root / "receipts/cosv/live/latest-state.json").read_text())
            baseline = json.loads((root / "receipts/cosv/live/HB31.json").read_text())
            self.assertTrue(verify(packet, baseline["records"]))
            self.assertEqual(packet["previous_packet_sha256"], baseline["packet_sha256"])
            self.assertGreaterEqual(len(packet["gradient_inputs"]), 3)
            self.assertEqual(cache["packet_sha256"], packet["packet_sha256"])
            self.assertEqual(cache["state_root_sha256"], packet["state_root_sha256"])
            self.assertEqual(packet["authority"]["credential_authority"], "TV/TVC")
            self.assertFalse(packet["authority"]["non_tv_tvc_secret_or_token_used"])

    def test_same_reference_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, epoch=31, worker_epoch=31)
            result = materialize(root)
            self.assertEqual(result["state"], "NO_NEW_REFERENCE")
            self.assertFalse((root / "receipts/cosv/live/latest-state.json").exists())

    def test_worker_reference_must_not_lag_carrier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, epoch=32, worker_epoch=31)
            with self.assertRaisesRegex(RuntimeError, "jointly admitted"):
                materialize(root)

    def test_delta_contains_precommitted_recovery_identity_actual_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            materialize(root)
            packet = json.loads((root / "receipts/cosv/live/HB32.json").read_text())
            identities = {row["identity"] for row in packet["records"]}
            self.assertIn("task:RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28", identities)
            gradient = {row["identity"]: row for row in packet["gradient_inputs"]}
            self.assertEqual(
                gradient["task:RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"]["transition_vector"],
                "9" * 14,
            )


if __name__ == "__main__":
    unittest.main()
