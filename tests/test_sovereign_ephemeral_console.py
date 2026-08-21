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

    def test_verifier_accepts_oscillator_v13_stegverse_ephemeral_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (
                "heartbeat_runtime/engine_v13.py",
                "heartbeat_runtime/independent_oscillator.py",
                "heartbeat_runtime/oscillator_producer.py",
                "heartbeat_runtime/worker_runtime.py",
                "scripts/run_heartbeat_runtime.py",
                "scripts/run_worker_runtime.py",
            ):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# materialized runtime surface\n", encoding="utf-8")

            materialization = {
                "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
                "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
                "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
                "heartbeat_interval_argument_controls_progression": False,
                "credential_authority": "TV/TVC",
                "credential_requirement": "NONE",
                "non_tv_tvc_secret_or_token_used": False,
            }
            materialization_path = root / "receipts/sovereign-host/materialization.latest.json"
            materialization_path.parent.mkdir(parents=True, exist_ok=True)
            materialization_path.write_text(json.dumps(materialization), encoding="utf-8")

            service = {
                "active": True,
                "registration_kind": "stegverse-ephemeral-console",
                "stegverse_process_supervision": True,
                "third_party_process_host_required": False,
                "restart_command": ["python", "restart-helper.py", "--runtime-root", str(root)],
            }
            service_path = root / "receipts/sovereign-host/activation.latest.json"
            service_path.write_text(json.dumps(service), encoding="utf-8")

            control = root / "control"
            control.mkdir(parents=True, exist_ok=True)
            legacy = {
                "schema": "stegverse.org-heartbeat-state/v1",
                "epoch": 29,
                "generation": 29,
            }
            (control / "heartbeat-state.json").write_text(json.dumps(legacy), encoding="utf-8")

            registry = {"tasks": [{"task_id": "A"}]}
            (control / "worker-registry.json").write_text(json.dumps(registry), encoding="utf-8")
            worker_state_path = control / "worker-runtime-state.json"
            worker_state_path.write_text(
                json.dumps({
                    "schema": "stegverse.worker-runtime-state/v1",
                    "runtime_tick": 1,
                    "last_observed_carrier_epoch": 30,
                    "last_observed_carrier_generation": 30,
                    "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
                    "carrier_controls_timer": False,
                    "credential_authority": "TV/TVC",
                    "github_token_runtime_authority": "NONE",
                }),
                encoding="utf-8",
            )

            def control_plane(epoch: int):
                return {
                    "schema": "stegverse.worker-control-plane-coordination/v1",
                    "generation": 1,
                    "observed_reference": {
                        "carrier_generation": epoch,
                        "reference_frame": f"heartbeat_epoch:{epoch}",
                        "heartbeat_is_authority": False,
                    },
                    "worker_coordination": {
                        "state": "ACTIVE",
                        "worker_registry_ref": "control/worker-registry.json",
                        "active_leases": [
                            {
                                "claim_id": "claim-A",
                                "fencing_token": 1,
                                "worker_instance_id": "worker-A",
                            }
                        ],
                    },
                    "authority": {
                        "heartbeat_grants_execution_authority": False,
                        "signal_grants_execution_authority": False,
                        "master_records_action_authority": False,
                        "credential_authority": "TV/TVC",
                        "github_token_runtime_authority": False,
                    },
                }

            control_plane_path = control / "worker-control-plane-coordination.json"
            control_plane_path.write_text(json.dumps(control_plane(30)), encoding="utf-8")

            def carrier_state(epoch: int, generation: int):
                return {
                    "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
                    "epoch": epoch,
                    "generation": generation,
                    "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
                    "reference_frame": f"heartbeat_epoch:{epoch}",
                    "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
                    "authority_effect": "NONE",
                    "activation_state": "ACTIVE",
                    "oscillator": {
                        "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
                        "period_ns": 10_000_000,
                        "phase_travel_time_ms": 10,
                        "reference_increment_interval_ms": 10,
                        "reference_frequency_hz": 100,
                        "anchor_epoch": 30,
                        "anchor_unix_ns": 1_000_000_000,
                        "progression_dependency": "OSCILLATOR_ONLY",
                        "downstream_gating": False,
                        "observation_is_causal": False,
                        "sampled_reference_epoch": epoch,
                        "snapshot_is_observation_only": True,
                    },
                    "legacy_cutover": {
                        "legacy_schema": "stegverse.org-heartbeat-state/v1",
                        "legacy_epoch": 29,
                        "legacy_generation": 29,
                        "legacy_state_sha256": "0" * 64,
                        "source_ref": "control/heartbeat-state.json",
                        "closed": True,
                    },
                }

            state_path = control / "heartbeat-carrier-runtime-state.json"
            state_path.write_text(json.dumps(carrier_state(30, 30)), encoding="utf-8")
            sleeps = {"count": 0}

            def sleeper(_seconds):
                sleeps["count"] += 1
                next_epoch = 31 if sleeps["count"] == 1 else 32
                state_path.write_text(json.dumps(carrier_state(next_epoch, next_epoch)), encoding="utf-8")
                control_plane_path.write_text(json.dumps(control_plane(next_epoch)), encoding="utf-8")
                worker_state_path.write_text(json.dumps({
                    "schema": "stegverse.worker-runtime-state/v1",
                    "runtime_tick": 1 + sleeps["count"],
                    "last_observed_carrier_epoch": next_epoch,
                    "last_observed_carrier_generation": next_epoch,
                    "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
                    "carrier_controls_timer": False,
                    "credential_authority": "TV/TVC",
                    "github_token_runtime_authority": "NONE",
                }), encoding="utf-8")

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
            self.assertTrue(result["detail"]["legacy_hb29_unchanged"])
            self.assertTrue(result["detail"]["oscillator_carrier_observed"])
            self.assertTrue(result["detail"]["oscillator_carrier_after_restart"])
            self.assertEqual(result["detail"]["epoch_before"], 30)
            self.assertEqual(result["detail"]["epoch_observed"], 31)
            self.assertEqual(result["detail"]["epoch_after_restart"], 32)
            self.assertEqual(result["detail"]["worker_runtime_tick_before"], 1)
            self.assertEqual(result["detail"]["worker_runtime_tick_observed"], 2)
            self.assertEqual(result["detail"]["worker_runtime_tick_after_restart"], 3)

    def test_hosted_environment_detector_is_not_credential_based(self):
        self.assertTrue(hosted_environment({"GITHUB_ACTIONS": "1", "GITHUB_TOKEN": ""}))
        self.assertFalse(hosted_environment({"GITHUB_ACTIONS": "0", "GITHUB_TOKEN": "secret-that-is-ignored-for-host-detection"}))


if __name__ == "__main__":
    unittest.main()
