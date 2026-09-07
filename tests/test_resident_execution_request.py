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
            "request_id": "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-001",
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
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
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
            self.assertEqual(receipt["request_id"], "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-001")

    def test_missing_request_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = mod.consume(Path(td) / "source", Path(td) / "runtime")
            self.assertEqual(receipt["state"], "NO_REQUEST")
            self.assertFalse(receipt["runtime_execution_attempted"])

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
