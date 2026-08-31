from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import sv002_self_characterization_worker as worker


class Sv002PortableSourceBundleTests(unittest.TestCase):
    def _fixture(self, base: Path):
        control = base / "resident-control-plane"
        files = []
        proofs = {}

        micro = control / "vendor" / "micro-node-runtime"
        micro_required = (
            "tools/run_self_characterization_principal.py",
            "tools/verify_self_characterization_runtime_identity.py",
            "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json",
            "schemas/self_characterization_runtime_identity.schema.json",
        )
        for rel in micro_required:
            path = micro / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            data = (rel + "\n").encode()
            path.write_bytes(data)
            files.append({"path": "vendor/micro-node-runtime/" + rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        proofs["micro-node-runtime"] = {
            "state": "VERIFIED_LOCAL_GIT_SOURCE",
            "repository": "StegVerse-002/micro-node-runtime",
            "materialized_subpath": "vendor/micro-node-runtime",
            "head": worker.MICRO_NODE_SOURCE_PIN,
            "exact_head_verified": True,
        }

        formal = control / "vendor" / "formal" / "TT"
        formal.mkdir(parents=True, exist_ok=True)
        formal_data = b"formal\n"
        (formal / "FORMAL.txt").write_bytes(formal_data)
        files.append({"path": "vendor/formal/TT/FORMAL.txt", "size": len(formal_data), "sha256": hashlib.sha256(formal_data).hexdigest()})
        proofs["formal-TT"] = {
            "state": "VERIFIED_LOCAL_GIT_SNAPSHOT",
            "repository": "Admissible-Existence/TT",
            "materialized_subpath": "vendor/formal/TT",
            "exact_commit": worker.PINS["TT"],
            "exact_commit_present": True,
        }

        master = control / "vendor" / "master-records-orchestration"
        verifier_rel = "scripts/verify_sv002_self_characterization_reconstruction.py"
        verifier = master / verifier_rel
        verifier.parent.mkdir(parents=True, exist_ok=True)
        verifier_data = b"# verifier\n"
        verifier.write_bytes(verifier_data)
        files.append({"path": "vendor/master-records-orchestration/" + verifier_rel, "size": len(verifier_data), "sha256": hashlib.sha256(verifier_data).hexdigest()})
        proofs["master-records-orchestration"] = {
            "state": "VERIFIED_LOCAL_GIT_SOURCE",
            "repository": "master-records/orchestration",
            "materialized_subpath": "vendor/master-records-orchestration",
            "required_ancestor": worker.MASTER_RECORDS_RECONSTRUCTION_COMMIT,
            "required_ancestor_present": True,
            "verifier_git_blob": worker.MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB,
        }

        manifest = {
            "schema": "stegverse.sovereign-control-plane-bundle/v1",
            "files": files,
            "vendor_source_proofs": proofs,
            "network_fetch_required": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "bundle_grants_authority": False,
        }
        manifest_path = control / ".stegverse-source-manifest.json"
        manifest_path.write_text(json.dumps(manifest) + "\n")
        return manifest_path, micro, formal, master, micro_required, verifier_rel

    def test_portable_micro_formal_and_master_sources_validate(self):
        with tempfile.TemporaryDirectory() as td:
            manifest, micro, formal, master, micro_required, verifier_rel = self._fixture(Path(td))
            env = {
                "STEGVERSE_RESIDENT_SOURCE_MANIFEST": str(manifest),
                "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": str(micro),
                "STEGVERSE_TT_ROOT": str(formal),
                "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT": str(master),
            }
            with mock.patch.dict(os.environ, env, clear=True):
                m, mmode = worker.portable_source_root(
                    "micro-node-runtime", "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", micro_required,
                    exact_head=worker.MICRO_NODE_SOURCE_PIN,
                )
                t, tmode = worker.portable_source_root(
                    "formal-TT", "STEGVERSE_TT_ROOT", (),
                    exact_commit=worker.PINS["TT"],
                    proof_states=("VERIFIED_LOCAL_GIT_SNAPSHOT",),
                )
                r, rmode = worker.portable_source_root(
                    "master-records-orchestration", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
                    (verifier_rel,),
                    required_ancestor=worker.MASTER_RECORDS_RECONSTRUCTION_COMMIT,
                    verifier_blob=worker.MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB,
                )
            self.assertEqual(m, micro.resolve())
            self.assertEqual(t, formal.resolve())
            self.assertEqual(r, master.resolve())
            self.assertEqual(mmode, "VERIFIED_PORTABLE_BUNDLE_PROOF")
            self.assertEqual(tmode, "VERIFIED_PORTABLE_BUNDLE_PROOF")
            self.assertEqual(rmode, "VERIFIED_PORTABLE_BUNDLE_PROOF")

    def test_portable_source_digest_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            manifest, micro, _formal, _master, micro_required, _verifier_rel = self._fixture(Path(td))
            (micro / micro_required[0]).write_text("drift\n")
            with mock.patch.dict(os.environ, {
                "STEGVERSE_RESIDENT_SOURCE_MANIFEST": str(manifest),
                "STEGVERSE_MICRO_NODE_RUNTIME_ROOT": str(micro),
            }, clear=True):
                selected, reason = worker.portable_source_root(
                    "micro-node-runtime", "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", micro_required,
                    exact_head=worker.MICRO_NODE_SOURCE_PIN,
                )
            self.assertIsNone(selected)
            self.assertEqual(reason, "PORTABLE_SOURCE_DIGEST_MISMATCH")


if __name__ == "__main__":
    unittest.main()
