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


def _synthetic_boundary(mod, *, consumed=False):
    """Inert test receipt; cannot establish a genuine resident claim or custody."""
    checks = {name: True for name in (
        "allow_consumed", "allow_result", "filesystem_not_exposed",
        "network_not_exposed", "deny_not_consumed", "deny_consequence_unreachable",
        "ambient_credentials_not_exposed", "temporary_state_destroyed",
        "egress_evidence_only",
    )}
    return {
        "schema": "stegverse.ungoverned-ai-defensive-envelope-resident-boundary/v1",
        "task_id": mod.TARGET_TASK,
        "component_id": "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011",
        "state": "REPRESENTATIVE_BOUNDARY_PROBE_OBSERVED",
        "claim": {"claim_id": "test-only-G1", "fencing_token": 1,
                  "worker_id": "ungoverned-ai-defensive-envelope-worker"},
        "tvc_source_floor": "0b82b45de7d214fbdb2f24bc4027a6aeb31a7312",
        "tvc_source_head": "test-only-TVC-floor",
        "external_provider_observed": False,
        "goal_runtime_completion_claimed": False,
        "probe": {"denied_interactions": [
            {"probe_id": key, "decision": "DENY",
             "consumed": consumed, "consequence_reachable": False}
            for key in ("FILESYSTEM_OPEN", "NETWORK_IMPORT", "ENVIRONMENT_IMPORT")
        ]},
        "checks": checks,
    }


def _completed_worker_response(mod):
    return {
        "state": "COMPLETED",
        "transition_id": "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_REPRESENTATIVE_BOUNDARY_OBSERVED",
        "checkpoint_ref": mod.BOUNDARY_REL.as_posix(),
        "evidence_refs": [mod.BOUNDARY_REL.as_posix()],
    }


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
            terminal["execution_result"] = _completed_worker_response(mod)
            calls = [nonterminal, terminal]

            def runner(*args, **kwargs):
                payload = calls.pop(0)
                if payload["execution_result"]["state"] == "COMPLETED":
                    boundary_path = runtime / mod.BOUNDARY_REL
                    boundary_path.parent.mkdir(parents=True, exist_ok=True)
                    boundary_path.write_text(json.dumps(_synthetic_boundary(mod)))
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

    def test_forged_completion_without_boundary_receipt_remains_retryable(self):
        mod = _module()
        request = json.loads(REQUEST.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            runtime, source = Path(tmp) / "runtime", Path(tmp) / "source"
            (runtime / mod.REQUEST_REL).parent.mkdir(parents=True)
            (runtime / mod.REQUEST_REL).write_text(json.dumps(request))
            (runtime / mod.TARGET_ENTRYPOINT).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.TARGET_ENTRYPOINT).write_text("# inert")
            source.mkdir()
            result = {
                "mode": mod.TARGET_MODE, "task_id": mod.TARGET_TASK,
                "runtime_execution_attempted": True,
                "network_fetch_performed": False,
                "github_token_runtime_authority": "NONE",
                "credential_authority": "TV/TVC",
                "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
                "execution_result": _completed_worker_response(mod),
            }
            calls = [dict(result), dict(result), dict(result)]
            def runner(*a, **kw):
                value = calls.pop(0)
                if len(calls) == 1:
                    p = runtime / mod.BOUNDARY_REL
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(json.dumps(_synthetic_boundary(mod, consumed=True)))
                if not calls:
                    p = runtime / mod.BOUNDARY_REL
                    p.write_text(json.dumps(_synthetic_boundary(mod, consumed=False)))
                return SimpleNamespace(returncode=0, stdout=json.dumps(value) + "\n", stderr="")
            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
            first = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(first["state"], "ATTEMPT_RECORDED")
            second = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(second["state"], "ATTEMPT_RECORDED")
            third = mod.consume(source, runtime, runner=runner, env=env)
            self.assertEqual(third["state"], "COMPLETED")
            self.assertTrue(third["boundary_receipt_sha256"].startswith("sha256:"))
            self.assertFalse(third["runtime_proof_promoted"])
            self.assertFalse(third["organization_ledger_custody_proven"])
            self.assertFalse(third["master_records_custody_proven"])
            (runtime / mod.BOUNDARY_REL).unlink()
            self.assertFalse(mod.previously_terminal(runtime, request, mod.stable(request)))

    def test_previous_stale_boundary_digest_cannot_authorize_replay(self):
        mod = _module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / mod.BOUNDARY_REL
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps(_synthetic_boundary(mod)))
            prior = mod._boundary_digest(json.loads(p.read_text()))
            self.assertIsNone(mod.verified_boundary_receipt(
                root, _completed_worker_response(mod), previous_digest=prior
            ))

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
