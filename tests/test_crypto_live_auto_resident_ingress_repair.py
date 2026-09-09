#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
TASK_ID = "CRYPTO-LIVE-AUTO-001"


def load_module():
    spec = importlib.util.spec_from_file_location("canonical_work_resident_consumer_repair", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CryptoLiveAutoResidentIngressRepairTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_missing_runtime_request_is_exactly_self_materialized(self):
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as runtime_dir:
            source = Path(source_dir)
            runtime = Path(runtime_dir)
            rel = self.mod.CRYPTO_LIVE_AUTO_SPEC["request_rel"]
            src = source / rel
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text('{"task_id":"CRYPTO-LIVE-AUTO-001"}\n', encoding="utf-8")
            row = self.mod.ensure_request_materialized(source, runtime, self.mod.CRYPTO_LIVE_AUTO_SPEC)
            dst = runtime / rel
            self.assertEqual(dst.read_bytes(), src.read_bytes())
            self.assertTrue(row["exact_copy"])
            self.assertEqual(row["purpose"], "EXPLICIT_STAGED_REQUEST_SELF_MATERIALIZATION")

    def test_stale_runtime_registry_gets_task_specific_fallback_shard(self):
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as runtime_dir:
            source = Path(source_dir)
            runtime = Path(runtime_dir)
            source_registry = source / "data/canonical-task-registry.json"
            source_registry.parent.mkdir(parents=True, exist_ok=True)
            task = {
                "task_id": TASK_ID,
                "correlation_id": TASK_ID,
                "coordination_state": "PROPOSED",
                "allowed_next_transitions": ["INGRESS_ADMITTED"],
                "worker_claim": {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
                "authority_model": {"task_registry_mints_execution_authority": False, "interlock_intr_required_for_governed_ingress_egress": True},
            }
            source_registry.write_text(json.dumps({"tasks": [task]}) + "\n", encoding="utf-8")
            runtime_registry = runtime / "data/canonical-task-registry.json"
            runtime_registry.parent.mkdir(parents=True, exist_ok=True)
            runtime_registry.write_text(json.dumps({"generation": 1, "tasks": []}) + "\n", encoding="utf-8")
            before = runtime_registry.read_bytes()

            row = self.mod.ensure_task_identity_materialized(source, runtime, TASK_ID)
            shard = runtime / "data/canonical-task-records" / f"{TASK_ID}.json"

            self.assertEqual(runtime_registry.read_bytes(), before)
            self.assertTrue(row["materialized"])
            self.assertTrue(row["registry_preserved"])
            self.assertEqual(json.loads(shard.read_text(encoding="utf-8"))["task_id"], TASK_ID)

    def test_existing_runtime_task_identity_is_preserved_without_fallback_shard(self):
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as runtime_dir:
            source = Path(source_dir)
            runtime = Path(runtime_dir)
            task = {"task_id": TASK_ID, "correlation_id": TASK_ID}
            for root in (source, runtime):
                registry = root / "data/canonical-task-registry.json"
                registry.parent.mkdir(parents=True, exist_ok=True)
                registry.write_text(json.dumps({"tasks": [task]}) + "\n", encoding="utf-8")

            row = self.mod.ensure_task_identity_materialized(source, runtime, TASK_ID)

            self.assertFalse(row["materialized"])
            self.assertEqual(row["state"], "MONOLITHIC_RUNTIME_IDENTITY_PRESENT")
            self.assertFalse((runtime / "data/canonical-task-records" / f"{TASK_ID}.json").exists())


if __name__ == "__main__":
    unittest.main()
