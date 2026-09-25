"""Source-only regression for KV/SDK authority/identity reconciliation.

This is non-authorizing documentation validation. It never accesses a provider
or treats a locally generated custody proposal as native Master Records proof.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/KV_SDK_MANIFEST_RUNTIME_OWNER_RECONCILIATION_MIRROR_HANDOFF.md"
VECTOR = ROOT / "control/task-vectors/KV-CONNECTION-REVALIDATION-WORKER-001.json"
TASK = ROOT / "handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json"


class KVSDKOwnerReconciliationTests(unittest.TestCase):
    def test_existing_goal_owner_and_cosv_not_reminted(self) -> None:
        vector = json.loads(VECTOR.read_text(encoding="utf-8"))
        task = json.loads(TASK.read_text(encoding="utf-8"))
        self.assertEqual(vector["vector"], "50000000102000")
        self.assertEqual(task["task"]["task_id"], "KV-CONNECTION-REVALIDATION-WORKER-001")
        self.assertIn("continuity-vault-kit#119", task["task"]["canonical_owner_ref"])
        self.assertEqual(task["goal"]["successor_policy"], "INHERIT_OR_NARROW")

    def test_source_handoff_does_not_promote_custody_or_provider_execution(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")
        for required in (
            "No authentic A-D runtime closure",
            "MASTER_RECORDS_CUSTODY_RECORDED",
            "without consuming an independently authoritative Master Records acceptance result",
            "Healer's scheduler/checkpoint",
            "SITE-CLOUD-KV-4347408852127319cbda574f02e03edb",
            "kvi_a31335d2cc3745fa987b635432cfed2c",
            "kvi_0d5d4cfd531db51bbcf7fdfc0311f5dc",
            "KV-CONNECTION-REVALIDATION-WORKER-001:TVC-CAPABILITY-RUNTIME-002:QUERY-SECRET-SAFE-INGRESS-001",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
