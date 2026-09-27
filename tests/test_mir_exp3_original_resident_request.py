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
            with patch.dict(os.environ, {key: '0' for key in mod.HOSTED_ENV}):
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
            with patch.dict(os.environ, {key: '0' for key in mod.HOSTED_ENV}):
                got = mod.consume(root, root)
            self.assertEqual(got["reason"], "ORIGINAL_RESIDENT_REQUEST_CONTRACT_INVALID")


    def test_source_deny_retains_exact_private_attempt_without_terminal_caching(self):
        from workers.manifest_state_transition_intr_ingress import REQUEST_DIR, IMMUTABLE_DIR
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = "a" * 64
            ticket_path = root / mod.REQUEST_REL
            ticket_path.parent.mkdir(parents=True)
            ticket_path.write_text(json.dumps(ticket(digest)))
            original_path = root / REQUEST_DIR / IMMUTABLE_DIR / "exp3" / (digest + ".json")
            original_path.parent.mkdir(parents=True)
            original_path.write_text("{}")
            validated = {
                "request_sha256": digest,
                "wire_manifest_sha256": mod.ORIGINAL_WIRE,
                "canonical_task_id": None,
                "processing_capability": "ecosystem_diagnostic",
                "requires_workercoordinator_claim_fence": False,
                "canonical_manifest": {
                    "payload": {"goal_task_id": mod.GOAL, "cosv": mod.COSV},
                    "completion": {"publisher": {"required": True}},
                },
            }
            first_deny = {"state": "DENY", "disposition": "DENY",
                          "terminal": False,
                          "failed_predicate": "AUTHENTIC_EVENT_EPHEMERAL_BINDING_LOCATOR_REQUIRED"}
            changed_deny = {**first_deny,
                            "failed_predicate": "CURRENT_EVENT_EPHEMERAL_LEASE_EXPIRY_REQUIRED"}
            with (patch.dict(os.environ, {key: "0" for key in mod.HOSTED_ENV}),
                  patch("workers.manifest_state_transition_intr_ingress.validate_request",
                        return_value=validated),
                  patch("workers.manifest_state_transition_intr_ingress.execute",
                        side_effect=[first_deny, first_deny, changed_deny]) as execute):
                one = mod.consume(root, root)
                replay = mod.consume(root, root)
                repaired = mod.consume(root, root)
            self.assertEqual(execute.call_count, 3)  # source DENY cannot freeze the request
            self.assertEqual(one["disposition"], "DENY")
            self.assertEqual(one["state"], "SOURCE_PROFILE_DISPOSITION")
            self.assertFalse(one["authentic_intr_disposition_observed"])
            self.assertFalse(one["runtime_execution_proven"])
            self.assertEqual(one["private_source_attempt_ref"], replay["private_source_attempt_ref"])
            self.assertNotEqual(one["private_source_attempt_ref"], repaired["private_source_attempt_ref"])
            stored = json.loads((root / one["private_source_attempt_ref"]).read_text())
            self.assertEqual(stored["first_failed_predicate"], first_deny["failed_predicate"])
            self.assertEqual(stored["authority_effect"], "NONE_SOURCE_PROFILE_ONLY")
            self.assertFalse(stored["organization_master_records_closure_observed"])
            self.assertEqual(len(list((root / mod.SOURCE_ATTEMPT_REL / digest).glob("*.json"))), 2)
            self.assertFalse((root / mod.RESULT_REL / (digest + ".json")).exists())



if __name__ == "__main__":
    unittest.main()
