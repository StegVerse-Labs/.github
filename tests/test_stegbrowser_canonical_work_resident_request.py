#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
COSV = "40000100100000"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-stegbrowser-ephemeral-runtime-binding-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
TASK_SHARD = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"


class StegBrowserCanonicalWorkResidentRequestTests(unittest.TestCase):
    def test_request_is_cosv_bound_and_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], "RESIDENT-EXEC-CANONICAL-WORK-STEGBROWSER-EPHEMERAL-RUNTIME-BINDING-001")
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["cosv_profile"], "task.v1")
        self.assertEqual(request["cosv_task_vector"], COSV)
        self.assertEqual(request["pointer_source"], f"control/task-vectors/{TASK_ID}.json")
        self.assertTrue(request["cosv_binding_required_before_execution"])
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["second_machine_required"])

    def test_task_shard_is_pre_ingress_eligible(self):
        task = json.loads(TASK_SHARD.read_text(encoding="utf-8"))
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertEqual(task["allowed_next_transitions"], ["INGRESS_ADMITTED"])
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertFalse(task["authority_model"]["task_registry_mints_execution_authority"])
        self.assertTrue(task["authority_model"]["interlock_intr_required_for_governed_admission"])

    def test_existing_consumer_visits_stegbrowser_request(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("STEGBROWSER_EPHEMERAL_SPEC", consumer)
        self.assertIn("canonical-work-stegbrowser-ephemeral-runtime-binding-001.json", consumer)
        self.assertIn("canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json", consumer)
        self.assertIn(f'"task_id": "{TASK_ID}"', consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_resident_consumer_preserves_target_task_shard(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        expected = f'Path("data/canonical-task-records/{TASK_ID}.json")'
        self.assertIn(expected, consumer)
        self.assertIn("existing_target_task_shard_preserved", consumer)
        self.assertNotIn("network source fetch", consumer.lower().split("def clean_env", 1)[0])


if __name__ == "__main__":
    unittest.main()
