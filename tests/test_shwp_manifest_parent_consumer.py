from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from workers import manifest_state_transition_intr_ingress as ingress
from workers import shwp_manifest_parent_consumer as mod

ROOT = Path(__file__).resolve().parents[1]
TASK = mod.TASK_ID
ROUTE_DECL = {
    "route_id": mod.ROUTE,
    "lane_class": "MANIFEST_BOUND_SOVEREIGN_INFERENCE",
    "routing_surface": "EXISTING_UNIVERSAL_INTR",
    "containment": "EXISTING_SHWP_PARENT_AUTHORITY_ONLY",
    "sandbox_required": False,
    "external_consequence_enabled": False,
}


def bound_request():
    original = json.loads((ROOT / mod.ORIGINAL).read_text(encoding="utf-8"))
    generation = json.loads((ROOT / mod.REGISTRY).read_text(encoding="utf-8"))["generation"]
    manifest = {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "manifest_profile_version": "1",
        "source_framework": "StegVerse-Labs/.github",
        "source_output_id": original["request_id"],
        "created_at": "2026-09-27T00:00:00Z",
        "declared_intent": "Execute original authorized SHWP request through existing InTr",
        "requested_consequence": "EXISTING_SHWP_PARENT_ONLY",
        "payload": original,
        "hashes": {"payload_sha256": ingress.sha256(original)},
        "processing": {"capability": "sovereign_inference", "route_id": mod.ROUTE},
        "extensions": {
            "stegverse_route": copy.deepcopy(ROUTE_DECL),
            "stegverse_canonical_task": {
                "task_id": TASK, "correlation_id": TASK,
                "registry_repository": "StegVerse-Labs/.github",
                "observed_registry_generation": generation,
                "cosv_task_vector": mod.COSV, "authority_effect": "NONE",
            },
        },
    }
    graph = {
        "schema": "stegverse.sdk.installed-state-transition-graph/v1",
        "graph_id": mod.GRAPH_ID, "canonical_task_id": TASK,
        "processing_capability": "sovereign_inference", "route_id": mod.ROUTE,
        "request": {
            "original_request_id": original["request_id"],
            "original_request_sha256": ingress.sha256(original),
            "observed_registry_generation": generation,
            "cosv_task_vector": mod.COSV,
            "source_request_ref": str(mod.ORIGINAL),
            "authority_effect": "NONE",
        },
        "ordered_transitions": [], "requires_workercoordinator_claim_fence": True,
        "predecessor_closure_required": True, "adapter_executes_lifecycle": False,
    }
    projection = {**manifest, "ingress_mode": "external_manifest"}
    body = {
        "schema": ingress.REQUEST_SCHEMA,
        "canonical_manifest": manifest,
        "wire_manifest_sha256": ingress.sha256(manifest),
        "canonical_manifest_projection": projection,
        "canonical_manifest_sha256": ingress.sha256(projection),
        "processing_capability": "sovereign_inference", "route_id": mod.ROUTE,
        "route_declaration_hash": ingress.sha256(ROUTE_DECL),
        "state_graph": graph, "graph_id": mod.GRAPH_ID,
        "canonical_task_id": TASK, "requires_workercoordinator_claim_fence": True,
        "predecessor_closure_required": True, **ingress.REQUIRED_AUTHORITIES,
    }
    body["request_sha256"] = ingress.sha256(body)
    return body


