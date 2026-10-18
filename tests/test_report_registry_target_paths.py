import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import report_registry_target_paths as rtp  # noqa: E402

TREE = {"stegverse/tier_pricing.py", "stegverse/cost_registry.py"}


def resolver(repo):
    if repo == "O/Private":
        return (None, None, "RuntimeError: not found")
    return ("a" * 40, TREE, None)


def row(paths, repos=("StegVerse-org/StegVerse-SDK",), task="T-1"):
    return {"task_id": task, "targets": {"paths": list(paths), "repositories": list(repos)}}


class TargetPathsReportTests(unittest.TestCase):
    def test_resolved_row_is_allow(self):
        r = rtp.build_report({"generation": 1, "tasks": [row(TREE)]}, [], resolver)
        self.assertEqual(r["rows"][0]["state"], "RESOLVED")
        self.assertEqual(r["resolved"], 1)

    def test_unresolved_row_is_six_field_fail_closed_report_only(self):
        r = rtp.build_report({"tasks": [row(["stegverse/tier_pricing.py", "stegverse/cost_component_registry.py"])]}, [], resolver)
        item = r["rows"][0]
        self.assertEqual(item["state"], "TARGET_PATHS_UNRESOLVED")
        self.assertEqual(item["unresolved_paths"], ["stegverse/cost_component_registry.py"])
        for f in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal", "next_attempt"):
            self.assertTrue(item[f])
        self.assertFalse(r["registry_written"]); self.assertFalse(r["shard_written"]); self.assertFalse(r["ledger_appended"])

    def test_unobservable_repository_fails_closed(self):
        r = rtp.build_report({"tasks": [row(["x.py"], repos=["O/Private"])]}, [], resolver)
        self.assertEqual(r["rows"][0]["failure_code"], "TARGET_PATHS_NOT_OBSERVABLE")

    def test_invalid_paths_and_repositories(self):
        r = rtp.build_report({"tasks": [row(["../x"]), row(["a.py"], repos=["bad"], task="T-2")]}, [], resolver)
        self.assertEqual([x["failure_code"] for x in r["rows"]], ["TARGET_PATHS_INVALID", "TARGET_REPOSITORIES_INVALID"])

    def test_registry_shard_drift_is_reported(self):
        reg = {"tasks": [row(["stegverse/cost_component_registry.py"], task="T-9")]}
        r = rtp.build_report(reg, [("T-9.json", row(["stegverse/cost_registry.py"], task="T-9"))], resolver)
        self.assertEqual(r["registry_shard_target_paths_drift"][0]["task_id"], "T-9")

    def test_rows_without_paths_are_ignored(self):
        r = rtp.build_report({"tasks": [{"task_id": "X", "targets": {"repositories": ["a/b"]}}]}, [], resolver)
        self.assertEqual(r["rows_with_target_paths"], 0)

    def test_report_mode_exits_zero_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Path(d) / "reg.json"
            content = json.dumps({"tasks": [row(["missing.py"], repos=["O/Private"])]})
            reg.write_text(content)
            original = rtp.git_resolver
            rtp.git_resolver = lambda w: resolver
            try:
                self.assertEqual(rtp.main(["--registry", str(reg), "--shards", str(Path(d) / "none")]), 0)
                self.assertEqual(rtp.main(["--registry", str(reg), "--shards", str(Path(d) / "none"), "--enforce"]), 1)
            finally:
                rtp.git_resolver = original
            self.assertEqual(reg.read_text(), content)


if __name__ == "__main__":
    unittest.main()
