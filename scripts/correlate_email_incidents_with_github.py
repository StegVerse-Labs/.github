#!/usr/bin/env python3
"""Correlate open email-discovered incidents with current GitHub state (issue #3039, P2).

The continuation state (``native_email_continuation_transition.py``) holds one
``OPEN_UNRESOLVED`` incident per (repository, workflow, head, class) seen in
GitHub notification mail. Mail is an observation, not the truth about the
repository: the failing head may since have been merged and the workflow
observed green, or the workflow may still be failing on the default branch.
This module reads the ACTUAL current state through the GitHub REST API
(read-only), groups incidents into lineages (repository, workflow) and
classifies each lineage:

    SUPERSEDED_BY_CURRENT_EVIDENCE  latest completed default-branch run of the
                                    workflow concluded ``success`` on a head
                                    newer than the newest failing head
    STILL_FAILING                   latest completed default-branch run failed
                                    (failure / cancelled / timed_out / ...)
    NO_RUN_SINCE_FAILURE            no completed default-branch run newer than
                                    the newest failing head
    WORKFLOW_NOT_FOUND              the workflow name/path no longer resolves
    REDACTED_UNVERIFIABLE           repository hidden (``repository_sha256``
                                    only); no API call is made
    UNCORRELATED_UNVERIFIABLE       notification never bound to a repository
    CORRELATION_ERROR               any API error (status recorded); fail closed

Within a lineage every incident whose own head predates the latest successful
default-branch run is superseded together (repeat-notification suppression),
and its ``resolution_evidence`` is emitted in exactly the shape that
``record_resolution`` admits for ``SUPERSEDED_BY_CURRENT_EVIDENCE``.
``--apply-resolutions`` replays those through the EXISTING ``resolve``
transition, one chained state per incident, verifying ``prior_state_sha256``
at every step; nothing else in the state changes.

Non-authorizing: ``authority_effect: NONE_OBSERVATION_ONLY``. An optional
bearer token (``GITHUB_TOKEN``) is used only for the API rate limit and is
never required or recorded; ``--fetcher gh`` shells to a locally installed
``gh api`` for operator runs (a local tool, not a repository dependency).
Standard library only. Introduces no worker, adapter, process or framework.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import native_email_continuation_transition as t  # noqa: E402

SCHEMA = "stegverse.email-incident-github-correlation/v1"
API_BASE = "https://api.github.com"

SUPERSEDED = "SUPERSEDED_BY_CURRENT_EVIDENCE"
STILL_FAILING = "STILL_FAILING"
NO_RUN = "NO_RUN_SINCE_FAILURE"
NOT_FOUND = "WORKFLOW_NOT_FOUND"
REDACTED = "REDACTED_UNVERIFIABLE"
UNCORRELATED = "UNCORRELATED_UNVERIFIABLE"
ERROR = "CORRELATION_ERROR"
CLASSIFICATIONS = (SUPERSEDED, STILL_FAILING, NO_RUN, NOT_FOUND, REDACTED, UNCORRELATED, ERROR)
OUTSTANDING_CLASSIFICATIONS = (STILL_FAILING, NO_RUN)

DISP_SUPERSEDED = "SUPERSEDED"
DISP_OUTSTANDING = "OUTSTANDING"
DISP_UNVERIFIABLE = "UNVERIFIABLE"

# Evidence bases. BASIS_PR is the shape already present in the committed state
# (7 incidents); BASIS_RUN is used when no merged PR is derivable for the head.
BASIS_PR = "PR_MERGED_AND_LATEST_COMPLETED_MAIN_RUN_SAME_WORKFLOW_SUCCESS_AFTER_MERGE"
BASIS_RUN = "LATEST_SUCCESSFUL_DEFAULT_BRANCH_RUN_SAME_WORKFLOW_AFTER_FAILURE_HEAD"
EVIDENCE_KEYS = ("basis", "branch", "ci_conclusion", "current_head_sha", "evidence_url",
                 "kind", "repository", "superseded_head_sha", "workflow")
EVIDENCE_PR_KEYS = EVIDENCE_KEYS + ("merged_pr_merge_commit_sha", "merged_pr_url", "source_branch")

FAILED_CONCLUSIONS = ("failure", "cancelled", "timed_out", "startup_failure", "action_required", "stale")
DECISIVE_CONCLUSIONS = ("success",) + FAILED_CONCLUSIONS
RELATION = {"ahead": "ANCESTOR_OF_CURRENT_HEAD", "behind": "DESCENDANT_OF_CURRENT_HEAD",
            "identical": "IDENTICAL", "diverged": "DIVERGED"}
HEAD_UNRESOLVABLE_STATUSES = (404, 422)
MAX_WORKFLOW_PAGES = 10


class ApiError(Exception):
    def __init__(self, status: int, path: str):
        super().__init__(f"HTTP {status} {path}")
        self.status = status
        self.path = path


# --------------------------------------------------------------------------- fetchers

class UrllibFetcher:
    """GET api.github.com with the standard library. Token only for rate limit."""

    def __init__(self, token: str | None = None, timeout: int = 60):
        self.token = token or None
        self.timeout = timeout

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> tuple[int, Any]:
        url = API_BASE + path + ("?" + urllib.parse.urlencode(dict(params)) if params else "")
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "stegverse-email-incident-correlator",
        })
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return int(resp.status), json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return int(exc.code), None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return 0, None


class GhFetcher:
    """Shell to a locally installed ``gh api`` (operator convenience, not a dependency)."""

    STATUS = re.compile(r"\(HTTP (\d{3})\)")

    def __init__(self, executable: str = "gh"):
        self.executable = executable

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> tuple[int, Any]:
        target = path + ("?" + urllib.parse.urlencode(dict(params)) if params else "")
        try:
            proc = subprocess.run([self.executable, "api", target], capture_output=True, text=True, check=False)
        except OSError:
            return 0, None
        if proc.returncode == 0:
            try:
                return 200, json.loads(proc.stdout)
            except ValueError:
                return 0, None
        m = self.STATUS.search(proc.stderr or "")
        return (int(m.group(1)) if m else 0), None


class GitHubReader:
    """Cached, counted, read-only view over a fetcher."""

    def __init__(self, fetcher: Any):
        self.fetcher = fetcher
        self.calls = 0
        self._cache: dict[tuple[str, tuple[tuple[str, Any], ...]], Any] = {}

    def get(self, path: str, **params: Any) -> Any:
        key = (path, tuple(sorted(params.items())))
        if key in self._cache:
            return self._cache[key]
        self.calls += 1
        status, body = self.fetcher.get(path, params or None)
        if status == 0:
            # One immediate retry for a transport-level failure (no HTTP status);
            # an HTTP error is never retried and fails the lineage closed.
            self.calls += 1
            status, body = self.fetcher.get(path, params or None)
        if status != 200 or body is None:
            raise ApiError(status, path)
        self._cache[key] = body
        return body

    def default_branch(self, repo: str) -> str:
        branch = self.get(f"/repos/{repo}").get("default_branch")
        if not isinstance(branch, str) or not branch:
            raise ApiError(0, f"/repos/{repo}#default_branch")
        return branch

    def workflows(self, repo: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        page = 1
        while True:
            body = self.get(f"/repos/{repo}/actions/workflows", per_page=100, page=page)
            rows = [r for r in (body.get("workflows") or []) if isinstance(r, Mapping)]
            out.extend(rows)
            total = int(body.get("total_count") or 0)
            if len(rows) < 100 or len(out) >= total or page >= MAX_WORKFLOW_PAGES:
                return out
            page += 1

    def resolve_workflow(self, repo: str, name: str) -> list[dict[str, Any]]:
        rows = self.workflows(repo)
        exact = [w for w in rows if w.get("name") == name or w.get("path") == name]
        if exact:
            return exact
        low = name.lower()
        return [w for w in rows if str(w.get("name") or "").lower() == low or str(w.get("path") or "").lower() == low]

    def runs(self, repo: str, workflow_id: int, branch: str, status: str, per_page: int) -> list[dict[str, Any]]:
        body = self.get(f"/repos/{repo}/actions/workflows/{workflow_id}/runs",
                        branch=branch, status=status, per_page=per_page, exclude_pull_requests="true")
        return [r for r in (body.get("workflow_runs") or []) if isinstance(r, Mapping)]

    def compare(self, repo: str, base: str, head: str) -> dict[str, Any]:
        return self.get(f"/repos/{repo}/compare/{base}...{head}")

    def commit(self, repo: str, sha: str) -> dict[str, Any]:
        return self.get(f"/repos/{repo}/commits/{sha}")

    def commit_pulls(self, repo: str, sha: str) -> list[dict[str, Any]]:
        body = self.get(f"/repos/{repo}/commits/{sha}/pulls")
        return [p for p in body if isinstance(p, Mapping)] if isinstance(body, list) else []


# --------------------------------------------------------------------------- helpers

def _parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def lineage_id(repository: str, workflow: str) -> str:
    return "LIN-" + hashlib.sha256(f"{repository}\n{workflow}".encode("utf-8")).hexdigest()[:20]


def _run_view(run: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if run is None:
        return None
    head_commit = run.get("head_commit") if isinstance(run.get("head_commit"), Mapping) else {}
    return {
        "id": run.get("id"),
        "html_url": run.get("html_url"),
        "conclusion": run.get("conclusion"),
        "event": run.get("event"),
        "head_sha": run.get("head_sha"),
        "head_branch": run.get("head_branch"),
        "head_commit_timestamp": head_commit.get("timestamp"),
        "run_started_at": run.get("run_started_at"),
        "updated_at": run.get("updated_at"),
    }


def _run_head_time(run: Mapping[str, Any]) -> dt.datetime | None:
    head_commit = run.get("head_commit") if isinstance(run.get("head_commit"), Mapping) else {}
    return _parse_ts(head_commit.get("timestamp")) or _parse_ts(run.get("run_started_at"))


def _open_retained(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Only OPEN_UNRESOLVED retained-class incidents are candidates.

    Incidents already ``SUPERSEDED_VERIFIED`` / ``RESOLVED_VERIFIED`` are never
    re-correlated or re-signalled (already-fixed suppression).
    """
    return [dict(i) for i in state["incidents"].values()
            if i.get("state") == t.INCIDENT_OPEN and i.get("notification_class") in t.RETAINED_CLASSES]


