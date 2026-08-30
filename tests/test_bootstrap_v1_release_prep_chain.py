from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_bootstrap_v1_release_prep_chain as chain
import consume_bootstrap_v1_release_prep_request as consumer
import dispatch_resident_execution_requests as dispatcher


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def source_prep_receipt(base: Path) -> dict:
    roots = {
        "stegverse.sdk": str(base / "sdk"),
        "stegverse.stegcore": str(base / "stegcore"),
        "stegverse.core-lite": str(base / "core-lite"),
        "stegverse.master-records": str(base / "master-records"),
    }
    return {
        "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
        "state": "COMPLETE",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "source_identity_scheme": "sha256-content-manifest",
        "migration_anchors_verified": True,
        "network_source_fetch_performed": False,
        "github_platform_required": False,
        "credential_used": False,
        "github_token_used": False,
        "repository_writeback_performed": False,
        "sdk_admitted": False,
        "source_roots": roots,
        "source_identities": {
            component: "sha256:" + (str(index + 1) * 64)[:64]
            for index, component in enumerate(roots)
        },
        "source_root_env": {
            "STEGVERSE_SDK_SOURCE_ROOT": roots["stegverse.sdk"],
            "STEGVERSE_STEGCORE_SOURCE_ROOT": roots["stegverse.stegcore"],
            "STEGVERSE_CORE_LITE_SOURCE_ROOT": roots["stegverse.core-lite"],
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": roots["stegverse.master-records"],
        },
    }


def request() -> dict:
    return {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-BOOTSTRAP-V1-RELEASE-PREP-001",
        "state": "REQUESTED",
        "task_id": consumer.TARGET_TASK,
        "mode": consumer.TARGET_MODE,
        "entrypoint": consumer.TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive": consumer.MINIMUM_FENCE_EXCLUSIVE,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "repository_writeback_authority": False,
        "release_activation_authority": False,
        "publication_authority": False,
        "package_execution_authority": False,
        "sdk_admission_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }


class BootstrapV1ReleasePrepChainTests(unittest.TestCase):
    def test_hosted_environment_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            with (
                mock.patch.object(chain, "refresh", return_value={"state": "PASS"}),
                self.assertRaisesRegex(RuntimeError, "hosted execution"),
            ):
                chain.execute_chain(base / "source", base / "runtime", env={"GITHUB_ACTIONS": "true"})

    def test_missing_carrier_is_retryable_without_task_execution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            with mock.patch.object(chain, "refresh", return_value={"state": "PASS"}):
                result = chain.execute_chain(source, runtime, env={"HOME": str(base)})
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "BOOTSTRAP_V1_SOVEREIGN_CARRIER_REFERENCE_PENDING")
            self.assertEqual(result["next_task"], chain.TASKS[0])

    def test_upstream_registry_must_be_completed_before_bootstrap_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "control").mkdir(parents=True)
            write_json(runtime / chain.CARRIER_REL, {"epoch": 31})
            (runtime / chain.RUNNER_REL).parent.mkdir(parents=True, exist_ok=True)
            (runtime / chain.RUNNER_REL).write_text("# runner\n", encoding="utf-8")
            write_json(runtime / chain.REGISTRY_REL, {"tasks": []})
            with mock.patch.object(chain, "refresh", return_value={"state": "PASS"}):
                result = chain.execute_chain(source, runtime, env={"HOME": str(base)})
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "BOOTSTRAP_V1_PRODUCTION_SOURCE_PREP_PENDING")

    def test_source_prep_prerequisite_validates_exact_identity_set(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            prep = base / "prep"
            write_json(prep / "receipts/latest.json", source_prep_receipt(base))
            result = chain.validate_source_prep_prerequisite({
                "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT": str(prep)
            })
            self.assertTrue(result["receipt_path"].endswith("receipts/latest.json"))
            value = source_prep_receipt(base)
            value["source_identities"]["stegverse.sdk"] = "sha256:xyz"
            write_json(prep / "receipts/latest.json", value)
            with self.assertRaisesRegex(RuntimeError, "sha256"):
                chain.validate_source_prep_prerequisite({
                    "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT": str(prep)
                })

    def test_full_sequence_runs_only_existing_admitted_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            prep = base / "prep"
            source.mkdir()
            (runtime / "control").mkdir(parents=True)
            write_json(runtime / chain.CARRIER_REL, {"epoch": 31})
            (runtime / chain.RUNNER_REL).parent.mkdir(parents=True, exist_ok=True)
            (runtime / chain.RUNNER_REL).write_text("# runner\n", encoding="utf-8")
            write_json(runtime / chain.REGISTRY_REL, {
                "tasks": [{"task_id": chain.UPSTREAM_TASK, "state": "COMPLETED"}]
            })
            write_json(prep / "receipts/latest.json", source_prep_receipt(base))

            seen = []
            def runner(command, **kwargs):
                task_id = command[-1]
                seen.append(task_id)
                registry = json.loads((runtime / chain.REGISTRY_REL).read_text())
                registry["tasks"] = [
                    row for row in registry["tasks"] if row.get("task_id") != task_id
                ] + [{"task_id": task_id, "state": "COMPLETED"}]
                write_json(runtime / chain.REGISTRY_REL, registry)
                return SimpleNamespace(returncode=0, stdout='{"workers_activated":1}\n', stderr="")

            def durable(task_id, values):
                return {
                    "task_id": task_id,
                    "receipt_path": str(base / f"{task_id}.json"),
                    "receipt": {"state": "COMPLETE"},
                }

            with (
                mock.patch.object(chain, "refresh", return_value={"state": "PASS"}),
                mock.patch.object(chain, "validate_durable_receipt", side_effect=durable),
            ):
                result = chain.execute_chain(
                    source,
                    runtime,
                    runner=runner,
                    env={
                        "HOME": str(base),
                        "PATH": "/usr/bin",
                        "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT": str(prep),
                        "GITHUB_TOKEN": "forbidden",
                    },
                )
            self.assertEqual(result["state"], "COMPLETE")
            self.assertEqual(result["transition_id"], "BOOTSTRAP_V1_SOVEREIGN_RELEASE_PREP_COMPLETE")
            self.assertEqual(seen, list(chain.TASKS))
            self.assertEqual(result["completed_tasks"], list(chain.TASKS))
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["repository_writeback_performed"])
            self.assertFalse(result["release_activated"])
            self.assertFalse(result["publication_performed"])

    def test_clean_env_strips_credentials_and_preserves_only_nonsecret_locators(self) -> None:
        env = chain.clean_exec_env({
            "HOME": "/tmp/home",
            "PATH": "/usr/bin",
            "STEGVERSE_SOURCE_PACKAGE_ROOT": "/srv/packages",
            "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT": "/srv/freeze",
            "GITHUB_TOKEN": "secret",
            "OPENAI_API_KEY": "secret",
        })
        self.assertEqual(env["STEGVERSE_SOURCE_PACKAGE_ROOT"], "/srv/packages")
        self.assertEqual(env["STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT"], "/srv/freeze")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")


