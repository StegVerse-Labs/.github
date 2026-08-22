from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_independent_orphan_recovery.py"
spec = importlib.util.spec_from_file_location("independent_orphan_recovery_executor", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class IndependentOrphanRecoveryExecutorTests(unittest.TestCase):
    def load_registry(self) -> dict:
        return json.loads((ROOT / "control" / "worker-registry.json").read_text(encoding="utf-8"))

    def task(self, registry: dict, task_id: str) -> dict:
        return next(row for row in registry["tasks"] if row.get("task_id") == task_id)

    def test_registered_executor_is_independent_and_available(self) -> None:
        mod.validate_registered_executor(ROOT)

    def test_acquire_claim_uses_new_generation_without_parent_or_g18_dependency(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        before_parent = copy.deepcopy(self.task(registry, mod.PARENT_ID))
        existing_max = mod.max_projected_fence(registry)

        recovery, fence = mod.acquire_recovery_claim(ROOT, registry, reference_epoch=31)

        self.assertGreater(fence, 20)
        self.assertGreater(fence, existing_max)
        self.assertEqual(registry["generation"], fence)
        self.assertEqual(recovery["state"], "ACTIVE")
        self.assertEqual(recovery["worker_id"], mod.RECOVERY_WORKER_ID)
        self.assertTrue(recovery["claim_id"].endswith(f"-G{fence}"))
        self.assertEqual(recovery["heartbeat_timing"]["fencing_token"], fence)
        self.assertTrue(recovery["independent_task_control"]["heartbeat_reference_only"])
        self.assertFalse(recovery["independent_task_control"]["heartbeat_granted_authority"])
        self.assertFalse(recovery["independent_task_control"]["g18_authority_used"])
        self.assertFalse(recovery["independent_task_control"]["g20_authority_reused"])
        self.assertFalse(recovery["independent_task_control"]["parent_authority_granted"])
        self.assertEqual(self.task(registry, mod.PARENT_ID), before_parent)

    def test_blocked_attempt_releases_claim_for_fresh_retry(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        recovery, fence = mod.acquire_recovery_claim(ROOT, registry, reference_epoch=31)
        claim = recovery["claim_id"]

        released = mod.release_recovery_claim(
            registry,
            response_state="BLOCKED",
            transition_id="MASTER_RECORDS_CUSTODY_NOT_PROVEN",
            transition_sequence=1,
            evidence_refs=["receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json"],
        )

        self.assertEqual(released["state"], "BLOCKED")
        self.assertIsNone(released["claim_id"])
        self.assertIsNone(released["worker_id"])
        self.assertIsNone(released["worker_instance_id"])
        self.assertIsNone(released["heartbeat_timing"])
        self.assertEqual(released["executor_binding"], "AUTHORIZED")
        self.assertEqual(released["independent_task_control"]["last_released_claim_id"], claim)
        self.assertEqual(released["independent_task_control"]["last_released_fencing_token"], fence)
        self.assertFalse(released["independent_task_control"]["parent_authority_granted"])

    def test_completed_attempt_releases_recovery_authority_without_minting_parent_authority(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        before_parent = copy.deepcopy(self.task(registry, mod.PARENT_ID))
        mod.acquire_recovery_claim(ROOT, registry, reference_epoch=31)

        released = mod.release_recovery_claim(
            registry,
            response_state="COMPLETED",
            transition_id="ORPHAN_LIFECYCLE_RECONSTRUCTED",
            transition_sequence=1,
            evidence_refs=["receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json"],
        )

        self.assertEqual(released["state"], "COMPLETED")
        self.assertIsNone(released["claim_id"])
        self.assertIsNone(released["worker_id"])
        self.assertFalse(released["independent_task_control"]["parent_authority_granted"])
        self.assertEqual(self.task(registry, mod.PARENT_ID), before_parent)


if __name__ == "__main__":
    unittest.main()
