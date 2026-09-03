#!/usr/bin/env python3
"""Deterministically allocate the first eligible queued task.

This script mutates only repository files in the current checkout. Atomicity is
provided by the workflow's serialized execution plus fast-forward-only push.
A rejected push is a CAS failure and causes a bounded retry by the workflow.

Repository-local scopes and repository-independent dependency surfaces are
separate. Two tasks in different repositories may still conflict when both
mutate the same external/runtime/deployment/dependency surface.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
CLAIMS_PATH = ROOT / "control" / "claims-active.json"
QUEUE_PATH = ROOT / "control" / "queue.json"
EVENTS_PATH = ROOT / "events" / "org-events.jsonl"
LOCK_PATH = ROOT / "control" / "claims-allocator.lock"
PRIORITY = {"security": 0, "release": 1, "critical": 2, "elevated": 3, "normal": 4}
MUTABLE_MODES = {"shared_write", "scoped_exclusive", "repository_exclusive"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def surfaces(claim: dict) -> set[tuple[str, str]]:
    """Return repository-local claim surfaces."""
    scope = claim.get("scope", {})
    result: set[tuple[str, str]] = set()
    for key in ("paths", "contracts", "release_surfaces", "capabilities", "workflows"):
        for value in scope.get(key, []):
            result.add((key, value))
    return result


def dependency_surfaces(claim: dict) -> set[str]:
    """Return normalized repository-independent dependency/work surfaces."""
    scope = claim.get("scope", {})
    return {
        str(value).strip().lower()
        for value in scope.get("dependency_surfaces", [])
        if str(value).strip()
    }


def dependency_declaration_present(claim: dict) -> bool:
    """Mutable claims must declare global surfaces or an explicit exemption."""
    if claim.get("mode") not in MUTABLE_MODES:
        return True
    scope = claim.get("scope", {})
    return bool(dependency_surfaces(claim)) or bool(str(scope.get("dependency_surface_exempt", "")).strip())


def conflicts(request: dict, active: dict) -> bool:
    """Return True when two claims cannot safely execute concurrently.

    Global dependency surfaces are checked before repository identity. This is
    the cross-repository collision gate that prevents adjacent tasks from both
    acquiring a shared external/runtime surface such as ``hosting:render``.
    """
    if request.get("mode") == active.get("mode") == "shared_read":
        return False

    shared_dependencies = dependency_surfaces(request) & dependency_surfaces(active)
    if shared_dependencies and (request.get("mode") in MUTABLE_MODES or active.get("mode") in MUTABLE_MODES):
        return True

    if request["repository"]["full_name"] != active["repository"]["full_name"]:
        return False
    if "repository_exclusive" in {request["mode"], active["mode"]}:
        return True
    if request["mode"] == active["mode"] == "shared_read":
        return False
    return bool(surfaces(request) & surfaces(active))


def dependencies_complete(task: dict, tasks: dict[str, dict]) -> bool:
    return all(tasks.get(dep, {}).get("status") == "completed" for dep in task.get("dependencies", []))


def task_claims_admissible(task: dict) -> bool:
    mandatory = task.get("requirements", {}).get("mandatory", [])
    return bool(mandatory) and all(dependency_declaration_present(request) for request in mandatory)



def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def acquire_allocator_lock(path: Path = LOCK_PATH) -> dict:
    """Acquire the deployment-local allocator serialization fence.

    The fence grants no task authority. It only prevents two resident dispatchers
    from mutating claim generation/state concurrently. A dead local owner may be
    recovered; a live owner causes this invocation to return ALLOCATOR_BUSY.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        body = {
            "schema": "stegverse.org-allocator-lock/v1",
            "owner_pid": os.getpid(),
            "state": "LOCKED",
            "authority_effect": "NONE_SERIALIZATION_ONLY",
        }
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            try:
                existing = load(path)
            except Exception:
                existing = {}
            owner_pid = int(existing.get("owner_pid") or 0)
            if owner_pid and _process_alive(owner_pid):
                return {
                    "acquired": False,
                    "state": "ALLOCATOR_BUSY",
                    "owner_pid": owner_pid,
                    "authority_effect": "NONE_SERIALIZATION_ONLY",
                }
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        else:
            try:
                os.write(fd, (json.dumps(body, sort_keys=True) + "\n").encode("utf-8"))
            finally:
                os.close(fd)
            return {"acquired": True, **body}
    raise RuntimeError("unable to acquire organization allocator lock")


def release_allocator_lock(path: Path = LOCK_PATH) -> None:
    if not path.is_file():
        return
    try:
        existing = load(path)
    except Exception:
        return
    if int(existing.get("owner_pid") or 0) == os.getpid():
        try:
            path.unlink()
        except FileNotFoundError:
            pass

def main() -> int:
    lock = acquire_allocator_lock()
    if not lock.get("acquired"):
        print(json.dumps({
            "selected": None,
            "queued": [],
            "blocked_missing_dependency_declaration": [],
            "state": "ALLOCATOR_BUSY",
            "allocator_lock_owner_pid": lock.get("owner_pid"),
            "authority_effect": "NONE_SERIALIZATION_ONLY",
        }))
        return 0
    try:
        return _main_locked()
    finally:
        release_allocator_lock()


def _main_locked() -> int:
    tasks = {p.stem: load(p) for p in sorted(TASKS.glob("TASK-*.json"))}
    claims_state = load(CLAIMS_PATH)
    queue_state = load(QUEUE_PATH)
    active_claims = claims_state.get("claims", [])

    queued = [t for t in tasks.values() if t.get("status") == "queued" and dependencies_complete(t, tasks)]
    queued.sort(key=lambda t: (PRIORITY.get(t.get("priority_class", "normal"), 4), t["requested_at"], t["task_id"]))
    queue_state["ordered_task_ids"] = [t["task_id"] for t in queued]

    selected = None
    blocked_missing_dependency_declaration: list[str] = []
    for task in queued:
        if not task_claims_admissible(task):
            blocked_missing_dependency_declaration.append(task["task_id"])
            continue
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
            "actor": "canonical_org_allocator",
            "task_id": selected["task_id"],
            "resources": [c["repository"]["full_name"] for c in granted],
            "dependency_surfaces": sorted({surface for c in granted for surface in dependency_surfaces(c)})
        }
        with EVENTS_PATH.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    queue_state["generation"] = int(queue_state.get("generation", 0)) + 1
    queue_state["updated_at"] = now.isoformat().replace("+00:00", "Z")
    queue_state["blocked_missing_dependency_declaration"] = blocked_missing_dependency_declaration
    dump(CLAIMS_PATH, claims_state)
    dump(QUEUE_PATH, queue_state)
    print(json.dumps({
        "selected": selected and selected["task_id"],
        "queued": queue_state["ordered_task_ids"],
        "blocked_missing_dependency_declaration": blocked_missing_dependency_declaration,
        "state": "ALLOCATION_COMPLETE",
        "authority_effect": "CLAIM_AUTHORITY_ONLY_WHEN_SELECTED_BY_CANONICAL_ALLOCATOR",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
