from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_sovereign_heartbeat_service",
    ROOT / "scripts" / "install_sovereign_heartbeat_service.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class SovereignHeartbeatServiceTests(unittest.TestCase):
    def test_materialization_is_network_independent_and_oscillator_separated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "heartbeat"
            receipt = mod.materialize(ROOT, target)
            self.assertFalse(receipt["network_fetch_required"])
            self.assertFalse(receipt["third_party_process_host_required"])
            self.assertFalse(receipt["third_party_deployment_required"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertFalse(receipt["github_runtime_dependency"])
            self.assertFalse(receipt["render_runtime_dependency"])
            self.assertFalse(receipt["cloudflare_runtime_dependency"])
            self.assertEqual(receipt["canonical_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(receipt["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(receipt["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
            self.assertEqual(receipt["carrier_producer_ref"], "heartbeat_runtime/oscillator_producer.py")
            self.assertEqual(receipt["heartbeat_production_mode"], "OSCILLATOR_PHASE_DRIVEN")
            self.assertEqual(receipt["heartbeat_period_ms"], 10.0)
            self.assertEqual(receipt["heartbeat_reference_frequency_hz"], 100.0)
            self.assertEqual(receipt["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertFalse(receipt["heartbeat_event_trigger_required"])
            self.assertFalse(receipt["heartbeat_interval_argument_controls_progression"])
            self.assertEqual(receipt["worker_default_interval_ms"], 10.0)
            self.assertEqual(receipt["nominal_carrier_references_per_second"], 100.0)
            self.assertEqual(receipt["nominal_worker_ticks_per_second"], 100.0)
            self.assertEqual(receipt["worker_lease_clock"], "WORKER_RUNTIME_INTERNAL_HB_UNIT")
            self.assertFalse(receipt["carrier_epoch_controls_worker_expiry"])
            self.assertFalse(receipt["carrier_presence_controls_worker_expiry"])
            self.assertFalse(receipt["wall_clock_worker_expiry_authority"])
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertEqual(receipt["credential_requirement"], "NONE")
            self.assertFalse(receipt["non_tv_tvc_secret_or_token_used"])
            self.assertTrue((target / "heartbeat_runtime" / "engine_v13.py").is_file())
            self.assertTrue((target / "heartbeat_runtime" / "oscillator_producer.py").is_file())
            self.assertTrue((target / "heartbeat_runtime" / "worker_runtime.py").is_file())
            self.assertTrue((target / "scripts" / "run_heartbeat_runtime.py").is_file())
            self.assertTrue((target / "scripts" / "run_worker_runtime.py").is_file())
            self.assertTrue((target / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json").is_file())
            written = json.loads((target / "receipts" / "sovereign-host" / "materialization.latest.json").read_text())
            self.assertEqual(written["canonical_runtime"], receipt["canonical_runtime"])
            self.assertEqual(written["carrier_producer_ref"], receipt["carrier_producer_ref"])
            self.assertTrue(written["initial_carrier_bootstrap_ready"])

    def test_linux_service_runs_carrier_and_worker_as_separate_native_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "heartbeat"
            mod.materialize(ROOT, root)
            receipt = mod.materialize_service(
                root,
                system="linux",
                env={"XDG_CONFIG_HOME": str(base / "config")},
            )
            carrier = Path(receipt["carrier_registration_path"]).read_text(encoding="utf-8")
            worker = Path(receipt["worker_registration_path"]).read_text(encoding="utf-8")
            self.assertEqual(receipt["registration_kind"], "systemd-user-separated")
            self.assertEqual(receipt["heartbeat_production_mode"], "OSCILLATOR_PHASE_DRIVEN")
            self.assertEqual(receipt["heartbeat_period_ms"], 10.0)
            self.assertEqual(receipt["heartbeat_reference_frequency_hz"], 100.0)
            self.assertFalse(receipt["heartbeat_interval_argument_controls_progression"])
            self.assertEqual(receipt["worker_interval_ms"], 10.0)
            self.assertTrue(receipt["native_process_supervision_only"])
            self.assertTrue(receipt["separate_carrier_and_worker_processes"])
            self.assertFalse(receipt["heartbeat_grants_execution_authority"])
            self.assertFalse(receipt["carrier_epoch_controls_worker_expiry"])
            self.assertIn("run_heartbeat_runtime.py", carrier)
            self.assertNotIn("run_worker_runtime.py", carrier)
            self.assertIn("--continuous", carrier)
            self.assertNotIn("--interval-ms", carrier)
            self.assertIn("run_worker_runtime.py", worker)
            self.assertNotIn("run_heartbeat_runtime.py", worker)
            self.assertIn("--continuous", worker)
            self.assertIn("--interval-ms", worker)
            self.assertIn("10.0", worker)
            for text in (carrier, worker):
                self.assertIn("Restart=always", text)
                self.assertNotIn("render", text.lower())
                self.assertNotIn("cloudflare", text.lower())
                self.assertNotIn("network-online.target", text.lower())


    def test_worker_service_receives_distinct_canonical_local_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "heartbeat"
            source = base / "canonical-source"
            source.mkdir()
            mod.materialize(ROOT, root)
            receipt = mod.materialize_service(
                root,
                system="linux",
                env={
                    "XDG_CONFIG_HOME": str(base / "config"),
                    "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source),
                },
            )
            carrier = Path(receipt["carrier_registration_path"]).read_text(encoding="utf-8")
            worker = Path(receipt["worker_registration_path"]).read_text(encoding="utf-8")
            self.assertTrue(receipt["native_local_source_refresh_configured"])
            self.assertEqual(receipt["canonical_local_source_root"], str(source.resolve()))
            self.assertNotIn("STEGVERSE_HEARTBEAT_SOURCE_ROOT", carrier)
            self.assertIn("STEGVERSE_HEARTBEAT_SOURCE_ROOT=" + str(source.resolve()), worker)

    def test_worker_service_rejects_source_root_equal_to_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "heartbeat"
            mod.materialize(ROOT, root)
            with self.assertRaisesRegex(RuntimeError, "distinct"):
                mod.materialize_service(
                    root,
                    system="linux",
                    env={
                        "XDG_CONFIG_HOME": str(base / "config"),
                        "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(root),
                    },
                )

    def test_carrier_command_has_no_configurable_cadence_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "heartbeat"
            command = mod._carrier_command(root)
            self.assertIn("run_heartbeat_runtime.py", " ".join(command))
            self.assertIn("--continuous", command)
            self.assertNotIn("--interval-ms", command)
            self.assertNotIn("5.0", command)

    def test_install_records_both_native_processes_without_carrier_authority(self) -> None:
        calls = []

        def runner(command, **_kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "heartbeat"
            receipt = mod.install(
                ROOT,
                target,
                runner=runner,
                system="linux",
                env={"XDG_CONFIG_HOME": str(base / "config")},
            )
            self.assertTrue(receipt["active"])
            self.assertTrue(receipt["carrier_active"])
            self.assertTrue(receipt["worker_active"])
            self.assertEqual(receipt["execution_authority_effect"], "NONE_FROM_CARRIER")
            self.assertEqual(receipt["canonical_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(receipt["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
            self.assertEqual(receipt["heartbeat_production_mode"], "OSCILLATOR_PHASE_DRIVEN")
            self.assertFalse(receipt["heartbeat_interval_argument_controls_progression"])
            self.assertTrue(receipt["initial_carrier_bootstrap_ready"])
            self.assertFalse(receipt["third_party_process_host_required"])
            self.assertFalse(receipt["third_party_deployment_required"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertFalse(receipt["render_production_runtime_used"])
            self.assertEqual(len(calls), 3)
            self.assertTrue((target / "heartbeat_runtime" / "oscillator_producer.py").is_file())
            self.assertTrue((target / "receipts" / "sovereign-host" / "activation.latest.json").is_file())

    def test_custom_worker_rate_does_not_change_carrier_frequency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "heartbeat"
            receipt = mod.materialize(ROOT, target, interval_ms=5.0)
            service = mod.materialize_service(
                target,
                interval_ms=5.0,
                system="linux",
                env={"XDG_CONFIG_HOME": str(Path(tmp) / "config")},
            )
            self.assertEqual(receipt["nominal_carrier_references_per_second"], 100.0)
            self.assertEqual(receipt["nominal_worker_ticks_per_second"], 200.0)
            self.assertEqual(service["nominal_carrier_references_per_second"], 100.0)
            self.assertEqual(service["nominal_worker_ticks_per_second"], 200.0)
            self.assertFalse(receipt["heartbeat_interval_argument_controls_progression"])
            self.assertFalse(service["heartbeat_interval_argument_controls_progression"])
            self.assertNotIn("--interval-ms", service["carrier_command"])
            self.assertIn("--interval-ms", service["worker_command"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertFalse(receipt["carrier_epoch_controls_worker_expiry"])


if __name__ == "__main__":
    unittest.main()
