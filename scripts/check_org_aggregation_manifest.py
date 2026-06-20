#!/usr/bin/env python3
"""Validate the org aggregation manifest structure."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ORG_AGGREGATION_MANIFEST.md"

REQUIRED = [
    "StegVerse-Labs Aggregation Manifest",
    "Aggregation State",
    "Known Validator Targets",
    "Known Observation Targets",
    "Promotion Rule",
    "thread_archive_ready: true",
    "StegVerse-Labs/.github",
    "StegVerse-Labs/stegfin-governance",
    "StegVerse-Labs/crypto-bot",
    "StegVerse-Labs/TV",
    "StegVerse-Labs/StegCore",
]

if not DOC.exists():
    print("missing aggregation manifest", file=sys.stderr)
    raise SystemExit(1)

text = DOC.read_text(encoding="utf-8")
missing = [item for item in REQUIRED if item not in text]
if missing:
    for item in missing:
        print(f"missing: {item}", file=sys.stderr)
    raise SystemExit(1)

print("OK: org aggregation manifest is valid.")
