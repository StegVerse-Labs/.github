"""Stub-fetcher tests for the email-incident <-> GitHub correlation (issue #3039, P2/P3).

Superseded, still failing, no run, workflow not found, redacted, API error,
repeat-notification suppression, already-fixed suppression, application through
the existing ``resolve`` transition, and the StegHealer observation projection.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import correlate_email_incidents_with_github as c  # noqa: E402
import native_email_continuation_transition as t  # noqa: E402

REPO = "StegVerse-Labs/StegDB"
PRIVATE = "StegVerse-Labs/SecretRepo"
WF = "workflow-lint"
WF_ID = 7
GREEN = "c" * 40
T_GREEN = "2026-10-01T00:00:00Z"
RED = "d" * 40
T_RED = "2026-10-06T00:00:00Z"
HEAD_A, T_A = "a" * 40, "2026-09-20T00:00:00Z"   # older than the green run
HEAD_B, T_B = "b" * 40, "2026-10-05T00:00:00Z"   # newer than the green run
HEAD_E, T_E = "e" * 40, "2026-09-21T00:00:00Z"   # older than the green run


def run(run_id: int, sha: str, ts: str, conclusion: str) -> dict:
    return {"id": run_id, "html_url": f"https://github.com/{REPO}/actions/runs/{run_id}", "conclusion": conclusion,
            "event": "push", "head_sha": sha, "head_branch": "main",
            "head_commit": {"id": sha, "timestamp": ts}, "run_started_at": ts, "updated_at": ts}


class StubFetcher:
    def __init__(self, world: dict):
        self.world = world
        self.log: list[tuple[str, dict]] = []

    def get(self, path, params=None):
        self.log.append((path, dict(params or {})))
        handler = self.world.get(path)
        if handler is None:
            return 404, None
        return handler(params or {}) if callable(handler) else handler


def world(*, completed: list, success: list | None = None, heads: dict | None = None,
          pulls: dict | None = None, workflows: list | None = None, workflows_status: int = 200) -> dict:
    """heads: short -> (full, committed_at, compare_status)."""
    rows = workflows if workflows is not None else [{"id": WF_ID, "name": WF, "path": ".github/workflows/lint.yml", "state": "active"}]
    w = {
        f"/repos/{REPO}": (200, {"default_branch": "main"}),
        f"/repos/{REPO}/actions/workflows": (workflows_status, {"total_count": len(rows), "workflows": rows} if workflows_status == 200 else None),
    }

    def runs(params):
        if params.get("status") == "completed":
            return 200, {"workflow_runs": completed}
        if params.get("status") == "success":
            return 200, {"workflow_runs": success or []}
        return 200, {"workflow_runs": []}
    w[f"/repos/{REPO}/actions/workflows/{WF_ID}/runs"] = runs
    for short, (full, ts, status) in (heads or {}).items():
        commit = {"sha": full, "commit": {"committer": {"date": ts}}}
        w[f"/repos/{REPO}/commits/{short}"] = (200, commit)
        for green in {GREEN}:
            w[f"/repos/{REPO}/compare/{short}...{green}"] = (200, {"status": status, "base_commit": commit})
        w[f"/repos/{REPO}/commits/{full}/pulls"] = (200, (pulls or {}).get(short, []))
    return w


def msg(i: int, *, repo: str = REPO, workflow: str = WF, sha: str = "aaaaaaa", epoch: int = 1000) -> dict:
    return {"message_id": f"1a0c{i:012x}", "repository": repo, "workflow": workflow, "head_sha": sha,
            "subject": f"Run failed: {workflow}", "internal_epoch": epoch}


def ok(result):
    state, disp = result
    assert disp["disposition"] == t.ALLOW, disp
    return state


def reconciling_state(mailbox: list[dict], public: list[str] | None = None) -> dict:
    s = ok(t.set_public_repositories(t.genesis(), public or [REPO]))
    s = ok(t.begin_cycle(s, 5000))
    s = ok(t.apply_page(s, 0, mailbox))
    return ok(t.complete_pagination(s, has_more=False))


def incident_for(state: dict, short: str, repo: str = REPO) -> dict:
    (inc,) = [i for i in state["incidents"].values() if i.get("head_sha") == short and (i.get("repository") == repo or repo is None)]
    return inc


def correlate(state: dict, w: dict, **kw) -> tuple[dict, StubFetcher]:
    fetcher = StubFetcher(w)
    return c.correlate_state(state, c.GitHubReader(fetcher), fetcher_name="stub", **kw), fetcher


class CorrelationTests(unittest.TestCase):
    def test_superseded_lineage_suppresses_repeats_and_emits_admissible_evidence(self):
        # Three notifications, two heads, both older than the green default-branch run.
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, sha="aaaaaaa"), msg(3, sha="eeeeeee")])
        corr, fetcher = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")],
                                           heads={"aaaaaaa": (HEAD_A, T_A, "ahead"), "eeeeeee": (HEAD_E, T_E, "diverged")}))
        (lin,) = corr["lineages"]
        self.assertEqual(lin["classification"], c.SUPERSEDED)
        self.assertEqual(lin["notification_count"], 3)
        self.assertEqual(lin["distinct_heads"], 2)
        self.assertEqual(lin["repeat_notification_count"], 1)
        self.assertEqual(len(lin["superseded_incident_ids"]), 2)
        self.assertEqual(lin["outstanding_incident_ids"], [])
        self.assertEqual(lin["newest_head"]["head_sha"], HEAD_E)
        self.assertEqual(corr["counts"]["lineages_by_classification"][c.SUPERSEDED], 1)
        self.assertEqual(corr["counts"]["incidents_by_disposition"][c.DISP_SUPERSEDED], 2)
        self.assertEqual(corr["authority_effect"], "NONE_OBSERVATION_ONLY")
        self.assertEqual(corr["evidence_class"], "GITHUB_API_READ_OBSERVED")
        self.assertEqual(corr["credential_authority"], "NONE_READ_ONLY_OBSERVATION")
        self.assertFalse(corr["continuation_state_mutated"])
        row = corr["incidents"][incident_for(s, "aaaaaaa")["incident_id"]]
        self.assertEqual(row["disposition"], c.DISP_SUPERSEDED)
        self.assertEqual(row["relation_to_current_head"], "ANCESTOR_OF_CURRENT_HEAD")
        evidence = row["resolution_evidence"]
        # Exactly the shape the committed state already carries for this kind.
        self.assertEqual(tuple(sorted(evidence)), tuple(sorted(c.EVIDENCE_KEYS)))
        self.assertEqual(evidence["kind"], "SUPERSEDED_BY_CURRENT_EVIDENCE")
        self.assertEqual(evidence["basis"], c.BASIS_RUN)
        self.assertEqual(evidence["current_head_sha"], GREEN)
        self.assertEqual(evidence["superseded_head_sha"], HEAD_A)
        self.assertEqual(evidence["branch"], "main")
        self.assertEqual(evidence["ci_conclusion"], "success")
        self.assertTrue(evidence["evidence_url"].startswith("https://"))
        # The existing validator admits it unchanged.
        self.assertEqual(t.record_resolution(s, row["incident_id"], evidence)[1]["disposition"], t.ALLOW)
        # Dedupe: the second head's compare was fetched once, the first head's once.
        compares = [p for p, _ in fetcher.log if "/compare/" in p]
        self.assertEqual(len(compares), 2)

    def test_merged_pr_derivation_uses_the_committed_pr_basis_shape(self):
        s = reconciling_state([msg(1, sha="aaaaaaa")])
        pr = {"number": 12, "merged_at": "2026-09-22T00:00:00Z", "merge_commit_sha": "f" * 40,
              "html_url": f"https://github.com/{REPO}/pull/12", "base": {"ref": "main"}, "head": {"ref": "fix/lint"}}
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")],
                                     heads={"aaaaaaa": (HEAD_A, T_A, "diverged")}, pulls={"aaaaaaa": [pr]}))
        (row,) = corr["incidents"].values()
        evidence = row["resolution_evidence"]
        self.assertEqual(evidence["basis"], c.BASIS_PR)
        self.assertEqual(tuple(sorted(evidence)), tuple(sorted(c.EVIDENCE_PR_KEYS)))
        self.assertEqual(evidence["merged_pr_url"], pr["html_url"])
        self.assertEqual(evidence["merged_pr_merge_commit_sha"], "f" * 40)
        self.assertEqual(evidence["source_branch"], "fix/lint")
        self.assertEqual(t.record_resolution(s, row["incident_id"], evidence)[1]["disposition"], t.ALLOW)

    def test_pr_merged_after_green_run_is_not_credited(self):
        s = reconciling_state([msg(1, sha="aaaaaaa")])
        pr = {"number": 12, "merged_at": "2026-10-02T00:00:00Z", "merge_commit_sha": "f" * 40,
              "html_url": f"https://github.com/{REPO}/pull/12", "base": {"ref": "main"}, "head": {"ref": "fix/lint"}}
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")],
                                     heads={"aaaaaaa": (HEAD_A, T_A, "diverged")}, pulls={"aaaaaaa": [pr]}))
        (row,) = corr["incidents"].values()
        self.assertEqual(row["resolution_evidence"]["basis"], c.BASIS_RUN)

    def test_still_failing_lineage_supersedes_only_heads_older_than_last_green(self):
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, sha="bbbbbbb")])
        corr, _ = correlate(s, world(completed=[run(2, RED, T_RED, "failure")], success=[run(1, GREEN, T_GREEN, "success")],
                                     heads={"aaaaaaa": (HEAD_A, T_A, "ahead"), "bbbbbbb": (HEAD_B, T_B, "diverged")}))
        (lin,) = corr["lineages"]
        self.assertEqual(lin["classification"], c.STILL_FAILING)
        self.assertEqual(lin["latest_completed_run"]["conclusion"], "failure")
        self.assertEqual(lin["latest_success_run"]["head_sha"], GREEN)
        self.assertEqual(lin["superseded_incident_ids"], [incident_for(s, "aaaaaaa")["incident_id"]])
        self.assertEqual(lin["outstanding_incident_ids"], [incident_for(s, "bbbbbbb")["incident_id"]])
        self.assertEqual(lin["newest_head"]["head_sha"], HEAD_B)
        self.assertEqual(corr["counts"]["outstanding_lineages"], 1)

    def test_no_run_since_failure_with_and_without_any_default_branch_run(self):
        s = reconciling_state([msg(1, sha="bbbbbbb")])
        corr, fetcher = correlate(s, world(completed=[], heads={"bbbbbbb": (HEAD_B, T_B, "diverged")}))
        (lin,) = corr["lineages"]
        self.assertEqual(lin["classification"], c.NO_RUN)
        self.assertIsNone(lin["latest_completed_run"])
        self.assertEqual(len(lin["outstanding_incident_ids"]), 1)
        self.assertTrue(any(p.endswith("/commits/bbbbbbb") for p, _ in fetcher.log))
        # A green run that predates the newest failing head is not supersession.
        corr2, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], heads={"bbbbbbb": (HEAD_B, T_B, "diverged")}))
        (lin2,) = corr2["lineages"]
        self.assertEqual(lin2["classification"], c.NO_RUN)
        self.assertEqual(lin2["superseded_incident_ids"], [])
        self.assertEqual(len(lin2["outstanding_incident_ids"]), 1)

    def test_green_run_at_the_failing_head_itself_is_not_supersession(self):
        s = reconciling_state([msg(1, sha="ccccccc")])
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], heads={"ccccccc": (GREEN, T_GREEN, "identical")}))
        (row,) = corr["incidents"].values()
        self.assertNotEqual(row["disposition"], c.DISP_SUPERSEDED)
        self.assertEqual(corr["lineages"][0]["classification"], c.NO_RUN)

    def test_workflow_not_found_fails_closed_without_fetching_runs(self):
        s = reconciling_state([msg(1, sha="aaaaaaa")])
        corr, fetcher = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], workflows=[]))
        (lin,) = corr["lineages"]
        self.assertEqual(lin["classification"], c.NOT_FOUND)
        self.assertEqual(lin["unverifiable_incident_ids"], lin["incident_ids"])
        (row,) = corr["incidents"].values()
        self.assertEqual(row["disposition"], c.DISP_UNVERIFIABLE)
        self.assertFalse(any("/runs" in p for p, _ in fetcher.log))

    def test_redacted_lineage_makes_no_api_call_and_leaks_no_name(self):
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, repo=PRIVATE, sha="1234567")])
        private = incident_for(s, "1234567", repo=None)
        self.assertTrue(private["redacted"])
        corr, fetcher = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], heads={"aaaaaaa": (HEAD_A, T_A, "ahead")}))
        redacted = [l for l in corr["lineages"] if l["classification"] == c.REDACTED]
        self.assertEqual(len(redacted), 1)
        self.assertIsNone(redacted[0]["repository"])
        self.assertEqual(redacted[0]["repository_sha256"], t.repository_sha256(PRIVATE))
        self.assertEqual(corr["incidents"][private["incident_id"]]["disposition"], c.DISP_UNVERIFIABLE)
        self.assertNotIn("SecretRepo", json.dumps(corr))
        self.assertFalse(any("1234567" in p or "SecretRepo" in p for p, _ in fetcher.log))
        self.assertEqual(corr["counts"]["redacted_open_incidents"], 1)

    def test_api_error_fails_closed_with_status(self):
        s = reconciling_state([msg(1, sha="aaaaaaa")])
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], workflows_status=403))
        (lin,) = corr["lineages"]
        self.assertEqual(lin["classification"], c.ERROR)
        self.assertEqual(lin["error"]["status"], 403)
        self.assertEqual(corr["counts"]["incidents_by_disposition"][c.DISP_SUPERSEDED], 0)
        # Transport failure (status 0) is an error too, never a classification.
        corr0, _ = correlate(s, {f"/repos/{REPO}": (0, None)})
        self.assertEqual(corr0["lineages"][0]["classification"], c.ERROR)
        self.assertEqual(corr0["lineages"][0]["error"]["status"], 0)

    def test_unresolvable_failure_head_is_listed_not_superseded(self):
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, sha="0000000")])
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], heads={"aaaaaaa": (HEAD_A, T_A, "ahead")}))
        (lin,) = corr["lineages"]
        self.assertEqual(lin["classification"], c.SUPERSEDED)
        gone = corr["incidents"][incident_for(s, "0000000")["incident_id"]]
        self.assertEqual(gone["disposition"], c.DISP_UNVERIFIABLE)
        self.assertEqual(gone["unverifiable_reason"], "FAILURE_HEAD_UNRESOLVABLE")
        self.assertEqual(lin["unverifiable_incident_ids"], [gone["incident_id"]])

    def test_already_superseded_incident_is_never_recorrelated_or_resignalled(self):
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, sha="bbbbbbb")])
        done = incident_for(s, "aaaaaaa")
        s2 = ok(t.record_resolution(s, done["incident_id"], {
            "kind": "SUPERSEDED_BY_CURRENT_EVIDENCE", "current_head_sha": GREEN, "ci_conclusion": "success",
            "evidence_url": "https://github.com/x/actions/runs/1", "repository": REPO}))
        corr, fetcher = correlate(s2, world(completed=[run(2, RED, T_RED, "failure")], success=[run(1, GREEN, T_GREEN, "success")],
                                            heads={"aaaaaaa": (HEAD_A, T_A, "ahead"), "bbbbbbb": (HEAD_B, T_B, "diverged")}))
        self.assertNotIn(done["incident_id"], corr["incidents"])
        self.assertFalse(any(p.endswith("...%s" % GREEN) and "/aaaaaaa" in p for p, _ in fetcher.log))
        projection = t.project_healer_observations(s2, corr)
        (obs,) = projection["observations"]
        self.assertEqual(obs["incident_ids"], [incident_for(s2, "bbbbbbb")["incident_id"]])
        self.assertNotIn(done["message_ids"][0], obs["related_message_ids"])
        # A stale SUPERSEDED row for it is skipped by the apply step, not re-applied.
        corr["incidents"][done["incident_id"]] = {"incident_id": done["incident_id"], "disposition": c.DISP_SUPERSEDED,
                                                  "resolution_evidence": s2["incidents"][done["incident_id"]]["resolution_evidence"]}
        final, disp = c.apply_resolutions(s2, corr)
        self.assertEqual(disp["disposition"], t.ALLOW)
        self.assertEqual(disp["skipped_not_open"], 1)
        self.assertEqual(disp["applied"], 0)
        self.assertEqual(t.state_sha256(final), t.state_sha256(s2))


class ApplyTests(unittest.TestCase):
    def test_apply_replays_resolve_transitions_and_changes_nothing_else(self):
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, sha="eeeeeee"), msg(3, sha="bbbbbbb")])
        corr, _ = correlate(s, world(completed=[run(2, RED, T_RED, "failure")], success=[run(1, GREEN, T_GREEN, "success")],
                                     heads={"aaaaaaa": (HEAD_A, T_A, "ahead"), "eeeeeee": (HEAD_E, T_E, "ahead"),
                                            "bbbbbbb": (HEAD_B, T_B, "diverged")}))
        final, disp = c.apply_resolutions(s, corr)
        self.assertEqual(disp["disposition"], t.ALLOW, disp)
        self.assertEqual(disp["applied"], 2)
        self.assertEqual(disp["transition_seq_to"], disp["transition_seq_from"] + 2)
        self.assertEqual(final["transition"], "RECORD_RESOLUTION")
        self.assertEqual(final["counters"]["resolved_verified"], 2)
        for short in ("aaaaaaa", "eeeeeee"):
            inc = incident_for(final, short)
            self.assertEqual(inc["state"], t.INCIDENT_SUPERSEDED)
            self.assertEqual(inc["resolution_evidence"]["superseded_head_sha"], {"aaaaaaa": HEAD_A, "eeeeeee": HEAD_E}[short])
        self.assertEqual(incident_for(final, "bbbbbbb")["state"], t.INCIDENT_OPEN)
        self.assertEqual(set(final["archive_proposed"]), set(incident_for(s, "aaaaaaa")["message_ids"]) | set(incident_for(s, "eeeeeee")["message_ids"]))
        # Nothing but the resolve-op fields moved.
        moved = {"incidents", "counters", "archive_proposed", "transition", "transition_seq", "prior_state_sha256"}
        for key in set(s) - moved:
            self.assertEqual(final[key], s[key], key)

    def test_apply_fails_closed_on_state_lineage_mismatch_and_bad_evidence(self):
        s = reconciling_state([msg(1, sha="aaaaaaa")])
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], heads={"aaaaaaa": (HEAD_A, T_A, "ahead")}))
        s_moved = ok(t.record_archive_receipt(s, []))  # no-op receipt still advances nothing; force sha mismatch below
        tampered = json.loads(json.dumps(corr))
        tampered["source_continuation"]["state_sha256"] = "0" * 64
        final, disp = c.apply_resolutions(s, tampered)
        self.assertEqual(disp["disposition"], t.FAIL_CLOSED)
        self.assertEqual(disp["failed_predicate"], "CORRELATION_STATE_LINEAGE_MISMATCH")
        self.assertEqual(t.state_sha256(final), t.state_sha256(s))
        bad = json.loads(json.dumps(corr))
        (row,) = bad["incidents"].values()
        row["resolution_evidence"]["current_head_sha"] = HEAD_A[:7] + "0" * 33  # not independent of the failing head
        final, disp = c.apply_resolutions(s, bad)
        self.assertEqual(disp["disposition"], t.FAIL_CLOSED)
        self.assertEqual(disp["failed_predicate"], "RESOLVE_TRANSITION_REFUSED")
        self.assertEqual(disp["refused"]["failed_predicate"], "SUPERSEDING_HEAD_NOT_INDEPENDENT")
        self.assertEqual(t.state_sha256(final), t.state_sha256(s))
        del s_moved

    def test_cli_round_trip_apply_and_dry_run(self):
        s = reconciling_state([msg(1, sha="aaaaaaa")])
        corr, _ = correlate(s, world(completed=[run(1, GREEN, T_GREEN, "success")], heads={"aaaaaaa": (HEAD_A, T_A, "ahead")}))
        with tempfile.TemporaryDirectory() as tmp:
            state_path, corr_path = Path(tmp) / "state.json", Path(tmp) / "corr.json"
            state_path.write_text(json.dumps(s, sort_keys=True), encoding="utf-8")
            corr_path.write_text(json.dumps(corr, sort_keys=True), encoding="utf-8")
            before = state_path.read_bytes()
            dry = subprocess.run([sys.executable, str(ROOT / "scripts/correlate_email_incidents_with_github.py"), "--state", str(state_path),
                                  "--apply-resolutions", str(corr_path), "--dry-run"], capture_output=True, text=True, check=False)
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertEqual(json.loads(dry.stdout)["applied"], 1)
            self.assertEqual(state_path.read_bytes(), before)
            real = subprocess.run([sys.executable, str(ROOT / "scripts/correlate_email_incidents_with_github.py"), "--state", str(state_path),
                                   "--apply-resolutions", str(corr_path)], capture_output=True, text=True, check=False)
            self.assertEqual(real.returncode, 0, real.stdout + real.stderr)
            written = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(written["prior_state_sha256"], t.state_sha256(s))
            self.assertTrue(t.verify_chain([s, written])[0])
            self.assertEqual(incident_for(written, "aaaaaaa")["state"], t.INCIDENT_SUPERSEDED)
            # Re-applying the same correlation now fails closed: the state moved on.
            again = subprocess.run([sys.executable, str(ROOT / "scripts/correlate_email_incidents_with_github.py"), "--state", str(state_path),
                                    "--apply-resolutions", str(corr_path)], capture_output=True, text=True, check=False)
            self.assertEqual(again.returncode, 1)
            self.assertEqual(json.loads(again.stdout)["failed_predicate"], "CORRELATION_STATE_LINEAGE_MISMATCH")


class HealerObservationProjectionTests(unittest.TestCase):
    def _fixture(self):
        other = "other-workflow"
        s = reconciling_state([msg(1, sha="aaaaaaa"), msg(2, sha="bbbbbbb"), msg(3, sha="bbbbbbb"),
                               msg(4, workflow=other, sha="aaaaaaa"), msg(5, repo=PRIVATE, sha="1234567"),
                               msg(6, workflow="gone", sha="aaaaaaa")])
        w = world(completed=[run(2, RED, T_RED, "failure")], success=[run(1, GREEN, T_GREEN, "success")],
                  heads={"aaaaaaa": (HEAD_A, T_A, "ahead"), "bbbbbbb": (HEAD_B, T_B, "diverged")},
                  workflows=[{"id": WF_ID, "name": WF, "path": ".github/workflows/lint.yml", "state": "active"},
                             {"id": 8, "name": other, "path": ".github/workflows/other.yml", "state": "active"}])
        w[f"/repos/{REPO}/actions/workflows/8/runs"] = lambda params: (200, {"workflow_runs": [run(9, GREEN, T_GREEN, "success")]})
        corr, _ = correlate(s, w)
        return s, corr

    def test_only_outstanding_public_lineages_are_signalled(self):
        s, corr = self._fixture()
        projection = t.project_healer_observations(s, corr)
        self.assertEqual(projection["schema"], t.HEALER_OBSERVATIONS_SCHEMA)
        self.assertEqual(projection["observation_schema"], "stegverse.healer.github-failure-observation/v0.2")
        self.assertEqual(projection["authority_effect"], "NONE_PROJECTION_ONLY")
        self.assertFalse(projection["resolved_transition_claimed"])
        self.assertFalse(projection["continuation_state_mutated"])
        (obs,) = projection["observations"]
        self.assertEqual(obs["repository"], REPO)
        self.assertEqual(obs["workflow"], WF)
        self.assertEqual(obs["classification"], c.STILL_FAILING)
        b = incident_for(s, "bbbbbbb")
        self.assertEqual(obs["incident_ids"], [b["incident_id"]])
        self.assertEqual(obs["related_message_ids"], sorted(b["message_ids"]))
        self.assertEqual(obs["message_id"], max(b["message_ids"]))
        self.assertEqual(obs["commit_sha"], HEAD_B)
        self.assertEqual(obs["received_at"], T_B)
        self.assertEqual(obs["run_id"], "2")
        self.assertEqual(obs["latest_run_url"], f"https://github.com/{REPO}/actions/runs/2")
        self.assertIs(obs["authority_effect"], False)
        for key in ("message_id", "repository", "workflow", "received_at"):
            self.assertTrue(obs[key])
        withheld = {w["classification"] for w in projection["withheld_lineages"]}
        self.assertEqual(withheld, {c.SUPERSEDED, c.NOT_FOUND, c.REDACTED})
        self.assertEqual(projection["withheld_lineage_count"], 3)
        self.assertNotIn("SecretRepo", json.dumps(projection))
        self.assertEqual(projection["source_correlation"]["state_sha256"], t.state_sha256(s))

    def test_projection_after_apply_drops_incidents_resolved_meanwhile_and_checks_lineage(self):
        s, corr = self._fixture()
        final, disp = c.apply_resolutions(s, corr)
        self.assertEqual(disp["applied"], 2)
        projection = t.project_healer_observations(final, corr)
        self.assertEqual(len(projection["observations"]), 1)
        self.assertEqual(projection["projection_source"]["transition_seq"], final["transition_seq"])
        wrong_cycle = json.loads(json.dumps(corr))
        wrong_cycle["source_continuation"]["cycle_seq"] = 99
        with self.assertRaises(ValueError):
            t.project_healer_observations(final, wrong_cycle)
        claims = json.loads(json.dumps(corr))
        claims["authority_effect"] = "ALLOW"
        with self.assertRaises(ValueError):
            t.project_healer_observations(final, claims)

    def test_cli_healer_observations_is_read_only(self):
        s, corr = self._fixture()
        with tempfile.TemporaryDirectory() as tmp:
            state_path, corr_path, out = Path(tmp) / "state.json", Path(tmp) / "corr.json", Path(tmp) / "obs.json"
            state_path.write_text(json.dumps(s, sort_keys=True), encoding="utf-8")
            corr_path.write_text(json.dumps(corr, sort_keys=True), encoding="utf-8")
            before = state_path.read_bytes()
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/native_email_continuation_transition.py"), "--state", str(state_path),
                                   "--op", "healer-observations", "--input", str(corr_path), "--output", str(out)],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            disp = json.loads(proc.stdout)
            self.assertEqual(disp["disposition"], t.ALLOW)
            self.assertFalse(disp["continuation_state_mutated"])
            self.assertEqual(disp["observation_count"], 1)
            self.assertEqual(state_path.read_bytes(), before)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["observation_count"], 1)
            missing = subprocess.run([sys.executable, str(ROOT / "scripts/native_email_continuation_transition.py"), "--state", str(state_path),
                                      "--op", "healer-observations"], capture_output=True, text=True, check=False)
            self.assertEqual(missing.returncode, 1)
            self.assertEqual(state_path.read_bytes(), before)


class FetcherTests(unittest.TestCase):
    def test_gh_fetcher_parses_http_status_from_stderr(self):
        with mock.patch.object(c.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "gh: Not Found (HTTP 404)")):
            self.assertEqual(c.GhFetcher().get("/repos/x/y"), (404, None))
        with mock.patch.object(c.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"a": 1}', "")):
            self.assertEqual(c.GhFetcher().get("/repos/x/y", {"per_page": 1}), (200, {"a": 1}))
        with mock.patch.object(c.subprocess, "run", side_effect=OSError("missing")):
            self.assertEqual(c.GhFetcher().get("/repos/x/y"), (0, None))

    def test_reader_caches_and_counts_calls(self):
        fetcher = StubFetcher({f"/repos/{REPO}": (200, {"default_branch": "main"})})
        reader = c.GitHubReader(fetcher)
        self.assertEqual(reader.default_branch(REPO), "main")
        self.assertEqual(reader.default_branch(REPO), "main")
        self.assertEqual(reader.calls, 1)
        with self.assertRaises(c.ApiError) as ctx:
            reader.get("/missing")
        self.assertEqual(ctx.exception.status, 404)

    def test_reader_retries_transport_failure_once_but_never_http_errors(self):
        answers = iter([(0, None), (200, {"default_branch": "main"})])
        flaky = StubFetcher({f"/repos/{REPO}": lambda params: next(answers)})
        reader = c.GitHubReader(flaky)
        self.assertEqual(reader.default_branch(REPO), "main")
        self.assertEqual(reader.calls, 2)
        dead = StubFetcher({f"/repos/{REPO}": (0, None)})
        with self.assertRaises(c.ApiError) as ctx:
            c.GitHubReader(dead).default_branch(REPO)
        self.assertEqual(ctx.exception.status, 0)
        self.assertEqual(len(dead.log), 2)
        forbidden = StubFetcher({f"/repos/{REPO}": (403, None)})
        with self.assertRaises(c.ApiError):
            c.GitHubReader(forbidden).default_branch(REPO)
        self.assertEqual(len(forbidden.log), 1)


if __name__ == "__main__":
    unittest.main()
