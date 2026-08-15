from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workers" / "erl_uap_media_source_worker.py"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "erl-uap-media-source-001.json"
REGISTRY = ROOT / "control" / "worker-registry.d" / "erl-uap-media-001.json"
HANDOFF = ROOT / "handoffs" / "SHWP-ERL-UAP-MEDIA-001.json"
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

    def test_adapter_binds_only_nonsecret_source_locator(self):
        adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))["adapters"][0]
        self.assertEqual(adapter["adapter_ref"], "process:erl-uap-media-source-v1")
        self.assertEqual(adapter["command"], ["python", "workers/erl_uap_media_source_worker.py"])
        self.assertEqual(adapter["env_allowlist"], ["STEGVERSE_ERL_SOURCE_ROOT"])
        forbidden = {"GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "AUTHORIZATION", "COOKIE"}
        self.assertTrue(forbidden.isdisjoint(adapter["env_allowlist"]))

    def test_registry_handoff_and_adapter_match_exact_capabilities(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        task = registry["tasks"][0]
        registered_worker = registry["workers"][0]
        adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))["adapters"][0]
        expected = {"runtime_observation", "bounded_process_execution", "public_source_acquisition", "evidence_class_preservation"}
        self.assertEqual(set(handoff["execution"]["required_capabilities"]), expected)
        self.assertEqual(set(registered_worker["capabilities"]), expected)
        self.assertEqual(set(adapter["capabilities"]), expected)
        self.assertEqual(task["admissible_existence"]["task_relationship"], "integrates_capability")
        self.assertFalse(registry["github_token_required"])
        self.assertFalse(registry["non_tv_tvc_secret_or_token_required"])
        self.assertFalse(registry["research_promotion_authority"])
        self.assertFalse(registry["publication_authority"])


if __name__ == "__main__":
    unittest.main()