# --------------------------------------------------------------------------- lineage correlation

def _resolve_head(gh: GitHubReader, repo: str, short: str, success_sha: str | None) -> tuple[str, str, str | None]:
    """Full sha, committer date and relation of a failing head to the green head."""
    if success_sha:
        cmp = gh.compare(repo, short, success_sha)
        base = cmp.get("base_commit") if isinstance(cmp.get("base_commit"), Mapping) else {}
        commit = base.get("commit") if isinstance(base.get("commit"), Mapping) else {}
        committer = commit.get("committer") if isinstance(commit.get("committer"), Mapping) else {}
        full, date = base.get("sha"), committer.get("date")
        relation = RELATION.get(str(cmp.get("status") or ""), "UNKNOWN")
    else:
        c = gh.commit(repo, short)
        commit = c.get("commit") if isinstance(c.get("commit"), Mapping) else {}
        committer = commit.get("committer") if isinstance(commit.get("committer"), Mapping) else {}
        full, date, relation = c.get("sha"), committer.get("date"), None
    if not (isinstance(full, str) and len(full) == 40 and _parse_ts(date)):
        raise ApiError(0, f"/repos/{repo}/commits/{short}#shape")
    return full.lower(), str(date), relation


def _merged_pr(gh: GitHubReader, repo: str, full_sha: str, branch: str, success_time: dt.datetime) -> dict[str, str] | None:
    try:
        pulls = gh.commit_pulls(repo, full_sha)
    except ApiError as exc:
        if exc.status in HEAD_UNRESOLVABLE_STATUSES:
            return None
        raise
    for pr in pulls:
        merged_at = _parse_ts(pr.get("merged_at"))
        base = pr.get("base") if isinstance(pr.get("base"), Mapping) else {}
        head = pr.get("head") if isinstance(pr.get("head"), Mapping) else {}
        merge_sha = pr.get("merge_commit_sha")
        if (merged_at and base.get("ref") == branch and isinstance(merge_sha, str) and merge_sha
                and isinstance(pr.get("html_url"), str) and merged_at < success_time):
            return {
                "merged_pr_merge_commit_sha": merge_sha.lower(),
                "merged_pr_url": pr["html_url"],
                "source_branch": str(head.get("ref") or ""),
            }
    return None


