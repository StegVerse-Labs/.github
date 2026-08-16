from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.run_sovereign_ephemeral_console import hosted_environment, run_console
from scripts.verify_sovereign_runtime_activation import evaluate_runtime


class SovereignEphemeralConsoleTests(unittest.TestCase):
    def test_hosted_environment_cannot_claim_production_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_console(
                Path(tmp),
                Path(tmp) / "console",
                env={"GITHUB_ACTIONS": "true"},
            )
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "HOSTED_RUNNER_MAY_VALIDATE_SOURCE_BUT_CANNOT_PRODUCE_SOVEREIGN_ACTIVATION")
        self.assertFalse(result["physical_additional_machine_required"])

    def test_hosted_validation_only_is_explicitly_non_authorizing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_console(
                Path(tmp),
                Path(tmp) / "console",
                validation_only=True,
                env={"GITHUB_ACTIONS": "true"},
            )
        self.assertEqual(result["state"], "VALIDATION_ONLY")
        self.assertTrue(result["hosted_environment_observed"])
        self.assertFalse(result["third_party_runtime_required"])
        self.assertEqual(result["credential_authority"], "TV/TVC")

    def test_three_nodes_required_for_third_machine_emulation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_console(
                Path(tmp),
                Path(tmp) / "console",
                node_count=2,
                env={},
            )
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["reason"], "THREE_LOGICAL_NODES_REQUIRED_FOR_THIRD_MACHINE_EMULATION")

    def test_verifier_accepts_engine_v11_and_stegverse_ephemeral_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (
                "heartbeat_runtime/engine_v11.py",
                "scripts/run_heartbeat_runtime.py",
                "receipts/sovereign-host/materialization.latest.json",
            ):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            service = {
                "active": True,
                "registration_kind": "stegverse-ephemeral-console",
                "stegverse_process_supervision": True,
                "third_party_process_host_required": False,
                "restart_command": ["python", "restart-helper.py", "--runtime-root", str(root)],
            }
            service_path = root / "receipts/sovereign-host/activation.latest.json"
            service_path.write_text(json.dumps(service), encoding="utf-8")
            registry = {"tasks": [{"task_id": "A"}]}
            registry_path = root / "control/worker-registry.json"
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            checkpoint = root / "checkpoints/workers/A.json"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_text("{}\n", encoding="utf-8")

            def state(epoch: int, generation: int):
                return {
                    "epoch": epoch,
                    "generation": generation,
                    "subsignals": {
                        "worker_coordination": {
                            "state": "ACTIVE",
                            "active_leases": [
                                {
                                    "claim_id": "claim-A",
                                    "fencing_token": 1,
                                    "worker_instance_id": "worker-A",
                                }
                            ],
                        }
                    },
                }

            state_path = root / "control/heartbeat-state.json"
            state_path.write_text(json.dumps(state(10, 10)), encoding="utf-8")
            sleeps = {"count": 0}

            def sleeper(_seconds):
                sleeps["count"] += 1
                next_epoch = 11 if sleeps["count"] == 1 else 12
                state_path.write_text(json.dumps(state(next_epoch, next_epoch)), encoding="utf-8")

            seen = {}

            def runner(command, **_kwargs):
                seen["command"] = command
                return SimpleNamespace(returncode=0)

            result = evaluate_runtime(
                root,
                runner=runner,
                sleeper=sleeper,
                env={"STEGVERSE_SOVEREIGN_NODE": "1"},
            )
            self.assertTrue(all(result["predicates"].values()), result)
            self.assertEqual(seen["command"], service["restart_command"])
            self.assertEqual(result["detail"]["registration_kind"], "stegverse-ephemeral-console")

    def test_hosted_environment_detector_is_not_credential_based(self):
        self.assertTrue(hosted_environment({"GITHUB_ACTIONS": "1", "GITHUB_TOKEN": ""}))
        self.assertFalse(hosted_environment({"GITHUB_ACTIONS": "0", "GITHUB_TOKEN": "secret-that-is-ignored-for-host-detection"}))


if __name__ == "__main__":
    unittest.main()
