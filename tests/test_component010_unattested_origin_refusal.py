"""Fail-closed authentic-origin boundary on the already-existing component-010 source CLI."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/evaluate_task_registry_ai_session_checkin.py"
REGISTRY = ROOT / "data/canonical-task-registry.json"

class UnattestedOriginRefusal(unittest.TestCase):
    def invoke(self, context, generation="CURRENT"):
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "events.jsonl"
            observed = json.loads(REGISTRY.read_text())["generation"]
            request = {"task_id": "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001",
                       "checkin_context": context}
            if generation == "CURRENT":
                request["observed_registry_generation"] = observed
            elif generation == "STALE":
                request["observed_registry_generation"] = observed - 1
            env = dict(os.environ, STEGVERSE_TASK_REGISTRY_EVENT_LEDGER=str(ledger))
            proc = subprocess.run([sys.executable, str(WRAPPER)], cwd=ROOT,
                                  input=json.dumps(request), text=True,
                                  capture_output=True, env=env, check=True)
            return json.loads(proc.stdout), ledger.exists()

    def test_declared_chatgpt_origin_never_writes_checkin(self):
        result, existed = self.invoke({"actor_kind": "CHATGPT_SESSION", "session_id": "self-declared"})
        self.assertEqual(result["disposition"], "STOP_AUTHENTIC_ORIGIN_UNAVAILABLE")
        self.assertFalse(result["runtime_identity_attestation_proven"])
        self.assertFalse(result["write_pr_merge_handoff_claim_admissible"])
        self.assertNotIn("checkin_event_sha256", result)
        self.assertFalse(existed)

    def test_claimed_attestation_field_cannot_impersonate_host(self):
        result, existed = self.invoke({"actor_kind": "CHATGPT_SESSION", "session_id": "self-declared",
                                        "runtime_identity_attestation_proven": True,
                                        "authenticated_origin": True,
                                        "attestation": {"trusted": True}})
        self.assertEqual(result["disposition"], "STOP_AUTHENTIC_ORIGIN_UNAVAILABLE")
        self.assertFalse(existed)

    def test_older_and_missing_generation_cannot_write_ledger(self):
        for generation in ("STALE", "MISSING"):
            result, existed = self.invoke({"actor_kind": "CHATGPT_SESSION", "session_id": "fake"}, generation)
            self.assertEqual(result["disposition"], "STOP_AUTHENTIC_ORIGIN_UNAVAILABLE")
            self.assertFalse(existed)

    def test_other_ai_actor_is_already_denied_before_ledger(self):
        result, existed = self.invoke({"actor_kind": "EXTERNAL_MODEL", "session_id": "fake"})
        self.assertEqual(result["disposition"], "STOP_AI_BOUNDARY_DENIED")
        self.assertFalse(existed)

    def test_no_session_id_denied_before_ledger(self):
        result, existed = self.invoke({"actor_kind": "CHATGPT_SESSION"})
        self.assertEqual(result["disposition"], "STOP_SESSION_ID_REQUIRED")
        self.assertFalse(existed)

    def test_source_only_boundary_remains_separate(self):
        policy = json.loads((ROOT / "data/task-registry-ai-ingress-policy.json").read_text())
        self.assertEqual(policy["source_only_coordination_boundary"]["authority_effect"], "NONE")
        self.assertEqual(policy["unattested_chatgpt_session_disposition"], "STOP_AUTHENTIC_ORIGIN_UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
