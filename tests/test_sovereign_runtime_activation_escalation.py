from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from heartbeat_runtime.engine_v11 import HeartbeatRuntime as HeartbeatRuntimeV11

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
        from heartbeat_runtime.engine_v2 import HeartbeatRuntime as HeartbeatRuntimeV2

        handoff = json.loads((ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text())
        self.assertEqual(handoff["task"]["priority"], "release")
        self.assertLess(
            HeartbeatRuntimeV2.PRIORITY["release"],
            HeartbeatRuntimeV2.PRIORITY["critical"],
        )
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(handoff["authority"]["github_token_production_authority"], "NONE")
        self.assertIn("STEGFIN-LIVE-ENTRY-003", handoff["release_downstream"])
        self.assertEqual(handoff["constraint"]["operational_state"], "ACTIVE_SOLUTION_EXECUTION")

    def test_v11_resolution_successor_inherits_release_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "handoffs").mkdir(parents=True)
            parent_handoff = json.loads(
                (ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json").read_text()
            )
            (root / "handoffs" / "parent.json").write_text(
                json.dumps(parent_handoff), encoding="utf-8"
            )
            parent = {
                "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                "goal_id": parent_handoff["goal"]["goal_id"],
                "state": "BLOCKED",
                "handoff_ref": "handoffs/parent.json",
                "executor_binding": "BOUND",
                "worker_id": None,
                "worker_instance_id": None,
                "claim_id": None,
                "heartbeat_timing": None,
                "last_checkpoint_ref": parent_handoff["continuity"]["checkpoint_ref"],
                "archive_eligible": False,
                "archive_reason_codes": [],
                "evidence_refs": [],
            }
            registry = {"generation": 18, "workers": [], "tasks": [parent]}
            contract = {
                "trigger_type": "CONDITIONAL_CONSTRAINT",
                "dependency_class": "PHYSICAL_RESOURCE",
                "problem_statement": "No declared sovereign carrier is observable.",
                "solution_required": True,
                "workaround_candidates": ["promote an eligible sovereign micro-node"],
                "next_solution_action": "select or materialize a sovereign carrier",
                "resolvable_by_current_worker": False,
                "escalation_target": "REPOSITORY_OWNER",
                "required_capabilities": ["repository_resolution", "sandbox_validation"],
                "completion_evidence": ["nine-predicate activation proof passes"],
            }
            runtime = HeartbeatRuntimeV11(root)
            events: list[dict] = []
            task_id = runtime._admit_resolution_task(
                registry,
                parent,
                30,
                events,
                "resolution-contract:test",
                contract,
            )
            generated = json.loads(
                (root / "handoffs" / "generated" / f"{task_id}.json").read_text()
            )
            self.assertEqual(generated["task"]["priority"], "release")
            self.assertTrue(
                any(event.get("event_type") == "resolution_priority_inherited" for event in events)
            )


if __name__ == "__main__":
    unittest.main()
