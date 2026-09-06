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


class SovereignRuntimeActivationVerifierTests(unittest.TestCase):
    def _runtime(self, base: Path, *, observation_only: bool = False) -> Path:
        root = base / "heartbeat"
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
            path.write_text("# runtime fixture\n", encoding="utf-8")

        receipts = root / "receipts" / "sovereign-host"
        receipts.mkdir(parents=True)
        (receipts / "materialization.latest.json").write_text(json.dumps({
            "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
            "carrier_producer_ref": "heartbeat_runtime/oscillator_producer.py",
            "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
            "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
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

        checkpoint = root / "checkpoints" / "workers" / "task" / "HB1.json"
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_text("{}\n", encoding="utf-8")

        control = root / "control"
        control.mkdir(parents=True)
        (control / "heartbeat-state.json").write_text(json.dumps({
            "schema": "stegverse.org-heartbeat-state/v1",
            "epoch": 29,
            "generation": 29,
        }) + "\n", encoding="utf-8")
        (control / "heartbeat-carrier-runtime-state.json").write_text(json.dumps({
            "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
            "epoch": 30,
            "generation": 30,
            "reference_frame": "heartbeat_epoch:30",
            "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
            "oscillator": {
                "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
                "period_ns": 10_000_000,
                "phase_travel_time_ms": 10,
                "reference_frequency_hz": 100,
                "progression_dependency": "OSCILLATOR_ONLY",
                "downstream_gating": False,
                "observation_is_causal": False,
                "snapshot_is_observation_only": True,
                "sampled_reference_epoch": 30,
            },
        }) + "\n", encoding="utf-8")
        (control / "worker-registry.json").write_text(json.dumps({
            "tasks": [{"task_id": "A"}, {"task_id": "B"}],
        }) + "\n", encoding="utf-8")
        worker = {
            "schema": "stegverse.worker-runtime-state/v1",
            "runtime_tick": 1,
            "last_observed_carrier_epoch": 30,
            "last_observed_carrier_generation": 30,
        }
        if observation_only:
            worker["observation_mode"] = "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
        (control / "worker-runtime-state.json").write_text(json.dumps(worker) + "\n", encoding="utf-8")
        self._write_control_plane(control / "worker-control-plane-coordination.json")
        return root

    @staticmethod
    def _write_control_plane(path: Path, *, duplicate_fence: bool = False) -> None:
        path.write_text(json.dumps({
            "schema": "stegverse.worker-control-plane-coordination/v1",
            "worker_coordination": {
                "state": "ACTIVE",
                "worker_registry_ref": "control/worker-registry.json",
                "active_leases": [
                    {"claim_id": "A-G1", "fencing_token": 1, "worker_instance_id": "w1"},
                    {"claim_id": "B-G2", "fencing_token": 1 if duplicate_fence else 2, "worker_instance_id": "w2"},
                ],
            },
        }) + "\n", encoding="utf-8")

    @staticmethod
    def _advance_carrier(carrier_path: Path) -> dict:
        state = json.loads(carrier_path.read_text())
        state["epoch"] += 1
        state["generation"] += 1
        state["reference_frame"] = f"heartbeat_epoch:{state['epoch']}"
        state["oscillator"]["sampled_reference_epoch"] = state["epoch"]
        carrier_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
        return state

    def test_hosted_environment_never_counts_as_sovereign(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.evaluate_runtime(
                self._runtime(Path(tmp)),
                env={"GITHUB_ACTIONS": "true", "STEGVERSE_SOVEREIGN_NODE": "1"},
            )
            self.assertFalse(any(result["predicates"].values()))
            self.assertEqual(result["detail"]["ineligible_reason"], "THIRD_PARTY_HOSTED_ENVIRONMENT")

    def test_real_node_proof_requires_carrier_and_worker_progress_restart_and_reconstruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self._runtime(base)
            carrier_path = root / "control" / "heartbeat-carrier-runtime-state.json"
            worker_path = root / "control" / "worker-runtime-state.json"
            calls = {"sleep": 0, "restart": 0}

            def sleeper(_seconds: float) -> None:
                calls["sleep"] += 1
                state = self._advance_carrier(carrier_path)
                worker = json.loads(worker_path.read_text())
                worker["runtime_tick"] += 1
                worker["last_observed_carrier_epoch"] = state["epoch"]
                worker["last_observed_carrier_generation"] = state["generation"]
                worker.pop("observation_mode", None)
                worker_path.write_text(json.dumps(worker) + "\n", encoding="utf-8")

            def runner(command, **_kwargs):
                calls["restart"] += 1
                self.assertIn("stegverse-heartbeat.service", command, command)
                self.assertNotIn("stegverse-worker-runtime.service", command, command)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            proof = mod.verify(
                root,
                runner=runner,
                sleeper=sleeper,
                observe_seconds=0,
                restart_seconds=0,
                system="linux",
                env={
                    "STEGVERSE_SOVEREIGN_NODE": "1",
                    "STEGVERSE_SOVEREIGN_PROOF_PATH": str(base / "activation.latest.json"),
                },
            )
            self.assertTrue(proof["all_predicates_pass"], proof)
            self.assertEqual(calls["sleep"], 2)
            self.assertEqual(calls["restart"], 1)
            for name in mod.REQUIRED_PREDICATES:
                self.assertTrue(proof[name], name)
            persisted = json.loads((base / "activation.latest.json").read_text())
            self.assertTrue(persisted["all_predicates_pass"])
            self.assertTrue(persisted["worker_task_capable_cycle_observed"])
            self.assertEqual(persisted["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertFalse(persisted["third_party_runtime_required"])
            self.assertEqual(persisted["credential_authority"], "TV/TVC")
            self.assertEqual(persisted["credential_requirement"], "NONE")

    def test_observation_only_worker_cannot_satisfy_activation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self._runtime(base, observation_only=True)
            carrier_path = root / "control" / "heartbeat-carrier-runtime-state.json"
            worker_path = root / "control" / "worker-runtime-state.json"

            def sleeper(_seconds: float) -> None:
                self._advance_carrier(carrier_path)
                worker = json.loads(worker_path.read_text())
                worker["runtime_tick"] += 1
                worker_path.write_text(json.dumps(worker) + "\n", encoding="utf-8")

            def runner(_command, **_kwargs):
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = mod.evaluate_runtime(
                root,
                runner=runner,
                sleeper=sleeper,
                observe_seconds=0,
                restart_seconds=0,
                system="linux",
                env={"STEGVERSE_SOVEREIGN_NODE": "1"},
            )
            self.assertFalse(result["predicates"]["worker_task_capable_cycle_observed"], result)
            self.assertFalse(result["predicates"]["continuous_runtime_live"], result)
            self.assertFalse(result["predicates"]["state_reconstruction_pass"], result)

    def test_worker_tick_must_advance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._runtime(Path(tmp))
            carrier_path = root / "control" / "heartbeat-carrier-runtime-state.json"

            def sleeper(_seconds: float) -> None:
                self._advance_carrier(carrier_path)

            result = mod.evaluate_runtime(
                root,
                runner=lambda _command, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
                sleeper=sleeper,
                observe_seconds=0,
                restart_seconds=0,
                system="linux",
                env={"STEGVERSE_SOVEREIGN_NODE": "1"},
            )
            self.assertFalse(result["predicates"]["worker_task_capable_cycle_observed"], result)
            self.assertFalse(result["predicates"]["all_predicates_pass"] if "all_predicates_pass" in result["predicates"] else False)

    def test_duplicate_fence_fails_closed(self) -> None:
        state = {
            "worker_coordination": {
                "active_leases": [
                    {"claim_id": "A", "fencing_token": 1, "worker_instance_id": "w1"},
                    {"claim_id": "B", "fencing_token": 1, "worker_instance_id": "w2"},
                ]
            }
        }
        self.assertFalse(mod.no_duplicate_claim_or_fence(state))


if __name__ == "__main__":
    unittest.main()
