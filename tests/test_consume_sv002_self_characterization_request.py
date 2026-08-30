from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "consume_sv002_self_characterization_request",
    ROOT / "scripts/consume_sv002_self_characterization_request.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def request():
    return {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-SV002-SELF-CHARACTERIZATION-001",
        "state": "REQUESTED",
        "task_id": mod.TASK_ID,
        "mode": "TARGETED_INDEPENDENT_TASK_CONTROL",
    }


class SV002SelfCharacterizationConsumerTests(unittest.TestCase):
    def test_terminal_detection_accepts_completed_worker_transition(self):
        self.assertTrue(
            mod.terminal_execution_observed(
                {
                    "execution_result": {
                        "state": "COMPLETED",
                        "transition_id": "SV002_SELF_CHARACTERIZATION_COMPLETED",
                    }
                }
            )
        )

    def test_terminal_detection_rejects_blocked_attempt(self):
        self.assertFalse(
            mod.terminal_execution_observed(
                {
                    "execution_result": {
                        "state": "BLOCKED",
                        "transition_id": "SV002_SELF_CHARACTERIZATION_BLOCKED",
                    }
                }
            )
        )

    def test_blocked_prior_attempt_is_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            source = root / "source"
            source.mkdir()
            request_path = runtime / mod.REQUEST_REL
            request_path.parent.mkdir(parents=True)
            req = request()
            request_path.write_text(json.dumps(req), encoding="utf-8")

            prior_path = runtime / mod.RECEIPT_REL
            prior_path.parent.mkdir(parents=True)
            prior_path.write_text(
                json.dumps(
                    {
                        "request_sha256": mod.stable(req),
                        "runtime_execution_attempted": True,
                        "terminal_execution_observed": False,
                        "state": "ATTEMPT_RECORDED",
                    }
                ),
                encoding="utf-8",
            )

            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps(
                        {
                            "state": "BLOCKED",
                            "transition_id": "SV002_SELF_CHARACTERIZATION_BLOCKED",
                        }
                    )
                    + "\n",
                    stderr="",
                )

            receipt = mod.consume(source, runtime, runner=runner)
            self.assertEqual(len(calls), 1)
            self.assertEqual(receipt["state"], "ATTEMPT_RECORDED")
            self.assertFalse(receipt["terminal_execution_observed"])
            self.assertTrue(receipt["retry_allowed"])

    def test_terminal_prior_attempt_is_exactly_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            source = root / "source"
            source.mkdir()
            request_path = runtime / mod.REQUEST_REL
            request_path.parent.mkdir(parents=True)
            req = request()
            request_path.write_text(json.dumps(req), encoding="utf-8")

            prior_path = runtime / mod.RECEIPT_REL
            prior_path.parent.mkdir(parents=True)
            prior_path.write_text(
                json.dumps(
                    {
                        "request_sha256": mod.stable(req),
                        "runtime_execution_attempted": True,
                        "terminal_execution_observed": True,
                        "state": "COMPLETED",
                    }
                ),
                encoding="utf-8",
            )

            def runner(*args, **kwargs):
                raise AssertionError("terminal request must not execute twice")

            receipt = mod.consume(source, runtime, runner=runner)
            self.assertEqual(receipt["state"], "ALREADY_CONSUMED")
            self.assertTrue(receipt["terminal_execution_observed"])
            self.assertFalse(receipt["runtime_execution_attempted"])

    def test_successful_attempt_terminalizes_request(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = root / "runtime"
            source = root / "source"
            source.mkdir()
            request_path = runtime / mod.REQUEST_REL
            request_path.parent.mkdir(parents=True)
            req = request()
            request_path.write_text(json.dumps(req), encoding="utf-8")

            def runner(command, **kwargs):
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps(
                        {
                            "state": "COMPLETED",
                            "transition_id": "SV002_SELF_CHARACTERIZATION_COMPLETED",
                        }
                    )
                    + "\n",
                    stderr="",
                )

            receipt = mod.consume(source, runtime, runner=runner)
            self.assertEqual(receipt["state"], "COMPLETED")
            self.assertTrue(receipt["terminal_execution_observed"])
            self.assertFalse(receipt["retry_allowed"])
            self.assertTrue(receipt["exactly_once_after_terminal"])


if __name__ == "__main__":
    unittest.main()
