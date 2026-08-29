from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_hil_resident_execution_request",
    ROOT / "scripts/consume_hil_resident_execution_request.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class HILResidentExecutionRequestTests(unittest.TestCase):
    def request(self) -> dict:
        return json.loads(
            (ROOT / "control/resident-execution-request.d/hil-sovereign-receiver-001.json").read_text(
                encoding="utf-8"
            )
        )

    def bridge_result(self) -> dict:
        return {
            "schema": "stegverse.resident-refresh-targeted-execution/v2",
            "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
            "task_id": mod.TARGET_TASK,
            "runtime_execution_attempted": True,
            "execution_result_observed": True,
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        }

    def test_canonical_request_is_intent_only(self) -> None:
        request = self.request()
        mod.validate_request(request)
        self.assertEqual(request["task_id"], mod.TARGET_TASK)
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["credential_requirement"], "NONE_FOR_PARTICIPANT_INTAKE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["github_token_required"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_consumer_invokes_only_existing_targeted_bridge_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# bridge\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(self.bridge_result()) + "\n",
                    stderr="",
                )

            first = mod.consume(
                source,
                runtime,
                runner=runner,
                env={
                    "PATH": "/bin",
                    "HOME": "/home/stegverse",
                    "STEGVERSE_SOVEREIGN_NODE": "1",
                    "STEGVERSE_LLM_ADAPTER_ROOT": "/srv/stegverse/llm-adapter",
                    "STEGVERSE_HIL_STATE_ROOT": "/srv/stegverse/hil",
                    "GITHUB_TOKEN": "forbidden",
                    "CLOUDFLARE_API_TOKEN": "forbidden",
                },
            )
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertIn("--task-id", command)
            self.assertIn(mod.TARGET_TASK, command)
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertNotIn("CLOUDFLARE_API_TOKEN", kwargs["env"])
            self.assertEqual(kwargs["env"]["STEGVERSE_LLM_ADAPTER_ROOT"], "/srv/stegverse/llm-adapter")
            self.assertFalse(first["request_granted_authority"])
            self.assertFalse(first["heartbeat_grants_execution_authority"])
            self.assertFalse(first["github_token_required"])
            self.assertFalse(first["second_machine_required"])

            second = mod.consume(source, runtime, runner=runner)
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
            self.assertFalse(second["runtime_execution_attempted"])
            self.assertEqual(len(calls), 1)

    def test_missing_execution_result_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# bridge\n", encoding="utf-8")

            def runner(command, **kwargs):
                return SimpleNamespace(returncode=1, stdout="", stderr="blocked")

            result = mod.consume(source, runtime, runner=runner)
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertTrue(result["runtime_execution_attempted"])
            self.assertFalse(result["execution_result_observed"])


if __name__ == "__main__":
    unittest.main()
