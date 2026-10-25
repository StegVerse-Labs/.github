#!/usr/bin/env python3
"""Planner admission predicate: a registration's parent goal must be registered.

Gap REGISTRATION_PARENT_EXISTENCE_NOT_CHECKED (StegVerse-Labs/.github#3195):
``scripts/canonical_task_registration_transition.py`` returned ALLOW for a
NEW_IDENTITY child whose ``parent_task_id`` was not a task on the canonical
Registry. This module is the missing predicate. The planner's derivation, used
by ``plan``, ``apply`` and ``verify`` alike, calls it at one hook point in two
steps: ``require_registry_readable`` before the planner reads the Registry, and
``check`` right after the planner's own generation-tip and identity-uniqueness
predicates, so their refusals keep precedence.

Rule. For the manifest record:

* ``parent_task_id``: when not null, it must name a task row of
  ``data/canonical-task-registry.json`` read from the predecessor tree. A task
  cannot be its own parent; the identity being registered is not on the
  predecessor Registry yet.
* ``root_correlation_id``: when not null and not the task's own id (a root
  goal correlates to itself), it must also name a registered task row.

The Registry is the one the planner already holds to
``observed_registry_generation`` (REGISTRY_GENERATION_NOT_OBSERVED_TIP), so a
parent resolved here is resolved at that generation.

Refusals (FAIL_CLOSED; the planner's receipt carries the six standard fields):

* REGISTRATION_PARENT_NOT_REGISTERED: the parent or root does not resolve.
* REGISTRATION_PARENT_REGISTRY_UNREADABLE: the Registry cannot be read or
  has no usable ``tasks`` rows. It never passes silently.

Read-only and stdlib only: the Registry is opened for reading and never
written. No clock, network, polling or dispatch. Authority: none; this module
only refuses.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

REGISTRY = "data/canonical-task-registry.json"
NOT_REGISTERED = "REGISTRATION_PARENT_NOT_REGISTERED"
REGISTRY_UNREADABLE = "REGISTRATION_PARENT_REGISTRY_UNREADABLE"
PREDICATES = (NOT_REGISTERED, REGISTRY_UNREADABLE)


class ParentExistenceRefusal(Exception):
    """Raised when ``check`` is called without the planner's refusal type."""

    def __init__(self, predicate: str, detail: str, repair: str):
        super().__init__(f"{predicate}: {detail}")
        self.predicate, self.detail, self.repair = predicate, detail, repair


def registered_task_ids(root: Path) -> tuple[set[str], Any]:
    """Return the task ids on the predecessor Registry and its generation.

    Raises ParentExistenceRefusal(REGISTRY_UNREADABLE) when the Registry cannot
    be read or parsed or has no list of task rows.
    """
    path = Path(root) / REGISTRY
    repair = (f"restore a readable {REGISTRY} with a 'tasks' list on the predecessor tree, "
              "then re-run the plan; parent existence is never assumed")
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ParentExistenceRefusal(REGISTRY_UNREADABLE, f"{REGISTRY} not readable: {type(exc).__name__}: {exc}",
                                     repair) from exc
    rows = registry.get("tasks") if isinstance(registry, dict) else None
    if not isinstance(rows, list):
        raise ParentExistenceRefusal(REGISTRY_UNREADABLE, f"{REGISTRY} has no 'tasks' list", repair)
    ids = {row["task_id"] for row in rows if isinstance(row, dict) and isinstance(row.get("task_id"), str)}
    return ids, registry.get("generation")


def unresolved(request: Any, ids: set[str]) -> list[str]:
    """Return a description of every parent or root reference that does not resolve."""
    record = request.get("record") if isinstance(request, dict) else None
    if not isinstance(record, dict):
        return []  # nothing declared to resolve; the record schema predicate owns a malformed record
    task_id = request.get("task_id")
    missing: list[str] = []
    for field in ("parent_task_id", "root_correlation_id"):
        ref = record.get(field)
        if ref is None:
            continue
        if field == "root_correlation_id" and ref == task_id:
            continue  # a root goal correlates to itself
        if not isinstance(ref, str) or not ref:
            missing.append(f"record.{field}={ref!r} is not a task id")
        elif ref == task_id:
            missing.append(f"record.{field}={ref!r} names the task being registered")
        elif ref not in ids:
            missing.append(f"record.{field}={ref!r} is not a task on {REGISTRY}")
    return missing


def require_registry_readable(root: Path, refusal: Callable[[str, str, str], Exception] = ParentExistenceRefusal) -> None:
    """Refuse (raise ``refusal``) unless the predecessor Registry can be read; called before the planner reads it."""
    try:
        registered_task_ids(root)
    except ParentExistenceRefusal as exc:
        raise refusal(exc.predicate, exc.detail, exc.repair) from exc


def check(root: Path, request: Any, refusal: Callable[[str, str, str], Exception] = ParentExistenceRefusal) -> None:
    """Refuse (raise ``refusal(predicate, detail, repair)``) unless every parent resolves."""
    try:
        ids, generation = registered_task_ids(root)
    except ParentExistenceRefusal as exc:
        raise refusal(exc.predicate, exc.detail, exc.repair) from exc
    missing = unresolved(request, ids)
    if missing:
        raise refusal(
            NOT_REGISTERED,
            "; ".join(missing) + f" (predecessor registry generation {generation!r})",
            "register the parent goal first (its own registration request through this transition), "
            "or set parent_task_id/root_correlation_id to a task already on the Registry; "
            "then re-plan against the new generation",
        )
