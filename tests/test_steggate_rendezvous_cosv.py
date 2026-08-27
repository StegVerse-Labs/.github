from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGGATE-STABLE-RENDEZVOUS-WORKER-001"
VECTOR_REF = f"control/task-vectors/{TASK_ID}.json"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class StegGateRendezvousCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / VECTOR_REF).read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "control/worker-registry.json").read_text(encoding="utf-8"))
        self.task = next(x for x in registry["tasks"] if x["task_id"] == TASK_ID)
        self.receipt = json.loads((ROOT / "receipts/steggate-rendezvous-worker/STEGGATE-STABLE-RENDEZVOUS-WORKER-001.json").read_text(encoding="utf-8"))
        self.handoff = json.loads((ROOT / "handoffs/STEGGATE-STABLE-RENDEZVOUS-WORKER-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_exact_metrics(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), self.record["vector"])
        self.assertEqual(self.record["vector"], "50000000100000")

    def test_third_party_workaround_is_not_counted_as_blocker(self):
        self.assertFalse(self.receipt["third_party_dependency_is_blocker"])
        self.assertFalse(self.receipt["blocker"]["may_remain_blocked"])
        self.assertIsNone(self.handoff["block"])
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], 0)

    def test_live_incomplete_state_is_not_promoted(self):
        m=self.record["exact_metrics"]
        self.assertEqual(self.task["state"], "ACTIVE")
        self.assertEqual(self.receipt["state"], "ACTIVE")
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])

    def test_binding_is_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
