import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_sovereign_heartbeat_carrier.py"
ROOT = SCRIPT.parents[1]
spec = importlib.util.spec_from_file_location("carrier_installer", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class CarrierOnlyInstallerTests(unittest.TestCase):
    @staticmethod
    def observed_progress(_root):
        return {
            "observed": True,
            "first_epoch": 32,
            "last_epoch": 33,
            "state_ref": "control/heartbeat-carrier-runtime-state.json",
        }

    def test_documented_direct_cli_entrypoint_resolves_repository_imports(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--runtime-root", completed.stdout)

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
                receipt = mod.install_carrier(
                    root, root, runner=runner, carrier_observer=self.observed_progress
                )

            self.assertEqual(calls, [["reload"], ["start-carrier"]])
            self.assertTrue(receipt["carrier_active"])
            self.assertTrue(receipt["carrier_start_reported"])
            self.assertTrue(receipt["carrier_progression_observation"]["observed"])
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

    def test_windows_registration_requires_immediate_task_start(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = {
                "carrier_success_index": 0,
                "activation_commands": [
                    ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Heartbeat", "/TR", "heartbeat-start.cmd"],
                    ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Worker Runtime", "/TR", "worker-start.cmd"],
                ],
                "carrier_registration_path": "heartbeat-start.cmd",
                "carrier_command": ["python", "run_heartbeat_runtime.py", "--continuous"],
                "registration_kind": "scheduled-task-separated",
            }
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return mock.Mock(returncode=0)

            with mock.patch.object(mod.base, "materialize", return_value={
                "network_fetch_required": False,
                "github_runtime_dependency": False,
            }), mock.patch.object(mod.base, "materialize_service", return_value=service):
                receipt = mod.install_carrier(
                    root, root, runner=runner, carrier_observer=self.observed_progress
                )

            self.assertEqual(calls, [
                service["activation_commands"][0],
                ["schtasks", "/Run", "/TN", "StegVerse Heartbeat"],
            ])
            self.assertTrue(receipt["carrier_active"])
            self.assertFalse(receipt["worker_start_attempted"])

    def test_windows_run_failure_cannot_claim_carrier_active(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = {
                "carrier_success_index": 0,
                "activation_commands": [
                    ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Heartbeat", "/TR", "heartbeat-start.cmd"],
                    ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Worker Runtime", "/TR", "worker-start.cmd"],
                ],
                "carrier_registration_path": "heartbeat-start.cmd",
                "carrier_command": ["python", "run_heartbeat_runtime.py", "--continuous"],
                "registration_kind": "scheduled-task-separated",
            }
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return mock.Mock(returncode=0 if len(calls) == 1 else 1)

            with mock.patch.object(mod.base, "materialize", return_value={
                "network_fetch_required": False,
                "github_runtime_dependency": False,
            }), mock.patch.object(mod.base, "materialize_service", return_value=service):
                receipt = mod.install_carrier(
                    root, root, runner=runner, carrier_observer=self.observed_progress
                )

            self.assertFalse(receipt["carrier_active"])
            self.assertFalse(receipt["carrier_start_reported"])

    def test_successful_registration_without_progress_cannot_claim_carrier_active(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            service = {
                "carrier_success_index": 0,
                "activation_commands": [["start-carrier"]],
                "carrier_registration_path": "/native/carrier",
                "carrier_command": ["python", "run_heartbeat_runtime.py", "--continuous"],
            }
            runner = mock.Mock(return_value=mock.Mock(returncode=0))
            no_progress = mock.Mock(return_value={
                "observed": False,
                "failure": "carrier state not observed",
                "state_ref": "control/heartbeat-carrier-runtime-state.json",
            })

            with mock.patch.object(mod.base, "materialize", return_value={
                "network_fetch_required": False,
                "github_runtime_dependency": False,
            }), mock.patch.object(mod.base, "materialize_service", return_value=service):
                receipt = mod.install_carrier(
                    root, root, runner=runner, carrier_observer=no_progress
                )

            self.assertTrue(receipt["carrier_start_reported"])
            self.assertFalse(receipt["carrier_active"])
            self.assertFalse(receipt["carrier_progression_observation"]["observed"])


if __name__ == "__main__":
    unittest.main()
