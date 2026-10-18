"""Lane B claim request: WorkerCoordinator allocation for StegVerse-org/StegVerse-SDK#533.

StegVerse-org/.github#162 comment 6245552151 classifies SDK#533's R2
(TASK_CLAIM_ABSENT) as class A: the organization claim allocator decides the
claim and answers with a GRANTED/REFUSED/FAIL_CLOSED receipt. The request grants
nothing by itself; a session is never claim or fence authority.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REL = Path("control/resident-execution-request.d/org-claim-allocator-sdk-ecosystem-diagnostic-processor-001.json")
TASK = ROOT / "tasks" / "TASK-2026-0016.json"
RECORD = ROOT / "data/canonical-task-records/SDK-ECOSYSTEM-DIAGNOSTIC-PROCESSOR-001.json"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


consumer = _load("lane_b_claim_consumer", "scripts/consume_org_claim_allocator_request.py")
bootstrap = _load("lane_b_claim_bootstrap", "scripts/bootstrap_sovereign_runtime.py")
allocator = _load("lane_b_claim_allocator", "scripts/allocate_claims.py")


class SdkEcosystemDiagnosticClaimRequest(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((ROOT / REL).read_text(encoding="utf-8"))
        self.task = json.loads(TASK.read_text(encoding="utf-8"))

    def test_request_is_consumed_and_grants_nothing_itself(self):
        consumer.validate_request(self.request)
        self.assertIn(REL, consumer.REQUEST_RELS)
        self.assertIn(REL, bootstrap.REQUIRED_SOURCE_FILES)
        self.assertEqual(self.request["target_task_id"], "TASK-2026-0016")
        self.assertEqual(self.request["authority_effect"], "NONE_REQUEST_ONLY")
        self.assertIs(self.request["request_grants_claim_authority"], False)
        self.assertIs(self.request["allocator_remains_claim_authority"], True)

    def test_source_catalog_floor_binds_the_exact_scope(self):
        floor = consumer.validate_source_catalog_floor(ROOT, self.request)
        self.assertEqual(floor["state"], "SOURCE_CATALOG_FLOOR_SATISFIED")
        self.assertEqual(floor["repository_full_name"], "StegVerse-org/StegVerse-SDK")
        self.assertEqual(floor["required_dependency_surface"],
                         "stegverse-org:sdk-ecosystem-diagnostic-processor-mpdv-regressions")

    def test_task_projects_the_existing_goal_record_and_its_cosv_unchanged(self):
        schema = json.loads((ROOT / "schemas/task.schema.json").read_text(encoding="utf-8"))
        for key in schema["required"]:
            self.assertIn(key, self.task)
        self.assertEqual(self.task["status"], "queued")
        self.assertEqual(self.task["canonical_task_record"], RECORD.relative_to(ROOT).as_posix())
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(consumer.task_cosv(ROOT, self.task), record["cosv_task_vector"])
        self.assertEqual(record["checkout_state"], "UNCLAIMED")
        self.assertIsNone(record.get("worker_claim"))
        scope = self.task["requirements"]["mandatory"][0]["scope"]
        self.assertEqual(sorted(scope["paths"]), sorted([
            "stegverse/manifest_path_differential.py",
            "tests/fixtures/ecosystem-diagnostic/steghealth-51-governed-deny-negative-control.json",
            "tests/test_manifest_path_differential.py",
        ]))

    def test_no_conflict_with_other_queued_allocator_tasks(self):
        mine = self.task["requirements"]["mandatory"]
        for path in sorted((ROOT / "tasks").glob("TASK-*.json")):
            if path == TASK:
                continue
            other = json.loads(path.read_text(encoding="utf-8"))
            for held in (other.get("requirements") or {}).get("mandatory") or []:
                for request_claim in mine:
                    self.assertFalse(allocator.conflicts(request_claim, held), path.name)


if __name__ == "__main__":
    unittest.main()
