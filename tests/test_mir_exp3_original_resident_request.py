"""Source-only contract tests. Mocks never produce resident authority."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import consume_mir_exp3_original_request as mod


def ticket(digest="a" * 64):
    return {"schema": mod.SCHEMA, "task_id": mod.GOAL,
            "cosv_task_vector": mod.COSV, "state": "REQUESTED",
            "credential_authority": "TV/TVC", "request_grants_authority": False,
            "wire_manifest_sha256": mod.ORIGINAL_WIRE,
            "request_sha256": digest}


class ResidentOriginalRequestTests(unittest.TestCase):
    def test_no_private_request_does_not_attempt_native_execution(self):
        with tempfile.TemporaryDirectory() as td:
            got = mod.consume(Path(td), Path(td))
            self.assertEqual(got["state"], "NO_REQUEST")
            self.assertFalse(got["runtime_execution_proven"])

    def test_source_tree_ticket_does_not_mint_private_admission(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / mod.REQUEST_REL).parent.mkdir(parents=True)
            (root / mod.REQUEST_REL).write_text(json.dumps(ticket()))
            got = mod.consume(root, root)
            self.assertEqual(got["state"], "SOURCE_BOUNDARY")
            self.assertEqual(got["reason"], "ORIGINAL_IMMUTABLE_REQUEST_NOT_UNIQUELY_RETAINED")
            self.assertFalse(got["runtime_execution_proven"])

    def test_hosted_source_ci_can_never_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / mod.REQUEST_REL).parent.mkdir(parents=True)
            (root / mod.REQUEST_REL).write_text(json.dumps(ticket()))
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                got = mod.consume(root, root)
            self.assertEqual(got["reason"], "HOSTED_ENVIRONMENT_FORBIDDEN")
            self.assertFalse(got["runtime_execution_proven"])

    def test_caller_auth_claim_does_not_override_protocol(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / mod.REQUEST_REL).parent.mkdir(parents=True)
            bad = ticket()
            bad["request_grants_authority"] = True
            bad["caller_attested_session_origin"] = "self-asserted"
            (root / mod.REQUEST_REL).write_text(json.dumps(bad))
            got = mod.consume(root, root)
            self.assertEqual(got["reason"], "ORIGINAL_RESIDENT_REQUEST_CONTRACT_INVALID")


if __name__ == "__main__":
    unittest.main()
