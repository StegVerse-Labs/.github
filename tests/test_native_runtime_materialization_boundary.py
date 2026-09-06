from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_heartbeat_service",
    ROOT / "scripts/install_sovereign_heartbeat_service.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class NativeRuntimeMaterializationBoundaryTests(unittest.TestCase):
    def test_mutable_runtime_directories_are_never_source_copy_inputs(self) -> None:
        self.assertEqual(
            set(mod.MUTABLE_RUNTIME_DIRS),
            {"receipts", "checkpoints", "events", "heartbeats"},
        )
        self.assertTrue(set(mod.MUTABLE_RUNTIME_DIRS).isdisjoint(set(mod.COPY_DIRS)))

    def test_fresh_materialization_contains_only_node_generated_receipt_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            receipt = mod.materialize(ROOT, runtime)

            self.assertFalse(receipt["source_mutable_runtime_state_copied"])
            self.assertEqual(
                set(receipt["mutable_runtime_dirs_excluded_from_source"]),
                {"receipts", "checkpoints", "events", "heartbeats"},
            )
            self.assertFalse((runtime / "checkpoints").exists())
            self.assertFalse((runtime / "events").exists())
            self.assertFalse((runtime / "heartbeats").exists())

            receipt_files = sorted(
                path.relative_to(runtime).as_posix()
                for path in (runtime / "receipts").rglob("*")
                if path.is_file()
            )
            self.assertEqual(
                receipt_files,
                ["receipts/sovereign-host/materialization.latest.json"],
            )

    def test_mutable_control_snapshots_are_not_source_bootstrap_inputs(self) -> None:
        self.assertEqual(
            set(mod.MUTABLE_CONTROL_FILES),
            {
                "heartbeat-carrier-runtime-state.json",
                "worker-runtime-state.json",
                "worker-control-plane-coordination.json",
                "worker-status.json",
            },
        )
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            receipt = mod.materialize(ROOT, runtime)
            self.assertFalse(receipt["source_mutable_control_state_copied"])
            self.assertEqual(
                set(receipt["mutable_control_files_excluded_from_source"]),
                set(mod.MUTABLE_CONTROL_FILES),
            )
            for name in mod.MUTABLE_CONTROL_FILES:
                self.assertFalse((runtime / "control" / name).exists())

    def test_rematerialization_preserves_existing_resident_control_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            control = runtime / "control"
            control.mkdir(parents=True)
            sentinel = control / "worker-runtime-state.json"
            sentinel.write_text('{"schema":"resident-sentinel"}\n', encoding="utf-8")
            mod.materialize(ROOT, runtime)
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"),
                '{"schema":"resident-sentinel"}\n',
            )

    def test_required_bootstrap_seeds_remain_materialized(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            mod.materialize(ROOT, runtime)
            self.assertTrue((runtime / "control/heartbeat-state.json").is_file())
            self.assertTrue((runtime / "control/worker-registry.json").is_file())
            self.assertTrue((runtime / "heartbeat_runtime/engine_v13.py").is_file())
            self.assertTrue((runtime / "scripts/dispatch_resident_execution_requests.py").is_file())
            self.assertTrue((runtime / "scripts/repair_resident_worker_presence.py").is_file())
            self.assertTrue((runtime / "state_language/reconcile.py").is_file())
            self.assertTrue((runtime / "management/COSV_HEARTBEAT_STATE_PACKET_CONTRACT.json").is_file())
            self.assertTrue((runtime / "scripts/materialize_live_cosv_packet.py").is_file())
            self.assertTrue((runtime / "scripts/cosv.py").is_file())
            self.assertTrue((runtime / "scripts/cosv_state_packet.py").is_file())
            self.assertTrue((runtime / "scripts/project_worker_control_plane_from_carrier.py").is_file())
            self.assertTrue((runtime / "scripts/verify_iphone_heartbeat_transition_receipt.py").is_file())

    def test_self_heal_dependency_is_copied_and_required_with_carrier_runner(self) -> None:
        self.assertIn("scripts/run_heartbeat_runtime.py", mod.COPY_FILES)
        self.assertIn("scripts/repair_resident_worker_presence.py", mod.COPY_FILES)
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            mod.materialize(ROOT, runtime)
            self.assertEqual(
                (runtime / "scripts/repair_resident_worker_presence.py").read_bytes(),
                (ROOT / "scripts/repair_resident_worker_presence.py").read_bytes(),
            )

    def test_native_materialization_covers_worker_source_refresh_static_dependencies(self) -> None:
        refresh_text = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        for rel in ("management", "state_language"):
            self.assertIn(f'Path("{rel}")', refresh_text)
            self.assertIn(rel, mod.COPY_DIRS)
        for rel in (
            "scripts/repair_resident_worker_presence.py",
            "scripts/materialize_live_cosv_packet.py",
            "scripts/cosv.py",
            "scripts/cosv_state_packet.py",
            "scripts/project_worker_control_plane_from_carrier.py",
            "scripts/verify_iphone_heartbeat_transition_receipt.py",
        ):
            self.assertIn(rel, mod.COPY_FILES)


if __name__ == "__main__":
    unittest.main()
