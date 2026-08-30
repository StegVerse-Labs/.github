from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_cmc028_resident_execution_request",
    ROOT / "scripts/consume_cmc028_resident_execution_request.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class CMC028ResidentExecutionRequestTests(unittest.TestCase):
    def request(self) -> dict:
        return json.loads((ROOT / mod.REQUEST_REL).read_text(encoding="utf-8"))

    def bridge_result(self) -> dict:
        return {
            "schema": "stegverse.resident-refresh-targeted-execution/v2",
            "mode": mod.TARGET_MODE,
            "task_id": mod.TARGET_TASK,
            "runtime_execution_attempted": True,
            "network_fetch_performed": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "second_machine_required": False,
            "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
            "execution_result": {"state": "BLOCKED"},
        }

    def stage(self, base: Path) -> tuple[Path, Path]:
        source, runtime = base / "source", base / "runtime"
        source.mkdir()
        request_path = runtime / mod.REQUEST_REL
        request_path.parent.mkdir(parents=True)
        request_path.write_text(json.dumps(self.request()) + "\n", encoding="utf-8")
        entrypoint = runtime / mod.TARGET_ENTRYPOINT
        entrypoint.parent.mkdir(parents=True, exist_ok=True)
        entrypoint.write_text("# bridge\n", encoding="utf-8")
        return source, runtime

    def test_request_is_strictly_non_authorizing(self) -> None:
        request = self.request()
        mod.validate_request(request)
        for key in (
            "github_token_required", "heartbeat_grants_execution_authority",
            "second_machine_required", "network_source_fetch_allowed",
            "request_granted_authority", "protected_material_allowed_in_request",
            "certificate_issuance_authority", "signing_authority",
        ):
            self.assertFalse(request[key], key)

    def test_exact_task_attempt_is_once_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.stage(Path(td))
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps(self.bridge_result()) + "\n", stderr=""
                )

            first = mod.consume(
                source,
                runtime,
                runner=runner,
                env={
                    "PATH": "/bin",
                    "HOME": "/home/stegverse",
                    "STEGVERSE_TVC_ROOT": "/srv/stegverse/TVC",
                    "GITHUB_TOKEN": "forbidden",
                    "ROOT_PRIVATE_KEY": "forbidden",
                    "RECOVERY_SHARE": "forbidden",
                },
            )
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertFalse(first["custody_verified_claimed_by_consumer"])
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertEqual(command[-2:], ["--task-id", mod.TARGET_TASK])
            self.assertEqual(kwargs["env"]["STEGVERSE_TVC_ROOT"], "/srv/stegverse/TVC")
            for name in ("GITHUB_TOKEN", "ROOT_PRIVATE_KEY", "RECOVERY_SHARE"):
                self.assertNotIn(name, kwargs["env"])
            second = mod.consume(source, runtime, runner=runner, env={"PATH": "/bin"})
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
            self.assertEqual(len(calls), 1)

    def test_request_mutation_fails_closed(self) -> None:
        for key, value in (
            ("task_id", "OTHER"),
            ("request_granted_authority", True),
            ("protected_material_allowed_in_request", True),
            ("certificate_issuance_authority", True),
            ("signing_authority", True),
            ("second_machine_required", True),
        ):
            request = self.request()
            request[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                mod.validate_request(request)

    def test_hosted_runtime_is_rejected_before_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, runtime = self.stage(Path(td))
            calls = []
            with self.assertRaises(RuntimeError):
                mod.consume(
                    source,
                    runtime,
                    runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                    env={"PATH": "/bin", "GITHUB_ACTIONS": "true"},
                )
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
