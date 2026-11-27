"""Input-only checks must conserve scope and cannot manufacture registration."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import canonical_task_registration_transition as transition
import goal_scope_seal as seal
import registration_input_preflight as preflight


class InputPreflight(unittest.TestCase):
    def setUp(self):
        path = ROOT / "control/canonical-task-registration-requests/banking-system-001.json"
        self.request = json.loads(path.read_text())

    def invalid(self, request, code):
        result = preflight.check_request(request)
        self.assertEqual(result["input_status"], "INVALID", result)
        self.assertEqual(result["failure"]["failure_code"], code)
        self.assertTrue(all(result["failure"].get(key) for key in preflight.SIX))
        self.assertFalse(result["registration_proven"])
        self.assertFalse(result["native_transition_attempted"])
        self.assertEqual(result["derived_files"], [])

    def test_valid_request_never_calls_transition_or_mutates_input(self):
        original = copy.deepcopy(self.request)
        with mock.patch.object(transition, "run", side_effect=AssertionError("registration attempted")):
            result = preflight.check_request(self.request)
        self.assertEqual(result["input_status"], "VALID")
        self.assertFalse(result["registration_proven"])
        self.assertEqual(result["authority_effect"], "NONE_INPUT_PREFLIGHT_ONLY")
        self.assertEqual(self.request, original)

    def test_old_schema_tag_is_rejected(self):
        self.request["sealed_scope"]["schema"] = "stegverse.dual-scope-seal/v1"
        self.invalid(self.request, "REGISTRATION_REQUEST_SCHEMA_INVALID")

    def test_tampered_digest_is_rejected(self):
        self.request["sealed_scope"]["scope_digest"] = "sha256:" + "0" * 64
        self.invalid(self.request, "GOAL_SCOPE_DIGEST_MISMATCH")

    def test_rehashed_record_divergence_is_rejected(self):
        self.request["sealed_scope"]["scope"]["goal"] = "Different scope"
        self.request["sealed_scope"]["scope_digest"] = seal.digest(self.request["sealed_scope"]["scope"])
        self.invalid(self.request, "GOAL_SCOPE_DIVERGES_FROM_RECORD")

    def test_missing_finish_point_field_is_rejected(self):
        del self.request["sealed_scope"]["scope"]["finish_point"]["acceptance_test"]
        self.invalid(self.request, "REGISTRATION_REQUEST_SCHEMA_INVALID")

    def test_new_identity_cannot_supersede_a_scope(self):
        self.request["sealed_scope"]["supersedes_scope_digest"] = "sha256:" + "1" * 64
        self.invalid(self.request, "GOAL_SCOPE_SUPERSEDE_ON_NEW_IDENTITY")

    def test_constructor_preserves_scope_and_uses_canonical_schema(self):
        old = self.request["sealed_scope"]
        built = seal.make_sealed_scope(self.request["task_id"], self.request["record"], old["scope"]["finish_point"])
        self.assertEqual(built, old)
        self.assertEqual(built["schema"], seal.SEAL_SCHEMA)

    def test_constructor_rejects_untestable_finish_point(self):
        with self.assertRaises(seal.ScopeRefusal) as caught:
            seal.make_sealed_scope(self.request["task_id"], self.request["record"], {})
        self.assertEqual(caught.exception.code, "GOAL_FINISH_POINT_NOT_TESTABLE")

    def test_constructor_rejects_new_identity_supersession(self):
        with self.assertRaises(seal.ScopeRefusal) as caught:
            seal.make_sealed_scope(self.request["task_id"], self.request["record"],
                                   self.request["sealed_scope"]["scope"]["finish_point"],
                                   supersedes_scope_digest="sha256:" + "1" * 64)
        self.assertEqual(caught.exception.code, "GOAL_SCOPE_SUPERSEDE_ON_NEW_IDENTITY")

    def test_current_producers_use_canonical_scope_schema_tag(self):
        for path in sorted((ROOT / transition.REQUESTS).glob("*.json")):
            request = json.loads(path.read_text())
            self.assertEqual(request["sealed_scope"]["schema"], seal.SEAL_SCHEMA, path)

    def test_foreign_scope_shape_is_reported_without_rewriting_it(self):
        self.request["sealed_scope"]["scope"] = {"queue_item": "fixture", "method": "fixture"}
        self.request["sealed_scope"]["scope_digest"] = seal.digest(self.request["sealed_scope"]["scope"])
        original = copy.deepcopy(self.request)
        self.invalid(self.request, "REGISTRATION_REQUEST_SCHEMA_INVALID")
        self.assertEqual(self.request, original)

    def test_existing_identity_without_seal_is_not_new_identity(self):
        self.request["registration_mode"] = transition.EXISTING_IDENTITY
        self.request.pop("sealed_scope")
        self.assertEqual(preflight.check_request(self.request)["input_status"], "VALID")

    def test_cli_bad_json_fails_without_writing(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.json"; path.write_text("{not-json")
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / "scripts/registration_input_preflight.py"), str(path)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            body = json.loads(result.stdout)
            self.assertEqual(body["results"][0]["failure"]["failure_code"], "REQUEST_INPUT_UNREADABLE")
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
