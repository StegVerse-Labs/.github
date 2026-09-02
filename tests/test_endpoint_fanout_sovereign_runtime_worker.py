from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "workers/endpoint_fanout_sovereign_runtime_worker.py"


def load_module():
    spec = importlib.util.spec_from_file_location("endpoint_fanout_worker", PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class EndpointFanoutSovereignWorkerTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()

    def result(self):
        return {
            "schema": "stegverse.endpoint-fanout-probe-result.v1",
            "pass": True,
            "report_count": 2,
            "reports": {
                "kv_interlock_endpoint_status": {
                    "schema": "stegverse.kv-interlock.endpoint-status-report.v1",
                    "endpoint_status": "PASS",
                    "canonical_state_changed": False,
                    "execution_authority": "NONE",
                    "credential_authority": "TV/TVC",
                    "return_interlock": {
                        "operation": "COMMIT_CANDIDATE",
                        "decision": "ALLOW_BOUNDED_CONTEXT",
                        "candidate_type": "ENDPOINT_STATUS_REPORT",
                        "candidate_only": True,
                        "canonical_state_changed": False,
                        "authority_effect": "NONE",
                        "writeback_candidate_ref": "urn:test:candidate",
                    },
                },
                "master_records_travel": {
                    "schema": "stegverse.master-records.travel-report.v1",
                    "authority_effect": "NONE",
                    "hops": [{"sequence": 1}],
                },
            },
        }

    def test_validates_exact_two_report_contract(self):
        kv, travel = self.m.validate_fanout(self.result())
        self.assertEqual(kv["endpoint_status"], "PASS")
        self.assertEqual(kv["return_interlock"]["candidate_type"], "ENDPOINT_STATUS_REPORT")
        self.assertTrue(kv["return_interlock"]["candidate_only"])
        self.assertFalse(kv["return_interlock"]["canonical_state_changed"])
        self.assertEqual(travel["schema"], "stegverse.master-records.travel-report.v1")

    def test_rejects_report_count_drift(self):
        value = self.result()
        value["report_count"] = 3
        with self.assertRaisesRegex(ValueError, "exactly two"):
            self.m.validate_fanout(value)

    def test_rejects_interlock_canonical_mutation(self):
        value = self.result()
        value["reports"]["kv_interlock_endpoint_status"]["return_interlock"]["canonical_state_changed"] = True
        with self.assertRaisesRegex(ValueError, "canonical_state_changed"):
            self.m.validate_fanout(value)

    def test_rejects_execution_authority_escalation(self):
        value = self.result()
        value["reports"]["kv_interlock_endpoint_status"]["execution_authority"] = "REMOTE"
        with self.assertRaisesRegex(ValueError, "authority boundary"):
            self.m.validate_fanout(value)


if __name__ == "__main__":
    unittest.main()
