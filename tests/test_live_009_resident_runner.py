import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("live009", ROOT / "scripts/run_live_009_resident.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class Live009ResidentRunnerTests(unittest.TestCase):
    def test_execution_sequence_uses_materialized_resident_root(self):
        source = Path("/source/stegverse").resolve()
        resident = Path("/resident/stegverse-heartbeat").resolve()
        commands = mod.execution_commands(source, resident, "/usr/bin/python3")

        install, install_cwd = commands[0]
        self.assertEqual(install_cwd, source)
        self.assertIn(str(source / "scripts/install_sovereign_heartbeat_carrier.py"), install)
        self.assertIn("--runtime-root", install)
        self.assertIn(str(resident), install)

        for command, cwd in commands[1:]:
            self.assertEqual(cwd, resident)
            self.assertIn("--root", command)
            self.assertIn(str(resident), command)
            self.assertNotIn(str(source / "scripts/run_worker_runtime.py"), command)
            self.assertNotIn(str(source / "scripts/run_heartbeat_runtime.py"), command)

    def make_valid_runtime(self, root: Path, *, fence: int = 22, terminal: bool = True, terminal_claim: str | None = "MATCH"):
        (root / "receipts/sovereign-host").mkdir(parents=True)
        (root / "control").mkdir(parents=True)
        (root / "events").mkdir(parents=True)
        activation = {
            "carrier_active": True,
            "activation_scope": "CARRIER_ONLY",
            "canonical_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
            "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
            "heartbeat_period_ms": 10.0,
            "heartbeat_reference_frequency_hz": 100.0,
            "network_fetch_required": False,
            "third_party_process_host_required": False,
            "third_party_scheduler_required": False,
            "third_party_deployment_required": False,
            "github_runtime_dependency": False,
            "credential_requirement": "NONE",
        }
        (root / "receipts/sovereign-host/carrier-activation.latest.json").write_text(json.dumps(activation))
        carrier = {
            "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
            "authority_effect": "NONE",
            "oscillator": {
                "progression_dependency": "OSCILLATOR_ONLY",
                "phase_travel_time_ms": 10,
                "reference_frequency_hz": 100,
                "snapshot_is_observation_only": True,
                "observation_is_causal": False,
            },
        }
        (root / "control/heartbeat-carrier-runtime-state.json").write_text(json.dumps(carrier))
        (root / "control/heartbeat-carrier-observation.json").write_text(json.dumps({"observation_is_causal": False, "authority_effect": "NONE"}))
        claim_id = f"SHWP-{mod.TASK_ID}-G{fence}"
        assignment = {
            "task_id": mod.TASK_ID,
            "claim_id": claim_id,
            "fencing_token": fence,
            "source_admission_ref": "handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json#admission",
            "source_carrier_event_ref": None,
        }
        (root / "events/master-records-worker-assignment.jsonl").write_text(json.dumps(assignment) + "\n")
        worker_event = {"task_id": mod.TASK_ID}
        if terminal_claim == "MATCH":
            worker_event["claim_id"] = claim_id
        elif terminal_claim is not None:
            worker_event["claim_id"] = terminal_claim
        if terminal:
            worker_event["transition_id"] = mod.TERMINAL
        (root / "events/worker-runtime.jsonl").write_text(json.dumps(worker_event) + "\n")

    def test_requires_real_activation_fresh_fence_and_terminal_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_valid_runtime(root)
            mod.require_runtime_evidence(root)

    def test_rejects_stale_fence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_valid_runtime(root, fence=21)
            with self.assertRaisesRegex(RuntimeError, "fresh independently admitted"):
                mod.require_runtime_evidence(root)

    def test_rejects_carrier_derived_assignment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_valid_runtime(root)
            assignment_path = root / "events/master-records-worker-assignment.jsonl"
            row = json.loads(assignment_path.read_text())
            row["source_carrier_event_ref"] = "events/heartbeat-runtime.jsonl#packet_id=x"
            assignment_path.write_text(json.dumps(row) + "\n")
            with self.assertRaisesRegex(RuntimeError, "fresh independently admitted"):
                mod.require_runtime_evidence(root)

    def test_rejects_missing_terminal_worker_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_valid_runtime(root, terminal=False)
            with self.assertRaisesRegex(RuntimeError, "terminal LIVE-009"):
                mod.require_runtime_evidence(root)

    def test_rejects_terminal_event_without_claim_binding(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_valid_runtime(root, terminal_claim=None)
            with self.assertRaisesRegex(RuntimeError, "terminal LIVE-009"):
                mod.require_runtime_evidence(root)

    def test_rejects_terminal_event_bound_to_different_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_valid_runtime(root, terminal_claim="SHWP-OTHER-G999")
            with self.assertRaisesRegex(RuntimeError, "terminal LIVE-009"):
                mod.require_runtime_evidence(root)


if __name__ == "__main__":
    unittest.main()
