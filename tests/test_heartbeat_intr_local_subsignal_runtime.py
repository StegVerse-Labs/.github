from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.engine_v12 import HeartbeatRuntime
from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_UNIX_NS
from heartbeat_runtime.intr_subsignal_runtime import (
    EVENT_LOG_REL,
    LocalDerivedCarrierError,
    default_heartbeat_runtime_root,
    persist_local_intr_subsignal,
    propagate_local_intr_subsignal,
    recover_local_intr_subsignal,
)


class HeartbeatIntrLocalSubsignalRuntimeTests(unittest.TestCase):
    def propagate(self, root: Path, packet: bytes = b'{"schema":"example.intr/v1","payload":"hello"}'):
        return propagate_local_intr_subsignal(
            root=root,
            packet_id="INTR-" + "5" * 24,
            payload_hash="sha256:" + "6" * 64,
            sampled_unix_ms=PROTOCOL_ANCHOR_UNIX_NS // 1_000_000 + 777,
            packet_bytes=packet,
            intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
            boundary_from="LOCAL_INTR_PRODUCER",
            boundary_to="LOCAL_INTR_OBSERVER",
            packet_receipt_hash="7" * 64,
        )

    def test_local_propagation_persists_and_recovers_exact_packet(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet = b'{"schema":"example.intr/v1","payload":"exact-bytes"}'
            result = self.propagate(root, packet)
            self.assertEqual(result["state"], "PROPAGATED_LOCAL")
            self.assertTrue(result["exact_packet_recovered"])
            signal_path = root / result["signal_ref"]
            self.assertTrue(signal_path.is_file())
            self.assertEqual(
                recover_local_intr_subsignal(root=root, signal_ref=result["signal_ref"]),
                packet,
            )
            events = (root / EVENT_LOG_REL).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 1)
            event = json.loads(events[0])
            self.assertEqual(event["event"], "HB_DERIVED_INTR_SUBSIGNAL_PROPAGATED_LOCAL")
            self.assertEqual(event["signal_sha256"], result["signal_sha256"])
            self.assertTrue(event["exact_packet_recovered"])
            self.assertFalse(event["worker_coordinator_invoked"])
            self.assertFalse(event["claim_or_fence_minted"])
            self.assertEqual(event["authority_effect"], "NONE_CARRIER_OBSERVATION_ONLY")

    def test_persist_existing_signal_preserves_exact_frame_identity(self):
        with tempfile.TemporaryDirectory() as td:
            source_root = Path(td) / "source"
            target_root = Path(td) / "target"
            first = self.propagate(source_root)
            signal = json.loads((source_root / first["signal_ref"]).read_text(encoding="utf-8"))
            persisted = persist_local_intr_subsignal(root=target_root, signal=signal)
            self.assertEqual(persisted["signal_sha256"], first["signal_sha256"])
            self.assertEqual(
                json.loads((target_root / persisted["signal_ref"]).read_text(encoding="utf-8")),
                signal,
            )
            self.assertEqual(
                recover_local_intr_subsignal(root=target_root, signal_ref=persisted["signal_ref"]),
                recover_local_intr_subsignal(root=source_root, signal_ref=first["signal_ref"]),
            )

    def test_default_runtime_root_matches_resident_execution_contract(self):
        explicit = default_heartbeat_runtime_root({"STEGVERSE_HEARTBEAT_ROOT": "/tmp/hb-root"})
        self.assertEqual(explicit, Path("/tmp/hb-root").resolve())
        derived = default_heartbeat_runtime_root({"XDG_STATE_HOME": "/tmp/state"})
        self.assertEqual(derived, Path("/tmp/state/stegverse/heartbeat-runtime").resolve())

    def test_identical_repropagation_is_idempotent_and_does_not_duplicate_event(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = self.propagate(root)
            second = self.propagate(root)
            self.assertEqual(first["signal_ref"], second["signal_ref"])
            self.assertEqual(first["signal_sha256"], second["signal_sha256"])
            self.assertEqual(second["state"], "ALREADY_PROPAGATED_IDENTICAL")
            events = (root / EVENT_LOG_REL).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 1)

    def test_write_once_collision_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = self.propagate(root)
            signal_path = root / first["signal_ref"]
            signal_path.write_text('{"tampered":true}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                LocalDerivedCarrierError,
                "derived_carrier_write_once_collision",
            ):
                self.propagate(root)

    def test_packet_tamper_is_rejected_on_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = self.propagate(root)
            signal_path = root / result["signal_ref"]
            signal = json.loads(signal_path.read_text(encoding="utf-8"))
            signal["intr"]["packet_base64"] = "eA=="
            signal_path.write_text(json.dumps(signal), encoding="utf-8")
            with self.assertRaisesRegex(
                LocalDerivedCarrierError,
                "derived_carrier_packet_hash_mismatch",
            ):
                recover_local_intr_subsignal(
                    root=root,
                    signal_ref=result["signal_ref"],
                )

    def test_current_heartbeat_runtime_observes_derived_signal_presence_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = self.propagate(root)
            runtime = HeartbeatRuntime.__new__(HeartbeatRuntime)
            runtime.root = root
            observed = runtime._derived_intr_signal_presence()
            self.assertIsNotNone(observed)
            self.assertEqual(observed["signal_count"], 1)
            self.assertEqual(observed["signals"][0]["signal_ref"], result["signal_ref"])
            self.assertEqual(
                observed["validation_role"],
                "PRESENCE_ONLY_PACKET_VALIDATION_EXTERNAL_TO_HEARTBEAT",
            )
            self.assertEqual(observed["authority_effect"], "NONE")

    def test_propagation_does_not_materialize_or_advance_heartbeat_runtime_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.propagate(root)
            self.assertFalse((root / "control/heartbeat-carrier-runtime-state.json").exists())
            self.assertFalse((root / "control/worker-runtime-state.json").exists())
            self.assertFalse((root / "control/worker-registry.json").exists())


if __name__ == "__main__":
    unittest.main()
