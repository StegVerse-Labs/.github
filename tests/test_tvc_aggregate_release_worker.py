import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.blocker_policy import validate_worker_response_blocker

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "tvc_aggregate_release_worker.py"
HANDOFF = ROOT / "handoffs" / "TVC-ODA3-AGGREGATE-RELEASE-027.json"


class AggregateReleaseWorkerTests(unittest.TestCase):
    def invocation(self):
        return {
            "schema": "stegverse.worker-invocation/v0.1",
            "heartbeat_epoch": 31,
            "task": {
                "task_id": "TVC-ODA3-AGGREGATE-RELEASE-027",
                "claim_id": "SHWP-TVC-ODA3-AGGREGATE-RELEASE-027-G31",
                "heartbeat_timing": {"fencing_token": 31},
            },
            "handoff": json.loads(HANDOFF.read_text(encoding="utf-8")),
            "scope": {
                "required_capabilities": [
                    "runtime_observation",
                    "bounded_process_execution",
                    "tvc_aggregate_release",
                ],
                "allowed_paths": ["receipts/tvc-aggregate-release/**"],
            },
        }

    def test_handoff_has_process_adapter_scope(self):
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        execution = handoff["execution"]
        self.assertIn("tvc_aggregate_release", execution["required_capabilities"])
        self.assertIn("receipts/tvc-aggregate-release/**", execution["allowed_paths"])
        self.assertEqual(execution["generalized_executor"], "tasks/aggregate_release.py")
        self.assertEqual(execution["release_set_id"], "ODA3-EVALUATOR-PATH-2026-08-18-R1")

    def test_worker_emits_policy_valid_blocked_protocol_without_tvc_materialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": tmp,
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
            }
            proc = subprocess.run(
                [sys.executable, str(WORKER)],
                cwd=ROOT,
                env=env,
                input=json.dumps(self.invocation()) + "\n",
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["schema"], "stegverse.worker-response/v0.1")
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["result"]["reason"], "TVC_ROOT_NOT_MATERIALIZED")
        self.assertEqual(result["result"]["credential_authority"], "TV/TVC")
        self.assertFalse(result["result"]["non_tv_tvc_credential_used"])
        self.assertIsInstance(result["blocker"], dict)
        self.assertTrue(result["blocker"]["solution_required"])
        self.assertTrue(result["blocker"]["workaround_candidates"])
        self.assertTrue(result["blocker"]["machine_observable_release_condition"])
        validate_worker_response_blocker(result)
        self.assertTrue(any(ref.startswith("resolution-contract:v1:") for ref in result["evidence_refs"]))


if __name__ == "__main__":
    unittest.main()
