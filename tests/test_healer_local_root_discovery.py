from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workers" / "healer_sovereign_scheduler_worker.py"
SPEC = importlib.util.spec_from_file_location("healer_root_discovery", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def make_healer(root: Path) -> Path:
    healer = root / "StegVerse-Labs" / "StegVerse-Healer"
    (healer / "app").mkdir(parents=True)
    (healer / "data").mkdir(parents=True)
    (healer / "docs").mkdir(parents=True)
    (healer / "app" / "dispatch_orchestrators.py").write_text("# dispatcher\n")
    (healer / "data" / "orchestrator_targets.json").write_text("{}\n")
    (healer / "docs" / "HEALER_MIRROR_HANDOFF.md").write_text("# handoff\n")
    return healer


class HealerLocalRootDiscoveryTests(unittest.TestCase):
    def test_discovers_unique_canonical_healer_root_without_env(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "repos"
            healer = make_healer(base)
            old = MOD.CANONICAL_REPO_BASES
            MOD.CANONICAL_REPO_BASES = (base,)
            try:
                root, source = MOD.discover_healer_root("")
            finally:
                MOD.CANONICAL_REPO_BASES = old
        self.assertEqual(root, healer.resolve())
        self.assertEqual(source, "CANONICAL_LOCAL_DISCOVERY")

    def test_discovers_local_repository_map_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "repos"
            healer = make_healer(base)
            site = base / "StegVerse-Labs" / "Site"
            site.mkdir(parents=True)
            old = MOD.CANONICAL_REPO_BASES
            MOD.CANONICAL_REPO_BASES = (base,)
            try:
                roots, source = MOD.discover_repo_roots("")
            finally:
                MOD.CANONICAL_REPO_BASES = old
        self.assertEqual(source, "CANONICAL_LOCAL_DISCOVERY")
        self.assertEqual(roots["StegVerse-Labs/StegVerse-Healer"], str(healer.resolve()))
        self.assertEqual(roots["StegVerse-Labs/Site"], str(site.resolve()))

    def test_explicit_nonsecret_map_takes_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "repo"
            path.mkdir()
            roots, source = MOD.discover_repo_roots(json.dumps({"Example/Repo": str(path)}))
        self.assertEqual(source, "EXPLICIT_NONSECRET_OVERRIDE")
        self.assertEqual(roots, {"Example/Repo": str(path.resolve())})


    def test_named_safe_local_roots_are_merged_without_overriding_explicit_map(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            llm = base / "llm"
            tvc = base / "tvc"
            llm.mkdir()
            tvc.mkdir()
            with mock.patch.dict(
                MOD.os.environ,
                {
                    "STEGVERSE_LLM_ADAPTER_ROOT": str(llm),
                    "STEGVERSE_TVC_ROOT": str(tvc),
                },
                clear=False,
            ):
                roots = MOD.merge_named_repository_roots({"Existing/Repo": "/existing"})
        self.assertEqual(roots["Existing/Repo"], "/existing")
        self.assertEqual(roots["StegVerse-org/LLM-adapter"], str(llm.resolve()))
        self.assertEqual(roots["StegVerse-Labs/TVC"], str(tvc.resolve()))

    def test_ambiguous_healer_discovery_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            first = Path(td) / "one"
            second = Path(td) / "two"
            make_healer(first)
            make_healer(second)
            old = MOD.CANONICAL_REPO_BASES
            MOD.CANONICAL_REPO_BASES = (first, second)
            try:
                root, source = MOD.discover_healer_root("")
            finally:
                MOD.CANONICAL_REPO_BASES = old
        self.assertIsNone(root)
        self.assertEqual(source, "AMBIGUOUS")


if __name__ == "__main__":
    unittest.main()
