#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("canonical_work_builder_native_email", ROOT / "scripts" / "build_canonical_work_intr_request.py")
bootstrap = load_module("canonical_work_bootstrap_native_email", ROOT / "scripts" / "run_canonical_work_event_bootstrap.py")


class NativeEmailCanonicalTaskRegistryTests(unittest.TestCase):
    def test_native_email_resolves_from_canonical_shard(self) -> None:
        task, source = builder.resolve_task(task_id=TASK_ID, registry=REGISTRY, registry_shards=SHARDS)
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertTrue(source.startswith("SHARDED_REGISTRY:"), source)
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertEqual(task["checkout_state"], "UNCLAIMED")
        self.assertEqual(task["cosv_task_vector"], "10100000100000")
        self.assertEqual(task["allowed_next_transitions"], ["INGRESS_ADMITTED"])
        self.assertFalse(task["completion"]["claimed"])
        self.assertFalse(task["completion"]["activation_proof_complete"])

    def test_native_email_is_generic_ingress_eligible(self) -> None:
        task = bootstrap.validate_target_task(registry=REGISTRY, registry_shards=SHARDS, task_id=TASK_ID)
        self.assertEqual(task["worker_claim"]["authority"], "WORKERCOORDINATOR")
        self.assertTrue(task["worker_claim"]["projection_only"])
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertEqual(task["authority_model"]["credential_authority"], "TV/TVC")
        self.assertEqual(task["authority_model"]["github_token_runtime_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
