from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.admitted_worker_runtime import WorkerCoordinator


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def handoff(policy: str) -> dict:
    return {
        "schema": "stegverse.executable-handoff/v0.1",
        "task": {"task_id": "TEST-001"},
        "authority": {"policy_version": policy},
    }


def fragment(policy: str) -> dict:
    return {
        "schema": "stegverse.worker-registry-fragment/v0.1",
        "fragment_id": "TEST-001",
        "tasks": [
            {
                "task_id": "TEST-001",
                "goal_id": "TEST-GOAL",
                "state": "HANDOFF_READY",
                "handoff_ref": "handoffs/TEST-001.json",
                "authorized_policy_version": policy,
                "claim_id": None,
                "worker_id": None,
                "worker_instance_id": None,
                "heartbeat_timing": None,
                "assignment_timer": None,
                "lease": None,
            }
        ],
        "workers": [],
        "authority_effect": "NONE_REGISTRATION_ONLY",
        "github_token_required": False,
    }


class PreclaimFragmentPolicyReconciliationTests(unittest.TestCase):
    def test_unclaimed_handoff_ready_policy_drift_reconciles_to_canonical_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "handoffs/TEST-001.json", handoff("policy-v2"))
            write(root / "control/worker-registry.d/test.json", fragment("policy-v2"))
            registry = {
                "schema": "stegverse.heartbeat-worker-registry/v0.1",
                "generation": 9,
                "tasks": [
                    {
                        "task_id": "TEST-001",
                        "goal_id": "TEST-GOAL",
                        "state": "HANDOFF_READY",
                        "handoff_ref": "handoffs/TEST-001.json",
                        "authorized_policy_version": "policy-v1",
                        "claim_id": None,
                        "worker_id": None,
                        "worker_instance_id": None,
                        "heartbeat_timing": None,
                        "assignment_timer": None,
                        "lease": None,
                    }
                ],
                "workers": [],
            }
            runtime = WorkerCoordinator(root)
            applied = runtime._apply_registry_fragments(registry, task_id_filter="TEST-001")
            task = registry["tasks"][0]
            self.assertEqual(task["authorized_policy_version"], "policy-v2")
            self.assertEqual(task["preclaim_policy_reconciliation"]["old_policy_version"], "policy-v1")
            self.assertEqual(task["preclaim_policy_reconciliation"]["new_policy_version"], "policy-v2")
            self.assertFalse(task["preclaim_policy_reconciliation"]["claim_authority_effect"])
            self.assertFalse(task["preclaim_policy_reconciliation"]["fence_authority_effect"])
            self.assertFalse(task["preclaim_policy_reconciliation"]["execution_authority_effect"])
            self.assertEqual(registry["generation"], 10)
            self.assertEqual(applied, ["control/worker-registry.d/test.json"])

    def test_claimed_or_timed_task_is_never_reconciled_from_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "handoffs/TEST-001.json", handoff("policy-v2"))
            write(root / "control/worker-registry.d/test.json", fragment("policy-v2"))
            registry = {
                "schema": "stegverse.heartbeat-worker-registry/v0.1",
                "generation": 9,
                "tasks": [
                    {
                        "task_id": "TEST-001",
                        "goal_id": "TEST-GOAL",
                        "state": "ACTIVE",
                        "handoff_ref": "handoffs/TEST-001.json",
                        "authorized_policy_version": "policy-v1",
                        "claim_id": "claim-1",
                        "worker_id": "worker-1",
                        "worker_instance_id": "instance-1",
                        "heartbeat_timing": {"fencing_token": 42},
                        "assignment_timer": {"fencing_token": 42},
                        "lease": {"fencing_token": 42},
                    }
                ],
                "workers": [],
            }
            runtime = WorkerCoordinator(root)
            applied = runtime._apply_registry_fragments(registry, task_id_filter="TEST-001")
            task = registry["tasks"][0]
            self.assertEqual(task["authorized_policy_version"], "policy-v1")
            self.assertNotIn("preclaim_policy_reconciliation", task)
            self.assertEqual(registry["generation"], 9)
            self.assertEqual(applied, [])

    def test_fragment_policy_must_match_canonical_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "handoffs/TEST-001.json", handoff("policy-v3"))
            write(root / "control/worker-registry.d/test.json", fragment("policy-v2"))
            registry = {
                "schema": "stegverse.heartbeat-worker-registry/v0.1",
                "generation": 9,
                "tasks": [
                    {
                        "task_id": "TEST-001",
                        "goal_id": "TEST-GOAL",
                        "state": "HANDOFF_READY",
                        "handoff_ref": "handoffs/TEST-001.json",
                        "authorized_policy_version": "policy-v1",
                        "claim_id": None,
                        "worker_id": None,
                        "worker_instance_id": None,
                        "heartbeat_timing": None,
                        "assignment_timer": None,
                        "lease": None,
                    }
                ],
                "workers": [],
            }
            runtime = WorkerCoordinator(root)
            with self.assertRaisesRegex(RuntimeError, "preclaim policy reconciliation mismatch"):
                runtime._apply_registry_fragments(registry, task_id_filter="TEST-001")


if __name__ == "__main__":
    unittest.main()
