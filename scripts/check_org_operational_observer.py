#!/usr/bin/env python3
"""Validate the StegVerse-Labs operational observer standard."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs" / "ORG_OPERATIONAL_OBSERVER_HANDOFF.md"
README = ROOT / "README.md"

REQUIRED_HANDOFF_TERMS = [
    "Org Operational Observer Handoff",
    "Current Assessment Goal",
    "Observer Standard",
    "Required Repository Inputs",
    "TV Reference Implementation",
    "Promotion Rule",
    "installed proof path != observed operational completion",
    "fresh workflow evidence + artifact evidence + receipt validation",
    "thread_archive_ready: true",
]

REQUIRED_README_TERMS = [
    "Operational Observer Standard",
    "docs/ORG_OPERATIONAL_OBSERVER_HANDOFF.md",
    "fresh workflow run",
    "expected artifacts",
    "receipt validation",
]


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def read_required(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path.relative_to(ROOT)))
    return path.read_text(encoding="utf-8")


def main() -> int:
    try:
        handoff = read_required(HANDOFF)
        readme = read_required(README)
    except FileNotFoundError as exc:
        return fail(f"missing required file: {exc}")

    errors = []
    for term in REQUIRED_HANDOFF_TERMS:
        if term not in handoff:
            errors.append(f"observer handoff missing term: {term}")

    for term in REQUIRED_README_TERMS:
        if term not in readme:
            errors.append(f"README missing observer term: {term}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("OK: org operational observer standard is installed and discoverable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
