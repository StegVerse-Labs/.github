from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_sovereign_control_plane_bundle.py"
spec = importlib.util.spec_from_file_location("package_sovereign_control_plane_bundle", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class SovereignControlPlaneBundleTests(unittest.TestCase):
    def test_bundle_contains_bootstrap_and_non_authorizing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            (root / "scripts").mkdir(parents=True)
            (root / "control").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            (root / "scripts" / "run_worker_runtime.py").write_text("# worker\n", encoding="utf-8")
            (root / "control" / "worker-registry.json").write_text("{}\n", encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"

            receipt = module.build_bundle(root, output)

            self.assertTrue(output.is_file())
            self.assertFalse(receipt["network_fetch_required"])
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
            self.assertFalse(receipt["heartbeat_grants_execution_authority"])
            self.assertFalse(receipt["bundle_grants_authority"])
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("scripts/bootstrap_sovereign_runtime.py", names)
                self.assertIn(module.MANIFEST_NAME, names)
                manifest = json.loads(archive.read(module.MANIFEST_NAME))
            self.assertEqual(manifest["schema"], "stegverse.sovereign-control-plane-bundle/v1")
            self.assertFalse(manifest["bundle_grants_authority"])


    def test_bundle_can_include_stegos_and_cvk_vendor_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            stegos = Path(tmp) / "StegOS"
            kv = Path(tmp) / "continuity-vault-kit"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            (stegos / "stegos").mkdir(parents=True)
            (stegos / "stegos" / "intr_backbone.py").write_text("# intr\n", encoding="utf-8")
            (kv / "runtime").mkdir(parents=True)
            (kv / "runtime" / "kv_interlock_endpoint.py").write_text("# kv\n", encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"

            receipt = module.build_bundle(root, output, stegos_root=stegos, kv_source_root=kv)

            self.assertEqual(receipt["vendor_sources"], {"StegOS": True, "continuity-vault-kit": True})
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("vendor/StegOS/stegos/intr_backbone.py", names)
            self.assertIn("vendor/continuity-vault-kit/runtime/kv_interlock_endpoint.py", names)


    def test_tvc_source_proof_verifies_clean_local_git_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tvc = Path(tmp) / "TVC"
            tvc.mkdir()
            subprocess.run(["git", "init", str(tvc)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(tvc), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(tvc), "config", "user.name", "Test"], check=True)
            for rel in module.TVC_HIL_PROTECTED_PATHS:
                path = tvc / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rel + "\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(tvc), "add", "."], check=True)
            subprocess.run(["git", "-C", str(tvc), "commit", "-m", "floor"], check=True, capture_output=True)
            floor = subprocess.run(
                ["git", "-C", str(tvc), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            proof = module.tvc_source_proof(tvc, source_floor=floor)

            self.assertEqual(proof["state"], "VERIFIED_LOCAL_GIT_SOURCE")
            self.assertEqual(proof["source_floor"], floor)
            self.assertTrue(proof["source_floor_present"])
            self.assertTrue(proof["protected_paths_unchanged_since_floor"])
            self.assertEqual(proof["materialized_subpath"], "vendor/TVC")
            self.assertFalse(proof["network_fetch_performed"])

    def test_tv_source_proof_requires_exact_clean_authorized_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tv = Path(tmp) / "TV"
            tv.mkdir()
            subprocess.run(["git", "init", str(tv)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(tv), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(tv), "config", "user.name", "Test"], check=True)
            for rel in module.TV_RESIDENT_PROOF_REQUIRED_PATHS:
                path = tv / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rel + "\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(tv), "add", "."], check=True)
            subprocess.run(["git", "-C", str(tv), "commit", "-m", "authorized"], check=True, capture_output=True)
            head = subprocess.run(["git", "-C", str(tv), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            old = module.TV_RESIDENT_PROOF_SHA
            module.TV_RESIDENT_PROOF_SHA = head
            try:
                proof = module.tv_source_proof(tv)
            finally:
                module.TV_RESIDENT_PROOF_SHA = old

            self.assertEqual(proof["state"], "VERIFIED_LOCAL_GIT_SOURCE")
            self.assertEqual(proof["head"], head)
            self.assertTrue(proof["exact_head_verified"])
            self.assertTrue(proof["clean_worktree_at_packaging"])
            self.assertEqual(proof["materialized_subpath"], "vendor/TV")

    def test_bundle_can_include_tv_vendor_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            tv = Path(tmp) / "TV"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            for rel in module.TV_RESIDENT_PROOF_REQUIRED_PATHS:
                path = tv / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rel + "\n", encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"

            receipt = module.build_bundle(root, output, tv_root=tv)

            self.assertTrue(receipt["vendor_sources"]["TV"])
            self.assertEqual(receipt["vendor_source_proofs"]["TV"]["state"], "UNVERIFIED_NO_LOCAL_GIT_IDENTITY")
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("vendor/TV/scripts/tv_run_resident_operational_proof.py", names)
    def test_bundle_can_include_healer_and_tvc_vendor_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            healer = Path(tmp) / "StegVerse-Healer"
            tvc = Path(tmp) / "TVC"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            (healer / "app").mkdir(parents=True)
            (healer / "data").mkdir(parents=True)
            (healer / "docs").mkdir(parents=True)
            (healer / "app" / "dispatch_orchestrators.py").write_text("# dispatch\n", encoding="utf-8")
            (healer / "data" / "orchestrator_targets.json").write_text("{}\n", encoding="utf-8")
            (healer / "docs" / "HEALER_MIRROR_HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
            (tvc / "scripts").mkdir(parents=True)
            (tvc / "tools").mkdir(parents=True)
            (tvc / "TVC_MIRROR_HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
            (tvc / "scripts" / "activate_coinbase_intr_resident.py").write_text("# activate\n", encoding="utf-8")
            (tvc / "tools" / "hil_intr_lifecycle_intake.py").write_text("# intake\n", encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"

            receipt = module.build_bundle(root, output, healer_root=healer, tvc_root=tvc)

            self.assertTrue(receipt["vendor_sources"]["StegVerse-Healer"])
            self.assertTrue(receipt["vendor_sources"]["TVC"])
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("vendor/StegVerse-Healer/app/dispatch_orchestrators.py", names)
            self.assertIn("vendor/TVC/scripts/activate_coinbase_intr_resident.py", names)


    def test_master_records_source_proof_verifies_clean_floor_and_protected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mr = Path(tmp) / "orchestration"
            mr.mkdir()
            subprocess.run(["git", "init", str(mr)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(mr), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(mr), "config", "user.name", "Test"], check=True)
            for rel in module.MASTER_RECORDS_SV001_PROTECTED_PATHS:
                path = mr / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rel + "\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(mr), "add", "."], check=True)
            subprocess.run(["git", "-C", str(mr), "commit", "-m", "sv001 resident intake floor"], check=True, capture_output=True)
            floor = subprocess.run(
                ["git", "-C", str(mr), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()

            proof = module.master_records_source_proof(mr, source_floor=floor)

            self.assertEqual(proof["state"], "VERIFIED_LOCAL_GIT_SOURCE")
            self.assertEqual(proof["repository"], "master-records/orchestration")
            self.assertEqual(proof["materialized_subpath"], "vendor/master-records-orchestration")
            self.assertTrue(proof["source_floor_present"])
            self.assertTrue(proof["protected_paths_unchanged_since_floor"])
            self.assertTrue(proof["clean_worktree_at_packaging"])
            self.assertFalse(proof["network_fetch_performed"])
            self.assertFalse(proof["credential_required"])

    def test_master_records_source_proof_rejects_protected_path_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mr = Path(tmp) / "orchestration"
            mr.mkdir()
            subprocess.run(["git", "init", str(mr)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(mr), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(mr), "config", "user.name", "Test"], check=True)
            for rel in module.MASTER_RECORDS_SV001_PROTECTED_PATHS:
                path = mr / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rel + "\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(mr), "add", "."], check=True)
            subprocess.run(["git", "-C", str(mr), "commit", "-m", "floor"], check=True, capture_output=True)
            floor = subprocess.run(
                ["git", "-C", str(mr), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            target = mr / module.MASTER_RECORDS_SV001_PROTECTED_PATHS[0]
            target.write_text("changed\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(mr), "add", "."], check=True)
            subprocess.run(["git", "-C", str(mr), "commit", "-m", "drift"], check=True, capture_output=True)

            proof = module.master_records_source_proof(mr, source_floor=floor)

            self.assertEqual(proof["state"], "UNVERIFIED_PROTECTED_PATH_DRIFT")

    def test_bundle_can_include_verified_master_records_vendor_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            mr = Path(tmp) / "orchestration"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            for rel in module.MASTER_RECORDS_SV001_PROTECTED_PATHS:
                path = mr / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# custody\n", encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"
            original = module.master_records_source_proof
            module.master_records_source_proof = lambda _root: {
                "schema": "stegverse.portable-source-proof/v1",
                "repository": "master-records/orchestration",
                "materialized_subpath": "vendor/master-records-orchestration",
                "source_floor": module.MASTER_RECORDS_SV001_SOURCE_FLOOR,
                "protected_paths": list(module.MASTER_RECORDS_SV001_PROTECTED_PATHS),
                "state": "VERIFIED_LOCAL_GIT_SOURCE",
                "source_floor_present": True,
                "protected_paths_unchanged_since_floor": True,
                "clean_worktree_at_packaging": True,
                "network_fetch_performed": False,
                "credential_required": False,
                "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
            }
            try:
                receipt = module.build_bundle(root, output, master_records_root=mr)
            finally:
                module.master_records_source_proof = original

            self.assertTrue(receipt["vendor_sources"]["master-records/orchestration"])
            proof = receipt["vendor_source_proofs"]["master-records/orchestration"]
            self.assertEqual(proof["state"], "VERIFIED_LOCAL_GIT_SOURCE")
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read(module.MANIFEST_NAME))
            self.assertIn(
                "vendor/master-records-orchestration/scripts/watch_stegverse001_autonomy_receipt.py",
                names,
            )
            self.assertIn(
                "vendor/master-records-orchestration/scripts/import_stegverse001_autonomy_receipt.py",
                names,
            )
            self.assertTrue(manifest["vendor_sources"]["master-records/orchestration"])
            self.assertFalse(manifest["bundle_grants_authority"])


if __name__ == "__main__":
    unittest.main()
