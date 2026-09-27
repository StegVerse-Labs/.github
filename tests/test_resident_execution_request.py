from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_resident_execution_request",
    ROOT / "scripts/consume_resident_execution_request.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ResidentExecutionRequestTests(unittest.TestCase):
    def request(self) -> dict:
        return {
            "schema": "stegverse.resident-execution-request/v1",
            "request_id": "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002",
            "state": "REQUESTED",
            "task_id": "SHWP-ECOSYSTEM-CHAT-INFERENCE-001",
            "mode": "DEDICATED_ECOSYSTEM_CHAT_PARENT",
            "entrypoint": "scripts/refresh_and_execute_resident_task.py",
            "fresh_fence_minimum_exclusive": 24,
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "heartbeat_grants_execution_authority": False,
            "second_machine_required": False,
            "network_source_fetch_allowed": False,
            "request_granted_authority": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }

    def test_request_is_intent_only_and_invokes_dedicated_portable_parent_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / "scripts").mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# target\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                payload = {"runtime_execution_attempted": True, "execution_result_observed": True}
                return SimpleNamespace(returncode=0, stdout=json.dumps(payload) + "\n", stderr="")

            first = mod.consume(source, runtime, runner=runner)
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertEqual(first["disposition"], "FAIL_CLOSED")
            self.assertEqual(first["failed_predicate"], "PORTABLE_BRIDGE_RESULT_NOT_VERIFIED")
            self.assertFalse(first["consequence_committed"])
            self.assertTrue(first["runtime_execution_attempted"])
            self.assertFalse(first["request_granted_authority"])
            self.assertEqual(first["fresh_fence_minimum_exclusive"], 24)
            self.assertEqual(len(calls), 1)
            self.assertFalse(first["post_parent_activation_projection"]["attempted"])
            command = calls[0][0]
            self.assertIn("--ecosystem-chat-parent", command)
            self.assertIn("--source-root", command)
            self.assertIn("--runtime-root", command)

            second = mod.consume(source, runtime, runner=runner)
            self.assertEqual(second["state"], "ALREADY_CONSUMED_NON_ALLOW")
            self.assertEqual(second["disposition"], "FAIL_CLOSED")
            self.assertEqual(second["failed_predicate"], "PORTABLE_BRIDGE_RESULT_NOT_VERIFIED")
            self.assertFalse(second["runtime_execution_attempted"])
            self.assertEqual(len(calls), 1)

    def test_unrelated_singleton_request_cannot_overwrite_ecosystem_chat_request(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            runtime = root / "runtime"
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / "scripts").mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / "control/resident-execution-request.json").write_text(
                json.dumps({
                    "schema": "stegverse.resident-execution-request/v1",
                    "request_id": "UNRELATED-REQUEST",
                    "state": "REQUESTED",
                    "task_id": "UNRELATED-TASK"
                }) + "\n",
                encoding="utf-8",
            )
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# target\n", encoding="utf-8")

            def runner(command, **kwargs):
                payload = {"runtime_execution_attempted": True, "execution_result_observed": True}
                return SimpleNamespace(returncode=0, stdout=json.dumps(payload) + "\n", stderr="")

            receipt = mod.consume(source, runtime, runner=runner)
            self.assertEqual(receipt["state"], "ATTEMPT_RECORDED")
            self.assertEqual(receipt["request_id"], "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002")

    def test_nested_parent_handoff_is_not_terminal_even_on_zero_exit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# fixture\n", encoding="utf-8")

            def runner(command, **kwargs):
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "schema": "stegverse.resident-refresh-targeted-execution/v3",
                    "task_id": mod.TARGET_TASK,
                    "mode": mod.TARGET_MODE,
                    "execution_returncode": 0,
                    "execution_result_observed": True,
                    "execution_result": {
                        "schema": "stegverse.independent-ecosystem-chat-parent-execution/v1",
                        "task_id": mod.TARGET_TASK,
                        "state": "HANDOFF_READY",
                        "attempt_fencing_token": 25,
                    },
                }) + "\n", stderr="")

            receipt = mod.consume(root / "source", runtime, runner=runner)
            self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
            self.assertEqual(receipt["failed_predicate"], "PARENT_TERMINAL_RECONSTRUCTION_NOT_VERIFIED")
            self.assertFalse(receipt["upstream_parent_terminal_claim_observed"])
            self.assertFalse(receipt["post_parent_activation_projection"]["attempted"])

    def test_nested_parent_completed_fails_closed_without_original_projection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# fixture\n", encoding="utf-8")
            activation = {
                "schema": "stegverse.ecosystem-chat-independent-parent-activation/v1",
                "task_id": mod.TARGET_TASK,
                "state": "PASS",
                "fencing_token": 25,
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                **{key: True for key in (
                    "sovereign_runtime_execution_surface_observed",
                    "ephemeral_e1_e2_execution_observed", "measured_usage_persisted",
                    "provider_usage_reconstruction_pass", "transition_reconstruction_pass",
                    "same_execution", "persistent_conversational_runtime_ready",
                )},
            }

            def runner(command, **kwargs):
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "schema": "stegverse.resident-refresh-targeted-execution/v3",
                    "task_id": mod.TARGET_TASK, "mode": mod.TARGET_MODE,
                    "execution_returncode": 0, "execution_result_observed": True,
                    "execution_result": {
                        "schema": "stegverse.independent-ecosystem-chat-parent-execution/v1",
                        "task_id": mod.TARGET_TASK,
                        "state": "COMPLETED", "attempt_fencing_token": 25,
                        "terminal_activation_receipt": activation,
                    },
                }) + "\n", stderr="")

            from unittest.mock import patch
            with patch.dict("os.environ", {"STEGVERSE_LLM_ADAPTER_ROOT": ""}):
                receipt = mod.consume(root / "source", runtime, runner=runner)
            self.assertTrue(receipt["upstream_parent_terminal_claim_observed"])
            self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
            self.assertEqual(receipt["failed_predicate"], "ACTIVATION_EVIDENCE_PROJECTION_NOT_VERIFIED")
            self.assertFalse(receipt["authentic_intr_disposition_observed_by_consumer"])
            self.assertFalse(receipt["consequence_committed"])

    def test_missing_request_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = mod.consume(Path(td) / "source", Path(td) / "runtime")
            self.assertEqual(receipt["state"], "NO_REQUEST")
            self.assertFalse(receipt["runtime_execution_attempted"])

    def test_exact_unchanged_canonical_g25_request_is_accepted(self):
        canonical_path = ROOT / mod.REQUEST_REL
        canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
        self.assertEqual(canonical["request_id"], "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002")
        self.assertEqual(canonical["fresh_fence_minimum_exclusive"], 24)
        mod.validate_request(canonical)

    def test_historical_g23_fence_is_not_eligible_for_current_parent(self):
        request = self.request()
        request["fresh_fence_minimum_exclusive"] = 22
        with self.assertRaisesRegex(RuntimeError, "fresh-fence floor mismatch"):
            mod.validate_request(request)

    def test_request_cannot_expand_authority(self):
        request = self.request()
        request["heartbeat_grants_execution_authority"] = True
        with self.assertRaises(RuntimeError):
            mod.validate_request(request)
        request = self.request()
        request["fresh_fence_minimum_exclusive"] = 20
        with self.assertRaises(RuntimeError):
            mod.validate_request(request)
        request = self.request()
        request["github_token_required"] = True
        with self.assertRaises(RuntimeError):
            mod.validate_request(request)


if __name__ == "__main__":
    unittest.main()
