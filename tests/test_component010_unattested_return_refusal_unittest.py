"""Component-010: untrusted JSON may not write ChatGPT RETURNED/CHECK_OUT."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDER = ROOT / "scripts/record_task_registry_session_return.py"
CLOSE = ROOT / "scripts/materialize_task_session_close.py"


def candidate(verified=False):
    return {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
        "disposition": "CONTINUE",
        "authority_effect": "NONE",
        "ai_session_ingress": {
            "actor_kind": "CHATGPT_SESSION",
            "reusable_component_id": "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010",
            "runtime_identity_attestation_proven": verified,
            "authenticated_origin": verified,
            "authority_effect": "NONE",
        },
    }


class UnattestedReturnRefusal(unittest.TestCase):
    def invoke(self, path, actor, payload, ledger):
        return subprocess.run([
            sys.executable, str(path),
            "--task-id", "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
            "--session-id", "self-declared-session",
            "--actor-kind", actor,
            "--ledger", str(ledger),
        ], input=json.dumps(payload), capture_output=True, text=True)

    def test_untrusted_and_spoofed_origin_never_write_return(self):
        for claimed in (False, True):
            with self.subTest(claimed=claimed), tempfile.TemporaryDirectory() as d:
                ledger = Path(d) / "events.jsonl"
                result = self.invoke(RECORDER, "CHATGPT_SESSION", candidate(claimed), ledger)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("STOP_AUTHENTIC_ORIGIN_UNAVAILABLE", result.stderr)
                self.assertFalse(ledger.exists())

    def test_untrusted_and_spoofed_origin_never_close_session(self):
        for claimed in (False, True):
            with self.subTest(claimed=claimed), tempfile.TemporaryDirectory() as d:
                ledger = Path(d) / "events.jsonl"
                result = self.invoke(CLOSE, "CHATGPT_SESSION", candidate(claimed), ledger)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(ledger.exists())

    def test_existing_internal_non_ai_return_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "events.jsonl"
            payload = {
                "schema": "stegverse.task-registry-checkin-disposition/v1",
                "task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
                "disposition": "CONTINUE",
                "authority_effect": "NONE",
            }
            result = self.invoke(RECORDER, "NON_AI_SYSTEM_COORDINATOR", payload, ledger)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(ledger.exists())
            self.assertEqual(json.loads(result.stdout)["actor_kind"], "NON_AI_SYSTEM_COORDINATOR")


if __name__ == "__main__":
    unittest.main()