def _evidence(repo: str, workflow: str, branch: str, success: Mapping[str, Any], full_sha: str,
              pr: Mapping[str, str] | None) -> dict[str, Any]:
    evidence = {
        "basis": BASIS_PR if pr else BASIS_RUN,
        "branch": branch,
        "ci_conclusion": "success",
        "current_head_sha": str(success.get("head_sha") or "").lower(),
        "evidence_url": str(success.get("html_url") or ""),
        "kind": "SUPERSEDED_BY_CURRENT_EVIDENCE",
        "repository": repo,
        "superseded_head_sha": full_sha,
        "workflow": workflow,
    }
    if pr:
        evidence.update(pr)
    return evidence


def _lineage_base(repo: str | None, workflow: str | None, incidents: list[dict[str, Any]], lid: str) -> dict[str, Any]:
    ids = sorted(i["incident_id"] for i in incidents)
    messages = sorted({m for i in incidents for m in (i.get("message_ids") or [])})
    heads = sorted({str(i.get("head_sha") or "") for i in incidents if i.get("head_sha")})
    return {
        "lineage_id": lid,
        "repository": repo,
        "workflow": workflow,
        "classification": None,
        "incident_ids": ids,
        "incident_count": len(ids),
        "notification_classes": sorted({i["notification_class"] for i in incidents}),
        "notification_count": len(messages),
        "distinct_heads": len(heads),
        "repeat_notification_count": max(0, len(messages) - len(heads)),
        "newest_head": None,
        "default_branch": None,
        "workflow_id": None,
        "workflow_path": None,
        "latest_completed_run": None,
        "latest_success_run": None,
        "superseded_incident_ids": [],
        "outstanding_incident_ids": [],
        "unverifiable_incident_ids": [],
        "error": None,
    }


