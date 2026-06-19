#!/usr/bin/env python3
"""Validate org repository inventory structure."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "ORG_REPOSITORY_INVENTORY.md"

REQUIRED_TERMS = [
    "StegVerse-Labs Repository Inventory",
    "inventory_state: initial_repository_inventory_installed",
    "Known Handoff Inventory",
    "Known Access Or Search Notes",
    "Known Remaining Files Or Modules To Install",
    "Promotion Rule",
    "Repository-local handoff present != repository completion",
    "thread_archive_ready: true",
]

MINIMUM_REPO_MARKERS = [
    "Site",
    "StegCore",
    "TV",
    "Continuity",
    "stegfin-governance",
    "crypto-bot",
]


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not INVENTORY.exists():
        return fail("missing docs/ORG_REPOSITORY_INVENTORY.md")

    text = INVENTORY.read_text(encoding="utf-8")
    errors = []

    for term in REQUIRED_TERMS:
        if term not in text:
            errors.append(f"inventory missing required term: {term}")

    for marker in MINIMUM_REPO_MARKERS:
        if marker not in text:
            errors.append(f"inventory missing repository marker: {marker}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("OK: org repository inventory structure is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
