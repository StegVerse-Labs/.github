from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import workers.formalism_source_discovery_worker as discovery
import scripts.run_formalism_manifold_with_discovered_roots as wrapper


class FormalismSourceDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_discovery_root = discovery.ROOT
        self.old_wrapper_root = wrapper.ROOT
        self.old_manifest = wrapper.MANIFEST
        self.old_worker = wrapper.WORKER

    def tearDown(self) -> None:
        discovery.ROOT = self.old_discovery_root
        wrapper.ROOT = self.old_wrapper_root
        wrapper.MANIFEST = self.old_manifest
        wrapper.WORKER = self.old_worker

    def _config(self) -> dict:
        return {
            "repositories": ["Admissible-Existence/AE", "StegVerse-Labs/StegCore"],
            "search_templates": ["workloads/{owner}/{repo}", "source/{repo}"]
        }

    def _repo(self, path: Path, handoff: str) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / handoff).write_text("# mirror handoff\n", encoding="utf-8")

    def test_canonical_local_paths_are_discovered_without_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            discovery.ROOT = root
            self._repo(root / "workloads/Admissible-Existence/AE", "AE_MIRROR_HANDOFF.md")
            self._repo(root / "source/StegCore", "STEGCORE_MIRROR_HANDOFF.md")
            with patch.dict(os.environ, {}, clear=True):
                result = discovery.discover(self._config())
            self.assertTrue(result["complete"])
            self.assertFalse(result["network_checkout_performed"])
            self.assertFalse(result["github_token_required"])
            self.assertEqual(set(result["roots"]), {"Admissible-Existence/AE", "StegVerse-Labs/StegCore"})

    def test_missing_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            discovery.ROOT = Path(tmp)
            with patch.dict(os.environ, {}, clear=True):
                result = discovery.discover(self._config())
            self.assertFalse(result["complete"])
            self.assertEqual(result["missing"], ["Admissible-Existence/AE", "StegVerse-Labs/StegCore"])

    def test_ambiguous_local_roots_are_not_silently_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            discovery.ROOT = root
            self._repo(root / "workloads/Admissible-Existence/AE", "AE_MIRROR_HANDOFF.md")
            self._repo(root / "source/AE", "AE_MIRROR_HANDOFF.md")
            self._repo(root / "source/StegCore", "STEGCORE_MIRROR_HANDOFF.md")
            with patch.dict(os.environ, {}, clear=True):
                result = discovery.discover(self._config())
            self.assertFalse(result["complete"])
            self.assertEqual(result["ambiguous"], ["Admissible-Existence/AE"])

    def test_explicit_nonsecret_override_resolves_search_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            discovery.ROOT = root
            explicit = root / "explicit-ae"
            self._repo(explicit, "AE_MIRROR_HANDOFF.md")
            self._repo(root / "workloads/Admissible-Existence/AE", "AE_MIRROR_HANDOFF.md")
            self._repo(root / "source/StegCore", "STEGCORE_MIRROR_HANDOFF.md")
            env = {"STEGVERSE_FORMALISM_ROOTS_JSON": json.dumps({"Admissible-Existence/AE": str(explicit)})}
            with patch.dict(os.environ, env, clear=True):
                result = discovery.discover(self._config())
            self.assertTrue(result["complete"])
            self.assertEqual(result["roots"]["Admissible-Existence/AE"], str(explicit.resolve()))

    def test_wrapper_consumes_completed_no_token_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "receipts/formalism-source-discovery/formalism-roots.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({
                "schema": "stegverse.formalism-roots-manifest/v0.1",
                "state": "COMPLETED",
                "roots": {"Admissible-Existence/AE": "/var/lib/stegverse/source/AE"},
                "credential_authority": "TV/TVC",
                "github_token_required": False,
                "network_checkout_performed": False
            }), encoding="utf-8")
            wrapper.ROOT = root
            wrapper.MANIFEST = manifest
            with patch.dict(os.environ, {}, clear=True):
                resolved = json.loads(wrapper.resolved_roots_json())
            self.assertEqual(resolved["Admissible-Existence/AE"], "/var/lib/stegverse/source/AE")

    def test_wrapper_rejects_authorizing_or_network_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema": "stegverse.formalism-roots-manifest/v0.1",
                "state": "COMPLETED",
                "roots": {"Admissible-Existence/AE": "/tmp/ae"},
                "credential_authority": "OTHER",
                "github_token_required": True,
                "network_checkout_performed": True
            }), encoding="utf-8")
            wrapper.MANIFEST = manifest
            with patch.dict(os.environ, {}, clear=True):
                self.assertIsNone(wrapper.resolved_roots_json())


if __name__ == "__main__":
    unittest.main()
