"""Concurrent organization append and replay regression (source-only)."""
import concurrent.futures
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "resident-runtime"))
import aggregate_repo_transition as org


def append_case(args):
    root, index = args
    os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = root
    source = {
        "schema": "stegverse.canonical-state-transition-receipt/v1",
        "transition_id": "HOLD-ATTEMPT-%02d" % index,
        "subject_or_correlation_id": "ELAN-PAPER-COAUTHOR-PUBLICATION-001",
        "transition_outcome": "FAIL_CLOSED",
        "failed_predicate": "AUTHENTICATED_GRANT_NOT_OBSERVED",
        "required_evidence_manifest": [],
    }
    return org.aggregate_transition(
        source, org_transition_class="HOLD_ATTEMPT_OBSERVATION",
        boundary_evidence={"task_id": source["subject_or_correlation_id"],
                           "transition_id": source["transition_id"],
                           "failed_predicate": source["failed_predicate"]},
    )["receipt_sha256"]


class AtomicOrganizationAppendTest(unittest.TestCase):
    def test_concurrent_appends_and_exact_retry(self):
        with tempfile.TemporaryDirectory() as root:
            with concurrent.futures.ProcessPoolExecutor(max_workers=6) as pool:
                digests = list(pool.map(append_case, [(root, i) for i in range(16)]))
            self.assertEqual(len(set(digests)), 16)
            ledger = Path(root)
            head = json.loads((ledger / "HEAD.json").read_text())
            cursor = head["receipt_sha256"]
            seen = set()
            while cursor is not None:
                self.assertNotIn(cursor, seen)
                seen.add(cursor)
                path = ledger / "receipts" / (cursor.split(":", 1)[1] + ".json")
                record = json.loads(path.read_text())
                body = dict(record)
                self.assertEqual(body.pop("receipt_sha256"), org.sha(body))
                cursor = record["previous_receipt_sha256"]
            self.assertEqual(seen, set(digests))
            self.assertEqual(len(list((ledger / "source-receipts").glob("*.json"))), 16)
            before = head["receipt_sha256"]
            self.assertEqual(append_case((root, 3)), digests[3])
            self.assertEqual(json.loads((ledger / "HEAD.json").read_text())["receipt_sha256"], before)

if __name__ == "__main__":
    unittest.main()
