"""Fixture tests for the native email continuation transitions (issue #3039).

AC1 gap tolerance, AC2 chained consecutive cycles, AC3 pagination beyond 100,
mid-pagination interruption resume, shifted-page dedup, incident grouping,
exact-head resolution and non-archival of unresolved failures.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import native_email_continuation_transition as t  # noqa: E402

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_FIX = "c" * 40


def msg(i: int, *, repo: str = "StegVerse-Labs/StegDB", workflow: str = "workflow-lint",
        sha: str = SHA_A, subject: str = "Run failed: workflow-lint", epoch: int = 1000) -> dict:
    return {"message_id": f"m{i:05d}", "repository": repo, "workflow": workflow,
            "head_sha": sha, "subject": subject, "internal_epoch": epoch}


def gen() -> dict:
    """Genesis with the fixture repository declared public (unredacted)."""
    return ok(t.set_public_repositories(t.genesis(), ["StegVerse-Labs/StegDB"]))


def pages(rows: list[dict], size: int = t.PAGE_LIMIT) -> list[list[dict]]:
    return [rows[i:i + size] for i in range(0, len(rows), size)] or [[]]


def ok(result):
    state, disp = result
    assert disp["disposition"] == t.ALLOW, disp
    return state


def run_cycle(state: dict, now: int, mailbox: list[dict]) -> list[dict]:
    chain = [ok(t.begin_cycle(state, now))]
    for i, page in enumerate(pages(mailbox)):
        chain.append(ok(t.apply_page(chain[-1], i, page)))
    chain.append(ok(t.complete_pagination(chain[-1], has_more=False)))
    return chain


class ContinuationTransitionTests(unittest.TestCase):
    def test_genesis_is_non_authorizing_and_needs_no_host_or_scheduler(self):
        g = t.genesis()
        self.assertEqual(g["public_repositories"], [])
        self.assertEqual(g["authority_effect"], "NONE")
        self.assertTrue(g["projection_only"])
        self.assertEqual(g["worker_claim"]["authority"], "WORKERCOORDINATOR")
        self.assertIsNone(g["worker_claim"]["claim_ref"])
        self.assertFalse(g["external_host_prerequisite"])
        self.assertFalse(g["scheduler_prerequisite"])
        self.assertEqual(g["github_actions_runtime_authority"], "NONE")

    def test_committed_state_is_valid_and_discloses_only_public_repositories(self):
        committed = json.loads((ROOT / "data/native-email-action-monitor/continuation.json").read_text(encoding="utf-8"))
        self.assertIsNone(t._check(committed))
        self.assertEqual(committed["authority_effect"], "NONE")
        public = set(committed["public_repositories"])
        for inc in committed["incidents"].values():
            self.assertTrue(inc["repository"] is None or inc["repository"] in public, inc["incident_id"])
        # Only messages of verified incidents may be proposed or archived (owner
        # authorized remediated-only archiving, #3039 2026-10-10); every verified
        # message is either still proposed or confirmed archived, never both.
        verified = {mid for inc in committed["incidents"].values() if inc["state"] in t.ARCHIVABLE
                    for mid in inc["message_ids"]}
        proposed = set(committed["archive_proposed"])
        archived = set(committed["archived_message_ids"])
        self.assertTrue(proposed.isdisjoint(archived))
        self.assertEqual(proposed | archived, verified)
        self.assertEqual(committed["counters"]["archived_confirmed"], len(archived))

    def test_pagination_beyond_100_with_grouping(self):
        mailbox = [msg(i, sha=SHA_A if i % 2 else SHA_B) for i in range(250)]
        chain = run_cycle(gen(), 5000, mailbox)
        end = chain[-1]
        self.assertEqual(end["counters"]["pages_scanned"], 3)
        self.assertEqual(end["counters"]["messages_seen"], 250)
        self.assertEqual(len(end["incidents"]), 2)  # grouped by exact head
        heads = {i["head_sha"] for i in end["incidents"].values()}
        self.assertEqual(heads, {SHA_A, SHA_B})
        self.assertTrue(all(i["correlation_complete"] for i in end["incidents"].values()))

    def test_interrupted_pagination_resumes_not_restarts(self):
        mailbox = [msg(i) for i in range(250)]
        p = pages(mailbox)
        s = ok(t.begin_cycle(gen(), 5000))
        s = ok(t.apply_page(s, 0, p[0]))
        # Executor stops here; state is persisted and reloaded by another executor.
        s = json.loads(json.dumps(s))
        again, disp = t.begin_cycle(s, 9000)
        self.assertEqual(disp["disposition"], t.DENY)
        self.assertEqual(disp["resume_page_index"], 1)
        _, disp = t.apply_page(s, 2, p[2])
        self.assertEqual(disp["failed_predicate"], "PAGE_INDEX_SKIPS_CONTINUATION")
        s = ok(t.apply_page(s, 1, p[1]))
        s = ok(t.apply_page(s, 2, p[2]))
        self.assertEqual(s["counters"]["messages_seen"], 250)
        self.assertEqual(len(s["processed_message_ids"]), 250)

    def test_shifted_page_is_deduplicated(self):
        mailbox = [msg(i) for i in range(200)]
        s = ok(t.begin_cycle(gen(), 5000))
        s = ok(t.apply_page(s, 0, mailbox[:100]))
        # Page 1 shifted by 10 after unrelated mailbox changes: overlaps page 0.
        s, disp = t.apply_page(s, 1, mailbox[90:190])
        self.assertEqual(disp["duplicates_suppressed"], 10)
        s = ok(t.apply_page(s, 2, mailbox[190:]))
        self.assertEqual(s["counters"]["messages_seen"], 200)

    def test_replayed_page_is_idempotent(self):
        s = ok(t.begin_cycle(gen(), 5000))
        s = ok(t.apply_page(s, 0, [msg(1)]))
        again, disp = t.apply_page(s, 0, [msg(1)])
        self.assertTrue(disp["idempotent_replay"])
        self.assertEqual(t.state_sha256(again), t.state_sha256(s))

    def test_missing_or_non_boolean_terminal_evidence_fails_closed(self):
        s = ok(t.begin_cycle(gen(), 5000))
        s = ok(t.apply_page(s, 0, [msg(1)]))
        for observed in (None, 0, "", "false", [], {}):
            same, disp = t.complete_pagination(s, observed)
            self.assertEqual(disp["disposition"], t.FAIL_CLOSED)
            self.assertEqual(disp["failed_predicate"], "PAGINATION_TERMINAL_EVIDENCE_REQUIRED")
            self.assertEqual(t.state_sha256(same), t.state_sha256(s))

    def test_cli_missing_terminal_evidence_does_not_advance(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"
            obs = Path(td) / "obs.json"
            script = str(ROOT / "scripts/native_email_continuation_transition.py")
            def run(op):
                return subprocess.run([sys.executable, "-I", script, "--state", str(state),
                                       "--op", op, "--input", str(obs)],
                                      capture_output=True, text=True, check=False)
            obs.write_text(json.dumps({}))
            self.assertEqual(run("genesis").returncode, 0)
            obs.write_text(json.dumps({"now_epoch": 5000}))
            self.assertEqual(run("begin").returncode, 0)
            obs.write_text(json.dumps({"page_index": 0, "messages": [msg(1)]}))
            self.assertEqual(run("page").returncode, 0)
            before = state.read_text()
            obs.write_text("{}")
            result = run("complete")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["failed_predicate"],
                             "PAGINATION_TERMINAL_EVIDENCE_REQUIRED")
            self.assertEqual(state.read_text(), before)

    def test_incomplete_pagination_never_claims_zero(self):
        s = ok(t.begin_cycle(gen(), 5000))
        s = ok(t.apply_page(s, 0, [msg(i) for i in range(100)]))
        _, disp = t.complete_pagination(s, has_more=True)
        self.assertEqual(disp["failed_predicate"], "PAGINATION_INCOMPLETE_NO_ZERO_REMAINING_CLAIM")
        self.assertFalse(t.summary(s)["operational_inbox_zero"])
        self.assertFalse(t.summary(gen())["operational_inbox_zero"])

    def test_unresolved_failures_are_never_proposed_for_archive(self):
        chain = run_cycle(gen(), 5000, [msg(i) for i in range(5)])
        s = chain[-1]
        self.assertEqual(s["archive_proposed"], [])
        _, disp = t.record_archive_receipt(s, ["m00000"])
        self.assertEqual(disp["failed_predicate"], "ARCHIVE_OF_UNPROPOSED_MESSAGE")
        summary = t.summary(s)
        self.assertEqual(len(summary["retained_in_inbox_incident_ids"]), 1)
        self.assertFalse(summary["operational_inbox_zero"])

    def test_classification_or_closed_pr_is_not_resolution(self):
        s = run_cycle(gen(), 5000, [msg(1)])[-1]
        inc = next(iter(s["incidents"]))
        for evidence in ({"kind": "CLASSIFIED", "evidence_url": "https://x"},
                         {"kind": "PR_CLOSED_UNMERGED", "evidence_url": "https://x"}):
            _, disp = t.record_resolution(s, inc, evidence)
            self.assertEqual(disp["failed_predicate"], "RESOLUTION_KIND_NOT_ADMISSIBLE")

    def test_resolution_requires_green_ci_at_exact_new_head(self):
        s = run_cycle(gen(), 5000, [msg(1), msg(2)])[-1]
        inc = next(iter(s["incidents"]))
        base = {"kind": "REPAIRED_AT_EXACT_HEAD", "repository": "StegVerse-Labs/StegDB",
                "evidence_url": "https://github.com/StegVerse-Labs/StegDB/actions/runs/1",
                "repaired_head_sha": SHA_FIX, "observed_head_sha": SHA_FIX, "ci_conclusion": "success"}
        _, disp = t.record_resolution(s, inc, {**base, "observed_head_sha": SHA_B})
        self.assertEqual(disp["failed_predicate"], "EXACT_HEAD_MISMATCH")
        _, disp = t.record_resolution(s, inc, {**base, "ci_conclusion": "failure"})
        self.assertEqual(disp["failed_predicate"], "CI_NOT_GREEN_AT_EXACT_HEAD")
        s = ok(t.record_resolution(s, inc, base))
        self.assertEqual(s["archive_proposed"], ["m00001", "m00002"])
        s = ok(t.record_archive_receipt(s, ["m00001", "m00002"]))
        self.assertEqual(s["counters"]["archived_confirmed"], 2)
        s = ok(t.close_cycle(s))
        self.assertTrue(t.summary(s)["operational_inbox_zero"])

    def test_archive_and_resolution_wait_for_complete_pagination(self):
        s = ok(t.begin_cycle(gen(), 5000))
        s = ok(t.apply_page(s, 0, [msg(1)]))
        _, disp = t.record_archive_receipt(s, [])
        self.assertEqual(disp["failed_predicate"], "ARCHIVE_ONLY_AFTER_PAGINATION")
        _, disp = t.record_resolution(s, next(iter(s["incidents"])), {})
        self.assertEqual(disp["failed_predicate"], "RESOLUTION_BEFORE_PAGINATION_COMPLETE")

    def test_gap_of_hours_loses_and_duplicates_nothing(self):
        """AC1: no invocation for k hours; next invocation is state N+1."""
        mailbox = [msg(i, epoch=1000 + i) for i in range(120)]
        s = ok(t.close_cycle(run_cycle(gen(), 1060, mailbox)[-1]))
        # Messages >= window end were deferred, not lost.
        self.assertEqual(s["counters"]["messages_seen"], 60)
        hours = 7
        later = mailbox + [msg(1000 + i, epoch=1060 + 3600 * hours + i) for i in range(30)]
        nxt = run_cycle(s, 1060 + 3600 * (hours + 1), later)
        end = ok(t.close_cycle(nxt[-1]))
        self.assertEqual(end["cycle_seq"], 2)
        self.assertEqual(end["counters"]["messages_seen"], 150)
        self.assertEqual(len(end["processed_message_ids"]), 150)
        self.assertEqual(len(set(end["processed_message_ids"])), 150)

    def test_two_consecutive_cycles_chain(self):
        """AC2: two committed transitions chained by prior_state_sha256."""
        chain = [gen()]
        chain += run_cycle(chain[-1], 5000, [msg(i) for i in range(3)])
        chain.append(ok(t.close_cycle(chain[-1])))
        chain += run_cycle(chain[-1], 9000, [msg(i) for i in range(6)])
        chain.append(ok(t.close_cycle(chain[-1])))
        self.assertEqual(chain[-1]["cycle_seq"], 2)
        self.assertEqual(t.verify_chain(chain), (True, None))
        tampered = [dict(c) for c in chain]
        tampered[3]["counters"] = {**tampered[3]["counters"], "messages_seen": 999}
        self.assertFalse(t.verify_chain(tampered)[0])

    def test_tampered_ledger_fails_closed(self):
        s = run_cycle(gen(), 5000, [msg(1)])[-1]
        s["processed_message_ids"] = []
        _, disp = t.close_cycle(s)
        self.assertEqual(disp["disposition"], t.FAIL_CLOSED)
        self.assertEqual(disp["failed_predicate"], "PROCESSED_ID_LEDGER_DIGEST_MISMATCH")

    def test_list_id_header_correlation(self):
        row = {"message_id": "x", "subject": "Run failed",
               "headers": {"List-ID": "StegDB <StegDB.StegVerse-Labs.github.com>", "X-GitHub-Sha": SHA_A},
               "workflow": "workflow-lint"}
        corr = t.correlate(row)
        self.assertEqual(corr["repository"], "StegVerse-Labs/StegDB")
        self.assertEqual(corr["head_sha"], SHA_A)
        self.assertTrue(corr["correlation_complete"])

    def test_security_and_quota_notices_are_retained(self):
        rows = [msg(1, subject="Security alert: vulnerable dependency"),
                msg(2, subject="Actions quota: spending limit reached")]
        s = run_cycle(gen(), 5000, rows)[-1]
        classes = sorted(i["notification_class"] for i in s["incidents"].values())
        self.assertEqual(classes, ["QUOTA", "SECURITY"])
        self.assertEqual(len(t.summary(s)["retained_in_inbox_incident_ids"]), 2)

    def test_non_public_repository_is_redacted_but_still_correlates(self):
        s = ok(t.begin_cycle(t.genesis(), 5000))
        s = ok(t.apply_page(s, 0, [msg(1, repo="Owner/private-repo"), msg(2, repo="Owner/private-repo")]))
        (inc,) = s["incidents"].values()
        self.assertIsNone(inc["repository"])
        self.assertIsNone(inc["workflow"])
        self.assertTrue(inc["redacted"])
        self.assertNotIn("private-repo", json.dumps(s))
        s = ok(t.complete_pagination(s, has_more=False))
        evidence = {"kind": "REPAIRED_AT_EXACT_HEAD", "evidence_url": "https://example.invalid/run",
                    "repaired_head_sha": SHA_FIX, "observed_head_sha": SHA_FIX, "ci_conclusion": "success"}
        _, disp = t.record_resolution(s, inc["incident_id"], {**evidence, "repository": "Owner/other"})
        self.assertEqual(disp["failed_predicate"], "REPOSITORY_MISMATCH")
        ok(t.record_resolution(s, inc["incident_id"], {**evidence, "repository": "Owner/private-repo"}))

    def test_subject_parsing_and_gmail_adapter(self):
        subject = ("[StegVerse-Labs/Site] PR run failed: Site Bootstrap Validate - No Non-TV/TVC Credential "
                   "Authority - Validate terminal claims (2ed35d1)")
        self.assertEqual(t.parse_subject(subject), {
            "repository": "StegVerse-Labs/Site",
            "workflow": "Site Bootstrap Validate - No Non-TV/TVC Credential Authority",
            "head_sha": "2ed35d1"})
        self.assertEqual(t.parse_subject("Re: [StegVerse-Labs/Site] Fix thing (PR #1484)"), {})
        payload = {"threads": [{"messages": [
            {"id": "a", "internalDate": "1790000000000", "labelIds": ["UNREAD", "INBOX"], "subject": subject},
            {"id": "b", "internalDate": "1790000001000", "labelIds": ["UNREAD"], "subject": subject}]}]}
        rows = t.rows_from_gmail_search(payload)
        self.assertEqual([r["message_id"] for r in rows], ["a"])
        self.assertEqual(rows[0]["internal_epoch"], 1790000000)
        corr = t.correlate(rows[0])
        self.assertEqual(corr["head_sha"], "2ed35d1")
        self.assertTrue(corr["correlation_complete"])
        self.assertEqual(t.notification_class({"subject": "[GitHub] Claude is requesting updated permissions"}),
                         "POLICY")

    def test_superseding_head_must_be_a_different_commit(self):
        s = run_cycle(gen(), 5000, [msg(1, sha="abc1234")])[-1]
        inc = next(iter(s["incidents"]))
        same = "abc1234" + "0" * 33
        _, disp = t.record_resolution(s, inc, {"kind": "SUPERSEDED_BY_CURRENT_EVIDENCE",
                                                "evidence_url": "https://x", "current_head_sha": same,
                                                "ci_conclusion": "success"})
        self.assertEqual(disp["failed_predicate"], "SUPERSEDING_HEAD_NOT_INDEPENDENT")

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "continuation.json"
            obs = Path(td) / "obs.json"
            script = str(ROOT / "scripts/native_email_continuation_transition.py")

            def run(*args):
                return subprocess.run([sys.executable, "-I", script, "--state", str(state), *args],
                                      capture_output=True, text=True, check=False)

            self.assertEqual(run("--op", "genesis").returncode, 0)
            self.assertEqual(run("--op", "genesis").returncode, 1)
            obs.write_text(json.dumps({"now_epoch": 5000}))
            self.assertEqual(run("--op", "begin", "--input", str(obs)).returncode, 0)
            obs.write_text(json.dumps({"page_index": 0, "messages": [msg(1)]}))
            self.assertEqual(run("--op", "page", "--input", str(obs)).returncode, 0)
            obs.write_text(json.dumps({"has_more": True}))
            self.assertEqual(run("--op", "complete", "--input", str(obs)).returncode, 1)
            loaded = json.loads(state.read_text())
            self.assertEqual(loaded["phase"], t.PHASE_PAGINATING)
            self.assertEqual(loaded["transition_seq"], 2)


if __name__ == "__main__":
    unittest.main()
