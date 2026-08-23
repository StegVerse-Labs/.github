from __future__ import annotations

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
        self.assertEqual(worker_mod.canonical_master_records_ref(path), "master-records/orchestration:custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json")

    def test_missing_carrier_snapshot_is_not_an_execution_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epoch, observed = mod.current_reference_epoch(Path(tmp))
        self.assertEqual(epoch, 0)
        self.assertFalse(observed)


if __name__ == "__main__":
    unittest.main()
