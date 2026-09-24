from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/ungoverned_ai_defensive_envelope_worker.py"
REGISTRY = ROOT / "control/worker-registry.d/ungoverned-ai-defensive-envelope-001.json"
ADAPTER = ROOT / "control/process-worker-adapters.d/ungoverned-ai-defensive-envelope-001.json"
REQUEST = ROOT / "control/resident-execution-request.d/ungoverned-ai-defensive-envelope-001.json"
HANDOFF = ROOT / "handoffs/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"


def _module():
    spec = importlib.util.spec_from_file_location("defensive_envelope_worker", WORKER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probe():
    return {
        "component_id": "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011",
        "candidate_origin": "REPRESENTATIVE_UNTRUSTED_SOURCE_NOT_EXTERNAL_PROVIDER_ATTESTATION",
        "external_provider_observed": False,
        "admitted_interaction": {
            "decision": "ALLOW", "consumed": True, "result_observed": 42,
            "filesystem_capability_exposed": False, "network_capability_exposed": False,
            "candidate_source_materialized_to_filesystem": False,
            "temporary_state_destroyed": True,
        },
        "denied_interactions": [{"decision": "DENY", "consumed": False, "consequence_reachable": False}],
        "ambient_credential_capability_exposed": False,
        "task_registry_authority_exposed": False,
        "tv_tvc_authority_exposed": False,
        "interlock_intr_authority_exposed": False,
        "master_records_authority_exposed": False,
        "publisher_authority_exposed": False,
        "host_runtime_authority_exposed": False,
        "candidate_internal_sovereignty_preserved": True,
        "governed_egress_disposition": "EVIDENCE_ONLY_NO_CONSEQUENTIAL_EGRESS_REQUESTED",
    }


class DefensiveEnvelopeWorkerTests(unittest.TestCase):
    def test_registry_adapter_request_and_handoff_are_same_existing_runtime_path(self):
        registry = json.loads(REGISTRY.read_text())
        adapter = json.loads(ADAPTER.read_text())
        request = json.loads(REQUEST.read_text())
        handoff = json.loads(HANDOFF.read_text())
        task = registry["tasks"][0]
        worker = registry["workers"][0]
        process = adapter["adapters"][0]
        self.assertEqual(task["task_id"], "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001")
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertEqual(task["admission"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertTrue(task["admission"]["fresh_fence_required"])
        self.assertFalse(task["admission"]["heartbeat_grants_execution_authority"])
        self.assertEqual(worker["adapter_ref"], process["adapter_ref"])
        self.assertEqual(process["adapter_ref"], request["fail_closed_requirements"]["exact_adapter_ref_required"])
        self.assertEqual(process["env_allowlist"], ["STEGVERSE_TVC_ROOT", "PATH"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["external_provider_origin_required_for_this_probe"])
        self.assertFalse(handoff["completion"]["runtime_observation_claimed"])
        self.assertNotIn("--cosv-task-vector", handoff["completion"]["targeted_command"])

    def test_worker_accepts_only_representative_boundary_evidence(self):
        mod = _module()
        fake = types.ModuleType("tasks.ungoverned_ai_defensive_envelope")
        fake.run_defensive_envelope_probe = _probe
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            task_pkg = types.ModuleType("tasks")
            task_pkg.__path__ = []
            clean_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
            with patch.object(mod, "_tvc_root", return_value=(Path(tmp), mod.TVC_SOURCE_FLOOR)), \
                 patch.object(mod, "RECEIPT_REL", receipt), \
                 patch.dict(sys.modules, {
                     "tasks": task_pkg,
                     "tasks.ungoverned_ai_defensive_envelope": fake,
                 }), \
                 patch.dict(os.environ, clean_env, clear=True):
                invocation = {
                    "schema": "stegverse.worker-invocation/v0.1",
                    "task": {
                        "task_id": mod.TASK_ID, "state": "ACTIVE",
                        "claim_id": "claim-G1",
                        "worker_id": "ungoverned-ai-defensive-envelope-worker",
                        "heartbeat_timing": {"fencing_token": 1},
                    },
                    "scope": {"claim_id": "claim-G1", "fencing_token": 1},
                    "handoff": {"execution": {"required_capabilities": [mod.CAPABILITY]}},
                }
                response = mod.run(invocation)
            self.assertEqual(response["state"], "COMPLETED")
            retained = json.loads(receipt.read_text())
            body = json.dumps(retained, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            self.assertEqual(response["boundary_receipt_sha256"], "sha256:" + hashlib.sha256(body).hexdigest())
            self.assertEqual(response["boundary_claim_id"], "claim-G1")
            self.assertEqual(response["boundary_fencing_token"], 1)
            self.assertFalse(retained["external_provider_observed"])
            self.assertFalse(retained["goal_runtime_completion_claimed"])
            self.assertFalse(retained["probe"]["denied_interactions"][0]["consumed"])
            self.assertFalse(retained["probe"]["denied_interactions"][0]["consequence_reachable"])

    def test_worker_rejects_ambient_protected_environment(self):
        mod = _module()
        invocation = {
            "schema": "stegverse.worker-invocation/v0.1",
            "task": {
                "task_id": mod.TASK_ID, "state": "ACTIVE",
                "claim_id": "claim-G2",
                "worker_id": "ungoverned-ai-defensive-envelope-worker",
                "heartbeat_timing": {"fencing_token": 2},
            },
            "scope": {"claim_id": "claim-G2", "fencing_token": 2},
            "handoff": {"execution": {"required_capabilities": [mod.CAPABILITY]}},
        }
        with patch.dict(os.environ, {"PATH": "/usr/bin:/bin", "GITHUB_TOKEN": "must-not-cross"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AMBIENT_PROTECTED_AUTHORITY_ENVIRONMENT_PRESENT"):
                mod.run(invocation)


if __name__ == "__main__":
    unittest.main()
