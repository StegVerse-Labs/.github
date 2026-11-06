#!/usr/bin/env python3
"""Validate exact repository -> component pairings in canonical task records.

``targets.repositories`` and ``targets.components`` are flat lists, so read alone they
put every repository x component pair in scope. A record that owns specific pairs
declares ``targets.repository_components`` (repository -> its components); then:

* its keys equal ``targets.repositories``;
* every value is a non-empty list of strings, without duplicates;
* the values partition ``targets.components``: each component under exactly one repository;
* ``pair_in_scope`` admits only the listed pairs.

A record without the field is not judged here. Exits 0 with a PASS line, or 1 with
FAIL_CLOSED lines naming each record and defect. Reads committed files only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "canonical-task-records"
FIELD = "repository_components"


def defects(record: dict[str, Any]) -> list[str]:
    targets = record.get("targets") or {}
    if FIELD not in targets:
        return []
    mapping = targets[FIELD]
    if not isinstance(mapping, dict):
        return [f"targets.{FIELD} is an object"]
    found = []
    if set(mapping) != set(targets.get("repositories") or []):
        found.append(f"targets.{FIELD} keys equal targets.repositories")
    seen: dict[str, str] = {}
    for repository, components in mapping.items():
        if not (isinstance(components, list) and components and all(isinstance(c, str) and c for c in components)):
            found.append(f"targets.{FIELD}[{repository}] is a non-empty list of strings")
            continue
        for component in components:
            if component in seen:
                found.append(f"component {component} is listed under one repository only "
                             f"({seen[component]} and {repository})")
            seen[component] = repository
    if sorted(seen) != sorted(set(targets.get("components") or [])) or \
            len(targets.get("components") or []) != len(set(targets.get("components") or [])):
        found.append(f"targets.{FIELD} values partition targets.components")
    return found


def pair_in_scope(record: dict[str, Any], repository: str, component: str) -> bool:
    """True only for a declared pair; without the field, the flat lists' cross product."""
    targets = record.get("targets") or {}
    if FIELD in targets:
        return component in (targets[FIELD].get(repository) or [])
    return repository in (targets.get("repositories") or []) and component in (targets.get("components") or [])


def main() -> int:
    failures, checked = [], 0
    for path in sorted(RECORDS.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if FIELD in (record.get("targets") or {}):
            checked += 1
            failures += [f"FAIL_CLOSED {path.name}: {defect}" for defect in defects(record)]
    if failures:
        print("\n".join(failures))
        return 1
    print(f"TARGET_REPOSITORY_COMPONENTS_PASS records_with_mapping={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
