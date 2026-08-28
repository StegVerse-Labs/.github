from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_ara_graph_resident_execution_request",
    ROOT / "scripts/consume_ara_graph_resident_execution_request.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class AraGraphResidentExecutionRequestTests(unittest.TestCase):
    def request(self) -> dict:
        return json.loads(
            (ROOT / "control/resident-execution-request.d/ara-graph-runtime-086.json").read_text(
                encoding="utf-8"
            )
        )

    def bridge_result(self) -> dict:
        return {
            "schema": "stegverse.resident-refresh-targeted-execution/v2",
            "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
            "task_id": mod.TARGET_TASK,
            "runtime_execution_attempted": True,
            "network_fetch_performed": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "second_machine_required": False,
            "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
            "execution_result": {
                "status": "blocked",
                "reason": "ARA_GRAPH_PREFLIGHT_BLOCKED",
            },
        }

    def test_canonical_request_is_intent_only(self) -> None:
        request = self.request()
        mod.validate_request(request)
        self.assertEqual(request["task_id"], mod.TARGET_TASK)
        self.assertEqual(request["mode"], "TARGETED_INDEPENDENT_TASK_CONTROL")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["provider_credential_material_allowed"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["github_token_required"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_consumer_invokes_exact_target_once_with_nonsecret_ara_bindings(self) -> None:
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

            env = {
                "PATH": "/bin",
                "HOME": "/home/stegverse",
                "STEGVERSE_TVC_ROOT": "/srv/stegverse/TVC",
                "STEGVERSE_ARA_MAIL_SENDER": "sender@example.invalid",
                "STEGVERSE_ARA_MAIL_RECIPIENT": "recipient@example.invalid",
                "STEGVERSE_VAULT_AGENT_SOCKET": "/run/stegverse/vault-agent.sock",
                "GITHUB_TOKEN": "forbidden",
                "STEGVERSE_MAIL_CLIENT_SECRET": "forbidden",
                "STEGVERSE_MAIL_ACCESS_TOKEN": "forbidden",
                "AZURE_CLIENT_SECRET": "forbidden",
            }
            first = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertTrue(first["bridge_contract_valid"])
            self.assertFalse(first["provider_success_claimed"])
            self.assertFalse(first["activation_claimed"])
            self.assertEqual(len(calls), 1)

            command, kwargs = calls[0]
            self.assertIn("--task-id", command)
            self.assertIn(mod.TARGET_TASK, command)
            self.assertEqual(kwargs["env"]["STEGVERSE_TVC_ROOT"], "/srv/stegverse/TVC")
            self.assertEqual(
                kwargs["env"]["STEGVERSE_ARA_MAIL_SENDER"], "sender@example.invalid"
            )
            self.assertEqual(
                kwargs["env"]["STEGVERSE_ARA_MAIL_RECIPIENT"], "recipient@example.invalid"
            )
            self.assertEqual(
                kwargs["env"]["STEGVERSE_VAULT_AGENT_SOCKET"],
                "/run/stegverse/vault-agent.sock",
            )
            for forbidden in (
                "GITHUB_TOKEN",
                "STEGVERSE_MAIL_CLIENT_SECRET",
                "STEGVERSE_MAIL_ACCESS_TOKEN",
                "AZURE_CLIENT_SECRET",
            ):
                self.assertNotIn(forbidden, kwargs["env"])

            second = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
            self.assertFalse(second["runtime_execution_attempted"])
            self.assertEqual(len(calls), 1)

    def test_bridge_mismatch_fails_closed_without_inventing_provider_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# bridge\n", encoding="utf-8")

            bad = self.bridge_result()
            bad["task_id"] = "SHWP-OTHER"

            def runner(command, **kwargs):
                return SimpleNamespace(returncode=0, stdout=json.dumps(bad) + "\n", stderr="")

            receipt = mod.consume(source, runtime, runner=runner, env={"PATH": "/bin"})
            self.assertEqual(receipt["state"], "FAIL_CLOSED")
            self.assertFalse(receipt["bridge_contract_valid"])
            self.assertFalse(receipt["provider_success_claimed"])
            self.assertFalse(receipt["activation_claimed"])

    def test_hosted_environment_fails_before_execution(self) -> None:
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
                calls.append(command)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with self.assertRaises(RuntimeError):
                mod.consume(
                    source,
                    runtime,
                    runner=runner,
                    env={"PATH": "/bin", "GITHUB_ACTIONS": "true"},
                )
            self.assertEqual(calls, [])

    def test_request_mutation_cannot_expand_authority(self) -> None:
        for key, value in (
            ("request_granted_authority", True),
            ("provider_credential_material_allowed", True),
            ("heartbeat_grants_execution_authority", True),
            ("github_token_required", True),
            ("network_source_fetch_allowed", True),
            ("second_machine_required", True),
            ("task_id", "SHWP-OTHER"),
            ("mode", "RESUME_EXISTING_CLAIM"),
        ):
            request = self.request()
            request[key] = value
            with self.subTest(key=key):
                with self.assertRaises(RuntimeError):
                    mod.validate_request(request)

    def test_missing_request_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            receipt = mod.consume(Path(td) / "source", Path(td) / "runtime")
            self.assertEqual(receipt["state"], "NO_REQUEST")
            self.assertFalse(receipt["runtime_execution_attempted"])


if __name__ == "__main__":
    unittest.main()
