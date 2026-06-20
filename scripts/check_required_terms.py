#!/usr/bin/env python3
"""Check that a document contains all required terms listed in a plain text file."""

from pathlib import Path
import sys


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 3:
        return fail("usage: check_required_terms.py <document> <terms-file>")

    document = Path(sys.argv[1])
    terms_file = Path(sys.argv[2])

    if not document.exists():
        return fail(f"missing document: {document}")
    if not terms_file.exists():
        return fail(f"missing terms file: {terms_file}")

    text = document.read_text(encoding="utf-8")
    terms = [
        line.strip()
        for line in terms_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    missing = [term for term in terms if term not in text]
    if missing:
        for term in missing:
            print(f"missing: {term}", file=sys.stderr)
        return 1

    print(f"OK: {document} contains {len(terms)} required terms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
