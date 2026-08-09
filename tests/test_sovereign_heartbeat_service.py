from __future__ import annotations

import importlib.util
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
    def test_materialization_is_network_independent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "heartbeat"
            receipt = mod.materialize(ROOT, target)
            self.assertFalse(receipt["network_fetch_required"])
            self.assertFalse(receipt["third_party_deployment_required"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertTrue((target / "heartbeat_runtime" / "engine_v8.py").is_file())
            self.assertTrue((target / "control" / "worker-registry.json").is_file())

    def test_linux_service_runs_continuous_runtime_directly(self) -> None:
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
            self.assertIn("run_heartbeat_runtime.py", text)
            self.assertIn("--continuous", text)
            self.assertIn("Restart=always", text)
            self.assertNotIn("github", text.lower())
            self.assertNotIn("render", text.lower())

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
            self.assertFalse(receipt["third_party_deployment_required"])
            self.assertEqual(len(calls), 2)
            self.assertTrue(
                (target / "receipts" / "sovereign-host" / "activation.latest.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
