"""Exact frozen MIR/SV Exp3 SDK-to-central ingress regression: SOURCE ONLY.

This test deliberately leaves native admission evidence absent and must yield
the actual evaluating SOURCE-profile DENY, not a simulated InTr verdict.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from workers import manifest_state_transition_intr_ingress as ingress

SDK_ROOT = os.environ.get("STEGVERSE_SDK_SOURCE_ROOT", "").strip()
if SDK_ROOT:
    sys.path.insert(0, SDK_ROOT)


@unittest.skipUnless(SDK_ROOT, "requires exact source-versioned installed SDK tree")
class OriginalExperiment3CrossOwnerTests(unittest.TestCase):
    def test_exact_original_and_first_profile_disposition(self):
        # Central ingress imports its own scripts package first. Load the
        # version-pinned SDK generator directly to avoid the shared package name.
        sdk_generator = Path(SDK_ROOT) / "scripts/build_mir_sv_exp3_manifest.py"
        spec = importlib.util.spec_from_file_location("frozen_mir_sdk_builder", sdk_generator)
        self.assertIsNotNone(spec)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from stegverse.manifest_state_transition_runtime import derive_execution_request
        original = module.build_exp3_manifest()
        request = derive_execution_request(original)
        self.assertEqual(request["wire_manifest_sha256"],
                         "ad9b8b8aab2beeea04bff2aac34fd2e7bfa5915133bcaef9209c16de7d9bea68")
        source_file = (json.dumps(original,indent=2,sort_keys=True,ensure_ascii=False) + chr(10)).encode()
        self.assertEqual(hashlib.sha256(source_file).hexdigest(),
                         "e1b05a082ce19d3d254e3cde1dced03019174a94287724959672c9e65510c8f3")
        self.assertTrue(original["completion"]["publisher"]["required"])
        self.assertEqual(request["canonical_task_id"], None)
        self.assertFalse(request["requires_workercoordinator_claim_fence"])
        self.assertEqual(ingress.validate_request(request)["request_sha256"],
                         request["request_sha256"])
        with tempfile.TemporaryDirectory() as td:
            outcome = ingress.execute(Path(td), request)
            self.assertEqual(outcome["disposition"], "DENY")
            self.assertEqual(outcome["reason_code"],
                             "AUTHENTIC_EVENT_EPHEMERAL_BINDING_LOCATOR_REQUIRED")
            self.assertEqual(outcome["evaluation_boundary"], "SDK_MANIFEST_PROFILE_SOURCE_ONLY")
            self.assertFalse(outcome["authentic_intr_disposition_observed"])
            self.assertFalse(outcome["organization_master_records_closure_observed"])
            self.assertFalse(outcome["terminal"])
            self.assertFalse(outcome["automatic_retry_permitted"])
            self.assertEqual(outcome["goal_task_id"], original["payload"]["goal_task_id"])
            self.assertEqual(outcome["cosv"], original["payload"]["cosv"])
            self.assertEqual(outcome["wire_manifest_sha256"], request["wire_manifest_sha256"])
            self.assertTrue(Path(outcome["source_disposition_ref"]).is_file())
            self.assertFalse((Path(td) / "receipts/sovereign-host/sdk-tt-purpose-bound-worker-runtime-proof.latest.json").exists())
            altered = copy.deepcopy(request)
            altered["canonical_manifest"]["payload"]["goal_task_id"] = "WRONG"
            altered.pop("request_sha256")
            altered["request_sha256"] = ingress.sha256(altered)
            with self.assertRaisesRegex(ValueError, "wire_manifest_sha256_mismatch"):
                ingress.validate_request(altered)


if __name__ == "__main__":
    unittest.main()
