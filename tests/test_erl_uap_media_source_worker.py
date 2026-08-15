from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workers" / "erl_uap_media_source_worker.py"
spec = importlib.util.spec_from_file_location("erl_uap_media_source_worker", MODULE_PATH)
worker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(worker)


class ErlUapMediaSourceWorkerTests(unittest.TestCase):
    def test_child_environment_excludes_github_tokens(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "forbidden", "GH_TOKEN": "forbidden", "PATH": "/usr/bin"}, clear=False):
            env = worker.child_env(Path("/tmp/erl"))
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertEqual(env["PYTHONPATH"], "/tmp/erl")

    def test_explicit_local_source_root_is_resolved_without_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "config").mkdir()
            (root / "docs").mkdir()
            (root / "scripts" / "process_uap_source_queue.py").write_text("# worker\n")
            (root / "config" / "uap-media-source-queue.json").write_text("{}\n")
            (root / "docs" / "UAP_MEDIA_RESEARCH_MIRROR_HANDOFF.md").write_text("# handoff\n")
            with mock.patch.dict(os.environ, {"STEGVERSE_ERL_SOURCE_ROOT": str(root)}, clear=False):
                resolved = worker.find_source_root()
            self.assertEqual(resolved, root.resolve())

    def test_missing_source_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with mock.patch.dict(os.environ, {"STEGVERSE_ERL_SOURCE_ROOT": str(missing), "HOME": str(Path(tmp) / "home")}, clear=False):
                with mock.patch.object(worker, "ROOT", Path(tmp) / "control"):
                    self.assertIsNone(worker.find_source_root())

    def test_blocker_never_requests_credentials_or_human_action(self):
        block = worker.blocker("problem", "action", "condition")
        self.assertFalse(block["github_token_required"])
        self.assertFalse(block["non_tv_tvc_secret_or_token_required"])
        self.assertFalse(block["human_action_required"])
        self.assertTrue(block["solution_required"])


if __name__ == "__main__":
    unittest.main()
