from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

CHAIN_SPEC = importlib.util.spec_from_file_location(
    "run_sv_dn1_first_round_chain",
    ROOT / "scripts/run_sv_dn1_first_round_chain.py",
)
assert CHAIN_SPEC and CHAIN_SPEC.loader
chain = importlib.util.module_from_spec(CHAIN_SPEC)
CHAIN_SPEC.loader.exec_module(chain)

CONSUMER_SPEC = importlib.util.spec_from_file_location(
    "consume_sv_dn1_resident_execution_request",
    ROOT / "scripts/consume_sv_dn1_resident_execution_request.py",
)
assert CONSUMER_SPEC and CONSUMER_SPEC.loader
consumer = importlib.util.module_from_spec(CONSUMER_SPEC)
CONSUMER_SPEC.loader.exec_module(consumer)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class SvDn1SovereignExecutionChainTests(unittest.TestCase):
    def test_hosted_environment_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            with (
                mock.patch.object(chain, "refresh", return_value={"state": "PASS"}),
                self.assertRaisesRegex(RuntimeError, "hosted execution"),
            ):
                chain.execute_chain(base / "source", base / "runtime", env={"GITHUB_ACTIONS": "true"})

    def test_missing_carrier_is_handoff_ready_without_task_execution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            with mock.patch.object(chain, "refresh", return_value={"state": "PASS"}):
                result = chain.execute_chain(source, runtime, env={"HOME": str(base)})
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "SV_DN1_SOVEREIGN_CARRIER_REFERENCE_PENDING")
            self.assertEqual(result["completed_tasks"], [])
            self.assertEqual(result["next_task"], chain.TASKS[0])

    def test_clean_exec_env_strips_credentials_and_keeps_nonsecret_roots(self) -> None:
        env = {
            "HOME": "/tmp/home",
            "PATH": "/usr/bin",
            "GITHUB_TOKEN": "secret",
            "HF_TOKEN": "secret",
            "OPENAI_API_KEY": "secret",
            "STEGVERSE_SDK_SOURCE_ROOT": "/srv/sdk",
            "STEGVERSE_STEGCORE_SOURCE_ROOT": "/srv/stegcore",
        }
        clean = chain.clean_exec_env(env)
        self.assertNotIn("GITHUB_TOKEN", clean)
        self.assertNotIn("HF_TOKEN", clean)
        self.assertNotIn("OPENAI_API_KEY", clean)
        self.assertEqual(clean["STEGVERSE_SDK_SOURCE_ROOT"], "/srv/sdk")
        self.assertEqual(clean["STEGVERSE_STEGCORE_SOURCE_ROOT"], "/srv/stegcore")
        self.assertEqual(clean["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")

    def test_receipt_validation_rejects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            state = base / ".stegverse/state/sv-dn1-source-materialization/receipts/latest.json"
            write_json(state, {
                "state": "COMPLETE",
                "transition_id": "WRONG",
                "github_token_used": False,
                "repository_writeback_performed": False,
            })
            with mock.patch.object(chain.Path, "home", return_value=base):
                with self.assertRaisesRegex(RuntimeError, "durable receipt failed validation"):
                    chain.validate_durable_receipt("SV-DN1-SOURCE-MATERIALIZATION-001", {"HOME": str(base)})

    def test_existing_active_task_stops_chain_without_reacquisition(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "control").mkdir(parents=True)
            write_json(runtime / chain.CARRIER_REL, {"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 31, "generation": 31})
            (runtime / chain.RUNNER_REL).parent.mkdir(parents=True, exist_ok=True)
            (runtime / chain.RUNNER_REL).write_text("# runner\n")
            write_json(runtime / chain.REGISTRY_REL, {
                "tasks": [{
                    "task_id": chain.TASKS[0],
                    "state": "ACTIVE",
                    "claim_id": "existing-claim",
                    "worker_id": "existing-worker",
                }]
            })
            with mock.patch.object(chain, "refresh", return_value={"state": "PASS"}):
                result = chain.execute_chain(source, runtime, env={"HOME": str(base)})
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "SV_DN1_EXISTING_TASK_LIFECYCLE_MUST_RESOLVE")
            self.assertEqual(result["claim_id"], "existing-claim")

    def test_simulated_sequence_advances_only_after_each_completed_registry_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "control").mkdir(parents=True)
            write_json(runtime / chain.CARRIER_REL, {"schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 31, "generation": 31})
            (runtime / chain.RUNNER_REL).parent.mkdir(parents=True, exist_ok=True)
            (runtime / chain.RUNNER_REL).write_text("# runner\n")
            write_json(runtime / chain.REGISTRY_REL, {"tasks": []})

            seen: list[str] = []
            def runner(command, **kwargs):
                task_id = command[-1]
                seen.append(task_id)
                registry = json.loads((runtime / chain.REGISTRY_REL).read_text())
                registry["tasks"] = [
                    row for row in registry.get("tasks", []) if row.get("task_id") != task_id
                ] + [{"task_id": task_id, "state": "COMPLETED"}]
                write_json(runtime / chain.REGISTRY_REL, registry)
                return SimpleNamespace(returncode=0, stdout='{"workers_activated":1}\n', stderr="")

            def receipt(task_id, values):
                return {"task_id": task_id, "receipt_path": str(base / f"{task_id}.json")}

            with (
                mock.patch.object(chain, "refresh", return_value={"state": "PASS"}),
                mock.patch.object(chain, "validate_durable_receipt", side_effect=receipt),
                mock.patch.object(chain, "_load", wraps=chain._load),
            ):
                # The source step reads its receipt to forward source_root. Intercept
                # only that read with a real tiny receipt.
                source_receipt = base / "SV-DN1-SOURCE-MATERIALIZATION-001.json"
                write_json(source_receipt, {"source_root": str(base / "materialized-demo")})
                original_validate = chain.validate_durable_receipt
                def receipt_with_source(task_id, values):
                    if task_id == chain.TASKS[0]:
                        return {"task_id": task_id, "receipt_path": str(source_receipt)}
                    return {"task_id": task_id, "receipt_path": str(base / f"{task_id}.json")}
                with mock.patch.object(chain, "validate_durable_receipt", side_effect=receipt_with_source):
                    result = chain.execute_chain(source, runtime, runner=runner, env={"HOME": str(base)})

            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(result["transition_id"], "SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE")
            self.assertEqual(seen, list(chain.TASKS))
            self.assertEqual(result["completed_tasks"], list(chain.TASKS))

    def test_consumer_request_is_intent_only_and_retries_until_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            runtime.mkdir()
            source.mkdir()
            request = {
                "schema": "stegverse.resident-execution-request/v1",
                "request_id": "RESIDENT-EXEC-SV-DN1-FIRST-ROUND-001",
                "state": "REQUESTED",
                "task_id": consumer.TARGET_TASK,
                "mode": consumer.TARGET_MODE,
                "entrypoint": consumer.TARGET_ENTRYPOINT,
                "fresh_fence_minimum_exclusive": 22,
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "github_token_runtime_authority": "NONE",
                "heartbeat_grants_execution_authority": False,
                "second_machine_required": False,
                "network_source_fetch_allowed": False,
                "request_granted_authority": False,
                "authority_effect": "NONE_REQUEST_ONLY",
            }
            write_json(runtime / consumer.REQUEST_REL, request)
            entrypoint = runtime / consumer.TARGET_ENTRYPOINT
            entrypoint.parent.mkdir(parents=True, exist_ok=True)
            entrypoint.write_text("# chain\n")

            def waiting_runner(*args, **kwargs):
                return SimpleNamespace(
                    returncode=0,
                    stdout='{"state":"HANDOFF_READY","transition_id":"SV_DN1_CHAIN_STEP_NOT_TERMINAL"}\n',
                    stderr="",
                )

            first = consumer.consume(source, runtime, runner=waiting_runner, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertFalse(first["request_granted_authority"])
            self.assertFalse(first["network_authority_granted_by_request"])
            self.assertFalse(consumer.previously_consumed(runtime, request, consumer.stable_hash(request)))

            def terminal_runner(*args, **kwargs):
                return SimpleNamespace(
                    returncode=0,
                    stdout='{"state":"COMPLETE","transition_id":"SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE"}\n',
                    stderr="",
                )

            second = consumer.consume(source, runtime, runner=terminal_runner, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(second["state"], "ATTEMPT_RECORDED")
            self.assertTrue(consumer.previously_consumed(runtime, request, consumer.stable_hash(request)))

    def test_consumer_rejects_hosted_environment(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            consumer.clean_exec_env({"GITHUB_ACTIONS": "true"})


if __name__ == "__main__":
    unittest.main()
