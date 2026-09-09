#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
TASK_ID = "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = load_module("canonical_work_builder", ROOT / "scripts" / "build_canonical_work_intr_request.py")
bootstrap = load_module("canonical_work_bootstrap", ROOT / "scripts" / "run_canonical_work_event_bootstrap.py")
projection = load_module("canonical_work_projection", ROOT / "scripts" / "apply_admitted_canonical_work_projection.py")


class ShardedCanonicalWorkIngressTests(unittest.TestCase):
    def test_stegbrowser_resolves_from_canonical_shard(self):
        task, source = builder.resolve_task(task_id=TASK_ID, registry=REGISTRY, registry_shards=SHARDS)
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertTrue(source.startswith("SHARDED_REGISTRY:"), source)
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertEqual(task["allowed_next_transitions"], ["INGRESS_ADMITTED"])

    def test_stegbrowser_is_ingress_eligible_through_generic_bootstrap(self):
        task = bootstrap.validate_target_task(registry=REGISTRY, registry_shards=SHARDS, task_id=TASK_ID)
        self.assertEqual(task["worker_claim"]["authority"], "WORKERCOORDINATOR")
        self.assertTrue(task["worker_claim"]["projection_only"])
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])

    def test_sharded_post_ingress_projection_updates_task_record_shape(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        materialization_id = "INTR-MAT-test-sharded-browser"
        request_hash = "sha256:" + "a" * 64
        payload_hash = "sha256:" + "b" * 64
        ingress_ref = "runtime://canonical-work-ingress/test-sharded-browser"
        consumption_ref = "runtime://canonical-work-consumption/test-sharded-browser"
        ingress = {
            "schema": projection.INGRESS_SCHEMA,
            "state": "INGRESS_ADMITTED",
            "authority_effect": "INGRESS_TRANSITION_ONLY",
            "claim_or_fence_minted": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "materialization_id": materialization_id,
            "request_hash": request_hash,
            "payload_hash": payload_hash,
            "operation_id": "TASK_INGRESS",
        }
        consumption = {
            "schema": projection.CONSUMPTION_SCHEMA,
            "state": "INGRESS_BOUND_COORDINATION_PROJECTED",
            "claim_or_fence_minted": False,
            "materialization_id": materialization_id,
            "request_hash": request_hash,
            "payload_hash": payload_hash,
            "operation_id": "TASK_INGRESS",
            "task_id": TASK_ID,
            "correlation_id": TASK_ID,
            "ingress_receipt_ref": ingress_ref,
            "consumption_receipt_ref": consumption_ref,
        }
        source_kind, projected, shard_path = projection.project(
            registry,
            ingress,
            consumption,
            task_shards=SHARDS,
        )
        self.assertEqual(source_kind, "SHARDED_REGISTRY")
        self.assertIsNotNone(shard_path)
        self.assertEqual(projected["task_id"], TASK_ID)
        self.assertEqual(projected["coordination_state"], "INGRESS_ADMITTED")
        self.assertEqual(projected["runtime_refs"]["materialization_id"], materialization_id)
        self.assertEqual(projected["allowed_next_transitions"], ["CLAIMABLE", "RECONCILIATION_REQUIRED"])

    def test_unknown_task_still_fails_closed(self):
        with self.assertRaises(SystemExit):
            builder.resolve_task(task_id="NO-SUCH-TASK-000", registry=REGISTRY, registry_shards=SHARDS)


if __name__ == "__main__":
    unittest.main()
