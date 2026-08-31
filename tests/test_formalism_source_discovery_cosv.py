from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-FORMALISM-SOURCE-DISCOVERY-001"
VECTOR_REF = f"control/task-vectors/{TASK_ID}.json"
CLAIM_REF = "control/session-implementation-claim-2026-08-13-formalism-source-discovery.json"

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class FormalismSourceDiscoveryCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / VECTOR_REF).read_text(encoding="utf-8"))
        fragment = json.loads((ROOT / "control/worker-registry.d/formalism-source-discovery-001.json").read_text(encoding="utf-8"))
        self.task = next(x for x in fragment["tasks"] if x["task_id"] == TASK_ID)
        self.handoff = json.loads((ROOT / "handoffs/SHWP-FORMALISM-SOURCE-DISCOVERY-001.json").read_text(encoding="utf-8"))
        self.claim = json.loads((ROOT / CLAIM_REF).read_text(encoding="utf-8"))
        self.coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_with_zero_registered_blockers(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), "50000000100000")
        self.assertEqual(self.record["vector"], "50000000100000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], 0)
        self.assertIsNone(self.task["block_ref"])
        self.assertIsNone(self.handoff["block"])

    def test_stale_implementation_claim_is_released_to_machine_continuation(self):
        self.assertEqual(self.claim["claim_state"], "RELEASED_TRANSFERRED_TO_MACHINE_CONTINUATION")
        ev = self.claim["release_evidence"]
        self.assertEqual(ev["pull_request"], 103)
        self.assertEqual(ev["merged_head"], "00ead9d14a44be827c4110f3866556402a2d899b")
        self.assertEqual(ev["merge_commit"], "5a5c77d45817407dc0b2f5010ba56a36ecdd5d5e")
        self.assertFalse(ev["resident_discovery_receipt_observed"])
        self.assertFalse(ev["missing_source_absence_set_observed"])
        self.assertFalse(ev["generalized_owner_mutation_deficiency_transferred_here"])
        self.assertFalse(self.claim["archive_dependency"])

    def test_release_does_not_promote_resident_activation_or_owner_mutation(self):
        m = self.record["exact_metrics"]
        self.assertFalse(m["thread_required"])
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        reconciliation = self.coverage["formalism_source_discovery_reconciliation"]
        self.assertFalse(reconciliation["resident_discovery_receipt_observed"])
        self.assertFalse(reconciliation["generalized_owner_mutation_deficiency_resolved"])
        self.assertEqual(reconciliation["registered_blocker_count"], 0)
        self.assertIn("no_source_mutation", self.handoff["goal"]["authority_ceiling"])
        self.assertIn("no_network_checkout", self.handoff["goal"]["authority_ceiling"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])

    def test_index_and_coverage_advance_exactly_one_task(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        indexed = {x["task_id"]: x for x in index["tasks"]}
        self.assertEqual(indexed[TASK_ID]["vector"], "50000000100000")
        self.assertEqual(self.task["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"], VECTOR_REF)
        self.assertNotIn(TASK_ID, self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertEqual(index["coverage"]["indexed_vectorized_tasks"], len(index["tasks"]))
        worker_indexed = [row for row in index["tasks"] if row.get("registry_ref") != "control/organization-task-registry.json"]
        self.assertEqual(
            self.coverage["worker_registry_summary"]["canonically_indexed_task_ids"],
            len(worker_indexed),
        )
        self.assertGreaterEqual(len(index["tasks"]), 31)
        worker_gap = self.coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"]
        self.assertEqual(worker_gap, len(self.coverage["active_worker_task_ids_missing_canonical_cosv"]))
        org_gap = self.coverage["organization_registry_summary"]["active_unvectorized_task_ids"]
        self.assertEqual(
            self.coverage["total_active_unvectorized_unique_task_ids"],
            worker_gap + org_gap,
        )


if __name__ == "__main__":
    unittest.main()
