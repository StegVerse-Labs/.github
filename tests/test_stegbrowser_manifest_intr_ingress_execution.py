from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py"
RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py"
WORKER = ROOT / "workers/stegbrowser_manifest_intr_ingress.py"
REQUEST = ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json"
TASK = ROOT / "data/canonical-task-records/STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001.json"

class StegBrowserManifestIntrIngressExecutionTests(unittest.TestCase):
    def test_request_and_consumer_bind_active_goal(self):
        req = json.loads(REQUEST.read_text())
        self.assertEqual(req["task_id"], "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001")
        source = CONSUMER.read_text()
        self.assertIn('ACTIVE_TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"', source)
        self.assertIn('mod.STEGBROWSER_RUNTIME_CONSUMPTION_SPEC["task_id"] = ACTIVE_TASK', source)
        self.assertIn("ACTIVE_SHARD", source)

    def test_worker_reuses_existing_org_boundary_with_claim_fence(self):
        source = WORKER.read_text()
        self.assertIn('ORG_TASK = "ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001"', source)
        self.assertIn('TARGETED = Path("scripts/refresh_and_execute_resident_task.py")', source)
        self.assertIn('claim.endswith(f"-G{fence}")', source)
        self.assertIn('"workercoordinator_claim_fence_observed":True', source)
        self.assertIn('"organization_local_intr_ingress_receipt_verified":True', source)
        self.assertIn('"external_runtime_required":False', source)

    def test_runner_orders_claim_fence_before_a4_projection(self):
        source = RUNNER.read_text()
        self.assertIn('"ENTER_GOVERNED_INTR_TRANSPORT"', source)
        self.assertIn('workercoordinator_claim_fence_observed', source)
        self.assertIn('organization_local_intr_ingress_receipt_verified', source)
        self.assertIn('authentic_intr_ingress_observed', source)
        self.assertNotIn('Remote_Desktop', source)
        self.assertNotIn('RENDER', source)

    def test_continuation_goal_forbids_external_runtime(self):
        task = json.loads(TASK.read_text())
        reqs = task["runtime_requirements"]
        self.assertFalse(reqs["standing_runtime_required"])
        self.assertFalse(reqs["external_runtime_connection_required"])
        self.assertFalse(reqs["external_device_required"])
        self.assertFalse(reqs["hosted_carrier_required"])

if __name__ == "__main__":
    unittest.main()
