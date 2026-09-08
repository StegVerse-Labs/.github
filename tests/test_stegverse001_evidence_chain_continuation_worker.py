from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "stegverse001_evidence_chain_continuation_worker.py"
CONTINUATION = ROOT / "scripts" / "continue_stegverse001_evidence_chain.py"
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
        self.assertIn("observed/**", process["bound_state_allowed_paths"])
        self.assertTrue(MOD.SITE_PROOF_REL.as_posix().startswith("observed/"))

    def test_retryable_continuation_returns_handoff_ready(self):
        response = MOD.worker_response({
            "continuation_state": "SITE_GOVERNED_CUSTODY_PENDING",
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

    def test_continuation_never_mutates_master_records_without_site_governance(self):
        source = CONTINUATION.read_text()
        self.assertNotIn("watch_stegverse001_autonomy_receipt.py", source)
        self.assertNotIn("import_stegverse001_autonomy_receipt.py", source)
        self.assertIn("SITE_GOVERNED_CUSTODY_PENDING", source)
        self.assertIn("StegOSWebBootstrap.executeMasterRecordsSv001Custody", source)
        self.assertIn('"master_records_mutation_performed":False', source)

    def test_governed_site_proof_requires_intr_and_reconstruction(self):
        source = CONTINUATION.read_text()
        self.assertIn('"intr_governance_admission_observed":True', source)
        self.assertIn('"reconstruction_state":"PASS"', source)
        self.assertIn('"prior_receipt_authorizes_transition":False', source)
        self.assertIn('"historical_state_retroactively_authorized":False', source)

    def test_worker_can_materialize_non_authorizing_site_proof_evidence(self):
        proof = {
            "schema": MOD.SITE_PROOF_SCHEMA,
            "state": "PASS",
            "execution_surface": "CURRENT_USER_IPHONE",
        }
        with tempfile.TemporaryDirectory() as tmp:
            target = MOD.materialize_invocation_evidence(
                {"evidence": {"site_governed_custody_proof": proof}}, Path(tmp)
            )
            self.assertIsNotNone(target)
            assert target is not None
            self.assertEqual(json.loads(target.read_text()), proof)
            self.assertEqual(target.relative_to(Path(tmp)).as_posix(), MOD.SITE_PROOF_REL.as_posix())
            self.assertTrue(target.relative_to(Path(tmp)).as_posix().startswith("observed/"))

    def test_worker_reuses_existing_observed_site_proof_when_invocation_has_none(self):
        proof = {"schema": MOD.SITE_PROOF_SCHEMA, "state": "PASS"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / MOD.SITE_PROOF_REL
            existing.parent.mkdir(parents=True, exist_ok=True)
            existing.write_text(json.dumps(proof))
            target = MOD.materialize_invocation_evidence({}, root)
            self.assertEqual(target, existing)

    def test_worker_rejects_non_site_proof_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "schema mismatch"):
                MOD.materialize_invocation_evidence(
                    {"evidence": {"site_governed_custody_proof": {"schema": "wrong"}}},
                    Path(tmp),
                )

    def test_site_proof_transport_does_not_create_authority(self):
        source = WORKER.read_text()
        self.assertIn("NONE_EVIDENCE_ONLY", source)
        self.assertIn("site_governed_custody_proof", source)
        self.assertNotIn("browser_claim", source)
        self.assertNotIn("browser_fence", source)


if __name__ == "__main__":
    unittest.main()
