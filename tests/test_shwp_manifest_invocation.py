from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from workers.manifest_state_transition_intr_ingress import sha256

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "shwp_manifest_invocation", ROOT / "scripts/consume_shwp_manifest_invocation.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class ShwpManifestInvocationTests(unittest.TestCase):
    def test_original_request_is_bound_to_manifest_from_current_registry(self):
        original = json.loads((ROOT / mod.REQUEST).read_text(encoding="utf-8"))
        registry = json.loads((ROOT / mod.REGISTRY).read_text(encoding="utf-8"))
        manifest = mod.build_manifest(ROOT, digest=sha256)
        self.assertEqual(manifest["payload"], original)
        self.assertEqual(manifest["hashes"]["payload_sha256"], sha256(original))
        self.assertEqual(manifest["source_output_id"], original["request_id"])
        self.assertEqual(manifest["processing"]["capability"], "sovereign_inference")
        self.assertEqual(manifest["processing"]["route_id"], mod.ROUTE)
        self.assertEqual(manifest["extensions"]["stegverse_canonical_task"]
                         ["observed_registry_generation"], registry["generation"])
        self.assertEqual(manifest["extensions"]["stegverse_canonical_task"]
                         ["cosv_task_vector"], mod.COSV)

    def test_original_request_mismatch_fails_before_sdk_execution(self):
        original = json.loads((ROOT / mod.REQUEST).read_text(encoding="utf-8"))
        registry = json.loads((ROOT / mod.REGISTRY).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            source = Path(td)
            (source / mod.REQUEST).parent.mkdir(parents=True)
            (source / mod.REGISTRY).parent.mkdir(parents=True)
            changed = copy.deepcopy(original)
            changed["fresh_fence_minimum_exclusive"] = 22
            (source / mod.REQUEST).write_text(json.dumps(changed), encoding="utf-8")
            (source / mod.REGISTRY).write_text(json.dumps(registry), encoding="utf-8")
            called = []
            result = mod.invoke(source, source / "runtime", digest=sha256,
                                sdk_execute=lambda _: called.append(True))
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"],
                         "SHWP_ORIGINAL_G25_TASK_BINDING_MISMATCH")
        self.assertFalse(result["runtime_execution_attempted"])
        self.assertEqual(called, [])

    def test_actual_sdk_attachment_failure_preserves_boundary_and_lineage(self):
        def execute(manifest):
            return {
                "schema": "stegverse.sdk.manifest-attachment-disposition/v1",
                "state": "FAIL_CLOSED", "disposition": "FAIL_CLOSED",
                "evaluation_boundary": "SDK_MANIFEST_TRANSPORT_ATTACHMENT",
                "failed_predicate": "UNIVERSAL_INTR_INGRESS_NOT_CONFIGURED",
                "canonical_task_id": mod.TASK_ID,
                "processing_capability": "sovereign_inference",
                "route_id": mod.ROUTE,
                "wire_manifest_sha256": sha256(manifest),
            }
        with tempfile.TemporaryDirectory() as td:
            result = mod.invoke(ROOT, Path(td), sdk_execute=execute, digest=sha256)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"],
                         "UNIVERSAL_INTR_INGRESS_NOT_CONFIGURED")
        self.assertEqual(result["evaluation_boundary"],
                         "SDK_MANIFEST_TRANSPORT_ATTACHMENT")
        self.assertFalse(result["organization_receipt_inferred"])

    def test_unbound_fake_sdk_success_cannot_promote_automation(self):
        with tempfile.TemporaryDirectory() as td:
            result = mod.invoke(ROOT, Path(td), digest=sha256,
                                sdk_execute=lambda _: {
                                    "schema": "stegverse.sdk.shwp-manifest-transition-result/v1",
                                    "state": "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED",
                                    "disposition": "ALLOW",
                                })
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"],
                         "SHWP_SDK_RETURN_LINEAGE_MISMATCH:canonical_task_id")

    def test_bound_synthetic_processing_is_nonterminal_original_readback_required(self):
        def execute(manifest):
            return {
                "schema": "stegverse.sdk.shwp-manifest-transition-result/v1",
                "state": "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED",
                "disposition": "ALLOW",
                "canonical_task_id": mod.TASK_ID,
                "processing_capability": "sovereign_inference",
                "route_id": mod.ROUTE,
                "wire_manifest_sha256": sha256(manifest),
                "original_request_sha256": sha256(manifest["payload"]),
                "organization_master_records_organization_record_observed": False,
                "terminal": False,
                "runtime_execution_attempted": True,
            }
        with tempfile.TemporaryDirectory() as td:
            result = mod.invoke(ROOT, Path(td), digest=sha256, sdk_execute=execute)
        self.assertEqual(result["state"],
                         "PROCESSING_RECORDED_CUSTODY_READBACK_REQUIRED")
        self.assertFalse(result["terminal"])
        self.assertFalse(result["organization_master_records_organization_record_observed"])
        self.assertEqual(result["next_transition"],
                         "EXISTING_ORIGINAL_ORGANIZATION_HEAD_AND_MASTER_RECORDS_READBACK")


if __name__ == "__main__":
    unittest.main()
