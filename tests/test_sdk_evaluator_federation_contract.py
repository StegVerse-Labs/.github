"""Source-only regression checks: never claim live federation or evaluator execution."""
import json
import unittest
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/sdk-evaluator-organization-federation-custody-contract.json"
REGISTRY = ROOT / "data/canonical-task-records/SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001.json"
FEDERATION = ROOT / "control/organization-federation.json"
KERNEL = ROOT / "org-kernel/kernel.py"
GATEWAY = ROOT / "resident-runtime/federation_gateway_transport.py"
UNIVERSAL = ROOT / "workers/universal_intr_profiled_ingress.py"
CONSUMER = ROOT / "scripts/consume_sdk_evaluator_governance_posture_request.py"

class ContractSourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text())
        cls.registry = json.loads(REGISTRY.read_text())
        cls.federation = json.loads(FEDERATION.read_text())

    def test_canonical_identity_and_first_predicate(self):
        self.assertEqual(self.contract["task_id"], self.registry["task_id"])
        self.assertEqual(self.contract["cosv"], self.registry["cosv_task_vector"])
        self.assertEqual(self.contract["first_unresolved_predicate"], self.registry["runtime_resolution"]["first_task_local_unresolved_predicate"])
        self.assertEqual(self.registry["coordination_state"], "ACTIVE")

    def test_authority_separation(self):
        self.assertEqual(self.contract["organization_transition"]["governance_authority"], "Interlock/InTr")
        self.assertTrue(self.contract["organization_transition"]["exact_immediate_predecessor_required"])
        self.assertFalse(self.contract["reusable_module"]["summary_grants_authority"])
        self.assertFalse(self.contract["master_records"]["grants_transition_authority"])
        self.assertFalse(self.contract["interorganizational_transport"]["receiver_ack_proves_execution"])
        self.assertFalse(self.contract["new_runtime_allowed"])

    def test_existing_paths_are_real_but_not_integrated_proof(self):
        kernel = KERNEL.read_text()
        gateway = GATEWAY.read_text()
        universal = UNIVERSAL.read_text()
        consumer = CONSUMER.read_text()
        self.assertIn("def ingest_frame(", kernel)
        self.assertIn("previous_receipt_id", kernel)
        self.assertIn("result = K.ingest_frame(repo_root, frame)", gateway)
        self.assertIn("INGRESS_PATH = \"/intr/materialization\"", universal)
        self.assertIn("run_evaluator_governance_manifest", consumer)
        self.assertEqual(self.contract["interorganizational_transport"]["current_implementation_status"], "SOURCE_ROUTED_FAIL_CLOSED_RUNTIME_UNVERIFIED")
        self.assertFalse(self.contract["runtime_proof"]["authentic_federation_observed"])
        self.assertFalse(self.contract["runtime_proof"]["authentic_evaluator_runtime_observed"])

    def test_legacy_kernel_rejects_governed_frame_before_dispatch(self):
        spec = importlib.util.spec_from_file_location("federation_kernel", KERNEL)
        kernel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(kernel)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "org-boundary/registry"
            registry.mkdir(parents=True)
            (registry / "services.json").write_text(json.dumps({
                "organization": "StegVerse-Labs",
                "services": [{"service_id": "test.service", "boundary_role": "BOUNDARY_LOCAL_CONTROL"}]
            }))
            packet = {"destination": {"org": "StegVerse-Labs", "service": "test.service"},
                      "transition": {"authority_effect": "ALLOW"}, "payload": {}, "packet_id": "test"}
            with self.assertRaisesRegex(ValueError, "governed_federation_requires_universal_intr_admission"):
                kernel.dispatch(root, packet)

    def test_federation_registry_not_runtime_proof(self):
        coverage = self.federation["coverage"]
        self.assertEqual(coverage["registered"], len(self.federation["organizations"]))
        self.assertEqual(coverage["live_federation_observed"], 0)
        self.assertEqual(self.contract["implementation_compatibility"]["classification"], "SOURCE_INTEGRATION_TESTED_NO_AUTHENTIC_RUNTIME_PROOF")

if __name__ == "__main__":
    unittest.main()
