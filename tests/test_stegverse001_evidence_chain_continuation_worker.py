from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "stegverse001_evidence_chain_continuation_worker.py"
REGISTRY = ROOT / "control" / "worker-registry.d" / "stegverse001-evidence-chain-continuation-001.json"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "stegverse001-evidence-chain-continuation-001.json"
HANDOFF = ROOT / "handoffs" / "STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001.json"
RUNTIME_SOLUTIONS = ROOT / "data" / "runtime-solution-registry.d" / "hb32-existing-runtime-solutions.json"

spec = importlib.util.spec_from_file_location("sv001_chain_worker", WORKER)
assert spec and spec.loader
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)


class TestSv001EvidenceChainContinuationWorker(unittest.TestCase):
    def test_registered_worker_reuses_existing_runtime(self):
        registry = json.loads(REGISTRY.read_text())
        adapter = json.loads(ADAPTER.read_text())
        handoff = json.loads(HANDOFF.read_text())
        task = registry["tasks"][0]
        worker = registry["workers"][0]
        process = adapter["adapters"][0]

        self.assertEqual(task["task_id"], MOD.TASK_ID)
        self.assertEqual(worker["worker_id"], MOD.WORKER_ID)
        self.assertEqual(worker["adapter_ref"], process["adapter_ref"])
        self.assertEqual(task["handoff_ref"], "handoffs/STEGVERSE001-EVIDENCE-CHAIN-CONTINUATION-001.json")
        self.assertEqual(handoff["task"]["task_id"], MOD.TASK_ID)
        self.assertFalse(handoff["task"]["manual_execution_allowed"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])
        self.assertFalse(handoff["execution"]["requires_other_machine"])
        self.assertFalse(handoff["continuity"]["terminal_autonomy_reexecution_allowed"])

    def test_retryable_continuation_returns_handoff_ready(self):
        response = MOD.worker_response({
            "continuation_state": "MASTER_RECORDS_RECONSTRUCTION_PENDING",
            "continuation_result": {"retry_allowed": True},
            "local_receipt_ref": "receipts/latest.json",
        })
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertEqual(response["transition_id"], "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_PENDING")

    def test_pass_is_only_terminal_completion(self):
        response = MOD.worker_response({
            "continuation_state": "PASS",
            "continuation_result": {"retry_allowed": False},
            "local_receipt_ref": "receipts/latest.json",
        })
        self.assertEqual(response["state"], "COMPLETED")
        self.assertEqual(response["transition_id"], "STEGVERSE001_EVIDENCE_CHAIN_CONTINUATION_COMPLETE")

    def test_runtime_solution_registry_records_reuse(self):
        registry = json.loads(RUNTIME_SOLUTIONS.read_text())
        matches = [row for row in registry["solutions"] if row.get("problem_class") == "POST_TERMINAL_CONTINUATION_COUPLED_TO_PARENT_TASK_RETRY"]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertIn("workers/stegverse001_evidence_chain_continuation_worker.py", row["support"])
        self.assertIn("second-WorkerCoordinator", row["do_not_create"])
        self.assertIn("manual-human-approval-loop", row["do_not_create"])

    def test_worker_never_calls_parent_sv001_execution(self):
        source = WORKER.read_text()
        self.assertNotIn("refresh_and_execute_resident_task.py", source)
        self.assertNotIn("consume_stegverse001_bounded_autonomy_request.py", source)
        self.assertIn("continue_stegverse001_evidence_chain.py", source)
        self.assertIn('"sv001_reexecution_performed": False', source)


if __name__ == "__main__":
    unittest.main()
