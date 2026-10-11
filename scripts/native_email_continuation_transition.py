#!/usr/bin/env python3
"""Manifest-bound continuation transitions for the native email action monitor.

Issue #3039 replaces the awaited resident/scheduler path and the proposed
"hourly watchdog" with a durable continuation state. One monitor cycle is a
chain of explicit state transitions:

    begin_cycle -> apply_page* -> complete_pagination
      -> record_resolution* -> record_archive_receipt* -> close_cycle

Every transition is a pure function ``(prior_state, observation) ->
(next_state, disposition)``. The next state carries ``prior_state_sha256`` so
the committed chain can be replayed and verified by ``verify_chain``. Nothing
waits for an executor and nothing schedules one: any executor may invoke the
next transition, and a missed hour loses nothing because the next invocation
resumes from committed state.

Continuation is not a Gmail pageToken (short-lived). It is a fixed time window
plus a processed-message-ID ledger and the last completed page index, so an
interrupted cycle resumes at ``last_completed_page_index + 1`` and a re-read or
shifted page is deduplicated rather than double counted. Archive is never
applied mid-pagination; the archive set is computed only after pagination
completes and only from incidents with verified exact-head resolution.

Non-authorizing. The state is a projection: it confers no transition
admission, WorkerCoordinator claim/fence, credential, custody or archive
authority. ``archive_proposed`` is a proposal for the governed archive
consequence; only an archive receipt naming proposed IDs moves counters.
``project_failure_map_receipt`` (``--op failure-map``) projects the open
retained incidents, read-only, in the monitor-receipt shape that
``reconcile_email_failure_incidents.py`` maps for StegHealth.
Standard library only.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "stegverse.native-email-continuation-state/v1"
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
COSV_TASK_VECTOR = "10100000100000"
QUERY = (
    '-in:spam -in:trash (from:notifications@github.com OR from:noreply@github.com '
    'OR subject:"[Task Update]")'
)
PAGE_LIMIT = 100

ALLOW = "ALLOW"
DENY = "DENY"
FAIL_CLOSED = "FAIL_CLOSED"

PHASE_IDLE = "IDLE"
PHASE_PAGINATING = "PAGINATING"
PHASE_RECONCILING = "RECONCILING"

INCIDENT_OPEN = "OPEN_UNRESOLVED"
INCIDENT_RESOLVED = "RESOLVED_VERIFIED"
INCIDENT_SUPERSEDED = "SUPERSEDED_VERIFIED"
# A success notification is informational about its own head; it never
# resolves a failure by itself (resolution needs exact-head evidence).
INCIDENT_SUCCESS_STATE = "INFORMATIONAL_SUCCESS_OBSERVED"
ARCHIVABLE = (INCIDENT_RESOLVED, INCIDENT_SUPERSEDED)

# Classes kept in INBOX until resolved regardless of anything else.
RETAINED_CLASSES = ("FAILURE", "SECURITY", "BILLING", "QUOTA", "CAPACITY", "POLICY")

# Shape consumed by scripts/reconcile_email_failure_incidents.py (the
# StegHealth failure-map bridge) and emitted by run_native_email_action_monitor.
MONITOR_RECEIPT_SCHEMA = "stegverse.native-email-action-monitor-receipt/v1"
INCIDENT_KIND = "GITHUB_FAILURE_EMAIL_CLUSTER"


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def state_sha256(state: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(state)).hexdigest()


def ids_digest(ids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()


def genesis() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "cosv_task_vector": COSV_TASK_VECTOR,
        "query": QUERY,
        "page_limit": PAGE_LIMIT,
        "cycle_seq": 0,
        "transition_seq": 0,
        "transition": "GENESIS",
        "phase": PHASE_IDLE,
        "high_water_epoch": 0,
        "window_after_epoch": None,
        "window_before_epoch": None,
        "last_completed_page_index": -1,
        "processed_message_ids": [],
        "processed_message_ids_digest": ids_digest([]),
        # Repository names not listed here are redacted from committed state:
        # this file lives in a public repository and incidents may concern
        # private ones. Correlation still works through repository_sha256.
        "public_repositories": [],
        "incidents": {},
        "archive_proposed": [],
        "archived_message_ids": [],
        "counters": {
            "pages_scanned": 0,
            "messages_seen": 0,
            "duplicates_suppressed": 0,
            "resolved_verified": 0,
            "archived_confirmed": 0,
        },
        "prior_state_sha256": None,
        "authority_effect": "NONE",
        "projection_only": True,
        "custody_authority": "NONE_PROJECTION_PENDING_ORGANIZATION_CUSTODY",
        "worker_claim": {
            "authority": "WORKERCOORDINATOR",
            "claim_ref": None,
            "fence_ref": None,
            "projection_only": True,
        },
        "credential_authority": "TV/TVC",
        "github_actions_runtime_authority": "NONE",
        "heartbeat": "OBSERVABILITY_ONLY",
        "external_host_prerequisite": False,
        "scheduler_prerequisite": False,
    }


def _disposition(disposition: str, transition: str, predicate: str | None = None, **detail: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"disposition": disposition, "transition": transition}
    if predicate:
        out["failed_predicate"] = predicate
    out.update(detail)
    return out


def _advance(prior: Mapping[str, Any], transition: str) -> dict[str, Any]:
    nxt = copy.deepcopy(dict(prior))
    nxt["prior_state_sha256"] = state_sha256(prior)
    nxt["transition_seq"] = int(prior["transition_seq"]) + 1
    nxt["transition"] = transition
    return nxt


def _check(state: Mapping[str, Any]) -> str | None:
    if not isinstance(state, Mapping) or state.get("schema") != SCHEMA:
        return "CONTINUATION_STATE_SCHEMA_INVALID"
    if state.get("query") != QUERY:
        return "CONTINUATION_QUERY_CHANGED_UNDER_STATE"
    if state.get("authority_effect") != "NONE" or state.get("projection_only") is not True:
        return "CONTINUATION_STATE_CLAIMS_AUTHORITY"
    if state.get("processed_message_ids_digest") != ids_digest(state.get("processed_message_ids", [])):
        return "PROCESSED_ID_LEDGER_DIGEST_MISMATCH"
    return None


def _field(row: Mapping[str, Any], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    headers = row.get("headers")
    if isinstance(headers, Mapping):
        for name in names:
            value = headers.get(name)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def notification_class(row: Mapping[str, Any]) -> str:
    text = " ".join(str(row.get(k) or "") for k in ("subject", "snippet")).lower()
    for klass, words in (
        ("SECURITY", ("security", "vulnerab", "dependabot alert", "secret scanning")),
        ("BILLING", ("billing", "payment", "invoice")),
        ("QUOTA", ("quota", "rate limit", "usage limit", "spending limit")),
        ("CAPACITY", ("storage", "capacity", "minutes used")),
        ("POLICY", ("policy", "ruleset", "branch protection", "permissions")),
        ("FAILURE", ("fail", "error", "cancelled", "blocked", "requires handoff", "needs attention")),
        ("SUCCESS", ("succeeded", "success", "passed", "completed successfully")),
    ):
        if any(word in text for word in words):
            return klass
    return "INFORMATIONAL"


# "[owner/repo] Run failed: <workflow> - <branch or PR title> (<sha>)"
RUN_SUBJECT = re.compile(
    r"^\[(?P<repo>[^\]/\s]+/[^\]\s]+)\] (?:PR )?[Rr]un failed: (?P<rest>.+) \((?P<sha>[0-9a-f]{7,40})\)$")


def parse_subject(subject: str) -> dict[str, str]:
    """Recover repository, workflow and head from a GitHub Actions subject."""
    m = RUN_SUBJECT.match(subject.strip()) if isinstance(subject, str) else None
    if not m:
        return {}
    workflow = m.group("rest").rsplit(" - ", 1)[0]
    workflow = re.sub(r", Attempt #\d+$", "", workflow)
    return {"repository": m.group("repo"), "workflow": workflow, "head_sha": m.group("sha")}


def repository_sha256(repo: str) -> str:
    return hashlib.sha256(repo.lower().encode("utf-8")).hexdigest()


def correlate(row: Mapping[str, Any]) -> dict[str, Any]:
    """Bind one notification to repository, workflow and exact head."""
    parsed = parse_subject(str(row.get("subject") or ""))
    row = {**parsed, **{k: v for k, v in row.items() if v}}
    repo = _field(row, "repository", "repo", "X-GitHub-Repository")
    if not repo:
        list_id = _field(row, "list_id", "List-ID")
        # GitHub List-ID: "<repo> <repo.owner.github.com>"
        if ".github.com" in list_id and "<" in list_id:
            inner = list_id[list_id.index("<") + 1:].split(">", 1)[0]
            parts = inner.split(".")
            if len(parts) >= 2:
                repo = f"{parts[1]}/{parts[0]}"
    workflow = _field(row, "workflow", "workflow_name")
    head_sha = _field(row, "head_sha", "sha", "X-GitHub-Sha").lower()
    run_id = _field(row, "run_id", "workflow_run_id")
    klass = notification_class(row)
    complete = bool(repo and workflow and head_sha)
    key = "\n".join([repo or "unknown-repo", workflow or "unknown-workflow", head_sha or "unknown-head", klass])
    return {
        "incident_id": "INC-EMAIL-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24],
        "repository": repo or None,
        "repository_sha256": repository_sha256(repo) if repo else None,
        "workflow": workflow or None,
        "head_sha": head_sha or None,
        "run_id": run_id or None,
        "notification_class": klass,
        "correlation_complete": complete,
    }


def set_public_repositories(prior: Mapping[str, Any], repositories: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Declare which repository names may appear unredacted in committed state."""
    name = "SET_PUBLIC_REPOSITORIES"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_IDLE:
        return dict(prior), _disposition(DENY, name, "DISCLOSURE_CHANGE_ONLY_BETWEEN_CYCLES")
    if not isinstance(repositories, list) or not all(isinstance(r, str) and "/" in r for r in repositories):
        return dict(prior), _disposition(FAIL_CLOSED, name, "PUBLIC_REPOSITORY_LIST_INVALID")
    nxt = _advance(prior, name)
    nxt["public_repositories"] = sorted(set(repositories))
    return nxt, _disposition(ALLOW, name, count=len(nxt["public_repositories"]))


