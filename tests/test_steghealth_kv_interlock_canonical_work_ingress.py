#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from scripts.apply_admitted_canonical_work_projection import project_task

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-steghealth-kv-interlock-production-endpoint-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
BOOTSTRAP = ROOT / "scripts" / "run_canonical_work_event_bootstrap.py"
LEGACY_CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.legacy.py"

def load_legacy_consumer():
    spec = importlib.util.spec_from_file_location("canonical_work_legacy_exception_retention_test", LEGACY_CONSUMER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

class StegHealthKvInterlockCanonicalWorkIngressTests(unittest.TestCase):
    def test_request_reuses_existing_non_authorizing_canonical_work_path(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["task_id"], "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_existing_consumer_registers_exact_steghealth_spec(self):
        source = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("STEGHEALTH_KV_INTERLOCK_SPEC", source)
        self.assertIn('"task_id": STEGHEALTH_KV_INTERLOCK_TASK', source)
        self.assertIn("mod.REQUEST_SPECS", source)
        self.assertNotIn("STEGHEALTH_KV_INTERLOCK_DISPATCHER", source)

    def test_active_checked_out_task_is_ingress_projectable_without_demotion(self):
        task = {"task_id":"STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001","correlation_id":"STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001","coordination_state":"ACTIVE","checkout_state":"CHECKED_OUT","allowed_next_transitions":["INGRESS_ADMITTED","CLAIMED_IMPLEMENTATION","MACHINE_OWNED","COMPLETE"]}
        ingress = {"materialization_id":"INTR-MAT-test","request_hash":"sha256:req","payload_hash":"sha256:payload"}
        consumption = {"ingress_receipt_ref":"runtime://ingress/test","consumption_receipt_ref":"runtime://consumption/test"}
        projected = project_task(task, correlation_id=task["correlation_id"], ingress=ingress, consumption=consumption)
        self.assertEqual(projected["coordination_state"], "ACTIVE")
        self.assertEqual(projected["checkout_state"], "CHECKED_OUT")
        self.assertEqual(projected["runtime_refs"]["ingress_state"], "INGRESS_ADMITTED")
        self.assertEqual(projected["allowed_next_transitions"], task["allowed_next_transitions"])

    def test_task_no_longer_waits_for_separate_authentic_runtime_proof(self):
        registry = json.loads((ROOT / "data" / "canonical-task-registry.json").read_text(encoding="utf-8"))
        task = next(row for row in registry["tasks"] if row["task_id"] == "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001")
        self.assertEqual(task["remaining_predicate"], "INGRESS_ADMITTED")
        self.assertEqual(task.get("dependencies", []), [])
        self.assertFalse(task["runtime_requirements"]["current_observation_required"])
        self.assertFalse(task["completion"]["duplicate_runtime_proof_required"])
        self.assertFalse(task["completion"]["separate_authentic_runtime_evidence_class_required"])
        self.assertTrue(task["completion"]["terminal_state_is_completion_truth"])
        self.assertEqual(task["carriage_repair"]["state"], "STATE_TRIGGERABLE_INGRESS_READY")
        self.assertNotIn("AUTHENTIC_STEGHEALTH_KV_INTERLOCK_RUNTIME_TRANSITION_OBSERVED", task["expected_evidence_predicates"])

    def test_pre_receipt_exception_is_retained_at_task_specific_consumption_path(self):
        legacy = load_legacy_consumer()
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            spec = {
                "request_rel": Path("control/resident-execution-request.d/canonical-work-steghealth-kv-interlock-production-endpoint-001.json"),
                "consumption_rel": Path("receipts/sovereign-host/canonical-work-steghealth-kv-interlock-production-endpoint-request-consumption.latest.json"),
                "bootstrap_runtime_rel": Path("runtime/canonical-work-steghealth-kv-interlock-production-endpoint"),
                "task_id": "STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001",
            }
            request_path = runtime / spec["request_rel"]
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps({"request_id": "RESIDENT-EXEC-STEGHEALTH-KV-INTERLOCK-PRODUCTION-ENDPOINT-001"}) + "\n", encoding="utf-8")
            receipt = legacy.retain_request_consumption_exception(runtime, spec, RuntimeError("deterministic-test-boundary"))
            retained = json.loads((runtime / spec["consumption_rel"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt, retained)
            self.assertEqual(retained["state"], "REQUEST_CONSUMPTION_EXCEPTION")
            self.assertEqual(retained["task_id"], spec["task_id"])
            self.assertTrue(retained["attempted"])
            self.assertTrue(retained["retained_failure_evidence"])
            self.assertEqual(retained["error"], "deterministic-test-boundary")
            self.assertEqual(retained["authority_effect"], "NONE_FAIL_CLOSED")

    def test_bootstrap_explicitly_accepts_active_checked_out_ingress(self):
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('"ACTIVE"', source)
        self.assertIn('"CHECKED_OUT"', source)
        self.assertIn("runtime_ingress_state", source)

if __name__ == "__main__":
    unittest.main()
