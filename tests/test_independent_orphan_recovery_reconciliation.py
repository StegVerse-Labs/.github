from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from heartbeat_runtime.orphan_recovery import (
    independent_orphan_recovery_contract_valid,
    reconcile_quarantined_orphan_recoveries,
)

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_ID = "RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"
PARENT_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"


class IndependentOrphanRecoveryReconciliationTests(unittest.TestCase):
    def load_registry(self) -> dict:
        return json.loads((ROOT / "control" / "worker-registry.json").read_text(encoding="utf-8"))

    def task(self, registry: dict, task_id: str) -> dict:
        return next(row for row in registry["tasks"] if row.get("task_id") == task_id)

    def test_current_authorized_recovery_contract_is_valid(self) -> None:
        registry = self.load_registry()
        recovery = self.task(registry, RECOVERY_ID)
        valid, reason = independent_orphan_recovery_contract_valid(ROOT, registry_task=recovery, registry=registry)
        self.assertTrue(valid, reason)
        self.assertEqual(reason, "AUTHORIZED_INDEPENDENT_ORPHAN_RECOVERY_CONTRACT_VALID")

    def test_blocked_existing_record_promotes_without_minting_authority(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        recovery = self.task(registry, RECOVERY_ID)
        parent = self.task(registry, PARENT_ID)
        self.assertEqual(recovery["state"], "BLOCKED")
        self.assertIsNone(recovery.get("claim_id"))
        self.assertIsNone(recovery.get("worker_id"))
        self.assertIsNone(parent.get("claim_id"))
        self.assertIsNone(parent.get("worker_id"))

        events: list[dict] = []
        changed = reconcile_quarantined_orphan_recoveries(
            ROOT,
            registry,
            epoch=31,
            event=lambda epoch, event_type, **payload: events.append({"epoch": epoch, "event_type": event_type, **payload}),
        )

        self.assertIn(RECOVERY_ID, changed)
        self.assertEqual(recovery["state"], "HANDOFF_READY")
        self.assertEqual(recovery["executor_binding"], "AUTHORIZED")
        self.assertIsNone(recovery.get("claim_id"))
        self.assertIsNone(recovery.get("worker_id"))
        self.assertIsNone(recovery.get("worker_instance_id"))
        self.assertIsNone(recovery.get("lease"))
        self.assertIsNone(recovery.get("heartbeat_timing"))
        self.assertIsNone(recovery.get("block_ref"))
        self.assertEqual(recovery["admission"]["minimum_fencing_token_exclusive"], 20)
        self.assertFalse(recovery["admission"]["heartbeat_grants_execution_authority"])
        self.assertFalse(recovery["admission"]["g18_terminalization_required"])
        self.assertEqual(parent["state"], "BLOCKED")
        self.assertIsNone(parent.get("claim_id"))
        self.assertIsNone(parent.get("worker_id"))
        self.assertTrue(any(e["event_type"] == "orphan_recovery_independent_admission_reconciled" for e in events))


if __name__ == "__main__":
    unittest.main()
