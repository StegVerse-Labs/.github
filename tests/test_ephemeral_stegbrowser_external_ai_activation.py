"""Source/ownership contract only: no runtime, credential, provider-call or publication proof."""
import json
import unittest
from pathlib import Path
from scripts.cosv import encode_task, validate_record

ROOT = Path(__file__).resolve().parents[1]
TASK = "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001"
PARENT = "ECOSYSTEM-ECONOMIC-WHITEPAPER-GATED-ROADMAP-001"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class EphemeralExternalAITaskTests(unittest.TestCase):
    def test_single_canonical_owner_and_no_mykv_dependency(self):
        reg = load("data/canonical-task-registry.json")
        task = load("data/canonical-task-records/" + TASK + ".json")
        matching = [t for t in reg["tasks"] if t["task_id"] == TASK]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0], task)
        self.assertEqual(task["parent_task_id"], PARENT)
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertEqual(task["worker_claim"]["authority"], "WORKERCOORDINATOR")
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertFalse(task["completion"]["claimed"])
        self.assertFalse(task["completion"]["validated"])
        self.assertEqual(len(task["blockers"]), 3)
        self.assertIn("STEG-BROWSER-IMMUTABLE-NONCE-A3-RESULT-OBSERVATION-001", task["adjacent_task_refs"])
        self.assertEqual(next(d for d in task["dependencies"] if d["dependency_id"] == "PRIVATE_NATIVE_MYKV")["state"], "NOT_APPLICABLE")
        self.assertFalse(task["runtime_requirements"]["deployment_required"])

    def test_cosv_is_exact_source_derived_non_authorizing(self):
        task = load("data/canonical-task-records/" + TASK + ".json")
        c = load("control/task-vectors/" + TASK + ".json")
        self.assertTrue(validate_record(c))
        self.assertEqual(c["exact_metrics"]["blocker_count"], len(task["blockers"]))
        self.assertEqual(c["vector"], encode_task(c["exact_metrics"]))
        self.assertEqual(c["vector"], "10100000103000")
        self.assertEqual(c["authority_effect"], "NONE")
        for flag in ("evidence_complete", "activated", "propagated"):
            self.assertFalse(c["exact_metrics"][flag])

    def test_complete_index_and_canonical_shard(self):
        idx = load("control/task-vector-index.json")
        shard = load("control/task-vector-index.d/" + TASK + ".json")
        rows = [r for r in idx["tasks"] if r["task_id"] == TASK]
        self.assertEqual(len(rows), 1)
        for k in ("registry_ref", "source_state_vector_ref", "vector", "authority_effect"):
            self.assertEqual(rows[0][k], shard[k])
        self.assertEqual(idx["coverage"]["indexed_vectorized_tasks"], len(idx["tasks"]))
        self.assertEqual(idx["coverage"]["local_cosv_record_tasks"] + idx["coverage"]["external_owner_projection_tasks"], len(idx["tasks"]))

    def test_no_synthetic_provider_proof_or_second_device(self):
        task = load("data/canonical-task-records/" + TASK + ".json")
        evidence = " ".join(task["expected_evidence_predicates"])
        self.assertIn("REAL_OPENAI_PROVIDER_RESPONSE", evidence)
        self.assertIn("INDEPENDENT_ANTHROPIC_CLAUDE", evidence)
        self.assertIn("TERMINAL_BROWSER_SESSION_DESTRUCTION", evidence)
        self.assertIn("MASTER_RECORDS_RECORDED_PASS", evidence)
        self.assertIn("NO_NEW_RUNTIME_SCHEDULER_DISPATCHER", evidence)
        self.assertTrue(all(x["state"] != "RESOLVED" for x in task["dependencies"] if x["kind"] == "RUNTIME_PREDICATE"))


if __name__ == "__main__":
    unittest.main()
