from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SV-DN1-RESIDENT-OBSERVER-001"
VECTOR_REF = f"control/task-vectors/{TASK_ID}.json"
SOURCE_BASIS = "4988d453419f43404100c69dd97dd1785d7e0a75"
PRODUCT_RECONCILIATION = "StegVerse-org/stegverse-demo-suite#21@a71b1263018cd5c7bba73b7182474c43a34c95bc"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class SVDN1ResidentObserverCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / VECTOR_REF).read_text(encoding="utf-8"))
        fragment = json.loads(
            (ROOT / "control/worker-registry.d/sv-dn1-resident-observer-001.json").read_text(encoding="utf-8")
        )
        self.task = fragment["tasks"][0]
        self.handoff = json.loads(
            (ROOT / "handoffs/SV-DN1-RESIDENT-OBSERVER-001.json").read_text(encoding="utf-8")
        )
        self.index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        self.coverage = json.loads(
            (ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8")
        )

    def test_vector_recomputes_from_three_exact_blockers(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), self.record["vector"])
        self.assertEqual(self.record["vector"], "50000000103000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], 3)
        self.assertEqual(
            self.task["admissible_existence"]["blockers"],
            self.handoff["admissible_existence"]["blockers"],
        )

    def test_product_scope_and_source_pin_are_reconciled(self):
        self.assertEqual(
            self.handoff["task"]["canonical_product_task_reconciliation_ref"],
            PRODUCT_RECONCILIATION,
        )
        self.assertEqual(
            self.handoff["input_contract"]["source_identity"]["source_basis_commit"],
            SOURCE_BASIS,
        )
        self.assertEqual(
            self.handoff["admissible_existence"]["blockers"],
            [
                "EXACT_PINNED_LOCAL_DEMO_SUITE_SOURCE_NOT_YET_OBSERVED",
                "CANONICAL_SCHEDULER_CLAIM_NOT_YET_BOUND",
                "SOVEREIGN_SV_DN1_RESIDENT_SOURCE_CAPTURE_RECEIPT_NOT_YET_OBSERVED",
            ],
        )

    def test_index_and_coverage_replace_conflict_with_vector(self):
        indexed = {x["task_id"]: x for x in self.index["tasks"]}
        self.assertIn(TASK_ID, indexed)
        self.assertEqual(indexed[TASK_ID]["vector"], "50000000103000")
        self.assertNotIn(TASK_ID, self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertNotIn("sv_dn1_resident_observer_conflict", self.coverage)
        reconciliation = self.coverage["sv_dn1_resident_observer_reconciliation"]
        self.assertTrue(reconciliation["local_blocker_parity"])
        self.assertEqual(reconciliation["product_owner_pr"], 21)
        self.assertFalse(reconciliation["runtime_receipt_observed"])

    def test_reconciliation_does_not_promote_runtime_or_authority(self):
        m = self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        self.assertFalse(self.handoff["task"]["manual_execution_allowed"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        self.assertFalse(self.handoff["authority"]["provider_credential_authority"])
        self.assertFalse(self.handoff["authority"]["sdk_admission_authority"])
        self.assertFalse(self.handoff["authority"]["publication_authority"])
        self.assertEqual(self.record["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
