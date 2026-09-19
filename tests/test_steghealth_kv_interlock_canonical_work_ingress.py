#!/usr/bin/env python3
import json
import unittest
from pathlib import Path
from scripts.apply_admitted_canonical_work_projection import project_task

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-steghealth-kv-interlock-production-endpoint-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
BOOTSTRAP = ROOT / "scripts" / "run_canonical_work_event_bootstrap.py"

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

    def test_bootstrap_explicitly_accepts_active_checked_out_ingress(self):
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('"ACTIVE"', source)
        self.assertIn('"CHECKED_OUT"', source)
        self.assertIn("runtime_ingress_state", source)

if __name__ == "__main__":
    unittest.main()
