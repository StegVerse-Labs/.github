import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_sovereign_heartbeat_carrier.py"
spec = importlib.util.spec_from_file_location("carrier_installer", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class CarrierOnlyInstallerTests(unittest.TestCase):
    def test_only_carrier_activation_commands_execute(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = {
                "carrier_success_index": 1,
                "activation_commands": [["reload"], ["start-carrier"], ["start-worker"]],
                "carrier_registration_path": "/native/carrier",
                "carrier_command": ["python", "run_heartbeat_runtime.py", "--continuous"],
            }
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return mock.Mock(returncode=0)

            with mock.patch.object(mod.base, "materialize", return_value={
                "network_fetch_required": False,
                "github_runtime_dependency": False,
            }), mock.patch.object(mod.base, "materialize_service", return_value=service):
                receipt = mod.install_carrier(root, root, runner=runner)

            self.assertEqual(calls, [["reload"], ["start-carrier"]])
            self.assertTrue(receipt["carrier_active"])
            self.assertFalse(receipt["worker_start_attempted"])
            self.assertFalse(receipt["worker_runtime_dependency_for_carrier_start"])
            self.assertFalse(receipt["third_party_process_host_required"])
            self.assertFalse(receipt["third_party_scheduler_required"])
            self.assertFalse(receipt["third_party_deployment_required"])
            self.assertFalse(receipt["github_runtime_dependency"])
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertEqual(receipt["credential_requirement"], "NONE")
            self.assertEqual(receipt["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertEqual(receipt["heartbeat_period_ms"], 10.0)
            self.assertEqual(receipt["heartbeat_reference_frequency_hz"], 100.0)
            self.assertTrue((root / "receipts/sovereign-host/carrier-activation.latest.json").is_file())


if __name__ == "__main__":
    unittest.main()
