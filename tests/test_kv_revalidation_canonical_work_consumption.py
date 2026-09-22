#!/usr/bin/env python3
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-kv-connection-revalidation-tvc-runtime-001.json"
TASK_ID = "KV-CONNECTION-REVALIDATION-WORKER-001"


def load_consumer():
    spec = importlib.util.spec_from_file_location("canonical_work_kv_revalidation_consumer_test", CONSUMER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KVRevalidationCanonicalWorkConsumptionTests(unittest.TestCase):
    def test_existing_consumer_registers_exact_kv_request_once(self):
        consumer = load_consumer()
        matches = [row for row in consumer.mod.REQUEST_SPECS if row.get("task_id") == TASK_ID]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        self.assertEqual(
            row["request_rel"].as_posix(),
            "control/resident-execution-request.d/canonical-work-kv-connection-revalidation-tvc-runtime-001.json",
        )
        self.assertEqual(
            row["consumption_rel"].as_posix(),
            "receipts/sovereign-host/canonical-work-kv-connection-revalidation-tvc-runtime-request-consumption.latest.json",
        )
        self.assertEqual(
            row["bootstrap_runtime_rel"].as_posix(),
            "runtime/canonical-work-kv-connection-revalidation-tvc-runtime",
        )

    def test_request_preserves_non_authorizing_runtime_boundaries(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["google_consent_allowed"])
        self.assertFalse(request["provider_connect_verify_allowed"])
        self.assertFalse(request["kv2_materialization_allowed"])

    def test_no_parallel_consumer_plane_is_added(self):
        source = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("KV_CONNECTION_REVALIDATION_TVC_RUNTIME_SPEC", source)
        self.assertIn("mod.REQUEST_SPECS", source)
        self.assertNotIn("KV_CONNECTION_REVALIDATION_DISPATCHER", source)
        self.assertNotIn("KV_CONNECTION_REVALIDATION_SCHEDULER", source)


if __name__ == "__main__":
    unittest.main()
