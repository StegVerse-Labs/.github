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



    def test_bundle_can_include_stegindex_vendor_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            stegindex = Path(tmp) / "StegIndex"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            (stegindex / "scripts").mkdir(parents=True)
            (stegindex / "registry").mkdir(parents=True)
            (stegindex / "STEGINDEX_MIRROR_HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
            (stegindex / "scripts" / "preflight.py").write_text("# preflight\n", encoding="utf-8")
            (stegindex / "registry" / "capabilities.json").write_text('{"entries":[]}\n', encoding="utf-8")
            (stegindex / "registry" / "predicates.json").write_text('{"predicates":[]}\n', encoding="utf-8")
            output = Path(tmp) / "control-plane.zip"

            receipt = module.build_bundle(root, output, stegindex_root=stegindex)

            self.assertTrue(receipt["vendor_sources"]["StegVerse-Labs/StegIndex"])
            self.assertFalse(receipt["bundle_grants_authority"])
            self.assertFalse(receipt["network_fetch_required"])
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read(module.MANIFEST_NAME))
            self.assertIn("vendor/StegIndex/STEGINDEX_MIRROR_HANDOFF.md", names)
            self.assertIn("vendor/StegIndex/scripts/preflight.py", names)
            self.assertIn("vendor/StegIndex/registry/capabilities.json", names)
            self.assertIn("vendor/StegIndex/registry/predicates.json", names)
            self.assertTrue(manifest["vendor_sources"]["StegVerse-Labs/StegIndex"])

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


    def _git_repo_with_commit(self, root: Path, files: dict[str, str]) -> str:
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", "pinned"], check=True, capture_output=True)
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def test_git_snapshot_entries_use_exact_pinned_commit_not_current_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            pinned = self._git_repo_with_commit(repo, {"a.txt": "pinned\n", "bin.sh": "#!/bin/sh\n"})
            (repo / "a.txt").write_text("later\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "later"], check=True, capture_output=True)

            entries = module.git_snapshot_entries(repo, commit=pinned, prefix="vendor/test")
            by_name = {rel: (data, mode) for rel, data, mode in entries}

            self.assertEqual(by_name["vendor/test/a.txt"][0], b"pinned\n")
            self.assertNotEqual(by_name["vendor/test/a.txt"][0], (repo / "a.txt").read_bytes())

    def test_git_snapshot_source_proof_rejects_missing_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self._git_repo_with_commit(repo, {"a.txt": "one\n"})
            proof = module.git_snapshot_source_proof(
                repo,
                repository="example/repo",
                materialized_subpath="vendor/example",
                commit="0" * 40,
            )
            self.assertEqual(proof["state"], "UNVERIFIED_PINNED_COMMIT_NOT_PRESENT")

    def test_bundle_materializes_exact_sv002_micro_and_formal_pins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "source"
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n", encoding="utf-8")
            micro = base / "micro"
            required = {rel: rel + "\n" for rel in module.SV002_MICRO_NODE_REQUIRED_PATHS}
            micro_pin = self._git_repo_with_commit(micro, required)
            formals = {}
            formal_pins = {}
            for name in ("TT", "RTG", "GTG", "AE"):
                fr = base / name
                pin = self._git_repo_with_commit(fr, {"PIN.txt": name + "-pinned\n"})
                formals[name] = fr
                formal_pins[name] = pin
            old_micro = module.SV002_MICRO_NODE_COMMIT
            old_formals = dict(module.SV002_FORMAL_PINS)
            module.SV002_MICRO_NODE_COMMIT = micro_pin
            module.SV002_FORMAL_PINS = formal_pins
            output = base / "bundle.zip"
            try:
                receipt = module.build_bundle(
                    root,
                    output,
                    micro_node_root=micro,
                    tt_root=formals["TT"],
                    rtg_root=formals["RTG"],
                    gtg_root=formals["GTG"],
                    ae_root=formals["AE"],
                )
            finally:
                module.SV002_MICRO_NODE_COMMIT = old_micro
                module.SV002_FORMAL_PINS = old_formals

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read(module.MANIFEST_NAME))
            self.assertIn(
                "vendor/micro-node-runtime/tools/run_self_characterization_principal.py",
                names,
            )
            for name in ("TT", "RTG", "GTG", "AE"):
                self.assertIn(f"vendor/formal/{name}/PIN.txt", names)
                self.assertTrue(manifest["vendor_sources"][f"Admissible-Existence/{name}"])
                self.assertEqual(
                    manifest["vendor_source_proofs"][f"Admissible-Existence/{name}"]["state"],
                    "VERIFIED_LOCAL_GIT_OBJECT_SNAPSHOT",
                )
            self.assertTrue(manifest["vendor_sources"]["StegVerse-002/micro-node-runtime"])
            self.assertFalse(receipt["bundle_grants_authority"])
            self.assertFalse(receipt["network_fetch_required"])


if __name__ == "__main__":
    unittest.main()
