from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "scripts/consume_ungoverned_ai_defensive_envelope_request.py"
REQUEST = ROOT / "control/resident-execution-request.d/ungoverned-ai-defensive-envelope-001.json"
DISPATCHER = ROOT / "scripts/dispatch_resident_execution_requests.py"
REFRESH = ROOT / "scripts/refresh_sovereign_worker_runtime_source.py"


def _module():
    spec = importlib.util.spec_from_file_location("defensive_envelope_consumer", CONSUMER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class DefensiveEnvelopeResidentConsumerTests(unittest.TestCase):
    def test_existing_dispatcher_and_source_refresh_own_the_consumer(self):
        dispatcher = DISPATCHER.read_text()
        refresh = REFRESH.read_text()
        self.assertIn(
            '("ungoverned_ai_defensive_envelope", "scripts/consume_ungoverned_ai_defensive_envelope_request.py")',
            dispatcher,
        )
        self.assertIn('Path("scripts/consume_ungoverned_ai_defensive_envelope_request.py")', refresh)

    def test_request_consumption_preserves_retry_until_terminal(self):
        mod = _module()
        request = json.loads(REQUEST.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            source = Path(tmp) / "source"
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(request))
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# placeholder")
            source.mkdir()

            nonterminal = {
                "mode": mod.TARGET_MODE,
                "task_id": mod.TARGET_TASK,
                "runtime_execution_attempted": True,
                "network_fetch_performed": False,
                "github_token_runtime_authority": "NONE",
                "credential_authority": "TV/TVC",
                "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
                "execution_result": {
                    "state": "HANDOFF_READY",
                    "transition_id": "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_RUNTIME_NOT_PROVEN",
                },
            }
            terminal = dict(nonterminal)
            terminal["execution_result"] = {
                "state": "COMPLETED",
                "transition_id": "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_REPRESENTATIVE_BOUNDARY_OBSERVED",
            }
            calls = [nonterminal, terminal]

            def runner(*args, **kwargs):
                payload = calls.pop(0)
                return SimpleNamespace(returncode=0, stdout=json.dumps(payload) + "\n", stderr="")

            env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "STEGVERSE_TVC_ROOT": str(Path(tmp) / "tvc"),
            }
            first = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            self.assertFalse(first["terminal"])
            second = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(second["state"], "COMPLETED")
            self.assertTrue(second["terminal"])
            third = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(third["state"], "ALREADY_TERMINAL")
            self.assertFalse(third["runtime_execution_attempted"])

    def test_consumer_never_forwards_protected_environment(self):
        mod = _module()
        source = {
            "PATH": "/usr/bin:/bin",
            "STEGVERSE_TVC_ROOT": "/tmp/tvc",
            "GITHUB_TOKEN": "forbidden",
            "OPENAI_API_KEY": "forbidden",
            "MASTER_RECORDS_RECEIPT_KEY": "forbidden",
        }
        clean = mod.clean_env(source)
        self.assertEqual(clean["STEGVERSE_TVC_ROOT"], "/tmp/tvc")
        self.assertNotIn("GITHUB_TOKEN", clean)
        self.assertNotIn("OPENAI_API_KEY", clean)
        self.assertNotIn("MASTER_RECORDS_RECEIPT_KEY", clean)
        self.assertEqual(clean["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")


if __name__ == "__main__":
    unittest.main()
