from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "workers" / "universal_governance_enforced_reference_worker.py"
SPEC = importlib.util.spec_from_file_location("universal_governance_enforced_reference_worker", PATH)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(worker)


def invocation():
    return {
        "task": {
            "task_id": worker.TASK_ID,
            "worker_id": worker.WORKER_ID,
            "claim_id": "claim:reference:1",
        },
        "handoff": {
            "authority": {
                "credential_authority": "TV/TVC",
                "repository_writeback_authority": False,
                "publication_authority": False,
                "continuity_mint_authority": False,
                "github_token_required": False,
            }
        },
    }


class UniversalGovernanceEnforcedReferenceWorkerTests(unittest.TestCase):
    def test_invocation_authority_ceiling(self):
        worker.validate_invocation(invocation())
        bad = invocation()
        bad["handoff"]["authority"]["repository_writeback_authority"] = True
        with self.assertRaisesRegex(RuntimeError, "authority escalation"):
            worker.validate_invocation(bad)

    def test_hosted_environment_is_rejected_before_execution(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environments"):
                worker.execute(invocation())

    def test_missing_sources_return_handoff_ready(self):
        response = worker.handoff_response(worker.SourceUnavailable("missing local source"))
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertEqual(
            response["transition_id"],
            "UNIVERSAL_GOVERNANCE_REFERENCE_SOURCE_MATERIALIZATION_PENDING",
        )
        self.assertEqual(response["credential_authority"], "TV/TVC")
        self.assertFalse(response["github_token_used"])
        self.assertFalse(response["repository_writeback_performed"])

    def test_completed_response_preserves_non_authority(self):
        response = worker.completed_response({"local_receipt_ref": "receipts/latest.json"})
        self.assertEqual(response["state"], "COMPLETED")
        self.assertEqual(response["credential_authority"], "TV/TVC")
        self.assertFalse(response["github_token_used"])
        self.assertFalse(response["repository_writeback_performed"])

    def test_process_adapter_confines_bound_state(self):
        value = json.loads(
            (ROOT / "control" / "process-worker-adapters.d" /
             "universal-governance-enforced-reference-001.json").read_text()
        )
        adapter = value["adapters"][0]
        self.assertEqual(adapter["adapter_ref"], "process:universal-governance-enforced-reference-v1")
        self.assertFalse(any("repository" in p for p in adapter["bound_state_allowed_paths"]))
        self.assertEqual(
            set(adapter["bound_state_allowed_paths"]),
            {"stegcore-reference/**", "master-records/**", "receipts/**"},
        )
        self.assertFalse("GITHUB_TOKEN" in adapter["env_allowlist"])

    def test_registry_declares_reference_only_capabilities(self):
        value = json.loads(
            (ROOT / "control" / "worker-registry.d" /
             "universal-governance-enforced-reference-001.json").read_text()
        )
        task = value["tasks"][0]
        wrk = value["workers"][0]
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertEqual(wrk["capability_profile_ref"],
                         "control/worker-capability-profiles.json#universal-governance-reference-v1")
        self.assertEqual(value["credential_authority"], "TV/TVC")
        self.assertFalse(value["github_token_required"])
        self.assertFalse(value["non_tv_tvc_secret_or_token_allowed"])


if __name__ == "__main__":
    unittest.main()
