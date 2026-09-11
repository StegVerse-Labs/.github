#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "runtime" / "task-registry" / "checkin-events.jsonl"
SCHEMA = "stegverse.task-registry-checkin-event/v1"
AUTHORITY_EFFECT = "NONE"
RECENT_RETURN_WINDOW_SECONDS = 1800


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("event_at must include timezone")
    return dt.astimezone(timezone.utc)


def normalize_context(value: dict[str, Any] | None) -> dict[str, Any]:
    source = dict(value or {})
    repositories = sorted({str(x).strip() for x in source.get("repositories", []) if str(x).strip()})
    components = sorted({str(x).strip() for x in source.get("components", []) if str(x).strip()})
    pull_request = source.get("pull_request")
    if pull_request is not None:
        pull_request = int(pull_request)
        if pull_request < 1:
            raise ValueError("pull_request must be positive")
    return {
        "repository": str(source.get("repository") or "").strip() or None,
        "branch": str(source.get("branch") or "").strip() or None,
        "pull_request": pull_request,
        "source_head": str(source.get("source_head") or "").strip() or None,
        "first_unresolved_predicate": str(source.get("first_unresolved_predicate") or "").strip() or None,
        "repositories": repositories,
        "components": components,
    }


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        validate_event(row)
        rows.append(row)
    validate_chain(rows)
    return rows


def validate_event(event: dict[str, Any]) -> None:
    if event.get("schema") != SCHEMA:
        raise ValueError("event schema mismatch")
    if event.get("event_type") not in {"CHECK_IN", "CHECK_OUT", "RETURNED", "STOPPED"}:
        raise ValueError("event_type invalid")
    if not str(event.get("task_id") or "").strip() or not str(event.get("session_id") or "").strip():
        raise ValueError("task_id/session_id required")
    parse_time(str(event.get("event_at") or ""))
    if event.get("authority_effect") != AUTHORITY_EFFECT:
        raise ValueError("event authority widening")
    expected = dict(event)
    observed = expected.pop("event_sha256", None)
    if observed != sha256_value(expected):
        raise ValueError("event hash mismatch")


def validate_chain(events: Iterable[dict[str, Any]]) -> None:
    prior: str | None = None
    for event in events:
        if event.get("predecessor_event_sha256") != prior:
            raise ValueError("event predecessor chain mismatch")
        prior = event["event_sha256"]


def build_event(request: dict[str, Any], predecessor: str | None) -> dict[str, Any]:
    event_type = str(request.get("event_type") or "").upper()
    state_map = {"CHECK_IN": "ACTIVE", "CHECK_OUT": "RETURNED", "RETURNED": "RETURNED", "STOPPED": "STOPPED"}
    if event_type not in state_map:
        raise ValueError("event_type invalid")
    disposition = request.get("registry_disposition")
    if not isinstance(disposition, dict) or disposition.get("authority_effect") != "NONE":
        raise ValueError("registry_disposition with authority_effect NONE required")
    task_id = str(request.get("task_id") or "").strip()
    if disposition.get("task_id") != task_id:
        raise ValueError("registry disposition task mismatch")
    event = {
        "schema": SCHEMA,
        "event_type": event_type,
        "task_id": task_id,
        "session_id": str(request.get("session_id") or "").strip(),
        "event_at": str(request.get("event_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
        "context": normalize_context(request.get("context")),
        "registry_disposition": str(disposition.get("disposition") or ""),
        "registry_disposition_sha256": sha256_value(disposition),
        "coordination_state": state_map[event_type],
        "predecessor_event_sha256": predecessor,
        "authority_effect": AUTHORITY_EFFECT,
    }
    if not event["session_id"]:
        raise ValueError("session_id required")
    parse_time(event["event_at"])
    event["event_sha256"] = sha256_value(event)
    return event


def append_event(path: Path, request: dict[str, Any]) -> dict[str, Any]:
    events = load_events(path)
    predecessor = events[-1]["event_sha256"] if events else None
    event = build_event(request, predecessor)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(canonical_json(event) + "\n")
    load_events(path)
    return event


def recent_collision_candidates(path: Path, *, now: datetime, task_id: str, repositories: list[str], components: list[str], window_seconds: int = RECENT_RETURN_WINDOW_SECONDS) -> list[dict[str, Any]]:
    events = load_events(path)
    latest_by_session: dict[tuple[str, str], dict[str, Any]] = {}
    for event in events:
        latest_by_session[(event["task_id"], event["session_id"])] = event
    cutoff = now.astimezone(timezone.utc).timestamp() - window_seconds
    wanted_repos, wanted_components = set(repositories), set(components)
    out: list[dict[str, Any]] = []
    for (other_task, _session), event in latest_by_session.items():
        if other_task == task_id or event.get("coordination_state") not in {"RETURNED", "STOPPED"}:
            continue
        event_ts = parse_time(event["event_at"]).timestamp()
        if event_ts < cutoff:
            continue
        context = event.get("context") or {}
        repo_overlap = sorted(wanted_repos & set(context.get("repositories") or []))
        component_overlap = sorted(wanted_components & set(context.get("components") or []))
        if repo_overlap or component_overlap:
            out.append({
                "task_id": other_task,
                "session_id": event["session_id"],
                "event_type": event["event_type"],
                "event_at": event["event_at"],
                "event_sha256": event["event_sha256"],
                "overlap": {"repositories": repo_overlap, "components": component_overlap},
                "source": "RECENT_EVENT_HISTORY",
            })
    return sorted(out, key=lambda row: (row["event_at"], row["task_id"], row["session_id"]), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--recent-for-task")
    parser.add_argument("--now")
    parser.add_argument("--repositories", default="")
    parser.add_argument("--components", default="")
    args = parser.parse_args()
    path = Path(args.ledger).expanduser().resolve()
    if args.recent_for_task:
        now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
        rows = recent_collision_candidates(
            path,
            now=now,
            task_id=args.recent_for_task,
            repositories=[x for x in args.repositories.split(",") if x],
            components=[x for x in args.components.split(",") if x],
        )
        print(json.dumps(rows, sort_keys=True))
        return 0
    request = json.load(sys.stdin)
    print(json.dumps(append_event(path, request), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
