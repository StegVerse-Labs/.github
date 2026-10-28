"""Negative checks for the existing Registry ingress projection (no authority minted)."""
import importlib.util
import tempfile
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("admitted_projection", ROOT / "scripts" / "apply_admitted_canonical_work_projection.py")
projection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projection)


def task(state="PROPOSED", transitions=None):
    return {"task_id": "TEST-INGRESS-001", "correlation_id": "TEST-INGRESS-001",
            "coordination_state": state,
            "allowed_next_transitions": ["NATIVE_ADMISSION_EVALUATION"] if transitions is None else transitions}


def receipts():
    ingress = {"schema": projection.INGRESS_SCHEMA, "state": "INGRESS_ADMITTED",
               "authority_effect": "INGRESS_TRANSITION_ONLY", "claim_or_fence_minted": False,
               "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
               "materialization_id": "fixture", "request_hash": "fixture-request",
               "payload_hash": "fixture-payload", "operation_id": "TASK_INGRESS"}
    consumption = {"schema": projection.CONSUMPTION_SCHEMA,
                   "state": "INGRESS_BOUND_COORDINATION_PROJECTED", "claim_or_fence_minted": False,
                   "materialization_id": "fixture", "request_hash": "fixture-request",
                   "payload_hash": "fixture-payload", "operation_id": "TASK_INGRESS",
                   "task_id": "TEST-INGRESS-001", "correlation_id": "TEST-INGRESS-001",
                   "ingress_receipt_ref": "fixture://not-sovereign"}
    return ingress, consumption


class AdmissionBoundaryNegativeTests(unittest.TestCase):
    def test_valid_single_shard_projection_is_not_execution_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "TEST-INGRESS-001.json"
            p.write_text(json.dumps(task()))
            kind, projected, target = projection.project({"tasks": []}, *receipts(), task_shards=Path(tmp))
            self.assertEqual((kind, target), ("SHARDED_REGISTRY", p))
            self.assertEqual(projected["coordination_state"], "INGRESS_ADMITTED")
            self.assertNotIn("worker_claim", projected)

    def test_replay_refused(self):
        with self.assertRaisesRegex(SystemExit, "current task state is not ingress-projectable"):
            projection.project_task(task("INGRESS_ADMITTED"), correlation_id="TEST-INGRESS-001",
                                    ingress=receipts()[0], consumption=receipts()[1])

    def test_disallowed_transition_refused(self):
        with self.assertRaisesRegex(SystemExit, "native admission transition not permitted"):
            projection.project_task(task(transitions=[]), correlation_id="TEST-INGRESS-001",
                                    ingress=receipts()[0], consumption=receipts()[1])

    def test_aggregate_and_shard_must_not_partially_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "TEST-INGRESS-001.json"
            p.write_text(json.dumps(task()))
            original = p.read_bytes()
            with self.assertRaisesRegex(SystemExit, "dual aggregate/shard projection"):
                projection.project({"tasks": [task()]}, *receipts(), task_shards=Path(tmp))
            self.assertEqual(p.read_bytes(), original)

    def test_divergent_aggregate_shard_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "TEST-INGRESS-001.json"
            p.write_text(json.dumps(task("CLAIMED")))
            with self.assertRaisesRegex(SystemExit, "aggregate/shard divergence"):
                projection.project({"tasks": [task()]}, *receipts(), task_shards=Path(tmp))

    def test_mismatched_receipt_binding_refused(self):
        ingress, consumption = receipts()
        consumption["request_hash"] = "different"
        with self.assertRaisesRegex(SystemExit, "binding mismatch"):
            projection.validate_receipts(ingress, consumption)


if __name__ == "__main__":
    unittest.main()
