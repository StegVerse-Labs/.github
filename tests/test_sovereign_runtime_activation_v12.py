from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_sovereign_runtime_activation",
    ROOT / "scripts" / "verify_sovereign_runtime_activation.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class SovereignRuntimeActivationTests(unittest.TestCase):
    def test_verifier_reads_oscillator_carrier_and_independent_worker_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runtime"
            control = root / "control"
            receipts = root / "receipts" / "sovereign-host"
            runtime_pkg = root / "heartbeat_runtime"
            scripts = root / "scripts"
            checkpoints = root / "checkpoints" / "workers"
            for path in (control, receipts, runtime_pkg, scripts, checkpoints):
                path.mkdir(parents=True, exist_ok=True)
            for path in (
                runtime_pkg / "engine_v13.py",
                runtime_pkg / "independent_oscillator.py",
                runtime_pkg / "oscillator_producer.py",
                runtime_pkg / "worker_runtime.py",
                scripts / "run_heartbeat_runtime.py",
                scripts / "run_worker_runtime.py",
            ):
                path.write_text("# test fixture\n", encoding="utf-8")

            legacy = {"schema": "stegverse.org-heartbeat-state/v1", "epoch": 29, "generation": 29}
            (control / "heartbeat-state.json").write_text(json.dumps(legacy) + "\n", encoding="utf-8")

            def carrier(epoch: int) -> dict:
                return {
                    "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
                    "epoch": epoch,
                    "generation": epoch,
                    "reference_frame": f"heartbeat_epoch:{epoch}",
                    "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
                    "oscillator": {
                        "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
                        "period_ns": 10_000_000,
                        "reference_frequency_hz": 100,
                        "progression_dependency": "OSCILLATOR_ONLY",
                        "downstream_gating": False,
                        "observation_is_causal": False,
                        "snapshot_is_observation_only": True,
                        "sampled_reference_epoch": epoch,
                    },
                }

            carrier_path = control / "heartbeat-carrier-runtime-state.json"
            carrier_path.write_text(json.dumps(carrier(30)) + "\n", encoding="utf-8")
            registry = {"schema": "x", "generation": 1, "workers": [], "tasks": [{"task_id": "A"}]}
            (control / "worker-registry.json").write_text(json.dumps(registry) + "\n", encoding="utf-8")
            control_plane = {
                "schema": "stegverse.worker-control-plane-coordination/v1",
                "worker_coordination": {"state": "IDLE", "active_leases": [], "worker_registry_ref": "control/worker-registry.json"},
            }
            control_plane_path = control / "worker-control-plane-coordination.json"
            control_plane_path.write_text(json.dumps(control_plane) + "\n", encoding="utf-8")
            worker_path = control / "worker-runtime-state.json"
            worker_path.write_text(json.dumps({
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 1,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
            }) + "\n", encoding="utf-8")
            (checkpoints / "checkpoint.json").write_text("{}\n", encoding="utf-8")
            (receipts / "materialization.latest.json").write_text(json.dumps({
                "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
                "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
                "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
                "heartbeat_interval_argument_controls_progression": False,
            }) + "\n", encoding="utf-8")
            (receipts / "activation.latest.json").write_text(json.dumps({
                "active": True,
                "carrier_active": True,
                "worker_active": True,
                "third_party_process_host_required": False,
                "native_process_supervision_only": True,
                "separate_carrier_and_worker_processes": True,
                "registration_kind": "systemd-user-separated",
            }) + "\n", encoding="utf-8")

            sleeps = {"count": 0}
            def sleeper(_seconds: float) -> None:
                sleeps["count"] += 1
                next_epoch = 30 + sleeps["count"]
                carrier_path.write_text(json.dumps(carrier(next_epoch)) + "\n", encoding="utf-8")
                worker_path.write_text(json.dumps({
                    "schema": "stegverse.worker-runtime-state/v1",
                    "runtime_tick": 1 + sleeps["count"],
                    "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
                    "last_observed_carrier_epoch": next_epoch,
                    "last_observed_carrier_generation": next_epoch,
                }) + "\n", encoding="utf-8")

            def runner(_command, **_kwargs):
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = mod.evaluate_runtime(
                root,
                runner=runner,
                sleeper=sleeper,
                system="linux",
                env={"STEGVERSE_SOVEREIGN_NODE": "1"},
            )
            self.assertTrue(all(result["predicates"].values()), result)
            self.assertTrue(result["detail"]["legacy_hb29_unchanged"])
            self.assertTrue(result["detail"]["oscillator_carrier_observed"])
            self.assertTrue(result["detail"]["oscillator_carrier_after_restart"])
            self.assertEqual(result["detail"]["worker_runtime_tick_before"], 1)
            self.assertEqual(result["detail"]["worker_runtime_tick_observed"], 2)
            self.assertEqual(result["detail"]["worker_runtime_tick_after_restart"], 3)
            self.assertEqual(result["detail"]["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertFalse(result["detail"]["worker_controls_heartbeat_progression"])
            self.assertEqual(result["detail"]["credential_authority"], "TV/TVC")
            self.assertFalse(result["detail"]["non_tv_tvc_secret_or_token_used"])

    def test_hosted_environment_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.evaluate_runtime(Path(tmp), env={"STEGVERSE_SOVEREIGN_NODE": "1", "RENDER": "true"})
            self.assertFalse(any(result["predicates"].values()))
            self.assertEqual(result["detail"]["ineligible_reason"], "THIRD_PARTY_HOSTED_ENVIRONMENT")


if __name__ == "__main__":
    unittest.main()
