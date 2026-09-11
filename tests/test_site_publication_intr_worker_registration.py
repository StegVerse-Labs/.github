from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SITE-PUBLICATION-INTR-CONSUMER-001"


class SitePublicationWorkerRegistrationTests(unittest.TestCase):
    def test_registration_requires_fresh_independent_fence_without_preclaim(self) -> None:
        registry = json.loads((ROOT / "control/worker-registry.d/site-publication-intr-consumer-001.json").read_text())
        adapter = json.loads((ROOT / "control/process-worker-adapters.d/site-publication-intr-consumer-001.json").read_text())
        handoff = json.loads((ROOT / "handoffs/SITE-PUBLICATION-INTR-CONSUMER-001.json").read_text())
        vector = json.loads((ROOT / "control/task-vectors/SITE-PUBLICATION-INTR-CONSUMER-001.json").read_text())
        task = registry["tasks"][0]
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertIsNone(task["claim_id"])
        self.assertIsNone(task["heartbeat_timing"])
        self.assertIsNone(task["lease"])
        self.assertEqual(task["admission"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertTrue(task["admission"]["fresh_fence_required"])
        self.assertFalse(task["admission"]["heartbeat_grants_execution_authority"])
        self.assertFalse(task["admission"]["event_materialization_grants_authority"])
        self.assertEqual(registry["authority_effect"], "NONE_REGISTRATION_ONLY")
        self.assertEqual(adapter["adapters"][0]["command"], ["python", "workers/site_publication_intr_consumer_worker.py"])
        self.assertEqual(adapter["adapters"][0]["env_allowlist"], ["STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID"])
        self.assertEqual(handoff["state"], "HANDOFF_READY")
        self.assertIsNone(handoff["task"]["fencing_token"])
        self.assertFalse(handoff["completion"]["runtime_observation_claimed"])
        self.assertFalse(handoff["completion"]["final_publication_transition_admitted"])
        self.assertEqual(vector["vector"], "50000000102000")
        self.assertFalse(vector["exact_metrics"]["activated"])

    def test_worker_source_requires_claim_and_fence(self) -> None:
        source = (ROOT / "workers/site_publication_intr_consumer_worker.py").read_text()
        self.assertIn('task.get("claim_id")', source)
        self.assertIn('get("fencing_token")', source)
        self.assertIn("return 3", source)
        self.assertIn("SITE_PUBLICATION_EVENT_CANDIDATE_VALIDATED", source)
        self.assertNotIn("final_publication_transition_admitted\": True", source)


if __name__ == "__main__":
    unittest.main()
