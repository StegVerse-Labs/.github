from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workers import tv_tvc_resident_proof_worker as worker


def invocation() -> dict:
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 30,
        "task": {
            "task_id": worker.TASK_ID,
            "claim_id": "SHWP-TV-TVC-RESIDENT-PROOF-001-G24",
            "worker_id": "tv-tvc-resident-proof-worker",
            "worker_instance_id": "tv-tvc-resident-proof-worker-HB30-G24",
            "heartbeat_timing": {"fencing_token": 24},
        },
        "handoff": {
            "goal": {"goal_id": "TVC-TV-CREDENTIAL-MIGRATION-089"},
            "authority": {"credential_authority": "TV/TVC", "g18_authority_inherited": False},
            "execution": {
                "required_capabilities": sorted(worker.ALLOWED_CAPABILITIES),
                "allowed_paths": worker.ALLOWED_PATHS,
                "allowed_services": worker.ALLOWED_SERVICES,
            },
        },
    }


class TvTvcResidentProofWorkerTests(unittest.TestCase):
    def _roots(self, base: Path, *, canonical: bool = False) -> tuple[Path, Path]:
        parent = base / ".stegverse" / "repos" / "StegVerse-Labs" if canonical else base
        tv = parent / "TV"
        tvc = parent / "TVC"
        (tv / "scripts").mkdir(parents=True)
        (tv / "docs").mkdir(parents=True)
        (tv / ".git").mkdir()
        (tv / "scripts/tv_run_resident_operational_proof.py").write_text("x=1\n", encoding="utf-8")
        (tv / "docs/TV_OPERATIONAL_PROOF_SCHEMA.json").write_text("{}\n", encoding="utf-8")
        (tvc / "tools").mkdir(parents=True)
        (tvc / "scripts").mkdir(parents=True)
        (tvc / ".git").mkdir()
        (tvc / "tools/task_dispatcher.py").write_text("x=1\n", encoding="utf-8")
        (tvc / "tv_resident_operational_proof_task.py").write_text("x=1\n", encoding="utf-8")
        (tvc / "scripts/activate_tv_resident_operational_proof.py").write_text("x=1\n", encoding="utf-8")
        return tv.resolve(), tvc.resolve()

    def test_hosted_runtime_blocks_before_source_execution(self):
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            receipt_root = base / "receipts" / "tv-tvc-resident-proof"
            with mock.patch.object(worker, "ROOT", base), mock.patch.object(worker, "RECEIPT_ROOT", receipt_root), \
                 mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))), mock.patch.object(worker.sys, "stdout", io.StringIO()) as out, \
                 mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True), mock.patch.object(worker.subprocess, "run") as run:
                self.assertEqual(worker.main(), 0)
                response = json.loads(out.getvalue())
            self.assertEqual(response["state"], "BLOCKED")
            self.assertEqual(run.call_count, 0)

    def test_missing_local_roots_remains_blocked_after_canonical_discovery(self):
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            receipt_root = base / "receipts" / "tv-tvc-resident-proof"
            out = io.StringIO()
            with mock.patch.object(worker, "ROOT", base), mock.patch.object(worker, "RECEIPT_ROOT", receipt_root), \
                 mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))), mock.patch.object(worker.sys, "stdout", out), \
                 mock.patch.dict(os.environ, {"HOME": str(base)}, clear=True), mock.patch.object(worker.subprocess, "run") as run:
                self.assertEqual(worker.main(), 0)
            self.assertEqual(json.loads(out.getvalue())["state"], "BLOCKED")
            receipt = json.loads((receipt_root / f"{worker.TASK_ID}.json").read_text())
            self.assertEqual(receipt["reason"], "LOCAL_TV_TVC_SOURCE_NOT_MATERIALIZED")
            self.assertFalse(receipt["evidence"]["network_lookup_performed"])
            self.assertFalse(receipt["credential_value_exposed"])
            run.assert_not_called()

    def test_canonical_local_roots_are_discovered_without_env_bindings(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            tv, tvc = self._roots(base, canonical=True)
            env = {"HOME": str(base)}
            def head(root: Path) -> str:
                return worker.TV_SHA if root == tv else "f" * 40
            with mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch.object(worker, "_git_head", side_effect=head), \
                 mock.patch.object(worker, "_clean_worktree", return_value=True), \
                 mock.patch.object(worker, "_git", return_value=SimpleNamespace(returncode=0, stdout="")):
                selected_tv, tv_seen = worker._locate_local_source("TV", "STEGVERSE_TV_ROOT", worker.TV_REQUIRED, exact_head=worker.TV_SHA)
                selected_tvc, tvc_seen = worker._locate_local_source("TVC", "STEGVERSE_TVC_ROOT", worker.TVC_REQUIRED, required_ancestor=worker.TVC_MIN_SHA)
            self.assertEqual(selected_tv, tv)
            self.assertEqual(selected_tvc, tvc)
            self.assertTrue(any(row.get("selected") for row in tv_seen))
            self.assertTrue(any(row.get("selected") for row in tvc_seen))
            self.assertNotIn("STEGVERSE_TV_ROOT", os.environ)
            self.assertNotIn("STEGVERSE_TVC_ROOT", os.environ)

    def test_success_requires_exact_source_preflight_and_activation(self):
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            tv, tvc = self._roots(base)
            receipt_root = base / "receipts" / "tv-tvc-resident-proof"
            preflight = json.dumps({"status":"ok","result":{"state":"READY_FOR_TV_TVC_RESIDENT_ACTIVATION"}})
            activation = json.dumps({"status":"ok","result":{"state":"TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED","runtime_execution_observed":True,"credential_value_exposed":False,"consumer_secret_received":False,"receipt_path":"/state/runtime.json","proof_sha256":"a"*64}})
            calls = [
                SimpleNamespace(stdout=preflight, stderr="", returncode=0),
                SimpleNamespace(stdout=activation, stderr="", returncode=0),
            ]
            out = io.StringIO()
            env = {"HOME":str(base),"PATH":"/usr/bin:/bin"}
            with mock.patch.object(worker, "ROOT", base), mock.patch.object(worker, "RECEIPT_ROOT", receipt_root), \
                 mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))), mock.patch.object(worker.sys, "stdout", out), \
                 mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch.object(worker, "_locate_local_source", side_effect=[(tv, []), (tvc, [])]), \
                 mock.patch.object(worker, "_git_head", return_value=worker.TV_SHA), \
                 mock.patch.object(worker, "_tvc_contains_required_source", return_value=True), \
                 mock.patch.object(worker.subprocess, "run", side_effect=calls) as run:
                self.assertEqual(worker.main(), 0)
            response = json.loads(out.getvalue())
            self.assertEqual(response["state"], "COMPLETED")
            receipt = json.loads((receipt_root / f"{worker.TASK_ID}.json").read_text())
            self.assertTrue(receipt["runtime_execution_observed"])
            self.assertFalse(receipt["credential_value_exposed"])
            self.assertFalse(receipt["g18_authority_reused"])
            self.assertEqual(receipt["tv_source_sha"], worker.TV_SHA)
            self.assertEqual(receipt["tv_source_root"], str(tv))
            self.assertEqual(receipt["tvc_source_root"], str(tvc))
            self.assertEqual(run.call_count, 2)
            activation_call = run.call_args_list[-1]
            child_env = activation_call.kwargs["env"]
            self.assertEqual(child_env["STEGVERSE_TV_SERVICE_MANAGER"], "user")
            self.assertEqual(child_env["STEGTV_TV_CREDENTIAL_MIGRATION_ACTIVATION_AUTHORITY"], "TV/TVC")
            self.assertNotIn("TV_HMAC_SIGNING_KEY", child_env)
            self.assertNotIn("GITHUB_TOKEN", child_env)

    def test_dispatcher_block_is_never_promoted(self):
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            tv, tvc = self._roots(base)
            receipt_root = base / "receipts" / "tv-tvc-resident-proof"
            blocked = json.dumps({"status":"blocked","result":{"state":"BLOCKED_DEPENDENCY","reason":"resident_activation_dependency_blocked"}})
            out = io.StringIO()
            env = {"HOME":str(base),"PATH":"/usr/bin:/bin"}
            with mock.patch.object(worker, "ROOT", base), mock.patch.object(worker, "RECEIPT_ROOT", receipt_root), \
                 mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))), mock.patch.object(worker.sys, "stdout", out), \
                 mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch.object(worker, "_locate_local_source", side_effect=[(tv, []), (tvc, [])]), \
                 mock.patch.object(worker, "_git_head", return_value=worker.TV_SHA), \
                 mock.patch.object(worker, "_tvc_contains_required_source", return_value=True), \
                 mock.patch.object(worker.subprocess, "run", return_value=SimpleNamespace(stdout=blocked, stderr="", returncode=2)):
                self.assertEqual(worker.main(), 0)
            self.assertEqual(json.loads(out.getvalue())["state"], "BLOCKED")
            receipt = json.loads((receipt_root / f"{worker.TASK_ID}.json").read_text())
            self.assertEqual(receipt["reason"], "TVC_PREFLIGHT_BLOCKED")

    def test_verified_portable_bundle_can_supply_exact_tv_and_tvc_sources_without_git(self):
        with tempfile.TemporaryDirectory() as td:
            control = Path(td) / "resident-control-plane"
            tv = control / "vendor" / "TV"
            tvc = control / "vendor" / "TVC"
            entries = []
            for repo_name, root, required in (("TV", tv, worker.TV_REQUIRED), ("TVC", tvc, worker.TVC_REQUIRED)):
                for rel in required:
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    data = (repo_name + ":" + rel.as_posix() + "\n").encode()
                    path.write_bytes(data)
                    entries.append({
                        "path": f"vendor/{repo_name}/{rel.as_posix()}",
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "size": len(data),
                    })
            manifest = {
                "schema": "stegverse.sovereign-control-plane-bundle/v1",
                "network_fetch_required": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "bundle_grants_authority": False,
                "files": entries,
                "vendor_source_proofs": {
                    "TV": {
                        "schema": "stegverse.portable-source-proof/v1",
                        "state": "VERIFIED_LOCAL_GIT_SOURCE",
                        "repository": "StegVerse-Labs/TV",
                        "materialized_subpath": "vendor/TV",
                        "head": worker.TV_SHA,
                        "exact_head_verified": True,
                        "clean_worktree_at_packaging": True,
                    },
                    "TVC": {
                        "schema": "stegverse.portable-source-proof/v1",
                        "state": "VERIFIED_LOCAL_GIT_SOURCE",
                        "repository": "StegVerse-Labs/TVC",
                        "materialized_subpath": "vendor/TVC",
                        "resident_proof_min_sha_present": True,
                        "verified_ancestors": [worker.TVC_MIN_SHA],
                    },
                },
            }
            manifest_path = control / ".stegverse-source-manifest.json"
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            env = {
                "STEGVERSE_RESIDENT_SOURCE_MANIFEST": str(manifest_path),
                "STEGVERSE_TV_ROOT": str(tv),
                "STEGVERSE_TVC_ROOT": str(tvc),
            }
            with mock.patch.dict(os.environ, env, clear=True):
                selected_tv, tv_mode = worker._portable_source("TV", "STEGVERSE_TV_ROOT", worker.TV_REQUIRED)
                selected_tvc, tvc_mode = worker._portable_source("TVC", "STEGVERSE_TVC_ROOT", worker.TVC_REQUIRED)

            self.assertEqual(selected_tv, tv.resolve())
            self.assertEqual(selected_tvc, tvc.resolve())
            self.assertEqual(tv_mode, "VERIFIED_PORTABLE_BUNDLE_PROOF")
            self.assertEqual(tvc_mode, "VERIFIED_PORTABLE_BUNDLE_PROOF")

    def test_portable_tv_source_fails_closed_on_digest_drift(self):
        with tempfile.TemporaryDirectory() as td:
            control = Path(td) / "resident-control-plane"
            tv = control / "vendor" / "TV"
            entries = []
            for rel in worker.TV_REQUIRED:
                path = tv / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                data = rel.as_posix().encode()
                path.write_bytes(data)
                entries.append({"path": f"vendor/TV/{rel.as_posix()}", "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
            manifest = {
                "schema": "stegverse.sovereign-control-plane-bundle/v1",
                "network_fetch_required": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "bundle_grants_authority": False,
                "files": entries,
                "vendor_source_proofs": {"TV": {
                    "state": "VERIFIED_LOCAL_GIT_SOURCE",
                    "repository": "StegVerse-Labs/TV",
                    "materialized_subpath": "vendor/TV",
                    "head": worker.TV_SHA,
                    "exact_head_verified": True,
                    "clean_worktree_at_packaging": True,
                }},
            }
            manifest_path = control / ".stegverse-source-manifest.json"
            manifest_path.write_text(json.dumps(manifest) + "\n")
            (tv / worker.TV_REQUIRED[0]).write_text("drift\n")
            with mock.patch.dict(os.environ, {
                "STEGVERSE_RESIDENT_SOURCE_MANIFEST": str(manifest_path),
                "STEGVERSE_TV_ROOT": str(tv),
            }, clear=True):
                selected, reason = worker._portable_source("TV", "STEGVERSE_TV_ROOT", worker.TV_REQUIRED)
            self.assertIsNone(selected)
            self.assertEqual(reason, "PORTABLE_SOURCE_DIGEST_MISMATCH")
    def test_source_discovery_has_no_network_or_source_mutation_path(self):
        source = Path(worker.__file__).read_text(encoding="utf-8")
        for forbidden in ("git clone", "git fetch", "git pull", "urllib", "urlopen(", "requests.get", "GITHUB_TOKEN", "GH_TOKEN"):
            self.assertNotIn(forbidden, source)
        self.assertIn("/var/lib/stegverse/source/StegVerse-Labs", source)
        self.assertIn("/srv/stegverse/repos/StegVerse-Labs", source)
        self.assertIn("/opt/stegverse/repos/StegVerse-Labs", source)


if __name__ == "__main__":
    unittest.main()
