from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import consume_healer_sovereign_scheduler_request as consumer
from scripts import dispatch_resident_execution_requests as dispatcher


class Completed:
    def __init__(self, result, returncode=0):
        self.returncode = returncode
        self.stdout = json.dumps(result) + "\n"
        self.stderr = ""


class HealerResidentRequestTests(unittest.TestCase):
    def request(self):
        return {
            "schema": "stegverse.resident-execution-request/v1",
            "request_id": "RESIDENT-EXEC-HEALER-SOVEREIGN-SCHEDULER-001",
            "state": "REQUESTED",
            "task_id": consumer.TARGET_TASK,
            "mode": consumer.TARGET_MODE,
            "entrypoint": consumer.TARGET_ENTRYPOINT,
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "heartbeat_grants_execution_authority": False,
            "second_machine_required": False,
            "network_source_fetch_allowed": False,
            "request_granted_authority": False,
            "authority_effect": "NONE_REQUEST_ONLY",
            "standing_request": True,
            "recurrence": "EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE",
        }

    def roots(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        source = root / "source"
        runtime = root / "runtime"
        source.mkdir()
        runtime.mkdir()
        (source / "scripts").mkdir()
        (source / consumer.TARGET_ENTRYPOINT).write_text("# canonical source placeholder\n", encoding="utf-8")
        (runtime / "control/resident-execution-request.d").mkdir(parents=True)
        (runtime / "scripts").mkdir()
        (runtime / consumer.TARGET_ENTRYPOINT).write_text("# resident placeholder\n", encoding="utf-8")
        (runtime / consumer.REQUEST_REL).write_text(json.dumps(self.request()), encoding="utf-8")
        return td, source, runtime

    def test_blocked_scheduler_attempt_remains_retryable(self):
        td, source, runtime = self.roots()
        try:
            result = consumer.consume(source, runtime, runner=lambda *args, **kwargs: Completed({
                "schema": "stegverse.resident-refresh-targeted-execution/v2",
                "execution_result": {"state": "BLOCKED", "transition_id": "HEALER_SOVEREIGN_SCHEDULER_BLOCKED"},
            }), env={"PATH": "/usr/bin", "STEGVERSE_HEALER_ROOT": "/local/healer"})
            self.assertEqual(result["state"], "ATTEMPT_RECORDED")
            self.assertTrue(result["retry_allowed"])
            self.assertTrue(result["standing_request"])
            self.assertFalse(result["terminal_scheduler_completion_observed"])
            self.assertTrue(result["source_runtime_separated"])
        finally:
            td.cleanup()

    def test_completed_cycle_does_not_consume_standing_request(self):
        td, source, runtime = self.roots()
        try:
            calls = {"count": 0}
            def runner(*args, **kwargs):
                calls["count"] += 1
                return Completed({
                    "schema": "stegverse.resident-refresh-targeted-execution/v2",
                    "execution_result": {"state": "HANDOFF_READY", "transition_id": "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"},
                })
            first = consumer.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
            second = consumer.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
            self.assertEqual(first["state"], "CYCLE_COMPLETED")
            self.assertEqual(second["state"], "CYCLE_COMPLETED")
            self.assertEqual(calls["count"], 2)
            self.assertTrue(first["scheduler_cycle_completion_observed"])
            self.assertFalse(first["terminal_scheduler_completion_observed"])
            self.assertFalse(first["request_consumed"])
            self.assertTrue(first["retry_allowed"])
        finally:
            td.cleanup()

    def test_runtime_as_dispatcher_source_resolves_distinct_service_source(self):
        td, source, runtime = self.roots()
        try:
            captured = {}
            def runner(command, **kwargs):
                captured["command"] = command
                return Completed({
                    "schema": "stegverse.resident-refresh-targeted-execution/v2",
                    "execution_result": {"state": "HANDOFF_READY", "transition_id": "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"},
                })
            result = consumer.consume(
                runtime,
                runtime,
                runner=runner,
                env={"PATH": "/usr/bin", "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source)},
            )
            self.assertEqual(result["source_resolution"], "STEGVERSE_HEARTBEAT_SOURCE_ROOT")
            self.assertEqual(Path(result["source_root"]), source.resolve())
            self.assertEqual(Path(result["runtime_root"]), runtime.resolve())
            self.assertTrue(result["source_runtime_separated"])
            self.assertIn(str(source.resolve()), captured["command"])
            self.assertIn(str(runtime.resolve()), captured["command"])
        finally:
            td.cleanup()

    def test_runtime_as_source_without_distinct_source_fails_closed(self):
        td, _source, runtime = self.roots()
        try:
            result = consumer.consume(runtime, runtime, env={"PATH": "/usr/bin"})
            self.assertEqual(result["state"], "ATTEMPT_RECORDED")
            self.assertFalse(result["runtime_execution_attempted"])
            self.assertEqual(result["source_resolution"], "DISTINCT_SOURCE_ROOT_NOT_PROVIDED")
            self.assertEqual(result["blocker"], "DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED")
            self.assertTrue(result["retry_allowed"])
        finally:
            td.cleanup()

    def test_dispatcher_has_exact_healer_selector(self):
        selected = dispatcher.select_consumers(("healer_sovereign_scheduler",))
        self.assertEqual(selected, (("healer_sovereign_scheduler", "scripts/consume_healer_sovereign_scheduler_request.py"),))

    def test_dispatcher_forwards_healer_and_hil_config_as_nonsecret(self):
        env = dispatcher.clean_exec_env({
            "PATH": "/usr/bin",
            "STEGVERSE_HEALER_ROOT": "/local/healer",
            "STEGVERSE_HEARTBEAT_SOURCE_ROOT": "/local/source",
            "STEGVERSE_HIL_INTR_ROUTE_CONFIG": "/local/config/hil-intr-runtime.json",
        })
        self.assertEqual(env["STEGVERSE_HEALER_ROOT"], "/local/healer")
        self.assertEqual(env["STEGVERSE_HEARTBEAT_SOURCE_ROOT"], "/local/source")
        self.assertEqual(env["STEGVERSE_HIL_INTR_ROUTE_CONFIG"], "/local/config/hil-intr-runtime.json")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")


if __name__ == "__main__":
    unittest.main()
