from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py"
RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.py"
LEGACY_RUNNER = ROOT / "scripts/run_stegbrowser_runtime_consumption_reusable.legacy.py"
WORKER = ROOT / "workers/stegbrowser_manifest_intr_ingress.py"
REQUEST = ROOT / "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json"
TASK = ROOT / "data/canonical-task-records/STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001.json"
REUSABLE = ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json"

class StegBrowserManifestIntrIngressExecutionTests(unittest.TestCase):
    def test_request_and_consumer_bind_active_goal(self):
        req = json.loads(REQUEST.read_text())
        self.assertEqual(req["task_id"], "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001")
        source = CONSUMER.read_text()
        self.assertIn('ACTIVE_TASK = "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001"', source)
        self.assertIn('mod.STEGBROWSER_RUNTIME_CONSUMPTION_SPEC["task_id"] = ACTIVE_TASK', source)
        self.assertIn("ACTIVE_SHARD", source)

    def test_request_requires_registered_node_interlock_binding_before_lease(self):
        req = json.loads(REQUEST.read_text())
        binding = req["reusable_task_binding"]
        self.assertTrue(binding["node_interlock_binding_required_before_lease"])
        self.assertEqual(binding["node_binding_receipt_schema"], "stegos.node_handoff_receipt.v1")
        self.assertEqual(binding["node_binding_receipt_number"], 1)
        self.assertIn("node_id", binding["required_node_binding_fields"])
        self.assertIn("interlock_id", binding["required_node_binding_fields"])
        self.assertIn("registration_receipt_sha256", binding["lease_must_bind"])
        self.assertIn("manifest_sha256", binding["runtime_identity_must_bind"])
        self.assertIn("runtime_id", binding["a4_must_bind"])
        self.assertEqual(binding["source_conformance_state"], "NODE_INTERLOCK_BINDING_SOURCE_MERGED_VALIDATED_RUNTIME_EVIDENCE_PENDING")
        self.assertFalse(binding["execution_before_node_interlock_binding_repair_allowed"])
        self.assertEqual(binding["path_parameters"]["node_genesis_receipt"], "STEGVERSE_NODE_GENESIS_RECEIPT")

    def test_reusable_task_tracks_validated_sv002_baseline_pending_stegbrowser_adaptation(self):
        reusable = json.loads(REUSABLE.read_text())
        trace = reusable["implementation_trace"]
        self.assertEqual(
            reusable["source_conformance_state"],
            "SV002_SITE_VALIDATED_LANE_BASELINE_RETEST_PASS_STEGBROWSER_BINDING_ADAPTATION_PENDING",
        )
        baseline = reusable["validated_runtime_baseline"]
        self.assertEqual(baseline["repository"], "StegVerse-Labs/Site")
        self.assertEqual(baseline["site_pr"], 1354)
        self.assertTrue(baseline["all_source_validation_passed"])
        self.assertEqual(baseline["runtime_authority_effect"], "NONE_FROM_SOURCE_OR_CI")
        self.assertEqual(trace["validated_site_baseline"], "RETEST_PASS_UNCHANGED")
        self.assertIn("CURRENT_STEGBROWSER_ADAPTER_BINDING_PENDING", trace["registered_stegverse_node_binding"])
        self.assertIn("CURRENT_STEGBROWSER_ADAPTER_BINDING_PENDING", trace["interlock_binding_from_node"])
        self.assertEqual(trace["event_ephemeral_stegos_materialization"], "VALIDATED_SITE_BASELINE_EXISTS")
        self.assertEqual(trace["execution_time_runtime_identity"], "VALIDATED_SITE_BASELINE_EXISTS")
        self.assertEqual(trace["workercoordinator_claim_fence"], "CURRENT_STEGBROWSER_EXACT_AUTHENTIC_EVIDENCE_PENDING")
        contract = reusable["canonical_node_binding_contract"]
        self.assertTrue(contract["a4_exact_correlation_required"])
        self.assertTrue(contract["fail_closed_on_missing_or_mismatch"])
        self.assertIn("manifest_sha256", contract["required_lease_identity_inputs"])
        self.assertIn("registration_receipt_sha256", contract["required_lease_identity_inputs"])
        self.assertIn("runtime_id", contract["required_runtime_correlation"])
        self.assertFalse(reusable["superseded_reconstruction"]["new_receipt_resolver_allowed"])
        self.assertFalse(reusable["superseded_reconstruction"]["new_runtime_materializer_allowed"])
        legacy = LEGACY_RUNNER.read_text()
        self.assertIn("validate_node_genesis_receipt", legacy)
        self.assertIn("LeaseRequest(", legacy)
        self.assertIn("RuntimeClass.EVENT_EPHEMERAL", legacy)
        self.assertIn("RendezvousRequirement.NOT_REQUIRED", legacy)
        self.assertIn('"node_id": node_id', legacy)
        self.assertIn('"interlock_id": interlock_id', legacy)
        self.assertIn('"runtime_id": runtime_id', legacy)

    def test_worker_reuses_existing_org_boundary_with_claim_fence_and_exact_correlation(self):
        source = WORKER.read_text()
        self.assertIn('ORG_TASK = "ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001"', source)
        self.assertIn('TARGETED = Path("scripts/refresh_and_execute_resident_task.py")', source)
        self.assertIn('claim.endswith(f"-G{fence}")', source)
        self.assertIn('"workercoordinator_claim_fence_observed":True', source)
        self.assertIn('"organization_local_intr_ingress_receipt_verified":True', source)
        self.assertIn('"node_interlock_lease_runtime_correlation_verified":True', source)
        for key in ("manifest_sha256", "node_id", "interlock_id", "registration_receipt_sha256", "lease_id", "runtime_id", "state_root_binding"):
            self.assertIn(f'"{key}"', source)
        self.assertIn('"external_runtime_required":False', source)

    def test_runner_orders_claim_fence_before_a4_projection(self):
        source = RUNNER.read_text()
        self.assertIn('"ENTER_GOVERNED_INTR_TRANSPORT"', source)
        self.assertIn('workercoordinator_claim_fence_observed', source)
        self.assertIn('organization_local_intr_ingress_receipt_verified', source)
        self.assertIn('authentic_intr_ingress_observed', source)
        self.assertIn('node_interlock_lease_runtime_correlation_verified', source)
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
