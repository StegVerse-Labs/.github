from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "sovereign_runtime_activation_worker.py"


class SovereignRuntimeActivationEscalationTests(unittest.TestCase):
    def invocation(self) -> dict:
        return {
            "schema": "stegverse.worker-invocation/v0.1",
            "heartbeat_epoch": 30,
            "task": {
                "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                "claim_id": "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18",
                "worker_id": "sovereign-runtime-activation-worker",
                "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                "heartbeat_timing": {"fencing_token": 18},
            },
            "handoff": {
                "execution": {
                    "required_capabilities": [
                        "runtime_observation",
                        "continuous_process_execution",
                        "durable_state_reconstruction",
                        "bounded_repository_mutation",
                    ],
                    "allowed_paths": ["receipts/sovereign-runtime-activation/**"],
                }
            },
        }

    def test_missing_declared_node_emits_next_level_resolution_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(Path(tmp) / "home"),
                "XDG_STATE_HOME": str(Path(tmp) / "state"),
            }
            completed = subprocess.run(
                [sys.executable, str(WORKER)],
                cwd=tmp,
                input=json.dumps(self.invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "BLOCKED")
            self.assertEqual(response["transition_id"], "SOVEREIGN_RUNTIME_RESOLUTION_ESCALATION_REQUIRED")
            self.assertEqual(response["expected_next_transition"], "DERIVE_AND_REGISTER_RESOLUTION_TASK")
            blocker = response["blocker"]
            self.assertEqual(blocker["dependency_class"], "PHYSICAL_RESOURCE")
            self.assertEqual(blocker["trigger_type"], "CONDITIONAL_CONSTRAINT")
            self.assertTrue(blocker["solution_required"])
            self.assertFalse(blocker["resolvable_by_current_worker"])
            self.assertEqual(blocker["escalation_target"], "REPOSITORY_OWNER")
            self.assertIn("repository_resolution", blocker["required_capabilities"])
            self.assertGreaterEqual(len(blocker["workaround_candidates"]), 1)
            self.assertGreaterEqual(len(blocker["completion_evidence"]), 1)
            self.assertNotIn("may_remain_blocked", blocker)
            self.assertNotIn("GITHUB_TOKEN", completed.stdout)

    def test_hosted_environment_is_not_used_as_sovereign_activation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(Path(tmp) / "home"),
                "XDG_STATE_HOME": str(Path(tmp) / "state"),
                "GITHUB_ACTIONS": "true",
                "STEGVERSE_SOVEREIGN_NODE": "1",
            }
            completed = subprocess.run(
                [sys.executable, str(WORKER)],
                cwd=tmp,
                input=json.dumps(self.invocation()) + "\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(response["state"], "BLOCKED")
            self.assertFalse(response["blocker"]["resolvable_by_current_worker"])
            receipt = json.loads(
                (Path(tmp) / "receipts" / "sovereign-runtime-activation" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text()
            )
            self.assertTrue(receipt["solution_attempt"]["hosted_environment_rejected"])
            self.assertEqual(receipt["solution_attempt"]["reason"], "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE")
            self.assertFalse(receipt["third_party_runtime_required"])

    def test_carrier_is_release_priority_and_names_stegfin_as_downstream(self) -> None:
        handoff = json.loads((ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text())
        self.assertEqual(handoff["task"]["priority"], "release")
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(handoff["authority"]["github_token_production_authority"], "NONE")
        self.assertIn("STEGFIN-LIVE-ENTRY-003", handoff["release_downstream"])
        self.assertEqual(handoff["constraint"]["operational_state"], "ACTIVE_SOLUTION_EXECUTION")


if __name__ == "__main__":
    unittest.main()
