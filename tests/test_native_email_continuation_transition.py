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

    def _mixed_state(self) -> dict:
        """RECONCILING state: open public FAILURE, open redacted FAILURE, open
        POLICY, open INFORMATIONAL, SUCCESS and one SUPERSEDED FAILURE."""
        rows = [msg(1), msg(2),
                msg(3, repo="Owner/private-repo", sha=SHA_B),
                msg(4, subject="[GitHub] Claude is requesting updated permissions", sha="d" * 40),
                msg(5, subject="Weekly digest", sha="e" * 40),
                msg(6, subject="Run succeeded: workflow-lint", sha="f" * 40),
                msg(7, workflow="other", sha="abc1234")]
        s = run_cycle(gen(), 5000, rows)[-1]
        inc7 = next(i for i in s["incidents"].values() if i["workflow"] == "other")
        s = ok(t.record_resolution(s, inc7["incident_id"], {
            "kind": "SUPERSEDED_BY_CURRENT_EVIDENCE", "evidence_url": "https://x",
            "current_head_sha": "9" * 40, "ci_conclusion": "success"}))
        return s

    def test_failure_map_projection_counts_shapes_and_redaction(self):
        s = self._mixed_state()
        before = t.state_sha256(s)
        receipt = t.project_failure_map_receipt(s)
        self.assertEqual(t.state_sha256(s), before)  # pure: input untouched
        self.assertEqual(receipt["schema"], "stegverse.native-email-action-monitor-receipt/v1")
        self.assertEqual(receipt["authority_effect"], "NONE_PROJECTION_ONLY")
        self.assertEqual(receipt["archived_replay"], {"state": "NOT_REQUESTED", "complete": True})
        self.assertEqual(receipt["projection_source"]["schema"], t.SCHEMA)
        self.assertEqual(receipt["projection_source"]["state_sha256"], before)
        # Open FAILURE (public), open FAILURE (redacted), open POLICY. Not the
        # INFORMATIONAL, SUCCESS or SUPERSEDED incidents.
        self.assertEqual(receipt["incident_count"], 3)
        self.assertEqual(len(receipt["incidents"]), 3)
        by_class = {i["notification_class"]: i for i in receipt["incidents"]}
        self.assertEqual(sorted(by_class), ["FAILURE", "POLICY"])
        for inc in receipt["incidents"]:
            self.assertTrue(inc["incident_id"].startswith("INC-EMAIL-"))
            self.assertEqual(inc["kind"], "GITHUB_FAILURE_EMAIL_CLUSTER")
            self.assertEqual(inc["state"], "INCIDENT_PROPOSED_NOT_ADMITTED")
            self.assertTrue(inc["task_ingress_required"])
            self.assertFalse(inc["email_observation_is_execution_evidence"])
            self.assertFalse(inc["incident_proposal_mints_execution_authority"])
            self.assertEqual(inc["observation_count"], len(inc["observation_refs"]))
            self.assertEqual(inc["source_continuation"],
                             {"cycle_seq": s["cycle_seq"], "transition_seq": s["transition_seq"],
                              "state_sha256": before})
        public = next(i for i in receipt["incidents"] if i["normalized_repository"] == "StegVerse-Labs/StegDB")
        self.assertFalse(public["redacted"])
        self.assertEqual(public["normalized_workflow"], "workflow-lint")
        self.assertEqual(public["normalized_error_signature"], f"failure:workflow-lint@{SHA_A}")
        self.assertEqual(public["observation_refs"], ["m00001", "m00002"])
        redacted = next(i for i in receipt["incidents"] if i["redacted"])
        self.assertEqual(redacted["normalized_repository"], t.repository_sha256("Owner/private-repo"))
        self.assertEqual(redacted["repository_sha256"], redacted["normalized_repository"])
        self.assertEqual(redacted["normalized_workflow"], "unknown-workflow")
        self.assertEqual(redacted["normalized_error_signature"], f"failure:unknown-workflow@{SHA_B}")
        self.assertNotIn("private-repo", json.dumps(receipt))
        # Run id, when present, is part of the signature.
        s2 = ok(t.apply_page(ok(t.begin_cycle(gen(), 5000)), 0, [{**msg(9), "run_id": "123"}]))
        (inc,) = t.project_failure_map_receipt(s2)["incidents"]
        self.assertEqual(inc["normalized_error_signature"], f"failure:workflow-lint@{SHA_A}#run:123")
        self.assertEqual(inc["run_id"], "123")

    def test_failure_map_projection_fails_closed_on_invalid_state(self):
        s = self._mixed_state()
        s["processed_message_ids"] = []
        with self.assertRaises(ValueError):
            t.project_failure_map_receipt(s)

    def test_cli_failure_map_is_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "continuation.json"
            out = Path(td) / "projected" / "receipt.json"
            state.write_text(json.dumps(self._mixed_state(), indent=2, sort_keys=True) + "\n")
            before = state.read_bytes()
            script = str(ROOT / "scripts/native_email_continuation_transition.py")
            result = subprocess.run([sys.executable, "-I", script, "--state", str(state),
                                     "--op", "failure-map", "--output", str(out)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            disp = json.loads(result.stdout)
            self.assertEqual(disp["disposition"], t.ALLOW)
            self.assertEqual(disp["incident_count"], 3)
            self.assertEqual(state.read_bytes(), before)
            self.assertFalse(state.with_name(".continuation.json.tmp").exists())
            written = json.loads(out.read_text())
            self.assertEqual(written["incident_count"], 3)
            # Without --output the projection goes to stdout.
            result = subprocess.run([sys.executable, "-I", script, "--state", str(state),
                                     "--op", "failure-map"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["incident_count"], 3)
            self.assertEqual(state.read_bytes(), before)

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


DIGEST = "ab" * 32
COUNTS = {k: 0 for k in t.CORRELATION_CLASSIFICATIONS}


def correlation_doc(state: dict, *, lineages: dict | None = None, generated_at: str = "2026-10-11T03:00:00Z") -> dict:
    """A minimal artifact in the correlator's shape, observing ``state``."""
    lineage_counts = {**COUNTS, **(lineages or {"STILL_FAILING": 1})}
    return {
        "schema": t.CORRELATION_SCHEMA, "generated_at": generated_at, "fetcher": "stub", "api_calls": 3,
        "source_continuation": {"schema": t.SCHEMA, "cycle_seq": state["cycle_seq"], "transition_seq": state["transition_seq"],
                                "phase": state["phase"], "state_sha256": t.state_sha256(state)},
        "counts": {"lineages_by_classification": lineage_counts,
                   "incidents_by_lineage_classification": {k: v * 2 for k, v in lineage_counts.items()}},
        "lineages": [], "incidents": {},
        "evidence_class": "GITHUB_API_READ_OBSERVED", "authority_effect": "NONE_OBSERVATION_ONLY",
    }


class RecordCorrelationTests(unittest.TestCase):
    """The ``correlate`` transition: binds the artifact, chains, replays, fails closed, touches no incident."""

    def _state(self) -> dict:
        return run_cycle(gen(), 5000, [msg(1), msg(2, sha=SHA_B)])[-1]

    def test_correlate_binds_digest_and_summary_into_the_chain(self):
        s = self._state()
        self.assertEqual(s["correlations"], [])
        doc = correlation_doc(s)
        digest = t.correlation_sha256(doc)
        nxt, disp = t.record_correlation(s, digest, t.correlation_summary(doc))
        self.assertEqual(disp["disposition"], t.ALLOW, disp)
        self.assertEqual(disp["correlation_sha256"], digest)
        self.assertEqual(disp["correlation_seq"], 1)
        self.assertEqual(nxt["transition"], "RECORD_CORRELATION")
        self.assertEqual(nxt["transition_seq"], s["transition_seq"] + 1)
        self.assertEqual(nxt["prior_state_sha256"], t.state_sha256(s))
        self.assertEqual(t.verify_chain([s, nxt]), (True, None))
        (bound,) = nxt["correlations"]
        self.assertEqual(bound["correlation_sha256"], digest)
        self.assertEqual(bound["produced_at"], "2026-10-11T03:00:00Z")
        self.assertEqual(bound["fetcher"], "stub")
        self.assertEqual(bound["evidence_class"], "GITHUB_API_READ_OBSERVED")
        self.assertEqual(bound["authority_effect"], "NONE_OBSERVATION_ONLY")
        self.assertFalse(bound["incidents_mutated"])
        self.assertEqual(bound["api_calls"], 3)
        self.assertEqual(bound["recorded_at_transition_seq"], nxt["transition_seq"])
        self.assertEqual(bound["source_continuation"], {"cycle_seq": s["cycle_seq"], "transition_seq": s["transition_seq"],
                                                        "state_sha256": t.state_sha256(s)})
        self.assertEqual(set(bound["lineage_counts"]), set(t.CORRELATION_CLASSIFICATIONS))
        self.assertEqual(bound["lineage_counts"]["STILL_FAILING"], 1)
        self.assertEqual(bound["incident_counts"]["STILL_FAILING"], 2)
        self.assertIn("WORKFLOW_REMOVED_ON_DEFAULT_BRANCH", bound["lineage_counts"])
        # Observation only: incidents, counters, ledger and proposals are untouched.
        for key in ("incidents", "counters", "archive_proposed", "archived_message_ids", "processed_message_ids", "phase"):
            self.assertEqual(nxt[key], s[key], key)
        self.assertEqual(nxt["authority_effect"], "NONE")
        # A second, different artifact chains after the first.
        doc2 = correlation_doc(nxt, generated_at="2026-10-11T04:00:00Z")
        third, disp2 = t.record_correlation(nxt, t.correlation_sha256(doc2), t.correlation_summary(doc2))
        self.assertEqual(disp2["correlation_seq"], 2)
        self.assertEqual([b["correlation_seq"] for b in third["correlations"]], [1, 2])
        self.assertEqual(t.verify_chain([s, nxt, third]), (True, None))
        # An artifact that observed an EARLIER state of the same cycle is still bindable.
        late = correlation_doc(s, generated_at="2026-10-11T05:00:00Z")
        fourth, disp3 = t.record_correlation(third, t.correlation_sha256(late), t.correlation_summary(late))
        self.assertEqual(disp3["disposition"], t.ALLOW)
        self.assertEqual(fourth["correlations"][-1]["source_continuation"]["transition_seq"], s["transition_seq"])

    def test_summary_lifts_a_pre_existing_artifact_without_relaxing_the_transition(self):
        s = self._state()
        # An artifact produced before WORKFLOW_REMOVED_ON_DEFAULT_BRANCH existed (the committed #3093 one).
        doc = correlation_doc(s)
        for key in ("lineages_by_classification", "incidents_by_lineage_classification"):
            del doc["counts"][key]["WORKFLOW_REMOVED_ON_DEFAULT_BRANCH"]
        summary = t.correlation_summary(doc)
        self.assertEqual(summary["lineage_counts"]["WORKFLOW_REMOVED_ON_DEFAULT_BRANCH"], 0)
        self.assertEqual(summary["lineage_counts"]["STILL_FAILING"], 1)
        self.assertEqual(t.record_correlation(s, t.correlation_sha256(doc), summary)[1]["disposition"], t.ALLOW)
        # No counts at all, or an unknown class, still fails closed.
        empty = correlation_doc(s)
        empty["counts"] = {}
        self.assertEqual(t.record_correlation(s, DIGEST, t.correlation_summary(empty))[1]["failed_predicate"], "CORRELATION_COUNTS_INVALID")
        odd = correlation_doc(s)
        odd["counts"]["lineages_by_classification"]["NEW_CLASS"] = 1
        self.assertEqual(t.record_correlation(s, DIGEST, t.correlation_summary(odd))[1]["failed_predicate"], "CORRELATION_COUNTS_INVALID")

    def test_replay_of_the_same_digest_is_idempotent(self):
        s = self._state()
        doc = correlation_doc(s)
        digest = t.correlation_sha256(doc)
        nxt = ok(t.record_correlation(s, digest, t.correlation_summary(doc)))
        again, disp = t.record_correlation(nxt, digest, t.correlation_summary(doc))
        self.assertEqual(disp["disposition"], t.ALLOW)
        self.assertTrue(disp["idempotent_replay"])
        self.assertEqual(t.state_sha256(again), t.state_sha256(nxt))
        # Replay with a garbage summary still returns the stored state: the digest is the identity.
        again2, disp2 = t.record_correlation(nxt, digest, {"nonsense": True})
        self.assertTrue(disp2["idempotent_replay"])
        self.assertEqual(t.state_sha256(again2), t.state_sha256(nxt))

    def test_malformed_summary_or_digest_fails_closed(self):
        s = self._state()
        good = t.correlation_summary(correlation_doc(s))
        cases = [
            ("CORRELATION_SHA256_INVALID", "not-a-sha", good),
            ("CORRELATION_SHA256_INVALID", DIGEST.upper(), good),
            ("CORRELATION_SUMMARY_REQUIRED", DIGEST, None),
            ("CORRELATION_SUMMARY_REQUIRED", DIGEST, "summary"),
            ("CORRELATION_EVIDENCE_CLASS_INVALID", DIGEST, {**good, "evidence_class": "ASSERTED"}),
            ("CORRELATION_CLAIMS_AUTHORITY", DIGEST, {**good, "authority_effect": "ALLOW"}),
            ("CORRELATION_PRODUCER_REQUIRED", DIGEST, {**good, "produced_at": None}),
            ("CORRELATION_PRODUCER_REQUIRED", DIGEST, {**good, "fetcher": ""}),
            ("CORRELATION_COUNTS_INVALID", DIGEST, {**good, "lineage_counts": {k: v for k, v in good["lineage_counts"].items() if k != "WORKFLOW_REMOVED_ON_DEFAULT_BRANCH"}}),
            ("CORRELATION_COUNTS_INVALID", DIGEST, {**good, "lineage_counts": {**good["lineage_counts"], "EXTRA": 0}}),
            ("CORRELATION_COUNTS_INVALID", DIGEST, {**good, "incident_counts": {**good["incident_counts"], "STILL_FAILING": -1}}),
            ("CORRELATION_COUNTS_INVALID", DIGEST, {**good, "incident_counts": {**good["incident_counts"], "STILL_FAILING": "2"}}),
            ("CORRELATION_COUNTS_INVALID", DIGEST, {**good, "incident_counts": {**good["incident_counts"], "STILL_FAILING": True}}),
            ("CORRELATION_SOURCE_LINEAGE_REQUIRED", DIGEST, {**good, "source_continuation": None}),
            ("CORRELATION_LINEAGE_MISMATCH", DIGEST, {**good, "source_continuation": {**good["source_continuation"], "cycle_seq": 2}}),
            ("CORRELATION_LINEAGE_MISMATCH", DIGEST, {**good, "source_continuation": {**good["source_continuation"], "transition_seq": s["transition_seq"] + 1}}),
            ("CORRELATION_LINEAGE_MISMATCH", DIGEST, {**good, "source_continuation": {**good["source_continuation"], "state_sha256": "xyz"}}),
            ("CORRELATION_API_CALLS_INVALID", DIGEST, {**good, "api_calls": -1}),
        ]
        for predicate, digest, summary in cases:
            same, disp = t.record_correlation(s, digest, summary)
            self.assertEqual(disp["disposition"], t.FAIL_CLOSED, (predicate, disp))
            self.assertEqual(disp["failed_predicate"], predicate, disp)
            self.assertEqual(t.state_sha256(same), t.state_sha256(s))
        # Before pagination completes the op is denied, never recorded.
        paginating = ok(t.apply_page(ok(t.begin_cycle(gen(), 5000)), 0, [msg(1)]))
        same, disp = t.record_correlation(paginating, DIGEST, good)
        self.assertEqual(disp["disposition"], t.DENY)
        self.assertEqual(disp["failed_predicate"], "CORRELATION_BEFORE_PAGINATION_COMPLETE")
        # A tampered ledger fails closed before anything else.
        tampered = dict(s, processed_message_ids=[])
        _, disp = t.record_correlation(tampered, DIGEST, good)
        self.assertEqual(disp["failed_predicate"], "PROCESSED_ID_LEDGER_DIGEST_MISMATCH")

    def test_resolve_evidence_may_name_only_a_bound_correlation(self):
        s = self._state()
        inc = next(iter(s["incidents"]))
        evidence = {"kind": "SUPERSEDED_BY_CURRENT_EVIDENCE", "evidence_url": "https://github.com/x/actions/runs/1",
                    "current_head_sha": SHA_FIX, "ci_conclusion": "success"}
        doc = correlation_doc(s)
        digest = t.correlation_sha256(doc)
        # Not yet bound: refused. Malformed: refused. Nothing relaxed.
        _, disp = t.record_resolution(s, inc, {**evidence, "correlation_sha256": digest})
        self.assertEqual(disp["failed_predicate"], "CORRELATION_SHA256_NOT_RECORDED")
        _, disp = t.record_resolution(s, inc, {**evidence, "correlation_sha256": "nope"})
        self.assertEqual(disp["failed_predicate"], "CORRELATION_SHA256_INVALID")
        _, disp = t.record_resolution(s, inc, {**evidence, "correlation_sha256": None})
        self.assertEqual(disp["failed_predicate"], "CORRELATION_SHA256_INVALID")
        bound = ok(t.record_correlation(s, digest, t.correlation_summary(doc)))
        _, disp = t.record_resolution(bound, inc, {**evidence, "correlation_sha256": digest, "ci_conclusion": "failure"})
        self.assertEqual(disp["failed_predicate"], "SUPERSEDING_HEAD_NOT_GREEN")
        _, disp = t.record_resolution(bound, inc, {**evidence, "correlation_sha256": "0" * 64})
        self.assertEqual(disp["failed_predicate"], "CORRELATION_SHA256_NOT_RECORDED")
        resolved = ok(t.record_resolution(bound, inc, {**evidence, "correlation_sha256": digest}))
        self.assertEqual(resolved["incidents"][inc]["resolution_evidence"]["correlation_sha256"], digest)
        self.assertEqual(resolved["incidents"][inc]["state"], t.INCIDENT_SUPERSEDED)
        self.assertEqual(t.verify_chain([s, bound, resolved]), (True, None))
        # Evidence without the key is still admitted exactly as before.
        ok(t.record_resolution(bound, next(i for i in s["incidents"] if i != inc), evidence))
        # The healer projection reports whether its source artifact is bound.
        self.assertFalse(t.project_healer_observations(s, doc)["source_correlation"]["bound_in_continuation_chain"])
        self.assertTrue(t.project_healer_observations(bound, doc)["source_correlation"]["bound_in_continuation_chain"])

    def test_cli_correlate_op_takes_the_artifact_and_replays_idempotently(self):
        s = self._state()
        doc = correlation_doc(s)
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "continuation.json"
            inp = Path(td) / "corr.json"
            state.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
            inp.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
            script = str(ROOT / "scripts/native_email_continuation_transition.py")

            def run(path):
                return subprocess.run([sys.executable, "-I", script, "--state", str(state), "--op", "correlate",
                                       "--input", str(path)], capture_output=True, text=True, check=False)

            first = run(inp)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(json.loads(first.stdout)["correlation_sha256"], t.correlation_sha256(doc))
            written = json.loads(state.read_text())
            self.assertEqual(written["transition"], "RECORD_CORRELATION")
            self.assertEqual(written["correlations"][0]["correlation_sha256"], t.correlation_sha256(doc))
            self.assertTrue(t.verify_chain([s, written])[0])
            before = state.read_bytes()
            again = run(inp)
            self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
            self.assertTrue(json.loads(again.stdout)["idempotent_replay"])
            self.assertEqual(state.read_bytes(), before)
            # Explicit {correlation_sha256, summary} form and malformed input.
            explicit = Path(td) / "explicit.json"
            doc2 = correlation_doc(written, generated_at="2026-10-11T06:00:00Z")
            explicit.write_text(json.dumps({"correlation_sha256": t.correlation_sha256(doc2), "summary": t.correlation_summary(doc2)}))
            self.assertEqual(run(explicit).returncode, 0)
            self.assertEqual(len(json.loads(state.read_text())["correlations"]), 2)
            before = state.read_bytes()
            bad = Path(td) / "bad.json"
            bad.write_text(json.dumps({"correlation_sha256": "zzz", "summary": {}}))
            result = run(bad)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["failed_predicate"], "CORRELATION_SHA256_INVALID")
            self.assertEqual(state.read_bytes(), before)
            bad.write_text(json.dumps([]))
            result = run(bad)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["failed_predicate"], "CORRELATION_INPUT_REQUIRED")
            self.assertEqual(state.read_bytes(), before)

    def test_committed_correlations_bind_the_committed_artifacts(self):
        root = ROOT / "data/native-email-action-monitor"
        committed = json.loads((root / "continuation.json").read_text(encoding="utf-8"))
        artifact = json.loads((root / "github-correlation.latest.json").read_text(encoding="utf-8"))
        healer = json.loads((root / "healer-observations.latest.json").read_text(encoding="utf-8"))
        bound = committed.get("correlations") or []
        self.assertTrue(bound, "committed state binds no correlation")
        self.assertEqual([b["correlation_seq"] for b in bound], list(range(1, len(bound) + 1)))
        for b in bound:
            self.assertRegex(b["correlation_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(b["evidence_class"], "GITHUB_API_READ_OBSERVED")
            self.assertEqual(b["authority_effect"], "NONE_OBSERVATION_ONLY")
            self.assertEqual(set(b["lineage_counts"]), set(t.CORRELATION_CLASSIFICATIONS))
            self.assertLessEqual(b["recorded_at_transition_seq"], committed["transition_seq"])
        digest = t.correlation_sha256(artifact)
        self.assertEqual(bound[-1]["correlation_sha256"], digest)
        self.assertEqual(bound[-1]["lineage_counts"], artifact["counts"]["lineages_by_classification"])
        self.assertEqual(healer["source_correlation"]["correlation_sha256"], digest)
        self.assertTrue(healer["source_correlation"]["bound_in_continuation_chain"])
        # Every resolution recorded after the first binding names a bound digest.
        digests = {b["correlation_sha256"] for b in bound}
        named = [i for i in committed["incidents"].values()
                 if (i.get("resolution_evidence") or {}).get("correlation_sha256") is not None]
        self.assertTrue(named)
        for inc in named:
            self.assertIn(inc["resolution_evidence"]["correlation_sha256"], digests)


if __name__ == "__main__":
    unittest.main()
