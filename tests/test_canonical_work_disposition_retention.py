import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bridge", ROOT / "scripts/refresh_and_dispatch_resident_requests.py")
bridge = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(bridge)

TASK = bridge.CANONICAL_WORK_PARENT_TASK_ID


class CanonicalWorkDispositionRetentionTests(unittest.TestCase):
    def _case(self, disposition, state="COMPLETED", failed_predicate=None):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            rel = bridge.CANONICAL_WORK_PARENT_CONSUMPTION_REL
            receipt = {
                "schema": "stegverse.canonical-work-bootstrap-request-consumption/v1",
                "task_id": TASK,
                "state": state,
                "request_sha256": "request-sha",
                "bootstrap_receipt_ref": "/runtime/bootstrap.json",
                "disposition": disposition,
                "disposition_authority": "INTERLOCK_INTR" if disposition != "FAIL_CLOSED" else "CANONICAL_WORK_CONSUMER_PRE_TRANSITION_BOUNDARY",
                "failed_predicate": failed_predicate,
                "disposition_evidence_refs": ["/runtime/bootstrap.json"],
                "credential_material_present": False,
                "network_source_fetch_performed": False,
            }
            path = runtime / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            dispatch = {
                "outcomes": [{
                    "consumer": "canonical_work_coordination",
                    "attempted": True,
                    "result": {"canonical_work_request_set": {"outcomes": [{
                        "task_id": TASK,
                        "state": state,
                        "request_sha256": "request-sha",
                        "bootstrap_receipt_ref": "/runtime/bootstrap.json",
                        "disposition": disposition,
                    }]}}
                }]
            }
            return bridge.canonical_work_goal_consumption_evidence(
                runtime, "canonical_work_coordination", TASK, dispatch
            )

    def test_allow_is_retained(self):
        receipt, _sha, required, valid, current = self._case("ALLOW")
        self.assertTrue(required and valid and current)
        self.assertEqual(receipt["disposition"], "ALLOW")

    def test_deny_is_retained(self):
        receipt, _sha, required, valid, current = self._case("DENY")
        self.assertTrue(required and valid and current)
        self.assertEqual(receipt["disposition"], "DENY")

    def test_fail_closed_is_retained_with_failed_predicate(self):
        receipt, _sha, required, valid, current = self._case(
            "FAIL_CLOSED", state="ATTEMPT_RECORDED",
            failed_predicate="AUTHENTIC_GOVERNED_DISPOSITION_RETAINED",
        )
        self.assertTrue(required and valid and current)
        self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
        self.assertEqual(receipt["failed_predicate"], "AUTHENTIC_GOVERNED_DISPOSITION_RETAINED")

    def test_missing_disposition_is_not_completion_evidence(self):
        receipt, _sha, required, valid, current = self._case(None)
        self.assertTrue(required and current)
        self.assertFalse(valid)
        self.assertIsNone(receipt["disposition"])


if __name__ == "__main__":
    unittest.main()
