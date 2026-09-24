import importlib.util
import json
import pathlib
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "retirement", ROOT / "scripts/repository_hygiene_retire_merged_refs.py")
retirement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retirement)

REPO = "StegVerse-Labs/.github"
TIP = "a" * 40

def evidence(branch="hygiene/merged-safe"):
    return {
        "repository": REPO,
        "branch": branch,
        "expected_sha": TIP,
        "release_authority": retirement.OWNER,
        "owner_disposition": "TERMINAL_UNOWNED_EVIDENCE_SAFE",
        "intr_decision": "ALLOW",
        "intr_receipt_sha256": "sha256:" + "b" * 64,
        "org_receipt_sha256": "sha256:" + "c" * 64,
        "master_records_receipt_sha256": "sha256:" + "d" * 64,
        "master_records_reconstruction": "PASS",
        "evidence_retention_clearance": True,
        "merge_pr": 123,
    }

def replies(command):
    target = command[-1]
    if "/branches/" in target:
        return json.dumps({"name": "hygiene/merged-safe", "protected": False, "commit": {"sha": TIP}})
    if "/pulls?" in target:
        return "[]"
    if "/pulls/" in target:
        return json.dumps({"merged": True, "head": {"ref": "hygiene/merged-safe", "sha": TIP}})
    if "/compare/" in target:
        return json.dumps({"ahead_by": 0, "files": []})
    if target == f"repos/{REPO}":
        return json.dumps({"default_branch": "main"})
    raise AssertionError(target)

class RetirementGuardTests(unittest.TestCase):
    def test_release_packet_is_not_optional(self):
        for key in ("release_authority", "owner_disposition", "intr_receipt_sha256",
                    "org_receipt_sha256", "master_records_receipt_sha256",
                    "master_records_reconstruction", "evidence_retention_clearance"):
            item = evidence()
            item.pop(key)
            self.assertIsNotNone(retirement.validate_entry(item, REPO), key)

    def test_protected_refs_are_never_approved(self):
        for name in ("main", "release/1.0", "support/long-term", "gh-pages"):
            self.assertEqual(retirement.validate_entry(evidence(name), REPO), "PROTECTED_REF")

    def test_closed_unmerged_requires_explicit_owner_release(self):
        item = evidence()
        item["merge_pr"] = None
        self.assertEqual(retirement.validate_entry(item, REPO),
                         "CLOSED_UNMERGED_PR_NOT_RELEASED")

    def test_exact_squash_merged_pr_head_does_not_require_git_ancestry(self):
        def squash(*args):
            if "/compare/" in args[-1]:
                self.fail("squash-merged head must be checked by exact GitHub merge proof")
            return replies(args)
        with patch.object(retirement, "command", side_effect=squash):
            self.assertIsNone(retirement.preflight_live(REPO, evidence()))

    def test_mismatched_merged_pr_head_fails_closed(self):
        def mismatched(*args):
            if "/pulls/" in args[-1] and "/pulls?" not in args[-1]:
                return json.dumps({"merged": True, "head": {"ref": "hygiene/merged-safe", "sha": "f" * 40}})
            return replies(args)
        with patch.object(retirement, "command", side_effect=mismatched):
            self.assertEqual(retirement.preflight_live(REPO, evidence()), "MERGE_PROOF_MISMATCH")

    def test_unmerged_explicit_release_does_not_skip_containment(self):
        item = evidence()
        item["merge_pr"] = None
        item["explicit_unmerged_release"] = True
        def divergent(*args):
            if "/compare/" in args[-1]:
                return json.dumps({"ahead_by": 1, "files": [{"filename": "unique.txt"}]})
            return replies(args)
        with patch.object(retirement, "command", side_effect=divergent):
            self.assertEqual(retirement.preflight_live(REPO, item), "UNMERGED_OR_UNIQUE_SOURCE")

    def test_live_tip_movement_fails_closed(self):
        def changed(*args):
            if "/branches/" in args[-1]:
                return json.dumps({"name": "hygiene/merged-safe", "protected": False,
                                   "commit": {"sha": "e" * 40}})
            return replies(args)
        with patch.object(retirement, "command", side_effect=changed):
            self.assertEqual(retirement.preflight_live(REPO, evidence()), "REF_TIP_MOVED")

    def test_active_open_pr_retains_branch(self):
        def active(*args):
            if "/pulls?" in args[-1]:
                return json.dumps([{"number": 55}])
            return replies(args)
        with patch.object(retirement, "command", side_effect=active):
            self.assertEqual(retirement.preflight_live(REPO, evidence()), "ACTIVE_PR_HEAD")

    def test_dry_run_never_pushes(self):
        with patch.object(retirement, "command", side_effect=lambda *x: replies(x)) as cmd:
            out = retirement.run({"schema": retirement.SCHEMA, "repository": REPO,
                                  "releases": [evidence()]}, apply=False)
            self.assertEqual(out["results"][0]["result"], "PREFLIGHT_ONLY_NO_DELETE")
            self.assertFalse(any(args[0][0] == "git" for args in cmd.call_args_list))

    def test_apply_uses_expected_tip_lease_only(self):
        def simulate(*args):
            if args[:3] == ("git", "remote", "get-url"):
                return "https://github.com/StegVerse-Labs/.github.git"
            if args[:2] == ("git", "ls-remote"):
                return ""
            if args[0] == "git":
                self.assertIn(f"--force-with-lease=refs/heads/hygiene/merged-safe:{TIP}", args)
                self.assertIn(":refs/heads/hygiene/merged-safe", args)
                return ""
            return replies(args)
        with patch.object(retirement, "command", side_effect=simulate):
            out = retirement.run({"schema": retirement.SCHEMA, "repository": REPO,
                                  "releases": [evidence()]}, apply=True)
            self.assertEqual(out["results"][0]["result"],
                             "REF_DELETED_ORG_MR_CLOSURE_REQUIRED")

    def test_wrong_checkout_origin_blocks_deletion(self):
        def wrong_origin(*args):
            if args[:3] == ("git", "remote", "get-url"):
                return "https://github.com/other/other.git"
            if args[0] == "git":
                self.fail("unexpected Git write or readback")
            return replies(args)
        with patch.object(retirement, "command", side_effect=wrong_origin):
            out = retirement.run({"schema": retirement.SCHEMA, "repository": REPO,
                                  "releases": [evidence()]}, apply=True)
            self.assertEqual(out["results"][0]["result"], "RETAIN")
            self.assertIn("origin does not match", out["results"][0]["reason"])

if __name__ == "__main__":
    unittest.main()
