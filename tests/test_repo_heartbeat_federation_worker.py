import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "workers" / "repo_heartbeat_federation_worker.py"
SPEC = importlib.util.spec_from_file_location("repo_hb_worker", WORKER_PATH)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(worker)


class RepoHeartbeatFederationTests(unittest.TestCase):
    def expected(self):
        return {
            "repo_id": "tvc",
            "organization": "StegVerse-Labs",
            "repository": "StegVerse-Labs/TVC",
            "participant_class": "CONTROL",
            "required": True,
        }

    def manifest(self, fresh=True):
        now = datetime.now(timezone.utc)
        return {
            "schema": "stegverse.repo-heartbeat-manifest/v0.1",
            "repo_id": "tvc",
            "org": "StegVerse-Labs",
            "repository": "StegVerse-Labs/TVC",
            "participant_class": "CONTROL",
            "commit_sha": "a" * 40,
            "ref": "main",
            "release_tag": None,
            "runtime_id": "tvc-control",
            "handoff_hash": "b" * 64,
            "sequence": 7,
            "emitted_at": (now - timedelta(minutes=1)).isoformat(),
            "fresh_until": (now + timedelta(minutes=5) if fresh else now - timedelta(seconds=1)).isoformat(),
            "status": "READY",
            "capabilities": ["route_admission"],
            "dependencies": [],
            "last_success": now.isoformat(),
            "evidence_refs": ["docs/SOVEREIGN_LOCAL_MODEL_ROUTE_MIRROR_HANDOFF.md"],
            "authority": {
                "credential_authority": "TV/TVC",
                "heartbeat_grants_execution_authority": False,
                "github_token_required": False,
            },
        }

    def test_current_tvtvc_manifest_is_valid_and_fresh(self):
        valid, errors, stale = worker.validate_manifest(self.manifest(), self.expected(), datetime.now(timezone.utc))
        self.assertTrue(valid)
        self.assertFalse(errors)
        self.assertFalse(stale)

    def test_github_token_requirement_fails_closed(self):
        value = self.manifest()
        value["authority"]["github_token_required"] = True
        valid, errors, _ = worker.validate_manifest(value, self.expected(), datetime.now(timezone.utc))
        self.assertFalse(valid)
        self.assertIn("GITHUB_TOKEN_REQUIRED", errors)

    def test_legacy_tc_tvc_authority_is_not_current(self):
        value = self.manifest()
        value["authority"]["credential_authority"] = "TC/TVC"
        valid, errors, _ = worker.validate_manifest(value, self.expected(), datetime.now(timezone.utc))
        self.assertFalse(valid)
        self.assertIn("CREDENTIAL_AUTHORITY", errors)

    def test_stale_manifest_is_detected(self):
        valid, errors, stale = worker.validate_manifest(self.manifest(fresh=False), self.expected(), datetime.now(timezone.utc))
        self.assertTrue(valid)
        self.assertFalse(errors)
        self.assertTrue(stale)

    def test_topology_hash_is_deterministic(self):
        value = {"b": 2, "a": [1, 3]}
        self.assertEqual(worker.canonical_hash(value), worker.canonical_hash({"a": [1, 3], "b": 2}))


if __name__ == "__main__":
    unittest.main()
