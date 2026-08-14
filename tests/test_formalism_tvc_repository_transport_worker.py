from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import unittest

from workers.formalism_tvc_repository_transport_worker import evaluate, inbox_receipts, source_requests

NOW = datetime(2026, 8, 14, 6, 0, tzinfo=timezone.utc)


def config(standing="CANONICAL_VALIDATED"):
    return {
        "schema": "stegverse.formalism-tvc-repository-transport/v0.1",
        "goal_id": "FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "consumer_secret_or_token_authority": False,
        "tvc_broker": {
            "repository": "StegVerse-Labs/TVC",
            "goal_id": "TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001",
            "canonical_required": True,
            "standing": standing,
        },
        "source_discovery_receipt": "missing.json",
        "owner_work_directory": "missing-owner-work",
        "tvc_receipt_directory": "receipts/tvc-repository-operations",
        "request_directory": "requests/tvc-repository-operations",
        "request_ttl_seconds": 900,
        "materialization_root": "/var/lib/stegverse/source",
        "max_materialization_bytes": 67108864,
        "max_mutation_files": 32,
        "max_mutation_bytes": 1048576,
    }


class TransportWorkerTests(unittest.TestCase):
    def test_blocks_until_tvc_broker_is_canonical_validated(self):
        result = evaluate(config("PENDING_CANONICAL_VALIDATION"), NOW)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["reason"], "TVC_BROKER_NOT_CANONICAL_VALIDATED")
        self.assertEqual(result["requests"], [])
        self.assertFalse(result["consumer_credential_present"])
        self.assertFalse(result["github_token_required"])

    def test_missing_source_emits_inspection_request_without_secret(self):
        receipt = {"result": {"missing": ["Admissible-Existence/AE"]}}
        requests = source_requests(config(), receipt, NOW)
        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertEqual(request["operation_class"], "INSPECT_REPOSITORY_STATE")
        self.assertEqual(request["repository"], "Admissible-Existence/AE")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertFalse(request["consumer_credential_present"])
        self.assertFalse(request["secret_values_present"])
        self.assertNotIn("token", request)
        self.assertEqual(request["next_operation_on_receipt"], "MATERIALIZE_SOURCE_ARCHIVE")

    def test_sanitized_tvc_inbox_receipt_is_observed(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_root = Path(temporary)
            inbox = state_root / "inbox"
            inbox.mkdir()
            (inbox / "ok.json").write_text(json.dumps({
                "schema": "stegverse.tvc-github-repository-inspection-receipt/v0.1",
                "credential_authority": "TV/TVC",
                "credential_value_exposed": False,
                "non_tv_tvc_secret_or_token_used": False,
                "request_id": "inspect-1",
            }) + "\n", encoding="utf-8")
            receipts = inbox_receipts(state_root)
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]["request_id"], "inspect-1")

    def test_unsafe_inbox_receipt_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_root = Path(temporary)
            inbox = state_root / "inbox"
            inbox.mkdir()
            (inbox / "bad.json").write_text(json.dumps({
                "credential_authority": "TV/TVC",
                "credential_value_exposed": True,
                "non_tv_tvc_secret_or_token_used": False,
            }) + "\n", encoding="utf-8")
            self.assertEqual(inbox_receipts(state_root), [])

    def test_no_actionable_inputs_remains_blocked_not_success(self):
        result = evaluate(config(), NOW)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["reason"], "NO_ACTIONABLE_TRANSPORT_INPUTS")
        self.assertFalse(result["github_token_required"])


if __name__ == "__main__":
    unittest.main()
