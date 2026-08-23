from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_independent_orphan_recovery.py"
WORKER = ROOT / "workers" / "ecosystem_chat_orphan_recovery_worker.py"
spec = importlib.util.spec_from_file_location("independent_orphan_recovery_executor", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
worker_spec = importlib.util.spec_from_file_location("ecosystem_chat_orphan_recovery_worker", WORKER)
assert worker_spec and worker_spec.loader
worker_mod = importlib.util.module_from_spec(worker_spec)
worker_spec.loader.exec_module(worker_mod)


class IndependentOrphanRecoveryExecutorTests(unittest.TestCase):
    def load_registry(self) -> dict:
        return json.loads((ROOT / "control" / "worker-registry.json").read_text(encoding="utf-8"))

    def task(self, registry: dict, task_id: str) -> dict:
        return next(row for row in registry["tasks"] if row.get("task_id") == task_id)

    def test_completed_registry_fragment_prevents_reacquisition(self) -> None:
        fragment = json.loads((ROOT / mod.FRAGMENT_PATH).read_text(encoding="utf-8"))
        task = next(row for row in fragment["tasks"] if row.get("task_id") == mod.RECOVERY_ID)
        self.assertEqual(task["state"], "COMPLETED")
        self.assertIsNone(task["claim_id"])
        self.assertEqual(task["admission"]["claim_state"], "TERMINAL_COMPLETED_NO_REACQUISITION")
        self.assertEqual(task["completion"]["recovery_fencing_token"], 22)
        self.assertFalse(task["completion"]["successor_authority_granted"])
        with self.assertRaisesRegex(RuntimeError, "not HANDOFF_READY"):
            mod.validate_registered_executor(ROOT)

    def test_current_terminal_receipt_binds_g22_without_parent_authority(self) -> None:
        receipt = json.loads((ROOT / "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["recovery_fencing_token"], 22)
        self.assertGreater(receipt["recovery_fencing_token"], receipt["old_fencing_token"])
        self.assertTrue(receipt["checkpoint_valid"])
        self.assertTrue(receipt["master_records_custody_valid"])
        self.assertTrue(receipt["old_authority_ended"])
        self.assertFalse(receipt["old_authority_reused"])
        self.assertFalse(receipt["successor_authority_granted"])
        self.assertEqual(receipt["next_transition"], "SEPARATE_HIGHER_FENCE_PARENT_SUCCESSOR_AUTHORIZATION")
        self.assertFalse(receipt["github_token_required"])
        self.assertFalse(receipt["third_party_execution_platform_required"])
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_recovery_package_contains_canonical_non_authorizing_g20_custody(self) -> None:
        path, custody = worker_mod.find_lifecycle_custody()
        self.assertIsNotNone(path)
        self.assertIsNotNone(custody)
        assert custody is not None
        self.assertEqual(custody["schema"], "stegverse.worker_lifecycle_custody.v2")
        self.assertEqual(custody["custody_id"], "SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001")
        self.assertTrue(custody["claim"]["released"])
        self.assertEqual(custody["claim"]["fencing_token"], 20)
        self.assertEqual(custody["custody"]["status"], "ACCEPTED_FOR_CUSTODY")
        self.assertEqual(custody["custody"]["reconstruction_status"], "PASS")
        self.assertEqual(custody["custody"]["authority_effect"], "NONE")
        self.assertFalse(custody["github_token_required"])
        self.assertEqual(custody["authority_effect"], "NONE")
        self.assertEqual(worker_mod.canonical_master_records_ref(path), "master-records/orchestration:custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json")

    def test_missing_carrier_snapshot_is_not_an_execution_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epoch, observed = mod.current_reference_epoch(Path(tmp))
        self.assertEqual(epoch, 0)
        self.assertFalse(observed)

    def test_acquire_claim_uses_new_generation_without_parent_or_g18_dependency(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        before_parent = copy.deepcopy(self.task(registry, mod.PARENT_ID))
        existing_max = mod.max_projected_fence(registry)

        recovery, fence = mod.acquire_recovery_claim(ROOT, registry, reference_epoch=0)

        self.assertGreater(fence, 20)
        self.assertGreater(fence, existing_max)
        self.assertEqual(registry["generation"], fence)
        self.assertEqual(recovery["state"], "ACTIVE")
        self.assertEqual(recovery["worker_id"], mod.RECOVERY_WORKER_ID)
        self.assertTrue(recovery["claim_id"].endswith(f"-G{fence}"))
        self.assertEqual(recovery["heartbeat_timing"]["fencing_token"], fence)
        self.assertEqual(recovery["heartbeat_timing"]["start_epoch"], 0)
        self.assertTrue(recovery["independent_task_control"]["heartbeat_reference_only"])
        self.assertFalse(recovery["independent_task_control"]["heartbeat_granted_authority"])
        self.assertFalse(recovery["independent_task_control"]["g18_authority_used"])
        self.assertFalse(recovery["independent_task_control"]["g20_authority_reused"])
        self.assertFalse(recovery["independent_task_control"]["parent_authority_granted"])
        self.assertEqual(self.task(registry, mod.PARENT_ID), before_parent)

    def test_blocked_attempt_releases_claim_for_fresh_retry(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        recovery, fence = mod.acquire_recovery_claim(ROOT, registry, reference_epoch=0)
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
        mod.acquire_recovery_claim(ROOT, registry, reference_epoch=0)

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
