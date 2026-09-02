import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "project_hb_runtime_presence_observability.py"
SPEC = importlib.util.spec_from_file_location("hb_obs", MODULE_PATH)
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)


class HbRuntimePresenceObservabilityTests(unittest.TestCase):
    def write_json(self, path: Path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_missing_runtime_artifacts_remain_not_observed(self):
        with tempfile.TemporaryDirectory() as td:
            result = M.project(Path(td), env={})
            self.assertEqual(result["resident"]["state"], "NOT_OBSERVED")
            self.assertEqual(result["governed_request"]["dispatch_state"], "NOT_OBSERVED")
            self.assertEqual(result["execution"]["state"], "NOT_OBSERVED")
            self.assertEqual(result["retained_evidence"]["reconstruction_state"], "NOT_OBSERVED")
            self.assertFalse(result["authority"]["heartbeat_grants_execution_authority"])
            self.assertEqual(result["authority"]["credential_authority"], "TV/TVC")

    def test_existing_canonical_state_is_projected_without_authority_widening(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            node = root / "node.json"
            self.write_json(node, {
                "schema": "stegverse.sovereign-node-declaration/v0.4",
                "declared": True,
                "node_id": "SV-NODE-0123456789abcdef01234567",
                "credential_authority": "TV/TVC",
            })
            self.write_json(root / "control/heartbeat-protocol-anchor.json", {
                "schema": "stegverse.heartbeat-protocol-anchor/v1",
                "heartbeat_id": "HB32",
            })
            self.write_json(root / "control/worker-runtime-state.json", {
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 5,
            })
            self.write_json(root / "receipts/sovereign-host/resident-request-dispatch.latest.json", {
                "schema": "stegverse.resident-request-dispatch/v1",
                "state": "COMPLETE",
            })
            result = M.project(root, env={"STEGVERSE_SOVEREIGN_NODE_MARKER": str(node)})
            self.assertEqual(result["resident"]["state"], "OBSERVED")
            self.assertEqual(result["resident"]["node_identity_state"], "OBSERVED")
            self.assertEqual(result["resident"]["node_id"], "SV-NODE-0123456789abcdef01234567")
            self.assertEqual(result["hb_reference"]["state"], "OBSERVED")
            self.assertEqual(result["governed_request"]["dispatch_state"], "OBSERVED")
            self.assertEqual(result["governed_request"]["request_consumption_state"], "NOT_OBSERVED")
            self.assertEqual(result["execution"]["state"], "NOT_OBSERVED")
            self.assertTrue(result["authority"]["interlock_intr_governs_transition"])
            self.assertTrue(result["authority"]["worker_coordinator_remains_admission_claim_fence_authority"])
            self.assertEqual(result["authority"]["authority_effect"], "NONE_OBSERVATION_ONLY")


if __name__ == "__main__":
    unittest.main()