def rows_from_gmail_search(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Adapt one Gmail thread-search page to transition rows (INBOX messages only)."""
    rows: list[dict[str, Any]] = []
    for thread in payload.get("threads") or []:
        for msg in thread.get("messages") or []:
            if "INBOX" not in (msg.get("labelIds") or []):
                continue
            rows.append({
                "message_id": msg.get("id"),
                "internal_epoch": int(msg["internalDate"]) // 1000 if msg.get("internalDate") else None,
                "subject": msg.get("subject") or "",
                "snippet": msg.get("snippet") or "",
            })
    return rows


def begin_cycle(prior: Mapping[str, Any], now_epoch: int) -> tuple[dict[str, Any], dict[str, Any]]:
    name = "BEGIN_CYCLE"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_IDLE:
        # Resume, never restart: an unfinished cycle continues where it stopped.
        return dict(prior), _disposition(DENY, name, "CYCLE_ALREADY_OPEN_RESUME_INSTEAD",
                                         resume_page_index=int(prior["last_completed_page_index"]) + 1)
    if not isinstance(now_epoch, int) or now_epoch <= int(prior["high_water_epoch"]):
        return dict(prior), _disposition(FAIL_CLOSED, name, "WINDOW_END_NOT_AFTER_HIGH_WATER_MARK")
    nxt = _advance(prior, name)
    nxt["cycle_seq"] = int(prior["cycle_seq"]) + 1
    nxt["phase"] = PHASE_PAGINATING
    nxt["window_after_epoch"] = int(prior["high_water_epoch"])
    nxt["window_before_epoch"] = now_epoch
    nxt["last_completed_page_index"] = -1
    return nxt, _disposition(ALLOW, name, cycle_seq=nxt["cycle_seq"],
                             window=[nxt["window_after_epoch"], now_epoch],
                             gap_seconds=now_epoch - int(prior["high_water_epoch"]))


def apply_page(prior: Mapping[str, Any], page_index: int, messages: list[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    name = "APPLY_PAGE"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_PAGINATING:
        return dict(prior), _disposition(DENY, name, "NOT_PAGINATING")
    expected = int(prior["last_completed_page_index"]) + 1
    if page_index < expected:
        return dict(prior), _disposition(ALLOW, name, None, idempotent_replay=True, page_index=page_index)
    if page_index != expected:
        return dict(prior), _disposition(FAIL_CLOSED, name, "PAGE_INDEX_SKIPS_CONTINUATION", expected_page_index=expected)
    if not isinstance(messages, list) or len(messages) > PAGE_LIMIT:
        return dict(prior), _disposition(FAIL_CLOSED, name, "PAGE_EXCEEDS_BOUND_OR_INVALID")
    lo, hi = int(prior["window_after_epoch"]), int(prior["window_before_epoch"])
    ids: list[str] = []
    for row in messages:
        mid = row.get("message_id") or row.get("id") if isinstance(row, Mapping) else None
        if not isinstance(mid, str) or not mid:
            return dict(prior), _disposition(FAIL_CLOSED, name, "MESSAGE_ID_REQUIRED")
        ids.append(mid)

    nxt = _advance(prior, name)
    seen = set(nxt["processed_message_ids"])
    new, dupes, outside = 0, 0, 0
    for row, mid in zip(messages, ids):
        if mid in seen:
            dupes += 1
            continue
        epoch = row.get("internal_epoch")
        # Messages already in INBOX from before the window remain in scope:
        # unresolved mail is never dropped. Only messages newer than the
        # window end are deferred to the next cycle so the set is stable.
        if isinstance(epoch, int) and epoch >= hi:
            outside += 1
            continue
        seen.add(mid)
        new += 1
        corr = correlate(row)
        if corr["repository"] and corr["repository"] not in set(nxt.get("public_repositories") or ()):
            corr.update(repository=None, workflow=None, redacted=True)
        inc = nxt["incidents"].setdefault(corr["incident_id"], {
            **corr,
            "state": INCIDENT_SUCCESS_STATE if corr["notification_class"] == "SUCCESS" else INCIDENT_OPEN,
            "message_ids": [],
            "first_cycle_seq": nxt["cycle_seq"],
            "resolution_evidence": None,
            "incident_proposal_mints_execution_authority": False,
        })
        inc["message_ids"] = sorted(set(inc["message_ids"]) | {mid})
        inc["last_cycle_seq"] = nxt["cycle_seq"]
        if inc["state"] in ARCHIVABLE:
            # A late copy of an already verified incident joins the proposal.
            nxt["archive_proposed"] = sorted(set(nxt["archive_proposed"]) | {mid})
    nxt["processed_message_ids"] = sorted(seen)
    nxt["processed_message_ids_digest"] = ids_digest(seen)
    nxt["last_completed_page_index"] = page_index
    c = nxt["counters"]
    c["pages_scanned"] += 1
    c["messages_seen"] += new
    c["duplicates_suppressed"] += dupes
    return nxt, _disposition(ALLOW, name, page_index=page_index, new_messages=new,
                             duplicates_suppressed=dupes, deferred_after_window=outside,
                             window=[lo, hi])


def complete_pagination(prior: Mapping[str, Any], has_more: bool | None) -> tuple[dict[str, Any], dict[str, Any]]:
    name = "COMPLETE_PAGINATION"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_PAGINATING:
        return dict(prior), _disposition(DENY, name, "NOT_PAGINATING")
    if type(has_more) is not bool:
        return dict(prior), _disposition(FAIL_CLOSED, name, "PAGINATION_TERMINAL_EVIDENCE_REQUIRED")
    if has_more:
        return dict(prior), _disposition(DENY, name, "PAGINATION_INCOMPLETE_NO_ZERO_REMAINING_CLAIM",
                                         resume_page_index=int(prior["last_completed_page_index"]) + 1)
    nxt = _advance(prior, name)
    nxt["phase"] = PHASE_RECONCILING
    return nxt, _disposition(ALLOW, name, **summary(nxt))


def record_resolution(prior: Mapping[str, Any], incident_id: str, evidence: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Mark an incident resolved only on observed green CI at the exact new head."""
    name = "RECORD_RESOLUTION"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_RECONCILING:
        return dict(prior), _disposition(DENY, name, "RESOLUTION_BEFORE_PAGINATION_COMPLETE")
    inc = prior["incidents"].get(incident_id)
    if inc is None:
        return dict(prior), _disposition(FAIL_CLOSED, name, "INCIDENT_UNKNOWN")
    if inc["state"] not in (INCIDENT_OPEN, INCIDENT_SUCCESS_STATE):
        return dict(prior), _disposition(DENY, name, "INCIDENT_NOT_OPEN", state=inc["state"])
    if not isinstance(evidence, Mapping):
        return dict(prior), _disposition(FAIL_CLOSED, name, "RESOLUTION_EVIDENCE_REQUIRED")
    kind = evidence.get("kind")
    url = evidence.get("evidence_url")
    if not (isinstance(url, str) and url.startswith("https://")):
        return dict(prior), _disposition(FAIL_CLOSED, name, "RESOLUTION_EVIDENCE_URL_REQUIRED")
    if kind == "REPAIRED_AT_EXACT_HEAD":
        head = str(evidence.get("repaired_head_sha") or "").lower()
        observed = str(evidence.get("observed_head_sha") or "").lower()
        if not (len(head) == 40 and head == observed):
            return dict(prior), _disposition(FAIL_CLOSED, name, "EXACT_HEAD_MISMATCH")
        if evidence.get("ci_conclusion") != "success":
            return dict(prior), _disposition(FAIL_CLOSED, name, "CI_NOT_GREEN_AT_EXACT_HEAD")
        repo = evidence.get("repository")
        if inc.get("repository_sha256") and not (
                isinstance(repo, str) and repository_sha256(repo) == inc["repository_sha256"]):
            return dict(prior), _disposition(FAIL_CLOSED, name, "REPOSITORY_MISMATCH")
        state = INCIDENT_RESOLVED
    elif kind == "SUPERSEDED_BY_CURRENT_EVIDENCE":
        # Staleness only from independent current evidence: a newer head on the
        # same workflow observed green.
        newer = str(evidence.get("current_head_sha") or "").lower()
        if not (len(newer) == 40 and not newer.startswith(inc.get("head_sha") or "\0")):
            return dict(prior), _disposition(FAIL_CLOSED, name, "SUPERSEDING_HEAD_NOT_INDEPENDENT")
        if evidence.get("ci_conclusion") != "success":
            return dict(prior), _disposition(FAIL_CLOSED, name, "SUPERSEDING_HEAD_NOT_GREEN")
        state = INCIDENT_SUPERSEDED
    else:
        # Classification, assignment, comments or a PR closed unmerged are
        # never resolution.
        return dict(prior), _disposition(FAIL_CLOSED, name, "RESOLUTION_KIND_NOT_ADMISSIBLE")
    nxt = _advance(prior, name)
    target = nxt["incidents"][incident_id]
    target["state"] = state
    target["resolution_evidence"] = dict(evidence)
    nxt["counters"]["resolved_verified"] += 1
    proposed = set(nxt["archive_proposed"]) | (set(target["message_ids"]) - set(nxt["archived_message_ids"]))
    nxt["archive_proposed"] = sorted(proposed)
    return nxt, _disposition(ALLOW, name, incident_id=incident_id, state=state,
                             archive_proposed_added=len(target["message_ids"]))


def record_archive_receipt(prior: Mapping[str, Any], confirmed_ids: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Count only confirmed mailbox mutations of proposed IDs."""
    name = "RECORD_ARCHIVE_RECEIPT"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_RECONCILING:
        return dict(prior), _disposition(DENY, name, "ARCHIVE_ONLY_AFTER_PAGINATION")
    proposed = set(prior["archive_proposed"])
    confirmed = set(confirmed_ids or [])
    stray = sorted(confirmed - proposed)
    if stray:
        return dict(prior), _disposition(FAIL_CLOSED, name, "ARCHIVE_OF_UNPROPOSED_MESSAGE", message_ids=stray)
    nxt = _advance(prior, name)
    nxt["archive_proposed"] = sorted(proposed - confirmed)
    nxt["archived_message_ids"] = sorted(set(nxt["archived_message_ids"]) | confirmed)
    nxt["counters"]["archived_confirmed"] += len(confirmed)
    return nxt, _disposition(ALLOW, name, archived_confirmed=len(confirmed))


def close_cycle(prior: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    name = "CLOSE_CYCLE"
    bad = _check(prior)
    if bad:
        return dict(prior), _disposition(FAIL_CLOSED, name, bad)
    if prior["phase"] != PHASE_RECONCILING:
        return dict(prior), _disposition(DENY, name, "CLOSE_BEFORE_PAGINATION_COMPLETE")
    nxt = _advance(prior, name)
    nxt["phase"] = PHASE_IDLE
    nxt["high_water_epoch"] = int(prior["window_before_epoch"])
    return nxt, _disposition(ALLOW, name, **summary(nxt))


def summary(state: Mapping[str, Any]) -> dict[str, Any]:
    incidents = state["incidents"].values()
    archived = set(state["archived_message_ids"])
    open_retained = sorted(i["incident_id"] for i in incidents
                           if i["state"] == INCIDENT_OPEN and i["notification_class"] in RETAINED_CLASSES)
    unresolved = sorted(i["incident_id"] for i in incidents if i["state"] == INCIDENT_OPEN)
    coverage_complete = state["phase"] in (PHASE_RECONCILING, PHASE_IDLE) and int(state["cycle_seq"]) > 0
    return {
        "cycle_seq": state["cycle_seq"],
        "counters": dict(state["counters"]),
        "unresolved_incident_ids": unresolved,
        "retained_in_inbox_incident_ids": open_retained,
        "archive_proposed_count": len(state["archive_proposed"]),
        "coverage_complete": coverage_complete,
        # Never report zero without complete coverage.
        "operational_inbox_zero": bool(coverage_complete and all(
            set(i["message_ids"]) <= archived for i in incidents)),
    }


def project_failure_map_receipt(state: Mapping[str, Any]) -> dict[str, Any]:
    """Project open retained incidents as a monitor receipt for the StegHealth bridge.

    Pure and read-only: the state is not mutated and no transition is recorded.
    Each ``OPEN_UNRESOLVED`` incident whose class is in ``RETAINED_CLASSES``
    becomes one ``GITHUB_FAILURE_EMAIL_CLUSTER`` incident in the shape that
    ``reconcile_email_failure_incidents.build_failure_map`` consumes. Redacted
    incidents stay redacted: ``repository_sha256`` stands in for the name and
    the workflow is ``unknown-workflow``. The projection confers nothing
    (``authority_effect: NONE_PROJECTION_ONLY``); corrective-task creation
    remains StegHealth's, registry import an owner-admitted step.
    """
    bad = _check(state)
    if bad:
        raise ValueError(bad)
    digest = state_sha256(state)
    lineage = {"cycle_seq": state["cycle_seq"], "transition_seq": state["transition_seq"], "state_sha256": digest}
    incidents: list[dict[str, Any]] = []
    for inc in state["incidents"].values():
        if inc["state"] != INCIDENT_OPEN or inc["notification_class"] not in RETAINED_CLASSES:
            continue
        repo, sha = inc.get("repository"), inc.get("repository_sha256")
        workflow = inc.get("workflow") or "unknown-workflow"
        head = inc.get("head_sha") or "unknown-head"
        signature = f"{inc['notification_class'].lower()}:{workflow}@{head}"
        if inc.get("run_id"):
            signature += f"#run:{inc['run_id']}"
        message_ids = sorted(inc.get("message_ids") or [])
        incidents.append({
            "incident_id": inc["incident_id"],
            "kind": INCIDENT_KIND,
            "normalized_repository": repo or sha or "unknown-repo",
            "repository_sha256": sha,
            "redacted": bool(inc.get("redacted")),
            "normalized_workflow": workflow,
            "normalized_error_signature": signature,
            "head_sha": inc.get("head_sha"),
            "run_id": inc.get("run_id"),
            "notification_class": inc["notification_class"],
            "correlation_complete": bool(inc.get("correlation_complete")),
            "observation_count": len(message_ids),
            "observation_refs": message_ids,
            "state": "INCIDENT_PROPOSED_NOT_ADMITTED",
            "task_ingress_required": True,
            "email_observation_is_execution_evidence": False,
            "incident_proposal_mints_execution_authority": False,
            "source_continuation": dict(lineage),
        })
    incidents.sort(key=lambda i: i["incident_id"])
    return {
        "schema": MONITOR_RECEIPT_SCHEMA,
        "state": "CONTINUATION_PROJECTION",
        "projection_source": {"schema": SCHEMA, "phase": state["phase"], **lineage},
        "task_id": TASK_ID,
        "cosv_task_vector": COSV_TASK_VECTOR,
        "incident_count": len(incidents),
        "incidents": incidents,
        "archived_replay": {"state": "NOT_REQUESTED", "complete": True},
        "archived_count": 0,
        "archive_failed_count": 0,
        "archive_failed_ids": [],
        "credential_authority": "TV/TVC",
        "credential_material_exported": False,
        "github_token_runtime_authority": "NONE",
        "task_creation_owner": "StegVerse-Labs/StegHealth",
        "projection_only": True,
        "continuation_state_mutated": False,
        "authority_effect": "NONE_PROJECTION_ONLY",
    }


def verify_chain(states: list[Mapping[str, Any]]) -> tuple[bool, str | None]:
    for i in range(1, len(states)):
        if states[i].get("prior_state_sha256") != state_sha256(states[i - 1]):
            return False, f"CHAIN_BREAK_AT:{i}"
        if int(states[i]["transition_seq"]) != int(states[i - 1]["transition_seq"]) + 1:
            return False, f"TRANSITION_SEQ_GAP_AT:{i}"
    return True, None


TRANSITIONS = {
    "begin": lambda s, a: begin_cycle(s, int(a["now_epoch"])),
    "page": lambda s, a: apply_page(s, int(a["page_index"]), a["messages"]),
    "complete": lambda s, a: complete_pagination(s, a.get("has_more")),
    "resolve": lambda s, a: record_resolution(s, a["incident_id"], a["evidence"]),
    "archive-receipt": lambda s, a: record_archive_receipt(s, a["confirmed_ids"]),
    "close": lambda s, a: close_cycle(s),
    "set-public-repositories": lambda s, a: set_public_repositories(s, a["repositories"]),
    "page-from-gmail": lambda s, a: apply_page(s, int(a["page_index"]), rows_from_gmail_search(a["search"])),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--op", required=True, choices=sorted(TRANSITIONS) + ["genesis", "summary", "failure-map"])
    parser.add_argument("--input", type=Path, help="JSON observation for the transition")
    parser.add_argument("--output", type=Path,
                        help="failure-map only: write the projected receipt here instead of stdout")
    args = parser.parse_args(argv)
    if args.op == "genesis":
        if args.state.exists():
            print(json.dumps(_disposition(DENY, "GENESIS", "STATE_ALREADY_EXISTS")))
            return 1
        state, disp = genesis(), _disposition(ALLOW, "GENESIS")
    else:
        prior = json.loads(args.state.read_text(encoding="utf-8"))
        if args.op == "summary":
            print(json.dumps(summary(prior), indent=2, sort_keys=True))
            return 0
        if args.op == "failure-map":
            # Read-only projection: never writes or re-commits the state file.
            try:
                receipt = project_failure_map_receipt(prior)
            except ValueError as exc:
                print(json.dumps(_disposition(FAIL_CLOSED, "FAILURE_MAP", str(exc)), sort_keys=True))
                return 1
            text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
            if args.output is None:
                sys.stdout.write(text)
                return 0
            args.output.parent.mkdir(parents=True, exist_ok=True)
            tmp = args.output.with_name("." + args.output.name + ".tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(args.output)
            print(json.dumps(_disposition(ALLOW, "FAILURE_MAP", incident_count=receipt["incident_count"],
                                          output=str(args.output), continuation_state_mutated=False), sort_keys=True))
            return 0
        observation = json.loads(args.input.read_text(encoding="utf-8")) if args.input else {}
        state, disp = TRANSITIONS[args.op](prior, observation)
        if disp["disposition"] != ALLOW or state_sha256(state) == state_sha256(prior):
            print(json.dumps(disp, sort_keys=True))
            return 0 if disp["disposition"] == ALLOW else 1
    tmp = args.state.with_name("." + args.state.name + ".tmp")
    args.state.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(args.state)
    print(json.dumps(disp, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
