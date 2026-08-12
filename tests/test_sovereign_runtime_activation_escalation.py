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
RESOLVER = ROOT / "workers" / "sovereign_node_repository_resolution_worker.py"


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

    def resolver_invocation(self) -> dict:
        return {
            "schema": "stegverse.worker-invocation/v0.1",
            "heartbeat_epoch": 31,
            "task": {
                "task_id": "ESCALATE-SHWP-DURABLE-RUNTIME-ACTIVATION-test",
                "claim_id": "SHWP-ESCALATE-SHWP-DURABLE-RUNTIME-ACTIVATION-test-G21",
                "worker_id": "sovereign-node-repository-resolution-worker-v1",
                "worker_instance_id": "sovereign-node-repository-resolution-worker-v1-HB31-G21",
                "heartbeat_timing": {"fencing_token": 21},
            },
            "handoff": {
                "execution": {
                    "required_capabilities": ["repository_resolution", "sandbox_validation"],
                    "allowed_paths": ["receipts/sovereign-runtime-activation/**"],
                }
            },
            "scope": {
                "required_capabilities": ["repository_resolution", "sandbox_validation"],
                "allowed_paths": ["receipts/sovereign-runtime-activation/**"],
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

    def test_g18_adapter_passes_only_sovereign_runtime_declaration_environment(self) -> None:
        adapters = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text())
        adapter = next(
            row for row in adapters["adapters"]
            if row["adapter_ref"] == "process:sovereign-runtime-activation-v1"
        )
        allowlist = set(adapter["env_allowlist"])
        self.assertIn("STEGVERSE_SOVEREIGN_NODE", allowlist)
        self.assertIn("STEGVERSE_HEARTBEAT_ROOT", allowlist)
        self.assertNotIn("GITHUB_TOKEN", allowlist)
        self.assertNotIn("GH_TOKEN", allowlist)
        self.assertNotIn("ZEROEX_API_KEY", allowlist)
        self.assertNotIn("WALLET_PRIVATE_KEY", allowlist)

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

    def test_repository_resolution_worker_is_uniquely_profile_eligible(self) -> None:
        fragment = json.loads(
            (ROOT / "control" / "worker-registry.d" / "sovereign-node-repository-resolution-v1.json").read_text()
        )
        worker = fragment["workers"][0]
        self.assertEqual(worker["capabilities"], ["repository_resolution", "sandbox_validation"])
        self.assertEqual(
            worker["capability_profile_ref"],
            "control/worker-capability-profiles.json#sovereign-resolution-worker-v1",
        )
        profiles = json.loads((ROOT / "control" / "worker-capability-profiles.json").read_text())
        profile = next(
            row for row in profiles["profiles"]
            if row["profile_id"] == "sovereign-resolution-worker-v1"
        )
        self.assertEqual(
            set(profile["allowed_capabilities"]),
            {"repository_resolution", "sandbox_validation"},
        )
        adapters = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text())
        matching = [
            row for row in adapters["adapters"]
            if set(row.get("capabilities") or []) == {"repository_resolution", "sandbox_validation"}
            and row.get("enabled") is True
        ]
        self.assertEqual([row["adapter_ref"] for row in matching], ["process:sovereign-node-repository-resolution-v1"])

    def test_repository_resolver_escalates_without_node_and_completes_with_authorized_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(root / "home"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            blocked = subprocess.run(
                [sys.executable, str(RESOLVER)],
                cwd=tmp,
                input=json.dumps(self.resolver_invocation()) + "\n",
                text=True,
                capture_output=True,
                env=base_env,
                check=False,
            )
            self.assertEqual(blocked.returncode, 0, blocked.stderr)
            blocked_response = json.loads(blocked.stdout)
            self.assertEqual(blocked_response["state"], "BLOCKED")
            self.assertEqual(blocked_response["blocker"]["escalation_target"], "COMPONENT_AUTHORITY")
            self.assertNotIn("GITHUB_TOKEN", blocked.stdout)

            declared_env = dict(base_env)
            declared_env["STEGVERSE_SOVEREIGN_NODE"] = "1"
            completed = subprocess.run(
                [sys.executable, str(RESOLVER)],
                cwd=tmp,
                input=json.dumps(self.resolver_invocation()) + "\n",
                text=True,
                capture_output=True,
                env=declared_env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            completed_response = json.loads(completed.stdout)
            self.assertEqual(completed_response["state"], "COMPLETED")
            self.assertEqual(completed_response["transition_id"], "SOVEREIGN_NODE_DECLARATION_RESOLVED")


if __name__ == "__main__":
    unittest.main()
