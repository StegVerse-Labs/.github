"""Ingress-gated StegApp allocator candidate; no live allocation input."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bootstrap_sovereign_runtime as bootstrap  # noqa: E402
import consume_org_claim_allocator_request as consumer  # noqa: E402

REL = Path("control/resident-execution-request.d/org-claim-allocator-stegapp-p0-001.json")
TASK = ROOT / "tasks" / "TASK-2026-0016.json"
RECORD = ROOT / "data/canonical-task-records/STEGAPP-EPHEMERAL-COMPOSITION-001.json"
DEPENDENCY = "stegapp:p0-native-composition-chat-delivery"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class StegAppAllocatorCandidateTests(unittest.TestCase):
    def setUp(self):
        self.request = load(ROOT / REL)
        self.task = load(TASK)
        self.record = load(RECORD)

    def test_candidate_binds_existing_goal_and_grants_nothing(self):
        consumer.validate_request(self.request)
        self.assertEqual(self.request["target_task_id"], "TASK-2026-0016")
        self.assertEqual(self.task["canonical_task_record"],
                         "data/canonical-task-records/STEGAPP-EPHEMERAL-COMPOSITION-001.json")
        self.assertEqual(self.record["task_id"], "STEGAPP-EPHEMERAL-COMPOSITION-001")
        self.assertEqual(self.record["targets"]["repositories"], ["StegVerse-Labs/StegApp"])
        self.assertEqual(self.request["authority_effect"], "NONE_REQUEST_ONLY")
        self.assertIs(self.request["request_grants_claim_authority"], False)
        self.assertIs(self.request["heartbeat_grants_execution_authority"], False)
        self.assertIs(self.request["allocator_remains_claim_authority"], True)
        self.assertEqual(self.task["authority"]["credential_authority"], "TV/TVC")
        self.assertIs(self.task["authority"]["runtime_execution_inferred"], False)

    def test_source_catalog_floor_binds_exact_scope(self):
        floor = consumer.validate_source_catalog_floor(ROOT, self.request)
        self.assertEqual(floor["state"], "SOURCE_CATALOG_FLOOR_SATISFIED")
        self.assertEqual(floor["repository_full_name"], "StegVerse-Labs/StegApp")
        self.assertEqual(floor["required_dependency_surface"], DEPENDENCY)
        self.assertEqual(floor["task_status_observed"], "proposed")
        self.assertEqual(floor["task_eligibility_effect"], "NONE")
        scope = self.task["requirements"]["mandatory"][0]["scope"]
        encoded = json.dumps(scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(encoded).hexdigest(),
                         self.request["source_catalog_floor"]["scope_sha256"])
        self.assertIn(DEPENDENCY, scope["dependency_surfaces"])
        self.assertEqual(scope["workflows"], [])

    def test_proposed_candidate_is_not_live_allocation_input(self):
        # Phase A must remain non-allocating. After authentic ingress, the owner
        # queues TASK-2026-0016, registers REL in both discovery surfaces, and
        # updates this test to require discovery. Until then, a targeted native
        # evaluation fails with the allocator's TARGET_TASK_NOT_QUEUED predicate.
        self.assertEqual(self.task["status"], "proposed")
        self.assertNotIn(REL, consumer.REQUEST_RELS)
        self.assertNotIn(REL, bootstrap.REQUIRED_SOURCE_FILES)
        self.assertEqual(consumer.allocate_claims.TARGET_TASK_NOT_QUEUED,
                         "TARGET_TASK_NOT_QUEUED")


if __name__ == "__main__":
    unittest.main()
