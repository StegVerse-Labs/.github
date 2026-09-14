#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_TASK_ID = "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
TASK_ID = "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
CONTINUATION_TASK_ID = "STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001"
COSV = "40000100100000"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-stegbrowser-runtime-consumption-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
TASK_SHARD = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"
PARENT_SHARD = ROOT / "data" / "canonical-task-records" / f"{PARENT_TASK_ID}.json"
BOOTSTRAP = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"


class StegBrowserCanonicalWorkResidentRequestTests(unittest.TestCase):
    def test_successor_request_is_cosv_bound_and_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], "RESIDENT-EXEC-CANONICAL-WORK-STEGBROWSER-RUNTIME-CONSUMPTION-001")
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

    def test_parent_is_superseded_to_runtime_consumption_successor(self):
        parent = json.loads(PARENT_SHARD.read_text(encoding="utf-8"))
        self.assertEqual(parent["task_id"], PARENT_TASK_ID)
        self.assertEqual(parent["coordination_state"], "SUPERSEDED")
        self.assertEqual(parent["checkout_state"], "SUPERSEDED")
        self.assertEqual(parent["continuation_task_id"], TASK_ID)

    def test_runtime_consumption_task_is_retired_to_custody_root_successor(self):
        task = json.loads(TASK_SHARD.read_text(encoding="utf-8"))
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["parent_task_id"], PARENT_TASK_ID)
        self.assertEqual(task["coordination_state"], "RETIRED")
        self.assertEqual(task["checkout_state"], "DECOMPOSED_AT_PROMPT_LIMIT")
        self.assertEqual(task["cosv_task_vector"], COSV)
        self.assertEqual(task["decomposition"]["canonical_successor_task_id"], CONTINUATION_TASK_ID)
        self.assertEqual(task["prompt_budget"]["continuation_task_id"], CONTINUATION_TASK_ID)
        self.assertFalse(task["authority_model"]["task_registry_mints_execution_authority"])
        self.assertTrue(task["authority_model"]["interlock_intr_required_for_governed_ingress_egress"])

    def test_existing_consumer_visits_successor_not_superseded_parent(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("STEGBROWSER_RUNTIME_CONSUMPTION_SPEC", consumer)
        self.assertIn("canonical-work-stegbrowser-runtime-consumption-001.json", consumer)
        self.assertIn("canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json", consumer)
        self.assertIn(f'"task_id": "{TASK_ID}"', consumer)
        self.assertNotIn("STEGBROWSER_EPHEMERAL_SPEC", consumer)
        self.assertNotIn("canonical-work-stegbrowser-ephemeral-runtime-binding-001.json", consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_resident_consumer_preserves_successor_task_shard(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        expected = f'Path("data/canonical-task-records/{TASK_ID}.json")'
        self.assertIn(expected, consumer)
        self.assertIn("existing_target_task_shard_preserved", consumer)
        self.assertIn("spec['task_id']", consumer)
        self.assertIn('"network_source_fetch_performed": False', consumer)
        self.assertIn('"claim_or_fence_minted": False', consumer)

    def test_bootstrap_applies_existing_stegbrowser_convergence_to_successor(self):
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn(f'STEGBROWSER_RUNTIME_CONSUMPTION_TASK_ID = "{TASK_ID}"', bootstrap)
        self.assertIn("STEGBROWSER_RUNTIME_CONSUMPTION_TASK_ID", bootstrap)
        self.assertIn("GLOBAL_CONVERGENCE_TASK_IDS", bootstrap)


if __name__ == "__main__":
    unittest.main()
