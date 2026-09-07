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
        return json.loads((ROOT / "control/resident-execution-request.d/hil-sovereign-receiver-001.json").read_text(encoding="utf-8"))

    def setup_runtime(self, base: Path) -> tuple[Path, Path]:
        source = base / "source"
        runtime = base / "runtime"
        source.mkdir()
        (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
        (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
        (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True, exist_ok=True)
        (runtime / mod.TARGET_ENTRYPOINT).write_text("# bridge\n", encoding="utf-8")
        return source, runtime

    def test_canonical_request_is_intent_only(self) -> None:
        request = self.request()
        mod.validate_request(request)
        self.assertEqual(request["task_id"], mod.TARGET_TASK)
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["second_machine_required"])

    def test_local_ready_consumes_request_without_gateway_or_broader_lifecycle_completion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.setup_runtime(Path(td))
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                self.assertIn(mod.TARGET_ENTRYPOINT, command[1])
                self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "schema": "stegverse.resident-refresh-targeted-execution/v2",
                    "transition_id": "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED",
                    "runtime_execution_attempted": True,
                }) + "\n", stderr="")

            first = mod.consume(source, runtime, runner=runner, env={"PATH": "/bin", "GITHUB_TOKEN": "forbidden"})
            self.assertEqual(first["state"], "COMPLETED")
            self.assertTrue(first["runtime_execution_attempted"])
            self.assertTrue(first["terminal_hil_transition_observed"])
            self.assertEqual(first["terminal_hil_transition"], "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED")
            self.assertFalse(first["broader_hil_lifecycle_complete"])
            self.assertFalse(first["retry_allowed"])
            self.assertFalse(first["public_gateway_required_for_lease_open"])
            self.assertEqual(first["route_materialization"]["state"], "NOT_REQUIRED_SAME_DEVICE")
            self.assertEqual(len(calls), 1)

            second = mod.consume(source, runtime, runner=runner, env={"PATH": "/bin"})
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
            self.assertEqual(len(calls), 1)

    def test_later_hil_transition_also_consumes_request_without_gateway(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.setup_runtime(Path(td))
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "schema": "stegverse.resident-refresh-targeted-execution/v2",
                    "transition_id": "HIL_PUBLIC_HTTPS_RENDEZVOUS",
                    "runtime_execution_attempted": True,
                }) + "\n", stderr="")

            first = mod.consume(source, runtime, runner=runner, env={"PATH": "/bin"})
            self.assertEqual(first["state"], "COMPLETED")
            self.assertTrue(first["terminal_hil_transition_observed"])
            self.assertFalse(first["broader_hil_lifecycle_complete"])
            self.assertFalse(first["retry_allowed"])
            self.assertEqual(len(calls), 1)

    def test_missing_execution_result_fails_closed_but_not_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.setup_runtime(Path(td))
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(returncode=1, stdout="", stderr="runtime attempt failed")

            result = mod.consume(source, runtime, runner=runner, env={"PATH": "/bin"})
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertTrue(result["runtime_execution_attempted"])
            self.assertFalse(result["terminal_hil_transition_observed"])
            self.assertFalse(result["broader_hil_lifecycle_complete"])
            self.assertTrue(result["retry_allowed"])
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
