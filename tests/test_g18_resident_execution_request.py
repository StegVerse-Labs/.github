from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_g18_resident_execution_request",
    ROOT / "scripts/consume_g18_resident_execution_request.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class G18ResidentExecutionRequestTests(unittest.TestCase):
    def request(self) -> dict:
        return json.loads(
            (ROOT / "control/resident-execution-request.d/g18-sovereign-runtime-resume.json").read_text(
                encoding="utf-8"
            )
        )

    def bridge_result(self, *, claim_id: str = mod.EXPECTED_CLAIM_ID, fence: int = mod.EXPECTED_FENCE) -> dict:
        return {
            "schema": "stegverse.resident-refresh-targeted-execution/v2",
            "mode": "RESUME_EXISTING_CLAIM",
            "task_id": mod.TARGET_TASK,
            "existing_claim_preflight": {
                "task_id": mod.TARGET_TASK,
                "state": "BLOCKED",
                "claim_id": claim_id,
                "worker_id": "sovereign-runtime-activation-worker",
                "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                "fencing_token": fence,
            },
            "existing_claim_postflight": {
                "task_id": mod.TARGET_TASK,
                "state": "BLOCKED",
                "claim_id": claim_id,
                "worker_id": "sovereign-runtime-activation-worker",
                "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                "fencing_token": fence,
            },
            "new_claim_requested": False,
            "existing_fence_preserved_by_mode": True,
            "runtime_execution_attempted": True,
        }

    def test_canonical_request_is_intent_only_for_existing_g18_fence(self) -> None:
        request = self.request()
        mod.validate_request(request)
        self.assertEqual(request["expected_claim_id"], mod.EXPECTED_CLAIM_ID)
        self.assertEqual(request["expected_fencing_token"], 18)
        self.assertTrue(request["existing_claim_required"])
        self.assertFalse(request["new_claim_allowed"])
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["github_token_required"])
        self.assertFalse(request["second_machine_required"])

    def test_consumer_invokes_resume_mode_once_and_records_exact_claim(self) -> None:
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
                    "STEGVERSE_HEARTBEAT_SOURCE_ROOT": "/srv/stegverse/source",
                    "GITHUB_TOKEN": "forbidden",
                    "ZEROEX_API_KEY": "forbidden",
                },
            )
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertTrue(first["exact_existing_claim_observed"])
            self.assertTrue(first["bridge_mode_valid"])
            self.assertFalse(first["new_claim_allowed"])
            self.assertEqual(first["expected_fencing_token"], 18)
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertIn("--resume-claimed-task-id", command)
            self.assertIn(mod.TARGET_TASK, command)
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertNotIn("ZEROEX_API_KEY", kwargs["env"])
            self.assertEqual(kwargs["env"]["STEGVERSE_SOVEREIGN_NODE"], "1")

            second = mod.consume(source, runtime, runner=runner)
            self.assertEqual(second["state"], "ALREADY_CONSUMED")
            self.assertFalse(second["runtime_execution_attempted"])
            self.assertEqual(len(calls), 1)

    def test_mismatched_claim_or_fence_fails_closed(self) -> None:
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
                return SimpleNamespace(
                    returncode=0,
                    stdout=json.dumps(self.bridge_result(fence=19)) + "\n",
                    stderr="",
                )

            receipt = mod.consume(source, runtime, runner=runner)
            self.assertEqual(receipt["state"], "FAIL_CLOSED")
            self.assertFalse(receipt["exact_existing_claim_observed"])
            self.assertTrue(receipt["runtime_execution_attempted"])

    def test_request_cannot_expand_or_replace_claim_authority(self) -> None:
        for key, value in (
            ("new_claim_allowed", True),
            ("request_granted_authority", True),
            ("heartbeat_grants_execution_authority", True),
            ("github_token_required", True),
            ("expected_fencing_token", 19),
            ("expected_claim_id", "SHWP-OTHER-G19"),
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
