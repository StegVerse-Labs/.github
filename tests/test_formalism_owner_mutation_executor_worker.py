from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workers import formalism_owner_mutation_executor_worker as worker


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class FormalismOwnerMutationExecutorTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "maximum_file_count": 8,
            "maximum_total_bytes": 65536,
            "require_handoff_first": True,
            "require_exact_inspection_receipt": True,
            "request_ttl_seconds": 900,
        }
        self.manifest = {
            "schema": worker.OWNER_MANIFEST_SCHEMA,
            "delta_id": "DELTA-001",
            "owner_repository": "StegVerse-Labs/StegCore",
            "claim_state": "READY_FOR_SEPARATE_OWNER_ADMISSION",
            "proposed_paths": [
                "MANIFOLD_GOVERNANCE_MIRROR_HANDOFF.md",
                "src/stegcore/manifold_governance.py",
            ],
        }
        handoff = "# owner handoff\n"
        source = "VALUE = 1\n"
        self.packet = {
            "schema": worker.SOURCE_PACKET_SCHEMA,
            "delta_id": "DELTA-001",
            "owner_repository": "StegVerse-Labs/StegCore",
            "generator_authority_ref": "authority://owner/code-change-agent/DELTA-001",
            "generator_profile_ref": "control/worker-capability-profiles.json#code-change-agent-v1",
            "source_generation_authorized": True,
            "base_ref": "main",
            "expected_base_sha": "a" * 40,
            "new_branch": "feat/delta-001",
            "commit_message": "Implement DELTA-001",
            "files": [
                {
                    "path": "MANIFOLD_GOVERNANCE_MIRROR_HANDOFF.md",
                    "content_utf8": handoff,
                    "expected_source_sha256": "b" * 64,
                    "replacement_sha256": sha(handoff),
                },
                {
                    "path": "src/stegcore/manifold_governance.py",
                    "content_utf8": source,
                    "expected_source_sha256": "c" * 64,
                    "replacement_sha256": sha(source),
                },
            ],
        }

    def inspection_root(self) -> tempfile.TemporaryDirectory:
        td = tempfile.TemporaryDirectory()
        inbox = Path(td.name) / "inbox"
        inbox.mkdir(parents=True)
        receipt = {
            "schema": worker.INSPECTION_RECEIPT_SCHEMA,
            "repository": "StegVerse-Labs/StegCore",
            "base_ref": "main",
            "base_sha": "a" * 40,
            "credential_authority": "TV/TVC",
            "credential_value_exposed": False,
            "non_tv_tvc_secret_or_token_used": False,
        }
        (inbox / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        return td

    def test_authorized_exact_packet_prepares_tvc_warrant(self):
        td = self.inspection_root()
        self.addCleanup(td.cleanup)
        prepared, error = worker.validate_source_packet(self.config, self.manifest, self.packet, Path(td.name))
        self.assertIsNone(error)
        self.assertEqual(prepared["repository"], "StegVerse-Labs/StegCore")
        warrant = worker.build_warrant(self.config, prepared, datetime(2026, 8, 14, tzinfo=timezone.utc))
        self.assertEqual(warrant["operation_class"], "APPLY_BOUNDED_FILE_SET")
        self.assertEqual(warrant["credential_authority"], "TV/TVC")
        self.assertFalse(warrant["consumer_credential_present"])
        self.assertFalse(warrant["secret_values_present"])
        self.assertEqual(warrant["files"][0]["path"], "MANIFOLD_GOVERNANCE_MIRROR_HANDOFF.md")

    def test_source_generation_authority_cannot_be_inferred(self):
        td = self.inspection_root()
        self.addCleanup(td.cleanup)
        packet = dict(self.packet)
        packet["source_generation_authorized"] = False
        prepared, error = worker.validate_source_packet(self.config, self.manifest, packet, Path(td.name))
        self.assertIsNone(prepared)
        self.assertEqual(error, "SOURCE_GENERATION_NOT_AUTHORIZED")

    def test_handoff_must_be_first_mutation(self):
        td = self.inspection_root()
        self.addCleanup(td.cleanup)
        packet = dict(self.packet)
        packet["files"] = list(reversed(self.packet["files"]))
        prepared, error = worker.validate_source_packet(self.config, self.manifest, packet, Path(td.name))
        self.assertIsNone(prepared)
        self.assertEqual(error, "HANDOFF_NOT_FIRST_MUTATION")

    def test_path_scope_cannot_expand(self):
        td = self.inspection_root()
        self.addCleanup(td.cleanup)
        packet = dict(self.packet)
        files = [dict(row) for row in self.packet["files"]]
        files[1]["path"] = "src/stegcore/steggate.py"
        packet["files"] = files
        prepared, error = worker.validate_source_packet(self.config, self.manifest, packet, Path(td.name))
        self.assertIsNone(prepared)
        self.assertEqual(error, "PATH_NOT_ADMITTED:src/stegcore/steggate.py")

    def test_traversal_and_wildcards_are_refused(self):
        self.assertFalse(worker.safe_repo_path("../StegCore/README.md"))
        self.assertFalse(worker.safe_repo_path("src/**/*.py"))
        self.assertTrue(worker.safe_repo_path("src/stegcore/manifold_governance.py"))

    def test_exact_tvc_inspection_receipt_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            prepared, error = worker.validate_source_packet(self.config, self.manifest, self.packet, Path(td))
        self.assertIsNone(prepared)
        self.assertEqual(error, "EXACT_TVC_INSPECTION_RECEIPT_MISSING")

    def test_replacement_hash_must_bind_content(self):
        td = self.inspection_root()
        self.addCleanup(td.cleanup)
        packet = dict(self.packet)
        files = [dict(row) for row in self.packet["files"]]
        files[1]["replacement_sha256"] = "0" * 64
        packet["files"] = files
        prepared, error = worker.validate_source_packet(self.config, self.manifest, packet, Path(td.name))
        self.assertIsNone(prepared)
        self.assertEqual(error, "REPLACEMENT_SHA_MISMATCH:src/stegcore/manifold_governance.py")


if __name__ == "__main__":
    unittest.main()
