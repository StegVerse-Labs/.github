from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"
VERIFIER = ROOT / "scripts" / "verify_sovereign_runtime_activation.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class CarrierFirstRuntimeReconciliationTests(unittest.TestCase):
    def test_bootstrap_starts_existing_carrier_only_installer_before_worker_observation(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")
        install_pos = source.index('install_sovereign_heartbeat_carrier.py')
        presence_pos = source.index('_wait_for_worker_presence(runtime_root)')
        verify_pos = source.index('verify_sovereign_runtime_activation.py')
        self.assertLess(install_pos, presence_pos)
        self.assertLess(presence_pos, verify_pos)
        self.assertNotIn(
            'str(source_root / "scripts/install_sovereign_heartbeat_service.py")',
            source,
        )
        self.assertIn('"workercoordinator_required_for_carrier_start": False', source)
        self.assertIn('"worker_start_attempted_by_carrier_installer": False', source)

    def test_carrier_receipt_validation_requires_zero_worker_start_dependency(self) -> None:
        module = load(BOOTSTRAP, "carrier_first_bootstrap_test")
        valid = {
            "schema": "stegverse.sovereign-heartbeat-carrier-activation/v1",
            "activation_scope": "CARRIER_ONLY",
            "carrier_active": True,
            "worker_start_attempted": False,
            "worker_runtime_dependency_for_carrier_start": False,
            "network_fetch_required": False,
            "third_party_process_host_required": False,
            "github_runtime_dependency": False,
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
            "heartbeat_period_ms": 10.0,
            "heartbeat_reference_frequency_hz": 100.0,
            "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
            "canonical_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        }
        self.assertTrue(module._carrier_activation_valid(valid))
        invalid = dict(valid)
        invalid["worker_start_attempted"] = True
        self.assertFalse(module._carrier_activation_valid(invalid))

    def test_verifier_controlled_restart_restarts_only_carrier(self) -> None:
        module = load(VERIFIER, "carrier_first_verifier_test")
        linux = module.restart_commands(system="Linux")
        self.assertEqual(linux, [["systemctl", "--user", "restart", "stegverse-heartbeat.service"]])
        windows = module.restart_commands(system="Windows")
        self.assertEqual(windows, [["schtasks", "/Run", "/TN", "StegVerse Heartbeat"]])
        flat = " ".join(item for command in linux + windows for item in command)
        self.assertNotIn("worker-runtime", flat)
        self.assertNotIn("Worker Runtime", flat)

    def test_verifier_requires_existing_self_heal_or_presence_evidence(self) -> None:
        module = load(VERIFIER, "carrier_first_verifier_presence_test")
        worker = {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 4,
            "observation_mode": "TASK_CAPABLE",
        }
        self.assertFalse(module._worker_presence_observed({}, {}, worker))
        healed = {
            "active": True,
            "carrier_active": True,
            "worker_active": True,
            "worker_task_capable_cycle_observed": True,
            "separate_carrier_and_worker_processes": True,
            "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
            "third_party_process_host_required": False,
            "heartbeat_grants_execution_authority": False,
            "authority_effect": "NONE_SUPERVISION_ONLY",
        }
        self.assertTrue(module._worker_presence_observed({}, healed, worker))


if __name__ == "__main__":
    unittest.main()
