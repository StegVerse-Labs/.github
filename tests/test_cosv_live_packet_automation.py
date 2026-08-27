from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS
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

    def fixture(self, root: Path) -> None:
        self.write(root, "control/heartbeat-protocol-anchor.json", {
            "schema": "stegverse.heartbeat-protocol-anchor/v1",
            "protocol": "STEGVERSE_HEARTBEAT",
            "authority_scope": "REFERENCE_DERIVATION_ONLY",
            "anchor_epoch": 32,
            "anchor_time_utc": "2026-08-23T19:00:00.000Z",
            "anchor_unix_ns": PROTOCOL_ANCHOR_UNIX_NS,
            "period_ns": 10_000_000,
            "period_ms": 10,
            "reference_frequency_hz": 100,
            "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
            "progression_dependency": "OSCILLATOR_ONLY",
            "continuous_process_required": False,
            "resident_sampler_required_for_progression": False,
            "observation_is_causal": False,
            "worker_task_state_is_causal": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_REFERENCE_ONLY",
        })
        self.write(root, "control/heartbeat-live-status.json", {
            "schema": "stegverse.heartbeat-live-status/v2",
            "state": "ACTIVE_PROTOCOL_VERIFIED",
            "working": True,
            "protocol_anchor_ref": "control/heartbeat-protocol-anchor.json",
            "progression_dependency": "OSCILLATOR_ONLY",
            "worker_runtime_required_for_progression": False,
            "resident_sampler_required_for_progression": False,
            "github_runtime_dependency": False,
            "third_party_runtime_required": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_STATUS_ONLY",
        })
        # Immutable pre-anchor observation evidence. It intentionally does not advance
        # to match the post-anchor protocol reference.
        self.write(root, "control/heartbeat-carrier-runtime-state.json", {
            "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
            "epoch": 31,
            "generation": 31,
            "last_cycle_at": "2026-08-18T19:47:00Z",
            "activation_state": "ACTIVE",
            "authority_effect": "NONE",
        })
        self.write(root, "control/worker-runtime-state.json", {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 2,
            "last_observed_carrier_epoch": 31,
            "last_observed_carrier_generation": 31,
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
            "generation": 21,
            "tasks": [
                {
                    "task_id": "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28",
                    "state": "COMPLETED",
                    "claim_id": None,
                    "worker_id": None,
                    "evidence_refs": ["receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json"],
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
        self.write(root, "control/task-vectors/SHWP-DURABLE-RUNTIME-ACTIVATION.json", {
            "identity": "StegVerse-Labs/.github:task:SHWP-DURABLE-RUNTIME-ACTIVATION",
            "profile": "task.v1",
            "level": "task",
            "vector": "60000000101000",
            "evidence_refs": ["handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json"],
            "observed_at": "2026-08-27T07:03:00-05:00",
            "exact_metrics": {"blocker_count": 1},
        })
        baseline = build_full("heartbeat_epoch:31", self.base_records(), "2026-08-18T19:47:00Z")
        self.write(root, "receipts/cosv/live/HB31.json", baseline)

    def test_materializes_first_post_anchor_delta_from_protocol_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            result = materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS)
            self.assertEqual(result["state"], "PACKET_MATERIALIZED")
            self.assertEqual(result["mode"], "DELTA")
            self.assertEqual(result["carrier_ref"], "heartbeat_epoch:32")
            self.assertEqual(result["heartbeat_id"], "HB-0000000W")
            self.assertEqual(result["reference_source"], "CANONICAL_PROTOCOL_DERIVATION")
            packet = json.loads((root / "receipts/cosv/live/HB32.json").read_text())
            cache = json.loads((root / "receipts/cosv/live/latest-state.json").read_text())
            baseline = json.loads((root / "receipts/cosv/live/HB31.json").read_text())
            self.assertTrue(verify(packet, baseline["records"]))
            self.assertEqual(packet["previous_packet_sha256"], baseline["packet_sha256"])
            self.assertGreaterEqual(len(packet["gradient_inputs"]), 4)
            self.assertEqual(cache["packet_sha256"], packet["packet_sha256"])
            self.assertEqual(packet["authority"]["credential_authority"], "TV/TVC")
            self.assertFalse(packet["authority"]["non_tv_tvc_secret_or_token_used"])

    def test_protocol_reference_does_not_require_worker_observation_to_catch_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            result = materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS + 100_000_000)
            self.assertEqual(result["carrier_ref"], "heartbeat_epoch:42")
            packet = json.loads((root / "receipts/cosv/live/HB42.json").read_text())
            heartbeat = next(
                row for row in packet["records"]
                if row["identity"] == "task:HEARTBEAT-WORKER-REFERENCE-OBSERVATION"
            )
            self.assertEqual(heartbeat["exact_metrics"]["protocol_reference_epoch"], 42)
            self.assertEqual(heartbeat["exact_metrics"]["worker_last_observed_carrier_epoch"], 31)
            self.assertFalse(heartbeat["exact_metrics"]["worker_runtime_required_for_reference"])

    def test_same_protocol_reference_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            first = materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS)
            second = materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS)
            self.assertEqual(first["state"], "PACKET_MATERIALIZED")
            self.assertEqual(second["state"], "NO_NEW_REFERENCE")
            self.assertEqual(second["carrier_ref"], "heartbeat_epoch:32")

    def test_next_protocol_reference_can_follow_delta_using_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS)
            result = materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS + 10_000_000)
            self.assertEqual(result["carrier_ref"], "heartbeat_epoch:33")
            self.assertEqual(result["mode"], "DELTA")
            self.assertTrue((root / "receipts/cosv/live/HB33.json").is_file())

    def test_g18_record_uses_current_canonical_blocked_vector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS)
            packet = json.loads((root / "receipts/cosv/live/HB32.json").read_text())
            g18 = next(row for row in packet["records"] if row["identity"] == "task:SHWP-DURABLE-RUNTIME-ACTIVATION")
            self.assertEqual(g18["vector"], "60000000101000")
            self.assertEqual(g18["exact_metrics"]["blocker_count"], 1)
            self.assertFalse(g18["exact_metrics"]["heartbeat_progression_dependency"])

    def test_inactive_protocol_status_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            status_path = root / "control" / "heartbeat-live-status.json"
            status = json.loads(status_path.read_text())
            status["state"] = "NOT_VERIFIED"
            self.write(root, "control/heartbeat-live-status.json", status)
            with self.assertRaisesRegex(RuntimeError, "not verified active"):
                materialize(root, now_ns=PROTOCOL_ANCHOR_UNIX_NS)


if __name__ == "__main__":
    unittest.main()