class ShwpManifestNativeProfileTests(unittest.TestCase):
    def test_original_task_manifest_graph_and_cosv_join(self):
        req = bound_request()
        ingress.validate_request(req)
        original = mod._check(req, ROOT)
        self.assertEqual(original["request_id"], "RESIDENT-EXEC-ECOSYSTEM-CHAT-PARENT-002")
        self.assertEqual(original["fresh_fence_minimum_exclusive"], 24)
        self.assertEqual(req["state_graph"]["request"]["cosv_task_vector"], mod.COSV)

    def test_registry_generation_staleness_fails_at_ingress_not_parent(self):
        req = bound_request()
        req["canonical_manifest"]["extensions"]["stegverse_canonical_task"]["observed_registry_generation"] -= 1
        with self.assertRaisesRegex(ValueError, "SHWP_STALE_CANONICAL_REGISTRY_GENERATION"):
            mod._check(req, ROOT)

    def test_substituted_original_and_wrong_route_never_dispatch(self):
        req = bound_request()
        req["canonical_manifest"]["payload"]["fresh_fence_minimum_exclusive"] = 22
        with self.assertRaisesRegex(ValueError, "SHWP_ORIGINAL_IMMUTABLE_REQUEST_MISMATCH"):
            mod._check(req, ROOT)
        req = bound_request()
        req["canonical_manifest"]["extensions"]["stegverse_route"]["route_id"] = "other"
        with self.assertRaisesRegex(ValueError, "SHWP_MANIFEST_ROUTE_DECLARATION_MISMATCH"):
            mod._check(req, ROOT)

    def test_bad_cosv_returns_actionable_source_boundary_nonallow_without_launch(self):
        req = bound_request()
        req["state_graph"]["request"]["cosv_task_vector"] = "0" * 14
        calls = []
        with tempfile.TemporaryDirectory() as td:
            receipt = mod.execute(ROOT, Path(td), req,
                                  refresh_fn=lambda *_: calls.append("refresh"),
                                  consumer_fn=lambda *_: calls.append("consume"))
        self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
        self.assertEqual(receipt["failed_predicate"],
                         "SHWP_SDK_GRAPH_REQUEST_BINDING_MISMATCH:cosv_task_vector")
        self.assertFalse(receipt["runtime_execution_attempted"])
        self.assertFalse(receipt["organization_master_records_closure_observed"])
        self.assertEqual(calls, [])

    def test_invoked_consumer_fail_closed_preserves_original_failed_predicate(self):
        req = bound_request()
        original = req["canonical_manifest"]["payload"]
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            def materialize(_, target):
                dest = target / mod.ORIGINAL
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(original), encoding="utf-8")
            def run(_, __):
                return {
                    "request_id": original["request_id"],
                    "request_sha256": ingress.sha256(original),
                    "runtime_execution_attempted": True,
                    "disposition": "FAIL_CLOSED",
                    "failed_predicate": "ORIGINAL_MASTER_RECORDS_RECONSTRUCTION_MISMATCH",
                }
            receipt = mod.execute(ROOT, runtime, req, refresh_fn=materialize,
                                  consumer_fn=run)
            self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
            self.assertEqual(receipt["failed_predicate"],
                             "ORIGINAL_MASTER_RECORDS_RECONSTRUCTION_MISMATCH")
            retained = mod.retain_source_result(runtime, receipt)
            self.assertTrue(Path(retained["source_disposition_ref"]).is_file())
            self.assertEqual(retained["diagnostic_sha256"],
                             ingress.sha256({k: v for k, v in retained.items()
                                            if k != "diagnostic_sha256"}))
            self.assertEqual(mod.retain_source_result(runtime, receipt), retained)

    def test_synthetic_consumer_allow_is_only_progress_not_organization_completion(self):
        req = bound_request()
        original = req["canonical_manifest"]["payload"]
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            def materialize(_, target):
                dest = target / mod.ORIGINAL
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(original), encoding="utf-8")
            def mocked_consumer(_, __):
                return {"request_id": original["request_id"],
                        "request_sha256": ingress.sha256(original),
                        "runtime_execution_attempted": True, "disposition": "ALLOW"}
            result = mod.execute(ROOT, runtime, req, refresh_fn=materialize,
                                 consumer_fn=mocked_consumer)
            self.assertEqual(result["state"],
                             "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED")
            self.assertFalse(result["terminal"])
            self.assertFalse(result["organization_master_records_closure_observed"])
            self.assertFalse(result["consequence_committed_by_this_adapter"])


if __name__ == "__main__":
    unittest.main()
