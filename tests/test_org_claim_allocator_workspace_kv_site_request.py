"""Lane D claim request: WorkerCoordinator allocation for the Site WorkSpace KV paths (D13/WU5).

StegVerse-org/.github#167 comment 6245553028. A session claim is never claim or fence
authority (TASK_REGISTRY_CANONICAL_INVARIANTS.md, Worker-claim field invariant), so the
Site WorkSpace paths are requested through the organization claim allocator; its
GRANTED/REFUSED/FAIL_CLOSED receipt decides. The request grants nothing by itself.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REL = Path("control/resident-execution-request.d/org-claim-allocator-workspace-kv-site-001.json")
TASK = ROOT / "tasks" / "TASK-2026-0015.json"
RECORD = ROOT / "data/canonical-task-records/STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001.json"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


consumer = _load("lane_d_claim_consumer", "scripts/consume_org_claim_allocator_request.py")
bootstrap = _load("lane_d_claim_bootstrap", "scripts/bootstrap_sovereign_runtime.py")
allocator = _load("lane_d_claim_allocator", "scripts/allocate_claims.py")


class WorkspaceKvSiteClaimRequest(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT / REL).read_text(encoding="utf-8"))
        self.task = json.loads(TASK.read_text(encoding="utf-8"))

    def test_request_is_consumed_and_grants_nothing_itself(self):
        consumer.validate_request(self.request)
        self.assertIn(REL, consumer.REQUEST_RELS)
        self.assertIn(REL, bootstrap.REQUIRED_SOURCE_FILES)
        self.assertEqual(self.request["target_task_id"], "TASK-2026-0015")
        self.assertEqual(self.request["authority_effect"], "NONE_REQUEST_ONLY")
        self.assertIs(self.request["request_grants_claim_authority"], False)
        self.assertIs(self.request["allocator_remains_claim_authority"], True)

    def test_source_catalog_floor_binds_the_exact_scope(self):
        floor = consumer.validate_source_catalog_floor(ROOT, self.request)
        self.assertEqual(floor["state"], "SOURCE_CATALOG_FLOOR_SATISFIED")
        self.assertEqual(floor["repository_full_name"], "StegVerse-Labs/Site")
        self.assertEqual(floor["required_dependency_surface"], "site:workspace-device-kv")

    def test_task_projects_the_registered_goal_and_its_cosv_unchanged(self):
        schema = json.loads((ROOT / "schemas/task.schema.json").read_text(encoding="utf-8"))
        for key in schema["required"]:
            self.assertIn(key, self.task)
        self.assertEqual(self.task["status"], "queued")
        self.assertEqual(self.task["canonical_task_record"], RECORD.relative_to(ROOT).as_posix())
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(consumer.task_cosv(ROOT, self.task), record["cosv_task_vector"])
        self.assertIsNone(record["worker_claim"]["claim_ref"])
        self.assertIsNone(record["worker_claim"]["fence_ref"])
        scope = self.task["requirements"]["mandatory"][0]["scope"]
        self.assertIn("assets/workspace.js", scope["paths"])
        self.assertEqual(scope["workflows"], [".github/workflows/workspace-kv-binding-validation.yml"])

    def test_no_conflict_with_other_queued_allocator_tasks(self):
        mine = self.task["requirements"]["mandatory"]
        for path in sorted((ROOT / "tasks").glob("TASK-*.json")):
            if path == TASK:
                continue
            other = json.loads(path.read_text(encoding="utf-8"))
            for held in (other.get("requirements") or {}).get("mandatory") or []:
                for request_claim in mine:
                    self.assertFalse(allocator.conflicts(request_claim, held), path.name)


# Phase A StegApp candidate cases share this registered ratchet set. The request
# remains undiscovered and the target proposed until authentic native ingress.
STEGAPP_REL = Path("control/resident-execution-request.d/org-claim-allocator-stegapp-p0-001.json")
STEGAPP_TASK = ROOT / "tasks" / "TASK-2026-0016.json"
STEGAPP_RECORD = ROOT / "data/canonical-task-records/STEGAPP-EPHEMERAL-COMPOSITION-001.json"
STEGAPP_DEPENDENCY = "stegapp:p0-native-composition-chat-delivery"


def stegapp_load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class StegAppAllocatorCandidateTests(unittest.TestCase):
    def setUp(self):
        self.request = stegapp_load(ROOT / STEGAPP_REL)
        self.task = stegapp_load(STEGAPP_TASK)
        self.record = stegapp_load(STEGAPP_RECORD)

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
        self.assertEqual(floor["required_dependency_surface"], STEGAPP_DEPENDENCY)
        self.assertEqual(floor["task_status_observed"], "proposed")
        self.assertEqual(floor["task_eligibility_effect"], "NONE")
        scope = self.task["requirements"]["mandatory"][0]["scope"]
        encoded = json.dumps(scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(encoded).hexdigest(),
                         self.request["source_catalog_floor"]["scope_sha256"])
        self.assertIn(STEGAPP_DEPENDENCY, scope["dependency_surfaces"])
        self.assertEqual(scope["workflows"], [])

    def test_proposed_candidate_is_not_live_allocation_input(self):
        # Phase A must remain non-allocating. After authentic ingress, the owner
        # queues TASK-2026-0016, registers STEGAPP_REL in both discovery surfaces,
        # and updates this test to require discovery. Until then, a targeted
        # native evaluation fails with TARGET_TASK_NOT_QUEUED.
        self.assertEqual(self.task["status"], "proposed")
        self.assertNotIn(STEGAPP_REL, consumer.REQUEST_RELS)
        self.assertNotIn(STEGAPP_REL, bootstrap.REQUIRED_SOURCE_FILES)
        self.assertEqual(allocator.TARGET_TASK_NOT_QUEUED, "TARGET_TASK_NOT_QUEUED")


if __name__ == "__main__":
    unittest.main()
