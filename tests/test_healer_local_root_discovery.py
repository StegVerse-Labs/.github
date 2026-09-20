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


    def test_local_git_healer_source_requires_pr92_floor_and_exact_schedule_binding(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            healer = make_healer(base)
            schedule = {
                "schema": "stegverse.reusable-task-schedule/v1",
                "tasks": [{
                    "reusable_task_id": MOD.HEALER_STEGHEALTH_REUSABLE_TASK_ID,
                    "tracking_task_id": MOD.HEALER_STEGHEALTH_TASK_ID,
                    "cosv_task_vector": "60000000111000",
                    "repository": "StegVerse-Labs/.github",
                    "enabled": True,
                    "invocation_key": MOD.HEALER_STEGHEALTH_TASK_ID,
                    "parameters": {
                        "only_consumer": "canonical_work_coordination",
                        "goal_task_id": MOD.HEALER_STEGHEALTH_TASK_ID,
                    },
                }],
            }
            (healer / "data" / "reusable_task_schedule.json").write_text(json.dumps(schedule) + "\n")
            subprocess = __import__("subprocess")
            subprocess.run(["git", "init", str(healer)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(healer), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(healer), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(healer), "add", "."], check=True)
            subprocess.run(["git", "-C", str(healer), "commit", "-m", "floor"], check=True, capture_output=True)
            floor = subprocess.run(["git", "-C", str(healer), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            old = MOD.HEALER_STEGHEALTH_SOURCE_FLOOR
            MOD.HEALER_STEGHEALTH_SOURCE_FLOOR = floor
            try:
                result = MOD.verify_healer_source_freshness(healer)
            finally:
                MOD.HEALER_STEGHEALTH_SOURCE_FLOOR = old
        self.assertEqual(result["state"], "CURRENT")
        self.assertEqual(result["source_mode"], "LOCAL_GIT_DESCENDANT")
        self.assertTrue(result["source_floor_present"])

    def test_vendored_healer_source_accepts_verified_bundle_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            control = Path(td) / "control"
            healer = control / "vendor" / "StegVerse-Healer"
            (healer / "app").mkdir(parents=True)
            (healer / "data").mkdir(parents=True)
            (healer / "docs").mkdir(parents=True)
            (healer / "app" / "dispatch_orchestrators.py").write_text("# dispatcher\n")
            (healer / "data" / "orchestrator_targets.json").write_text("{}\n")
            (healer / "docs" / "HEALER_MIRROR_HANDOFF.md").write_text("# handoff\n")
            schedule = {
                "schema": "stegverse.reusable-task-schedule/v1",
                "tasks": [{
                    "reusable_task_id": MOD.HEALER_STEGHEALTH_REUSABLE_TASK_ID,
                    "tracking_task_id": MOD.HEALER_STEGHEALTH_TASK_ID,
                    "cosv_task_vector": "60000000111000",
                    "repository": "StegVerse-Labs/.github",
                    "enabled": True,
                    "invocation_key": MOD.HEALER_STEGHEALTH_TASK_ID,
                    "parameters": {
                        "only_consumer": "canonical_work_coordination",
                        "goal_task_id": MOD.HEALER_STEGHEALTH_TASK_ID,
                    },
                }],
            }
            (healer / "data" / "reusable_task_schedule.json").write_text(json.dumps(schedule) + "\n")
            manifest = {
                "vendor_source_proofs": {
                    "StegVerse-Healer": {
                        "state": "VERIFIED_LOCAL_GIT_SOURCE",
                        "source_floor": MOD.HEALER_STEGHEALTH_SOURCE_FLOOR,
                        "source_floor_present": True,
                        "required_steghealth_binding_present": True,
                        "required_schedule_task_id": MOD.HEALER_STEGHEALTH_TASK_ID,
                        "clean_worktree_at_packaging": True,
                        "network_fetch_performed": False,
                    }
                }
            }
            (control / MOD.CONTROL_BUNDLE_MANIFEST).write_text(json.dumps(manifest) + "\n")
            result = MOD.verify_healer_source_freshness(healer)
        self.assertEqual(result["state"], "CURRENT")
        self.assertEqual(result["source_mode"], "VERIFIED_CONTROL_BUNDLE")

    def test_healer_source_without_required_schedule_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            healer = make_healer(Path(td))
            result = MOD.verify_healer_source_freshness(healer)
        self.assertEqual(result["state"], "STALE_OR_INCOMPLETE")
        self.assertEqual(result["schedule_binding_state"], "REQUIRED_SCHEDULE_MISSING")


if __name__ == "__main__":
    unittest.main()
