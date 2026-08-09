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
    def test_materialization_is_network_independent_and_runtime_v9(self) -> None:
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
            self.assertEqual(receipt["canonical_runtime"], "heartbeat_runtime.engine_v9.HeartbeatRuntime")
            self.assertEqual(receipt["heartbeat_default_interval_ms"], 10.0)
            self.assertEqual(receipt["nominal_cycles_per_second"], 100.0)
            self.assertEqual(receipt["worker_lease_clock"], "canonical_heartbeat_cycle")
            self.assertFalse(receipt["wall_clock_worker_expiry_authority"])
            self.assertTrue((target / "heartbeat_runtime" / "engine_v9.py").is_file())
            self.assertTrue((target / "control" / "heartbeat-subsignals.json").is_file())
            self.assertTrue((target / "control" / "worker-registry.json").is_file())
            written = json.loads((target / "receipts" / "sovereign-host" / "materialization.latest.json").read_text())
            self.assertEqual(written["canonical_runtime"], receipt["canonical_runtime"])

    def test_linux_service_runs_continuous_runtime_directly_at_high_frequency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "heartbeat"
            mod.materialize(ROOT, root)
            receipt = mod.materialize_service(
                root,
                system="linux",
                env={"XDG_CONFIG_HOME": str(base / "config")},
            )
            text = Path(receipt["registration_path"]).read_text(encoding="utf-8")
            self.assertEqual(receipt["registration_kind"], "systemd-user")
            self.assertEqual(receipt["heartbeat_interval_ms"], 10.0)
            self.assertEqual(receipt["nominal_cycles_per_second"], 100.0)
            self.assertTrue(receipt["native_process_supervision_only"])
            self.assertIn("run_heartbeat_runtime.py", text)
            self.assertIn("--continuous", text)
            self.assertIn("--interval-ms", text)
            self.assertIn("10.0", text)
            self.assertIn("Restart=always", text)
            self.assertNotIn("github", text.lower())
            self.assertNotIn("render", text.lower())
            self.assertNotIn("cloudflare", text.lower())
            self.assertNotIn("network-online.target", text.lower())

    def test_install_records_native_activation_without_granting_authority(self) -> None:
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
            self.assertEqual(receipt["execution_authority_effect"], "NONE")
            self.assertEqual(receipt["canonical_runtime"], "heartbeat_runtime.engine_v9.HeartbeatRuntime")
            self.assertFalse(receipt["third_party_process_host_required"])
            self.assertFalse(receipt["third_party_deployment_required"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertEqual(len(calls), 2)
            self.assertTrue(
                (target / "receipts" / "sovereign-host" / "activation.latest.json").is_file()
            )

    def test_custom_cycle_rate_is_local_runtime_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "heartbeat"
            receipt = mod.materialize(ROOT, target, interval_ms=5.0)
            service = mod.materialize_service(target, interval_ms=5.0, system="linux", env={"XDG_CONFIG_HOME": str(Path(tmp) / "config")})
            self.assertEqual(receipt["nominal_cycles_per_second"], 200.0)
            self.assertEqual(service["nominal_cycles_per_second"], 200.0)
            self.assertFalse(receipt["third_party_scheduler_required"])


if __name__ == "__main__":
    unittest.main()
