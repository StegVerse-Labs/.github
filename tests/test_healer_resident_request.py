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
        (source / consumer.REQUEST_REL).parent.mkdir(parents=True)
        (source / consumer.REQUEST_REL).write_text(json.dumps(self.request()), encoding="utf-8")
        (runtime / "control/resident-execution-request.d").mkdir(parents=True)
        (runtime / "scripts").mkdir()
        (runtime / consumer.TARGET_ENTRYPOINT).write_text("# resident placeholder\n", encoding="utf-8")
        (runtime / consumer.REQUEST_REL).write_text(json.dumps(self.request()), encoding="utf-8")
        for rel in consumer.NEUTRAL_SCHEDULER_REQUIRED:
            path = runtime / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n" if path.suffix == ".json" else "# scheduler\n", encoding="utf-8")
        return td, source, runtime

    @staticmethod
    def completed_cycle():
        return Completed({
            "schema": "stegverse.resident-refresh-targeted-execution/v3",
            "execution_result": {
                "schema": "stegverse.worker-runtime-cycle-result/v1",
                "target_task_id": consumer.TARGET_TASK,
                "targeted_independent_task_control": True,
                "events": [{
                    "event_type": "worker_response",
                    "task_id": consumer.TARGET_TASK,
                    "transition_id": "HEALER_SOVEREIGN_SCHEDULER_COMPLETED",
                    "transition_sequence": 1,
                    "response_state": "HANDOFF_READY",
                }],
            },
        })

    def test_missing_request_and_source_retains_no_request_receipt_without_execution(self):
        td, _source, runtime = self.roots()
        try:
            (runtime / consumer.REQUEST_REL).unlink()
            calls = []
            result = consumer.consume(
                runtime, runtime,
                runner=lambda *args, **kwargs: calls.append(args),
                env={"PATH": "/usr/bin"},
            )
            persisted = json.loads((runtime / consumer.CONSUMPTION_REL).read_text(encoding="utf-8"))
            self.assertEqual(result, persisted)
            self.assertEqual(result["state"], "NO_REQUEST")
            self.assertEqual(result["source_resolution"], "DISTINCT_SOURCE_ROOT_NOT_PROVIDED")
            self.assertEqual(result["task_id"], consumer.TARGET_TASK)
            self.assertIsNone(result["request_id"])
            self.assertFalse(result["runtime_execution_attempted"])
            self.assertFalse(result["request_consumed"])
            self.assertFalse(result["scheduler_cycle_completion_observed"])
            self.assertFalse(result["request_granted_authority"])
            self.assertTrue(result["retry_allowed"])
            self.assertEqual(calls, [])
        finally:
            td.cleanup()

    def test_missing_request_observation_is_replaced_by_authentic_later_source_cycle(self):
        td, source, runtime = self.roots()
        try:
            (runtime / consumer.REQUEST_REL).unlink()
            before = consumer.consume(runtime, runtime, env={"PATH": "/usr/bin"})
            self.assertEqual(before["state"], "NO_REQUEST")
            after = consumer.consume(
                source, runtime,
                runner=lambda *args, **kwargs: self.completed_cycle(),
                env={"PATH": "/usr/bin"},
            )
            retained = json.loads((runtime / consumer.CONSUMPTION_REL).read_text(encoding="utf-8"))
            self.assertEqual(after, retained)
            self.assertEqual(after["state"], "CYCLE_COMPLETED")
            self.assertTrue(after["request_materialization"]["copied"])
            self.assertFalse(after["request_consumed"])
        finally:
            td.cleanup()

    def test_existing_request_missing_distinct_source_retains_retryable_failure(self):
        td, _source, runtime = self.roots()
        try:
            result = consumer.consume(runtime, runtime, env={"PATH": "/usr/bin"})
            retained = json.loads((runtime / consumer.CONSUMPTION_REL).read_text(encoding="utf-8"))
            self.assertEqual(result, retained)
            self.assertEqual(result["state"], "ATTEMPT_RECORDED")
            self.assertEqual(result["blocker"], "DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED")
            self.assertFalse(result["runtime_execution_attempted"])
            self.assertFalse(result["request_consumed"])
            self.assertTrue(result["retry_allowed"])
        finally:
            td.cleanup()

    def test_missing_runtime_request_self_materializes_from_canonical_source(self):
        td, source, runtime = self.roots()
        try:
            (runtime / consumer.REQUEST_REL).unlink()
            captured = {}
            def runner(command, **kwargs):
                captured["command"] = command
                return self.completed_cycle()
            result = consumer.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
            self.assertEqual(result["state"], "CYCLE_COMPLETED")
            self.assertTrue((runtime / consumer.REQUEST_REL).is_file())
            self.assertEqual((runtime / consumer.REQUEST_REL).read_bytes(), (source / consumer.REQUEST_REL).read_bytes())
            self.assertEqual(result["request_materialization"]["state"], "EXACT_CANONICAL_REQUEST_MATERIALIZED")
            self.assertFalse(result["request_materialization"]["request_granted_authority"])
            self.assertEqual(result["neutral_scheduler_materialization"]["state"], "NEUTRAL_SCHEDULER_ALREADY_MATERIALIZED")
            self.assertEqual(Path(captured["command"][1]), (source / consumer.TARGET_ENTRYPOINT).resolve())
        finally:
            td.cleanup()

    def test_missing_neutral_scheduler_is_materialized_before_healer_execution(self):
        td, source, runtime = self.roots()
        try:
            for rel in consumer.NEUTRAL_SCHEDULER_REQUIRED:
                (runtime / rel).unlink()
                source_path = source / rel
                source_path.parent.mkdir(parents=True, exist_ok=True)
                source_path.write_text("{}\n" if source_path.suffix == ".json" else "# canonical scheduler\n", encoding="utf-8")
            adapter = source / consumer.REUSABLE_REFRESH_ENTRYPOINT
            adapter.write_text("# canonical reusable refresh adapter\n", encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                if Path(command[1]) == adapter.resolve():
                    params = json.loads(kwargs["env"]["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"])
                    self.assertEqual(Path(params["source_root"]), source.resolve())
                    self.assertEqual(Path(params["runtime_root"]), runtime.resolve())
                    for rel in consumer.NEUTRAL_SCHEDULER_REQUIRED:
                        target = runtime / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes((source / rel).read_bytes())
                    return Completed({
                        "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                        "network_fetch_performed": False,
                        "credential_read_or_acquired": False,
                        "mutable_runtime_state_preserved": True,
                    })
                return self.completed_cycle()

            result = consumer.consume(source, runtime, runner=runner, env={"PATH": "/usr/bin"})
            self.assertEqual(result["state"], "CYCLE_COMPLETED")
            self.assertEqual(result["neutral_scheduler_materialization"]["state"], "NEUTRAL_SCHEDULER_MATERIALIZED_FROM_LOCAL_CANONICAL_SOURCE")
            self.assertTrue(result["neutral_scheduler_materialization"]["attempted"])
            self.assertEqual(result["neutral_scheduler_materialization"]["missing_after"], [])
            self.assertEqual(len(calls), 2)
            self.assertEqual(Path(calls[0][1]), adapter.resolve())
            self.assertEqual(Path(calls[1][1]), (source / consumer.TARGET_ENTRYPOINT).resolve())
        finally:
            td.cleanup()

    def test_stale_runtime_request_is_replaced_by_exact_canonical_bytes(self):
        td, source, runtime = self.roots()
        try:
            (runtime / consumer.REQUEST_REL).write_text('{"stale":true}\n', encoding="utf-8")
            result = consumer.consume(source, runtime, runner=lambda *args, **kwargs: self.completed_cycle(), env={"PATH": "/usr/bin"})
            self.assertEqual(result["state"], "CYCLE_COMPLETED")
            self.assertEqual((runtime / consumer.REQUEST_REL).read_bytes(), (source / consumer.REQUEST_REL).read_bytes())
            self.assertTrue(result["request_materialization"]["copied"])
        finally:
            td.cleanup()

    def test_projected_checkpoint_retention_pointer_is_carried_into_consumption_result(self):
        td, source, runtime = self.roots()
        try:
            packet_path = runtime / consumer.ROOT_OBSERVATION_REL
            packet_path.parent.mkdir(parents=True, exist_ok=True)
            packet_path.write_text(json.dumps({"state":"RESIDENT_CUSTODY_ROOT_OBSERVED"}, sort_keys=True) + "\n", encoding="utf-8")
            pointer = {
                "packet_ref": str(packet_path),
                "packet_relative_path": consumer.ROOT_OBSERVATION_REL.as_posix(),
                "packet_sha256": consumer.file_sha256(packet_path),
                "retained_under_root": str(runtime.resolve()),
                "retained_under_root_source": "CANONICAL_LOCAL_RUNTIME",
                "packet_state": "RESIDENT_CUSTODY_ROOT_OBSERVED",
            }
            checkpoint_path = runtime / consumer.CHECKPOINT_REL
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_text(json.dumps({"child_receipt":{"resident_custody_root_observation_retention":pointer}}, sort_keys=True) + "\n", encoding="utf-8")
            result = consumer.consume(source, runtime, runner=lambda *args, **kwargs: self.completed_cycle(), env={"PATH":"/usr/bin"})
            self.assertEqual(result["state"], "CYCLE_COMPLETED")
            self.assertEqual(result["execution_result"]["resident_custody_root_observation_retention"], pointer)
            self.assertEqual(result["execution_result"]["resident_custody_root_observation_retention_binding"]["state"], "VALIDATED_PROJECTED_RETENTION_POINTER_BOUND")
            persisted = json.loads((runtime / consumer.CONSUMPTION_REL).read_text(encoding="utf-8"))
            self.assertEqual(persisted["execution_result"]["resident_custody_root_observation_retention"], pointer)
        finally:
            td.cleanup()

    def test_projected_checkpoint_pointer_fails_closed_on_packet_hash_mismatch(self):
        td, source, runtime = self.roots()
        try:
            packet_path = runtime / consumer.ROOT_OBSERVATION_REL
            packet_path.parent.mkdir(parents=True, exist_ok=True)
            packet_path.write_text('{"state":"RESIDENT_CUSTODY_ROOT_OBSERVED"}\n', encoding="utf-8")
            checkpoint_path = runtime / consumer.CHECKPOINT_REL
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_text(json.dumps({"child_receipt":{"resident_custody_root_observation_retention":{
                "packet_ref":str(packet_path),
                "packet_relative_path":consumer.ROOT_OBSERVATION_REL.as_posix(),
                "packet_sha256":"0"*64,
                "retained_under_root":str(runtime.resolve()),
                "retained_under_root_source":"CANONICAL_LOCAL_RUNTIME",
                "packet_state":"RESIDENT_CUSTODY_ROOT_OBSERVED"
            }}}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "sha256 mismatch"):
                consumer.consume(source, runtime, runner=lambda *args, **kwargs: self.completed_cycle(), env={"PATH":"/usr/bin"})
        finally:
            td.cleanup()

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
                return self.completed_cycle()
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
                return self.completed_cycle()
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
            self.assertEqual(Path(captured["command"][1]), (source / consumer.TARGET_ENTRYPOINT).resolve())
            self.assertIn(str(source.resolve()), captured["command"])
            self.assertIn(str(runtime.resolve()), captured["command"])
        finally:
            td.cleanup()

    def test_runtime_as_source_resolves_canonical_source_from_existing_repo_map(self):
        td, source, runtime = self.roots()
        try:
            captured = {}
            def runner(command, **kwargs):
                captured["command"] = command
                return self.completed_cycle()
            result = consumer.consume(
                runtime,
                runtime,
                runner=runner,
                env={
                    "PATH": "/usr/bin",
                    "STEGVERSE_REPO_ROOTS_JSON": json.dumps({"StegVerse-Labs/.github": str(source)}),
                },
            )
            self.assertEqual(result["state"], "CYCLE_COMPLETED")
            self.assertEqual(result["source_resolution"], "STEGVERSE_REPO_ROOTS_JSON")
            self.assertEqual(Path(result["source_root"]), source.resolve())
            self.assertEqual(Path(captured["command"][1]), (source / consumer.TARGET_ENTRYPOINT).resolve())
        finally:
            td.cleanup()

    def test_invalid_repo_map_fails_closed_without_execution(self):
        td, _source, runtime = self.roots()
        try:
            result = consumer.consume(
                runtime,
                runtime,
                env={"PATH": "/usr/bin", "STEGVERSE_REPO_ROOTS_JSON": "not-json"},
            )
            self.assertEqual(result["state"], "ATTEMPT_RECORDED")
            self.assertFalse(result["runtime_execution_attempted"])
            self.assertEqual(result["source_resolution"], "REPO_ROOTS_JSON_INVALID")
            self.assertEqual(result["blocker"], "DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED")
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

    def test_real_workercoordinator_cycle_envelope_is_recognized_as_completed(self):
        result = json.loads(self.completed_cycle().stdout)
        self.assertTrue(consumer.completed_healer_cycle_observed(result))

    def test_dispatcher_accepts_cycle_completed_as_successful_consumer_state(self):
        import inspect
        source = inspect.getsource(dispatcher.dispatch)
        self.assertIn('"CYCLE_COMPLETED"', source)

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