def _incident_row(inc: Mapping[str, Any], lid: str, disposition: str, **extra: Any) -> dict[str, Any]:
    row = {
        "incident_id": inc["incident_id"],
        "lineage_id": lid,
        "repository": inc.get("repository"),
        "repository_sha256": inc.get("repository_sha256"),
        "workflow": inc.get("workflow"),
        "notification_class": inc.get("notification_class"),
        "head_sha": inc.get("head_sha"),
        "head_sha_full": None,
        "head_committed_at": None,
        "relation_to_current_head": None,
        "message_count": len(inc.get("message_ids") or []),
        "disposition": disposition,
        "unverifiable_reason": None,
        "resolution_evidence": None,
    }
    row.update(extra)
    return row


def correlate_lineage(gh: GitHubReader, repo: str, workflow: str, incidents: list[dict[str, Any]],
                      pr_lookup: bool = True) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lid = lineage_id(repo, workflow)
    row = _lineage_base(repo, workflow, incidents, lid)

    def fail_closed(classification: str, error: dict[str, Any] | None, reason: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        row["classification"] = classification
        row["error"] = error
        row["unverifiable_incident_ids"] = row["incident_ids"]
        return row, [_incident_row(i, lid, DISP_UNVERIFIABLE, unverifiable_reason=reason) for i in incidents]

    try:
        branch = gh.default_branch(repo)
        row["default_branch"] = branch
        matches = gh.resolve_workflow(repo, workflow)
        if not matches:
            return fail_closed(NOT_FOUND, None, NOT_FOUND)
        if len(matches) > 1:
            active = [m for m in matches if m.get("state") == "active"]
            if len(active) != 1:
                return fail_closed(ERROR, {"status": None, "error": "WORKFLOW_NAME_AMBIGUOUS",
                                           "candidates": sorted(str(m.get("path")) for m in matches)}, "WORKFLOW_NAME_AMBIGUOUS")
            matches = active
        wf = matches[0]
        row["workflow_id"], row["workflow_path"] = wf.get("id"), wf.get("path")

        completed = gh.runs(repo, int(wf["id"]), branch, "completed", 10)
        decisive = [r for r in completed if r.get("conclusion") in DECISIVE_CONCLUSIONS]
        latest = decisive[0] if decisive else None
        if latest is not None and latest.get("conclusion") == "success":
            success: Mapping[str, Any] | None = latest
        elif latest is not None:
            green = gh.runs(repo, int(wf["id"]), branch, "success", 1)
            success = green[0] if green else None
        else:
            success = None
        row["latest_completed_run"] = _run_view(latest)
        row["latest_success_run"] = _run_view(success)
        success_sha = str(success.get("head_sha") or "").lower() if success else None
        success_time = _run_head_time(success) if success else None
        if success is not None and not (success_sha and len(success_sha) == 40 and success_time
                                        and str(success.get("html_url") or "").startswith("https://")):
            return fail_closed(ERROR, {"status": None, "error": "SUCCESS_RUN_SHAPE_INVALID"}, "SUCCESS_RUN_SHAPE_INVALID")

        incident_rows: list[dict[str, Any]] = []
        resolved_heads: dict[str, tuple[str, str, str | None]] = {}
        pr_cache: dict[str, dict[str, str] | None] = {}
        for inc in sorted(incidents, key=lambda i: i["incident_id"]):
            short = str(inc.get("head_sha") or "").lower()
            if short not in resolved_heads:
                try:
                    resolved_heads[short] = _resolve_head(gh, repo, short, success_sha)
                except ApiError as exc:
                    if exc.status in HEAD_UNRESOLVABLE_STATUSES:
                        incident_rows.append(_incident_row(inc, lid, DISP_UNVERIFIABLE, unverifiable_reason="FAILURE_HEAD_UNRESOLVABLE"))
                        continue
                    raise
            full, date, relation = resolved_heads[short]
            head_time = _parse_ts(date)
            superseded = bool(
                success is not None and success_time and head_time and head_time < success_time
                and relation not in ("IDENTICAL", "DESCENDANT_OF_CURRENT_HEAD")
                and not success_sha.startswith(short) and full != success_sha)
            if superseded:
                if full not in pr_cache:
                    pr_cache[full] = _merged_pr(gh, repo, full, branch, success_time) if pr_lookup else None
                evidence = _evidence(repo, workflow, branch, success, full, pr_cache[full])
                incident_rows.append(_incident_row(inc, lid, DISP_SUPERSEDED, head_sha_full=full, head_committed_at=date,
                                                   relation_to_current_head=relation, resolution_evidence=evidence))
            else:
                incident_rows.append(_incident_row(inc, lid, DISP_OUTSTANDING, head_sha_full=full, head_committed_at=date,
                                                   relation_to_current_head=relation))
    except ApiError as exc:
        return fail_closed(ERROR, {"status": exc.status, "path": exc.path}, ERROR)

    row["superseded_incident_ids"] = sorted(r["incident_id"] for r in incident_rows if r["disposition"] == DISP_SUPERSEDED)
    row["outstanding_incident_ids"] = sorted(r["incident_id"] for r in incident_rows if r["disposition"] == DISP_OUTSTANDING)
    row["unverifiable_incident_ids"] = sorted(r["incident_id"] for r in incident_rows if r["disposition"] == DISP_UNVERIFIABLE)
    dated = [r for r in incident_rows if r["head_committed_at"]]
    if dated:
        newest = max(dated, key=lambda r: (r["head_committed_at"], r["incident_id"]))
        row["newest_head"] = {"head_sha": newest["head_sha_full"], "committed_at": newest["head_committed_at"],
                              "incident_id": newest["incident_id"], "disposition": newest["disposition"]}

    if latest is None:
        row["classification"] = NO_RUN
    elif latest.get("conclusion") != "success":
        row["classification"] = STILL_FAILING
    elif not dated:
        row["classification"] = ERROR
        row["error"] = {"status": None, "error": "FAILURE_HEADS_UNRESOLVABLE"}
    elif row["newest_head"]["disposition"] == DISP_SUPERSEDED:
        row["classification"] = SUPERSEDED
    else:
        # A green run exists but the newest failing head is newer than it.
        row["classification"] = NO_RUN
    if row["classification"] not in OUTSTANDING_CLASSIFICATIONS:
        # Only outstanding lineages carry outstanding incidents; a superseded
        # lineage with an undated head keeps that head listed as unverifiable.
        for r in incident_rows:
            if r["disposition"] == DISP_OUTSTANDING:
                r["disposition"] = DISP_UNVERIFIABLE
                r["unverifiable_reason"] = "LINEAGE_" + str(row["classification"])
        row["unverifiable_incident_ids"] = sorted(set(row["unverifiable_incident_ids"]) | set(row["outstanding_incident_ids"]))
        row["outstanding_incident_ids"] = []
    return row, incident_rows


def correlate_state(state: Mapping[str, Any], gh: GitHubReader, *, pr_lookup: bool = True,
                    fetcher_name: str = "stub", now: dt.datetime | None = None) -> dict[str, Any]:
    bad = t._check(state)
    if bad:
        raise ValueError(bad)
    now = now or dt.datetime.now(dt.timezone.utc)
    public_set = set(state.get("public_repositories") or ())
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    redacted: dict[str, list[dict[str, Any]]] = {}
    uncorrelated: list[dict[str, Any]] = []
    for inc in _open_retained(state):
        repo, workflow = inc.get("repository"), inc.get("workflow")
        if inc.get("redacted") or (repo is None and inc.get("repository_sha256")):
            redacted.setdefault(str(inc.get("repository_sha256")), []).append(inc)
        elif not repo or not workflow or not inc.get("head_sha") or repo not in public_set:
            # A name outside the declared public list is never sent to the API.
            uncorrelated.append(inc)
        else:
            groups.setdefault((repo, workflow), []).append(inc)

    lineages: list[dict[str, Any]] = []
    incident_rows: dict[str, dict[str, Any]] = {}
    for (repo, workflow) in sorted(groups):
        row, rows = correlate_lineage(gh, repo, workflow, groups[(repo, workflow)], pr_lookup=pr_lookup)
        lineages.append(row)
        for r in rows:
            incident_rows[r["incident_id"]] = r
    for sha in sorted(redacted):
        incidents = redacted[sha]
        lid = "LIN-REDACTED-" + sha[:20]
        row = _lineage_base(None, None, incidents, lid)
        row["repository_sha256"] = sha
        row["classification"] = REDACTED
        row["unverifiable_incident_ids"] = row["incident_ids"]
        lineages.append(row)
        for inc in incidents:
            incident_rows[inc["incident_id"]] = _incident_row(inc, lid, DISP_UNVERIFIABLE, repository=None, workflow=None,
                                                              unverifiable_reason=REDACTED)
    if uncorrelated:
        lid = "LIN-UNCORRELATED"
        row = _lineage_base(None, None, uncorrelated, lid)
        row["classification"] = UNCORRELATED
        row["unverifiable_incident_ids"] = row["incident_ids"]
        lineages.append(row)
        for inc in uncorrelated:
            incident_rows[inc["incident_id"]] = _incident_row(inc, lid, DISP_UNVERIFIABLE, unverifiable_reason=UNCORRELATED)

    by_class = {c: 0 for c in CLASSIFICATIONS}
    incidents_by_class = {c: 0 for c in CLASSIFICATIONS}
    for row in lineages:
        by_class[row["classification"]] += 1
        incidents_by_class[row["classification"]] += row["incident_count"]
    by_disp = {DISP_SUPERSEDED: 0, DISP_OUTSTANDING: 0, DISP_UNVERIFIABLE: 0}
    for r in incident_rows.values():
        by_disp[r["disposition"]] += 1
    public_count = sum(len(v) for v in groups.values())
    return {
        "schema": SCHEMA,
        "task_id": t.TASK_ID,
        "cosv_task_vector": t.COSV_TASK_VECTOR,
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_continuation": {
            "schema": t.SCHEMA,
            "cycle_seq": state["cycle_seq"],
            "transition_seq": state["transition_seq"],
            "phase": state["phase"],
            "state_sha256": t.state_sha256(state),
        },
        "fetcher": fetcher_name,
        "api_calls": gh.calls,
        "pr_lookup": bool(pr_lookup),
        "counts": {
            "open_retained_incidents": len(incident_rows),
            "public_open_incidents": public_count,
            "redacted_open_incidents": sum(len(v) for v in redacted.values()),
            "uncorrelated_open_incidents": len(uncorrelated),
            "public_lineages": len(groups),
            "lineages_by_classification": by_class,
            "incidents_by_lineage_classification": incidents_by_class,
            "incidents_by_disposition": by_disp,
            "outstanding_lineages": sum(1 for r in lineages if r["classification"] in OUTSTANDING_CLASSIFICATIONS),
        },
        "lineages": lineages,
        "incidents": {k: incident_rows[k] for k in sorted(incident_rows)},
        "credential_authority": "NONE_READ_ONLY_OBSERVATION",
        "credential_material_exported": False,
        "evidence_class": "GITHUB_API_READ_OBSERVED",
        "authority_effect": "NONE_OBSERVATION_ONLY",
        "projection_only": True,
        "continuation_state_mutated": False,
        "github_actions_runtime_authority": "NONE",
    }


