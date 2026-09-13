from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "reusable_task_lifecycle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("reusable_task_lifecycle_tested", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReusableTaskLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.predicates = ["P1", "P2"]
        self.manifest = {
            "invocation_id": "inv-1",
            "reusable_task_id": "RT-X",
            "task_id": "TASK-X",
            "cosv_task_vector": "10100000100000",
            "manifest_hash": "a" * 64,
            "recording_levels": ["task", "goal", "master_records"],
        }
        self.result = {
            "schema": self.m.RUNNER_RESULT_SCHEMA,
            "invocation_id": "inv-1",
            "reusable_task_id": "RT-X",
            "manifest_hash": "a" * 64,
            "runtime_observed": True,
            "completion_evidence_observed": True,
            "completion_predicates_satisfied": list(self.predicates),
            "authority_effect": "NONE",
        }

    def test_runner_result_must_match_every_declared_predicate(self):
        self.m.validate_runner_result(self.result, invocation_id="inv-1", reusable_task_id="RT-X", manifest_hash="a" * 64, completion_predicates=self.predicates)
        bad = dict(self.result)
        bad["completion_predicates_satisfied"] = ["P1"]
        with self.assertRaises(ValueError):
            self.m.validate_runner_result(bad, invocation_id="inv-1", reusable_task_id="RT-X", manifest_hash="a" * 64, completion_predicates=self.predicates)

    def test_expiry_residual_request_and_entropy_are_hash_bound(self):
        expiry = self.m.build_runner_expiry(invocation_id="inv-1", reusable_task_id="RT-X", manifest_hash="a" * 64, runner_ref="scripts/x.py", returncode=0, result=self.result)
        residual = self.m.build_residual_recording(manifest=self.manifest, runner_result=self.result, runner_expiry=expiry)
        trigger = {"invocation_id":"inv-1","reusable_task_id":"RT-X","manifest_hash":"a"*64,"completion_predicates":self.predicates}
        request = self.m.build_custody_request(manifest=self.manifest, trigger_receipt=trigger, runner_result=self.result, runner_expiry=expiry, residual_recording=residual)
        record = {
            "schema": self.m.CUSTODY_RECORD_SCHEMA,
            "invocation_id": "inv-1",
            "reusable_task_id": "RT-X",
            "source_request_sha256": self.m.stable_hash(request),
            "evidence_bundle_sha256": request["evidence_bundle_sha256"],
            "destination_custody_accepted": True,
            "destination_acknowledgement_minted": True,
            "independent_validation_complete": True,
            "reconstruction_confirmed": True,
            "runtime_activation": False,
            "execution_authority_granted": False,
            "publication_authority_granted": False,
            "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }
        entropy = self.m.build_entropy_recovery(manifest=self.manifest, runner_expiry=expiry, residual_recording=residual, custody_request=request, custody_record=record)
        self.assertTrue(entropy["residual_construct_displaced"])
        self.assertTrue(entropy["master_records_reconstruction_confirmed"])
        self.assertFalse(entropy["required_evidence_deleted"])

    def test_entropy_rejects_source_side_or_incomplete_custody(self):
        expiry = self.m.build_runner_expiry(invocation_id="inv-1", reusable_task_id="RT-X", manifest_hash="a" * 64, runner_ref="scripts/x.py", returncode=0, result=self.result)
        residual = self.m.build_residual_recording(manifest=self.manifest, runner_result=self.result, runner_expiry=expiry)
        request = self.m.build_custody_request(manifest=self.manifest, trigger_receipt={}, runner_result=self.result, runner_expiry=expiry, residual_recording=residual)
        bad = {
            "schema": self.m.CUSTODY_RECORD_SCHEMA,
            "invocation_id": "inv-1",
            "reusable_task_id": "RT-X",
            "source_request_sha256": self.m.stable_hash(request),
            "evidence_bundle_sha256": request["evidence_bundle_sha256"],
            "destination_custody_accepted": False,
            "destination_acknowledgement_minted": False,
            "independent_validation_complete": False,
            "reconstruction_confirmed": False,
            "runtime_activation": False,
            "execution_authority_granted": False,
            "publication_authority_granted": False,
            "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }
        with self.assertRaises(ValueError):
            self.m.build_entropy_recovery(manifest=self.manifest, runner_expiry=expiry, residual_recording=residual, custody_request=request, custody_record=bad)


if __name__ == "__main__":
    unittest.main()
