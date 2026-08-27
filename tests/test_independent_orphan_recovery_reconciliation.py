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


class IndependentOrphanRecoveryReconciliationTests(unittest.TestCase):
    def load_registry(self) -> dict:
        return json.loads((ROOT / "control" / "worker-registry.json").read_text(encoding="utf-8"))

    def task(self, registry: dict, task_id: str) -> dict:
        return next(row for row in registry["tasks"] if row.get("task_id") == task_id)

    def test_current_terminal_recovery_contract_is_not_reclaimable(self) -> None:
        registry = self.load_registry()
        recovery = self.task(registry, RECOVERY_ID)
        fragment = json.loads((ROOT / "control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json").read_text(encoding="utf-8"))
        terminal = fragment["tasks"][0]
        self.assertEqual(recovery, terminal)
        self.assertEqual(recovery["state"], "COMPLETED")
        self.assertTrue(recovery["archive_eligible"])
        self.assertEqual(recovery["admission"]["claim_state"], "TERMINAL_COMPLETED_NO_REACQUISITION")
        valid, reason = independent_orphan_recovery_contract_valid(ROOT, registry_task=recovery, registry=registry)
        self.assertFalse(valid)
        self.assertEqual(reason, "RECOVERY_HANDOFF_NOT_READY")
        receipt = json.loads((ROOT / "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["recovery_fencing_token"], 22)
        self.assertFalse(receipt["successor_authority_granted"])

    def test_terminal_fragment_is_not_promoted_or_reclaimed(self) -> None:
        registry = copy.deepcopy(self.load_registry())
        fragment = json.loads((ROOT / "control/worker-registry.d/ecosystem-chat-orphan-recovery-hb28.json").read_text(encoding="utf-8"))
        terminal = fragment["tasks"][0]
        recovery = self.task(registry, RECOVERY_ID)
        recovery.clear()
        recovery.update(copy.deepcopy(terminal))

        events: list[dict] = []
        changed = reconcile_quarantined_orphan_recoveries(
            ROOT,
            registry,
            epoch=31,
            event=lambda epoch, event_type, **payload: events.append({"epoch": epoch, "event_type": event_type, **payload}),
        )

        self.assertNotIn(RECOVERY_ID, changed)
        self.assertEqual(recovery["state"], "COMPLETED")
        self.assertIsNone(recovery.get("claim_id"))
        self.assertIsNone(recovery.get("worker_id"))
        self.assertEqual(recovery["admission"]["claim_state"], "TERMINAL_COMPLETED_NO_REACQUISITION")
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
