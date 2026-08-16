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
    def _runtime(self, base: Path) -> Path:
        root = base / "heartbeat"
        (root / "heartbeat_runtime").mkdir(parents=True)
        (root / "heartbeat_runtime" / "engine_v11.py").write_text("# runtime\n", encoding="utf-8")
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "run_heartbeat_runtime.py").write_text("# runner\n", encoding="utf-8")
        (root / "receipts" / "sovereign-host").mkdir(parents=True)
        (root / "receipts" / "sovereign-host" / "materialization.latest.json").write_text("{}\n", encoding="utf-8")
        (root / "receipts" / "sovereign-host" / "activation.latest.json").write_text(
            json.dumps({
                "active": True,
                "third_party_process_host_required": False,
                "native_process_supervision_only": True,
                "registration_kind": "systemd-user",
            }) + "\n",
            encoding="utf-8",
        )
        (root / "checkpoints" / "workers" / "task").mkdir(parents=True)
        (root / "checkpoints" / "workers" / "task" / "HB1.json").write_text("{}\n", encoding="utf-8")
        (root / "control").mkdir(parents=True)
        state = {
            "epoch": 10,
            "generation": 10,
            "subsignals": {
                "worker_coordination": {
                    "state": "ACTIVE",
                    "active_leases": [
                        {"claim_id": "A-G1", "fencing_token": 1, "worker_instance_id": "w1"},
                        {"claim_id": "B-G2", "fencing_token": 2, "worker_instance_id": "w2"},
                    ],
                }
            },
        }
        (root / "control" / "heartbeat-state.json").write_text(json.dumps(state) + "\n", encoding="utf-8")
        (root / "control" / "worker-registry.json").write_text(
            json.dumps({"tasks": [{"task_id": "A"}, {"task_id": "B"}]}) + "\n",
            encoding="utf-8",
        )
        return root

    def test_hosted_environment_never_counts_as_sovereign(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.evaluate_runtime(
                self._runtime(Path(tmp)),
                env={"GITHUB_ACTIONS": "true", "STEGVERSE_SOVEREIGN_NODE": "1"},
            )
            self.assertFalse(any(result["predicates"].values()))
            self.assertEqual(result["detail"]["ineligible_reason"], "THIRD_PARTY_HOSTED_ENVIRONMENT")

    def test_real_node_proof_requires_advance_restart_and_reconstruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = self._runtime(base)
            state_path = root / "control" / "heartbeat-state.json"
            calls = {"sleep": 0, "restart": 0}

            def sleeper(_seconds: float) -> None:
                calls["sleep"] += 1
                state = json.loads(state_path.read_text())
                state["epoch"] += 1
                state["generation"] += 1
                state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")

            def runner(command, **_kwargs):
                calls["restart"] += 1
                self.assertIn("stegverse-heartbeat.service", command)
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
            self.assertTrue(proof["all_predicates_pass"])
            self.assertEqual(calls["sleep"], 2)
            self.assertEqual(calls["restart"], 1)
            for name in mod.REQUIRED_PREDICATES:
                self.assertTrue(proof[name], name)
            persisted = json.loads((base / "activation.latest.json").read_text())
            self.assertTrue(persisted["all_predicates_pass"])
            self.assertFalse(persisted["third_party_runtime_required"])

    def test_duplicate_fence_fails_closed(self) -> None:
        state = {
            "subsignals": {
                "worker_coordination": {
                    "active_leases": [
                        {"claim_id": "A", "fencing_token": 1, "worker_instance_id": "w1"},
                        {"claim_id": "B", "fencing_token": 1, "worker_instance_id": "w2"},
                    ]
                }
            }
        }
        self.assertFalse(mod.no_duplicate_claim_or_fence(state))


if __name__ == "__main__":
    unittest.main()
