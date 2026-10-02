import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.legacy.py"
SPEC = importlib.util.spec_from_file_location("canonical_work_legacy_attempt_test", LEGACY)
consumer = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(consumer)


class CanonicalWorkAttemptCorrelationTests(unittest.TestCase):
    def test_stale_completed_receipt_cannot_satisfy_new_attempt(self):
        previous = {
            "state": "COMPLETED",
            "request_sha256": "same-request",
            "execution_attempt_id": "attempt-old",
            "disposition": "ALLOW",
        }
        self.assertFalse(
            consumer.completed_receipt_matches_execution_attempt(previous, "attempt-new")
        )

    def test_same_attempt_preserves_idempotent_completed_receipt(self):
        previous = {
            "state": "COMPLETED",
            "request_sha256": "same-request",
            "execution_attempt_id": "attempt-1",
            "disposition": "ALLOW",
        }
        self.assertTrue(
            consumer.completed_receipt_matches_execution_attempt(previous, "attempt-1")
        )

    def test_historical_non_attempt_call_preserves_idempotence(self):
        previous = {
            "state": "COMPLETED",
            "request_sha256": "same-request",
            "disposition": "ALLOW",
        }
        self.assertTrue(
            consumer.completed_receipt_matches_execution_attempt(previous, None)
        )


if __name__ == "__main__":
    unittest.main()
