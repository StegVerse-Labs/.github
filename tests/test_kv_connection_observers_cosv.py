from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "KV-CONNECTION-HEALTH-RECONCILER-001": {
        "fragment": "control/worker-registry.d/kv-connection-health-reconciler-001.json",
        "handoff": "handoffs/KV-CONNECTION-HEALTH-RECONCILER-001.json",
        "blockers": [
            "SOVEREIGN_RUNTIME_NOT_YET_LIVE_PROVEN",
            "PRIVATE_KV_RUNTIME_BINDINGS_NOT_YET_OBSERVED",
        ],
    },
    "KV-PROVIDER-CHANGE-OBSERVER-001": {
        "fragment": "control/worker-registry.d/kv-provider-change-observer-001.json",
        "handoff": "handoffs/KV-PROVIDER-CHANGE-OBSERVER-001.json",
        "blockers": [
            "SOVEREIGN_RUNTIME_NOT_YET_LIVE_PROVEN",
            "LIVE_KV_MONITOR_TARGET_BINDING_NOT_YET_OBSERVED",
        ],
    },
}

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class KVConnectionObserverCOSVTests(unittest.TestCase):
    def load(self, task_id):
        cfg = TASKS[task_id]
        record = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text(encoding="utf-8"))
        fragment = json.loads((ROOT / cfg["fragment"]).read_text(encoding="utf-8"))
        task = next(x for x in fragment["tasks"] if x["task_id"] == task_id)
        handoff = json.loads((ROOT / cfg["handoff"]).read_text(encoding="utf-8"))
        return cfg, record, task, handoff

    def test_both_vectors_recompute_from_exact_two_blocker_contracts(self):
        for task_id in TASKS:
            cfg, record, task, handoff = self.load(task_id)
            self.assertTrue(cosv.validate_record(record), task_id)
            self.assertEqual(cosv.encode_task(record["exact_metrics"]), "50000000102000", task_id)
            self.assertEqual(record["vector"], "50000000102000", task_id)
            self.assertEqual(record["exact_metrics"]["blocker_count"], 2, task_id)
            self.assertEqual(task["admissible_existence"]["blockers"], cfg["blockers"], task_id)
            self.assertEqual(handoff["admissible_existence"]["blockers"], cfg["blockers"], task_id)

    def test_source_bindings_and_index_coverage_are_canonical(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        indexed = {x["task_id"]: x for x in index["tasks"]}
        for task_id in TASKS:
            cfg, record, task, handoff = self.load(task_id)
            ref = f"control/task-vectors/{task_id}.json"
            self.assertEqual(task["source_state_vector_ref"], ref)
            self.assertEqual(handoff["source_state_vector_ref"], ref)
            self.assertEqual(indexed[task_id]["vector"], "50000000102000")
            self.assertNotIn(task_id, coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertEqual(index["coverage"]["indexed_vectorized_tasks"], len(index["tasks"]))
        worker_indexed = [row for row in index["tasks"] if row.get("registry_ref") != "control/organization-task-registry.json"]
        self.assertEqual(
            coverage["worker_registry_summary"]["canonically_indexed_task_ids"],
            len(worker_indexed),
        )
        self.assertGreaterEqual(len(index["tasks"]), 30)
        worker_gap = coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"]
        self.assertEqual(worker_gap, len(coverage["active_worker_task_ids_missing_canonical_cosv"]))
        org_gap = coverage["organization_registry_summary"]["active_unvectorized_task_ids"]
        self.assertEqual(
            coverage["total_active_unvectorized_unique_task_ids"],
            worker_gap + org_gap,
        )

    def test_health_reconciler_cannot_promote_connection_verification_or_provider_authority(self):
        _, record, task, handoff = self.load("KV-CONNECTION-HEALTH-RECONCILER-001")
        self.assertFalse(handoff["completion"]["runtime_activation_claimed"])
        self.assertEqual(handoff["authority"]["provider_operation_authority"], "NONE")
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(handoff["authority"]["github_token_runtime_authority"], "NONE")
        self.assertIn("no connection verification authority", handoff["goal"]["authority_ceiling"])
        self.assertFalse(record["exact_metrics"]["evidence_complete"])
        self.assertFalse(record["exact_metrics"]["activated"])
        self.assertFalse(record["exact_metrics"]["propagated"])
        self.assertIsNone(task["admissible_existence"]["activation_proof_ref"])

    def test_provider_observer_cannot_use_credentials_or_mutate_provider(self):
        _, record, task, handoff = self.load("KV-PROVIDER-CHANGE-OBSERVER-001")
        self.assertFalse(handoff["completion"]["runtime_activation_claimed"])
        self.assertEqual(handoff["authority"]["provider_operation_authority"], "NONE")
        self.assertFalse(handoff["authority"]["non_tv_tvc_secret_or_token_allowed"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(handoff["authority"]["github_token_runtime_authority"], "NONE")
        self.assertIn("no provider mutation", handoff["goal"]["authority_ceiling"])
        self.assertIn("no credential resolution", handoff["goal"]["authority_ceiling"])
        self.assertFalse(record["exact_metrics"]["evidence_complete"])
        self.assertFalse(record["exact_metrics"]["activated"])
        self.assertFalse(record["exact_metrics"]["propagated"])
        self.assertIsNone(task["admissible_existence"]["activation_proof_ref"])

    def test_owner_reconciliation_is_recorded_without_runtime_promotion(self):
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        owner = coverage["kv_connection_owner_reconciliation"]
        self.assertEqual(owner["reconciliation_merge"], "d0c966d557dc437d1d2e6da5b68e6c31912af501")
        self.assertEqual(owner["source_state"], "MERGED_VALIDATED")
        self.assertFalse(owner["runtime_activation_claimed"])
        self.assertEqual(owner["provider_operation_authority"], "NONE")
        self.assertEqual(owner["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