# --------------------------------------------------------------------------- apply through the existing state machine

def apply_resolutions(state: Mapping[str, Any], correlation: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay every SUPERSEDED incident through ``record_resolution`` (op ``resolve``).

    Returns ``(final_state, disposition)``. On any non-ALLOW transition other
    than ``INCIDENT_NOT_OPEN`` (already resolved elsewhere) the whole batch
    fails closed and the prior state is returned unchanged. Each link of the
    chain is verified with ``verify_chain`` as it is produced.
    """
    name = "APPLY_CORRELATION_RESOLUTIONS"
    if correlation.get("schema") != SCHEMA:
        return dict(state), t._disposition(t.FAIL_CLOSED, name, "CORRELATION_SCHEMA_INVALID")
    if correlation.get("authority_effect") != "NONE_OBSERVATION_ONLY":
        return dict(state), t._disposition(t.FAIL_CLOSED, name, "CORRELATION_CLAIMS_AUTHORITY")
    source = correlation.get("source_continuation") or {}
    if source.get("state_sha256") != t.state_sha256(state):
        return dict(state), t._disposition(t.FAIL_CLOSED, name, "CORRELATION_STATE_LINEAGE_MISMATCH",
                                           expected=source.get("state_sha256"), actual=t.state_sha256(state))
    rows = [r for r in (correlation.get("incidents") or {}).values() if r.get("disposition") == DISP_SUPERSEDED]
    rows.sort(key=lambda r: r["incident_id"])
    current: dict[str, Any] = dict(state)
    first_seq = int(state["transition_seq"])
    applied, skipped = [], []
    for r in rows:
        evidence = r.get("resolution_evidence")
        if not isinstance(evidence, Mapping) or evidence.get("kind") != "SUPERSEDED_BY_CURRENT_EVIDENCE":
            return dict(state), t._disposition(t.FAIL_CLOSED, name, "SUPERSEDED_ROW_WITHOUT_EVIDENCE", incident_id=r["incident_id"])
        nxt, disp = t.record_resolution(current, r["incident_id"], evidence)
        if disp["disposition"] == t.DENY and disp.get("failed_predicate") == "INCIDENT_NOT_OPEN":
            skipped.append(r["incident_id"])
            continue
        if disp["disposition"] != t.ALLOW:
            return dict(state), t._disposition(t.FAIL_CLOSED, name, "RESOLVE_TRANSITION_REFUSED",
                                               incident_id=r["incident_id"], refused=disp)
        ok, why = t.verify_chain([current, nxt])
        if not ok:
            return dict(state), t._disposition(t.FAIL_CLOSED, name, str(why), incident_id=r["incident_id"])
        current = nxt
        applied.append(r["incident_id"])
    return current, t._disposition(t.ALLOW, name, applied=len(applied), skipped_not_open=len(skipped),
                                   transition_seq_from=first_seq, transition_seq_to=int(current["transition_seq"]),
                                   prior_state_sha256=t.state_sha256(state), state_sha256=t.state_sha256(current),
                                   applied_incident_ids=applied, skipped_incident_ids=skipped)


# --------------------------------------------------------------------------- CLI

def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_fetcher(name: str) -> Any:
    if name == "gh":
        return GhFetcher()
    return UrllibFetcher(token=os.environ.get("GITHUB_TOKEN") or None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--state", required=True, type=Path, help="continuation.json")
    parser.add_argument("--output", type=Path, help="write the correlation here (correlate mode)")
    parser.add_argument("--fetcher", choices=("urllib", "gh"), default="urllib")
    parser.add_argument("--no-pr-lookup", action="store_true", help="skip /commits/{sha}/pulls derivation")
    parser.add_argument("--apply-resolutions", type=Path, metavar="CORRELATION",
                        help="replay SUPERSEDED incidents through the existing resolve transition and write the state")
    parser.add_argument("--dry-run", action="store_true", help="with --apply-resolutions: do not write the state")
    args = parser.parse_args(argv)
    state = json.loads(args.state.read_text(encoding="utf-8"))

    if args.apply_resolutions is not None:
        correlation = json.loads(args.apply_resolutions.read_text(encoding="utf-8"))
        nxt, disp = apply_resolutions(state, correlation)
        if disp["disposition"] == t.ALLOW and disp["applied"] > 0 and not args.dry_run:
            _write_json(args.state, nxt)
            disp["state_written"] = str(args.state)
        else:
            disp["state_written"] = None
        print(json.dumps(disp, sort_keys=True))
        return 0 if disp["disposition"] == t.ALLOW else 1

    if args.output is None:
        parser.error("--output is required unless --apply-resolutions is given")
    gh = GitHubReader(build_fetcher(args.fetcher))
    try:
        correlation = correlate_state(state, gh, pr_lookup=not args.no_pr_lookup, fetcher_name=args.fetcher)
    except ValueError as exc:
        print(json.dumps(t._disposition(t.FAIL_CLOSED, "CORRELATE", str(exc)), sort_keys=True))
        return 1
    _write_json(args.output, correlation)
    print(json.dumps(t._disposition(t.ALLOW, "CORRELATE", output=str(args.output), api_calls=gh.calls,
                                    counts=correlation["counts"], continuation_state_mutated=False), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
