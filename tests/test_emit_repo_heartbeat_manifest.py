import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emit_repo_heartbeat_manifest.py"


class EmitRepoHeartbeatManifestTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        (root / "HANDOFF_MIRROR_HANDOFF.md").write_text("canonical\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "init"], check=True)
        return temp, root

    def test_emitter_binds_git_identity_tvtvc_and_no_token(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        result = subprocess.run([
            sys.executable, str(SCRIPT),
            "--repo-root", str(root),
            "--repo-id", "example",
            "--org", "StegVerse-Labs",
            "--repository", "StegVerse-Labs/example",
            "--participant-class", "RUNTIME",
            "--runtime-id", "example-runtime",
            "--handoff", "HANDOFF_MIRROR_HANDOFF.md",
            "--sequence", "1",
            "--capability", "runtime",
            "--dependency", "tvc",
        ], capture_output=True, text=True, check=True)
        value = json.loads(result.stdout)
        self.assertEqual(len(value["commit_sha"]), 40)
        self.assertEqual(value["authority"]["credential_authority"], "TV/TVC")
        self.assertFalse(value["authority"]["github_token_required"])
        self.assertFalse(value["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(value["dependencies"], [{"repo_id": "tvc", "required": True}])
        self.assertEqual(len(value["handoff_hash"]), 64)

    def test_runtime_requires_runtime_id(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        result = subprocess.run([
            sys.executable, str(SCRIPT),
            "--repo-root", str(root),
            "--repo-id", "example",
            "--org", "StegVerse-Labs",
            "--repository", "StegVerse-Labs/example",
            "--participant-class", "RUNTIME",
            "--sequence", "1",
        ], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
