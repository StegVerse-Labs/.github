#!/usr/bin/env python3
"""Deterministically allocate the first eligible queued task.

This script mutates only repository files in the current checkout. Atomicity is
provided by the workflow's serialized execution plus fast-forward-only push.
A rejected push is a CAS failure and causes a bounded retry by the workflow.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
CLAIMS_PATH = ROOT / "control" / "claims-active.json"
QUEUE_PATH = ROOT / "control" / "queue.json"
EVENTS_PATH = ROOT / "events" / "org-events.jsonl"
PRIORITY = {"security": 0, "release": 1, "critical": 2, "elevated": 3, "normal": 4}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def surfaces(claim: dict) -> set[tuple[str, str]]:
    scope = claim.get("scope", {})
    result: set[tuple[str, str]] = set()
    for key in ("paths", "contracts", "release_surfaces", "capabilities", "workflows"):
        for value in scope.get(key, []):
            result.add((key, value))
    return result


def conflicts(request: dict, active: dict) -> bool:
    if request["repository"]["full_name"] != active["repository"]["full_name"]:
        return False
    if "repository_exclusive" in {request["mode"], active["mode"]}:
        return True
    if request["mode"] == active["mode"] == "shared_read":
        return False
    return bool(surfaces(request) & surfaces(active))


def dependencies_complete(task: dict, tasks: dict[str, dict]) -> bool:
    return all(tasks.get(dep, {}).get("status") == "completed" for dep in task.get("dependencies", []))


def main() -> int:
    tasks = {p.stem: load(p) for p in sorted(TASKS.glob("TASK-*.json"))}
    claims_state = load(CLAIMS_PATH)
    queue_state = load(QUEUE_PATH)
    active_claims = claims_state.get("claims", [])

    queued = [t for t in tasks.values() if t.get("status") == "queued" and dependencies_complete(t, tasks)]
    queued.sort(key=lambda t: (PRIORITY.get(t.get("priority_class", "normal"), 4), t["requested_at"], t["task_id"]))
    queue_state["ordered_task_ids"] = [t["task_id"] for t in queued]

    selected = None
    for task in queued:
        mandatory = task.get("requirements", {}).get("mandatory", [])
        if all(not any(conflicts(req, held) for held in active_claims) for req in mandatory):
            selected = task
            break

    now = datetime.now(timezone.utc).replace(microsecond=0)
    if selected is not None:
        generation = int(claims_state.get("generation", 0)) + 1
        granted = []
        for request in selected["requirements"]["mandatory"]:
            claim = copy.deepcopy(request)
            claim["task_id"] = selected["task_id"]
            claim["lease"] = {
                "expires_at": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
                "heartbeat_due_at": (now + timedelta(hours=8)).isoformat().replace("+00:00", "Z"),
                "fencing_token": generation,
                "service_class": "low_contention"
            }
            granted.append(claim)
        active_claims.extend(granted)
        claims_state["claims"] = active_claims
        claims_state["generation"] = generation
        claims_state["updated_at"] = now.isoformat().replace("+00:00", "Z")
        selected["status"] = "active"
        dump(TASKS / f"{selected['task_id']}.json", selected)
        event = {
            "event_id": f"ORG-EVENT-{generation + 1:06d}",
            "event_type": "claims_granted",
            "generation": generation,
            "occurred_at": claims_state["updated_at"],
            "actor": "allocator_workflow",
            "task_id": selected["task_id"],
            "resources": [c["repository"]["full_name"] for c in granted]
        }
        with EVENTS_PATH.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    queue_state["generation"] = int(queue_state.get("generation", 0)) + 1
    queue_state["updated_at"] = now.isoformat().replace("+00:00", "Z")
    dump(CLAIMS_PATH, claims_state)
    dump(QUEUE_PATH, queue_state)
    print(json.dumps({"selected": selected and selected["task_id"], "queued": queue_state["ordered_task_ids"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