class BootstrapV1ReleasePrepConsumerTests(unittest.TestCase):
    def test_request_contract_is_intent_only(self) -> None:
        value = request()
        consumer.validate_request(value)
        self.assertFalse(value["request_granted_authority"])
        self.assertFalse(value["network_source_fetch_allowed"])
        self.assertFalse(value["repository_writeback_authority"])
        self.assertFalse(value["release_activation_authority"])
        self.assertFalse(value["publication_authority"])
        self.assertFalse(value["package_execution_authority"])
        self.assertFalse(value["sdk_admission_authority"])

    def test_consumer_retries_until_terminal_chain_result(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            write_json(runtime / consumer.REQUEST_REL, request())
            entrypoint = runtime / consumer.TARGET_ENTRYPOINT
            entrypoint.parent.mkdir(parents=True, exist_ok=True)
            entrypoint.write_text("# chain\n", encoding="utf-8")

            waiting = lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout='{"state":"HANDOFF_READY","transition_id":"BOOTSTRAP_V1_PRODUCTION_SOURCE_PREP_PENDING"}\n',
                stderr="",
            )
            first = consumer.consume(source, runtime, runner=waiting, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertFalse(consumer.previously_consumed(runtime, request(), consumer.stable_hash(request())))

            terminal = lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout='{"state":"COMPLETE","transition_id":"BOOTSTRAP_V1_SOVEREIGN_RELEASE_PREP_COMPLETE"}\n',
                stderr="",
            )
            second = consumer.consume(source, runtime, runner=terminal, env={"HOME": str(base), "PATH": "/usr/bin"})
            self.assertEqual(second["state"], "ATTEMPT_RECORDED")
            self.assertTrue(consumer.previously_consumed(runtime, request(), consumer.stable_hash(request())))

    def test_consumer_rejects_hosted_environment(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            consumer.clean_exec_env({"GITHUB_ACTIONS": "true"})


class BootstrapV1DispatcherRegistrationTests(unittest.TestCase):
    def test_dispatcher_visits_bootstrap_after_sv_dn1(self) -> None:
        names = [name for name, _ in dispatcher.CONSUMERS]
        self.assertIn("bootstrap_v1_release_prep", names)
        self.assertLess(names.index("sv_dn1"), names.index("bootstrap_v1_release_prep"))
        mapping = dict(dispatcher.CONSUMERS)
        self.assertEqual(
            mapping["bootstrap_v1_release_prep"],
            "scripts/consume_bootstrap_v1_release_prep_request.py",
        )


if __name__ == "__main__":
    unittest.main()
