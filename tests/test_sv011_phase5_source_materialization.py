from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

materializer=load_module("sv011_materializer",ROOT/"workers/sv011_phase5_source_materialization_worker.py")
boundary=load_module("sv011_boundary",ROOT/"workers/sv011_phase5_boundary_worker.py")

def git_blob_sha1(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

class SV011Phase5SourceMaterializationTests(unittest.TestCase):
    def test_bundle_is_exactly_pinned_to_sv011_source(self):
        manifest=json.loads((ROOT/"source-bundles/sv011-phase5/manifest.json").read_text())
        self.assertEqual(manifest["source_basis_commit"],"cf2777d9d21a97289f4ec7b0d9b0b21597047666")
        self.assertFalse(manifest["credential_material_included"])
        self.assertFalse(manifest["network_source_fetch_required"])
        self.assertEqual(manifest["authority_effect"],"NONE_SOURCE_TRANSPORT_ONLY")
        self.assertEqual(len(manifest["files"]),7)
        for row in manifest["files"]:
            path=ROOT/"source-bundles/sv011-phase5"/row["path"]
            self.assertTrue(path.is_file(),row["path"])
            self.assertEqual(git_blob_sha1(path.read_bytes()),row["git_blob_sha1"],row["path"])

    def test_materialization_is_atomic_and_boundary_worker_accepts_verified_tree(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/"SV-011"/".github"
            first=materializer.materialize(dest)
            self.assertEqual(first["state"],"MATERIALIZED_VERIFIED")
            self.assertTrue(first["filesystem_mutated"])
            status=boundary.source_ok(dest)
            self.assertTrue(status["verified"])
            self.assertEqual(status["source_mode"],"VERIFIED_MATERIALIZED_TREE")
            self.assertTrue(status["exact_git_blobs_verified"])
            self.assertEqual(boundary.REQUIRED_ANCESTOR,"cf2777d9d21a97289f4ec7b0d9b0b21597047666")
            second=materializer.materialize(dest)
            self.assertEqual(second["state"],"ALREADY_MATERIALIZED_VERIFIED")
            self.assertFalse(second["filesystem_mutated"])

    def test_materialized_tree_fails_closed_after_byte_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/"SV-011"/".github"
            materializer.materialize(dest)
            target=dest/"resident-runtime/requests/phase5-allow.json"
            target.write_text(target.read_text()+"\n",encoding="utf-8")
            status=boundary.source_ok(dest)
            self.assertFalse(status["verified"])
            self.assertFalse(status["exact_git_blobs_verified"])
            self.assertEqual(status["source_mode"],"UNVERIFIED")

    def test_dispatcher_orders_materialization_before_phase5(self):
        source=(ROOT/"scripts/dispatch_resident_execution_requests.py").read_text()
        materialize='("sv011_phase5_source_materialization", "scripts/consume_sv011_phase5_source_materialization_request.py")'
        phase5='("sv011_phase5", "scripts/consume_sv011_phase5_resident_execution_request.py")'
        self.assertIn(materialize,source)
        self.assertIn(phase5,source)
        self.assertLess(source.index(materialize),source.index(phase5))

    def test_refresh_carries_bundle_and_consumers(self):
        for name in ("scripts/refresh_sovereign_worker_runtime_source.py","scripts/refresh_sovereign_worker_runtime_source_base.py"):
            source=(ROOT/name).read_text()
            self.assertIn('Path("source-bundles")',source)
            self.assertIn('Path("scripts/consume_sv011_phase5_source_materialization_request.py")',source)
            self.assertIn('Path("scripts/consume_sv011_phase5_resident_execution_request.py")',source)
        installer=(ROOT/"scripts/install_sovereign_worker_source_refresh_service.py").read_text()
        self.assertIn('source / "source-bundles"',installer)

    def test_source_materialization_request_is_non_authorizing(self):
        request=json.loads((ROOT/"control/resident-execution-request.d/sv011-phase5-source-materialization-001.json").read_text())
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["github_token_required"])
        self.assertFalse(request["network_source_fetch_allowed"])
        self.assertFalse(request["provider_credential_material_allowed"])

    def test_phase5_worker_receipt_contract_carries_source_basis_commit(self):
        source=(ROOT/"workers/sv011_phase5_boundary_worker.py").read_text()
        self.assertIn('"sv011_source_basis_commit":REQUIRED_ANCESTOR',source)
        self.assertIn('"sv011_source_mode":source_ok(source)["source_mode"]',source)

if __name__=="__main__":
    unittest.main()
