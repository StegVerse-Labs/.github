"""Registry generation fence: a registry change must be the live tip + 1.

Deterministic: each case builds a throwaway git repository with fixed
identities and dates. Nothing touches the network or the real registry.
"""
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_registry_generation_fence.py"
spec = importlib.util.spec_from_file_location("registry_generation_fence", SCRIPT)
fence = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fence)

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
       "GIT_AUTHOR_DATE": "2026-10-17T00:00:00Z", "GIT_COMMITTER_DATE": "2026-10-17T00:00:00Z",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


class Repo:
    def __init__(self, path: Path):
        self.path = path
        self.git("init", "-q", "-b", "main")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.path), *args], env=ENV, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, generation=None, rows=(), raw=None, other=None):
        target = self.path / fence.REGISTRY_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        if raw is not None:
            target.write_text(raw, encoding="utf-8")
        elif generation is not None:
            target.write_text(json.dumps({"generation": generation, "tasks": list(rows)}),
                              encoding="utf-8")
        if other is not None:
            (self.path / "other.txt").write_text(other, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", f"g{generation}")
        return self.git("rev-parse", "HEAD")


class RegistryGenerationFenceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self._tmp.name))
        self.root = self.repo.commit(317, ["A"])

    def tearDown(self):
        self._tmp.cleanup()

    def branch(self, name, start):
        self.repo.git("checkout", "-q", "-b", name, start)

    def pr(self, base="main", head="HEAD"):
        return fence.check_pull_request(self.repo.path, base, head)

    def push(self, before, after):
        return fence.check_push(self.repo.path, before, after)

    def assertSixFields(self, result, code):
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], code)
        for key in fence.SIX_FIELDS:
            self.assertTrue(result[key], key)
        self.assertEqual(result["owning_goal"], "STEGVERSE-CANONICAL-WORK-COORDINATION-001")

    def test_pr_at_tip_plus_one_passes(self):
        self.branch("lane", self.root)
        self.repo.commit(318, ["A", "B"])
        result = self.pr()
        self.assertEqual(result["state"], "PASS")
        self.assertTrue(result["session_mutation_generation_fence"]["coordination_generation_current"])

    def test_pr_at_tip_fails(self):
        self.branch("lane", self.root)
        self.repo.commit(317, ["A", "B"])
        self.assertSixFields(self.pr(), fence.NOT_TIP_PLUS_ONE)

    def test_pr_stale_at_old_tip_plus_one_fails(self):
        # The 4683db2/60d90c4 shape: both lanes branch at 317 and take 318.
        self.branch("lane", self.root)
        self.repo.commit(318, ["A", "LANE"])
        self.repo.git("checkout", "-q", "main")
        self.repo.commit(318, ["A", "OTHER"])
        result = self.pr(head="lane")
        self.assertSixFields(result, fence.NOT_TIP_PLUS_ONE)
        self.assertIn("319", result["required_repair"])
        self.assertEqual(result["evidence"]["tip_generation"], 318)

    def test_pr_rebased_after_tip_moved_passes(self):
        self.repo.commit(318, ["A", "OTHER"])
        self.branch("lane", "main")
        self.repo.commit(319, ["A", "OTHER", "LANE"])
        self.assertEqual(self.pr(head="lane")["state"], "PASS")

    def test_pr_not_touching_registry_is_not_applicable(self):
        self.branch("lane", self.root)
        self.repo.commit(other="x")
        self.repo.git("checkout", "-q", "main")
        self.repo.commit(318, ["A", "OTHER"])
        self.assertEqual(self.pr(head="lane")["state"], "PASS_NOT_APPLICABLE")

    def test_pr_unreadable_generation_fails(self):
        self.branch("lane", self.root)
        self.repo.commit(raw="{not json")
        self.assertSixFields(self.pr(), fence.UNREADABLE)

    def test_pr_non_integer_generation_fails(self):
        self.branch("lane", self.root)
        self.repo.commit(raw=json.dumps({"generation": "318"}))
        self.assertSixFields(self.pr(), fence.UNREADABLE)

    def test_pr_unresolvable_base_fails(self):
        self.assertSixFields(self.pr(base="refs/heads/absent"), fence.UNREADABLE)

    def test_push_advancing_generation_passes(self):
        after = self.repo.commit(318, ["A", "B"])
        self.assertEqual(self.push(self.root, after)["state"], "PASS")

    def test_push_duplicate_generation_with_changed_content_fails(self):
        first = self.repo.commit(318, ["A", "B"])
        second = self.repo.commit(318, ["A", "B", "C"])
        result = self.push(first, second)
        self.assertSixFields(result, fence.DUPLICATED)
        self.assertIn("319", result["required_repair"])

    def test_push_range_catches_duplicate_inside_range(self):
        self.repo.commit(318, ["A", "B"])
        after = self.repo.commit(318, ["A", "B", "C"])
        self.assertSixFields(self.push(self.root, after), fence.DUPLICATED)

    def test_push_regressed_generation_fails(self):
        first = self.repo.commit(318, ["A", "B"])
        second = self.repo.commit(316, ["A", "B", "C"])
        self.assertSixFields(self.push(first, second), fence.DUPLICATED)

    def test_push_unchanged_registry_passes(self):
        after = self.repo.commit(other="x")
        self.assertEqual(self.push(self.root, after)["state"], "PASS")

    def test_push_unreadable_generation_fails(self):
        after = self.repo.commit(raw="")
        self.assertSixFields(self.push(self.root, after), fence.UNREADABLE)

    def test_push_zero_before_uses_first_parent(self):
        after = self.repo.commit(317, ["A", "B"])
        self.assertSixFields(self.push("0" * 40, after), fence.DUPLICATED)

    def test_main_exits_non_zero_and_writes_six_field_summary(self):
        first = self.repo.commit(318, ["A", "B"])
        second = self.repo.commit(318, ["A", "B", "C"])
        summary = Path(self._tmp.name) / "summary.md"
        old = os.environ.get("GITHUB_STEP_SUMMARY")
        os.environ["GITHUB_STEP_SUMMARY"] = str(summary)
        try:
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                code = fence.main(["--mode", "push", "--repo", str(self.repo.path),
                                   "--before", first, "--after", second])
        finally:
            if old is None:
                os.environ.pop("GITHUB_STEP_SUMMARY", None)
            else:
                os.environ["GITHUB_STEP_SUMMARY"] = old
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out.getvalue())["event_ledger_written"])
        text = summary.read_text(encoding="utf-8")
        for key in fence.SIX_FIELDS:
            self.assertIn(f"| {key} |", text)
        self.assertIn(fence.DUPLICATED, text)

    def test_reuses_policy_fence_and_collision_gate_payload(self):
        self.assertTrue(fence.session_fence_policy()["exact_generation_match_required"])
        self.assertFalse(fence.generation_fence_payload(317, 318)["coordination_generation_current"])


if __name__ == "__main__":
    unittest.main()
