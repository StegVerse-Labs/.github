#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ORG_COMPLETION_DASHBOARD.md"

REQUIRED = [
    "StegVerse-Labs Completion Dashboard",
    "Dashboard Status",
    "Installed Organization Sources",
    "Source Of Truth Map",
    "Missing Organization Modules",
    "Promotion Rule",
    "thread_archive_ready: true",
]

if not DOC.exists():
    print("missing dashboard", file=sys.stderr)
    raise SystemExit(1)

text = DOC.read_text(encoding="utf-8")
missing = [item for item in REQUIRED if item not in text]
if missing:
    for item in missing:
        print(f"missing: {item}", file=sys.stderr)
    raise SystemExit(1)

print("OK: org completion dashboard is valid.")
