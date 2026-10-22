#!/usr/bin/env python3
"""Every workflow call into StegVerse-SDK pins the SDK at a full 40-hex commit (V-P6).

A ``uses: StegVerse-org/StegVerse-SDK/<path>@<ref>`` line, job-level (reusable workflow)
or step-level (action), must name ``<ref>`` as a 40-hex commit. A branch, a tag or an
abbreviated sha moves or is ambiguous, and the SDK's route installer refuses an
abbreviated ``sdk_ref``. When the call passes ``sdk_ref`` in its ``with:`` block, that
value must be the same commit.

Reads workflow text only (no YAML library, network or clock). Exits 0 with a PASS line
naming the calls checked (zero is a pass: no call is unpinned), or 1 with one six-field
FAIL_CLOSED record per defect.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
USES = re.compile(r"^(\s*)(?:-\s+)?uses:\s*[\"']?StegVerse-org/StegVerse-SDK(?:/[^@\s\"']*)?@([^\s\"'#]*)", re.I)
SDK_REF = re.compile(r"^\s*sdk_ref:\s*[\"']?([^\s\"'#]*)")
FULL_SHA = re.compile(r"[0-9a-f]{40}")


def defect(path: Path, line: int, predicate: str, repair: str) -> dict:
    return {
        "failure_code": "SDK_WORKFLOW_REF_NOT_FULL_COMMIT",
        "failed_predicate": f"{path.name}:{line}: {predicate}",
        "required_evidence_or_repair": repair,
        "retry_entrypoint": "python scripts/check_sdk_reusable_workflow_pins.py",
        "owning_existing_goal": "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001",
        "next_attempt": "on the next push that pins the ref",
    }


def call_block(lines: list[str], start: int, column: int) -> list[tuple[int, str]]:
    """The lines after a uses: line that belong to the same job or step: those indented
    at least as far as the uses: key itself (its sibling with:, and what is under it)."""
    block = []
    for number in range(start + 1, len(lines)):
        text = lines[number]
        if text.strip() and len(text) - len(text.lstrip()) < column:
            break
        block.append((number, text))
    return block


def check(root: Path = WORKFLOWS) -> tuple[int, list[dict]]:
    checked, failures = 0, []
    for path in sorted(root.glob("*.y*ml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, text in enumerate(lines):
            match = USES.match(text)
            if not match:
                continue
            checked += 1
            ref = match.group(2)
            if not FULL_SHA.fullmatch(ref):
                failures.append(defect(
                    path, index + 1, f"uses: StegVerse-SDK ref {ref or '<none>'!r} is a 40-hex commit",
                    "pin the ref to the full 40-hex StegVerse-SDK commit it resolves to "
                    "(git ls-remote https://github.com/StegVerse-org/StegVerse-SDK.git <ref>)"))
                continue
            for number, line in call_block(lines, index, text.index("uses:")):
                sdk_ref = SDK_REF.match(line)
                if sdk_ref and sdk_ref.group(1) != ref:
                    failures.append(defect(
                        path, number + 1, f"sdk_ref {sdk_ref.group(1)!r} equals the uses: commit {ref}",
                        "set sdk_ref to the same 40-hex commit as the uses: ref"))
    return checked, failures


def main(root: Path | None = None) -> int:
    checked, failures = check(root or WORKFLOWS)
    if failures:
        for failure in failures:
            print("FAIL_CLOSED " + json.dumps(failure, sort_keys=True))
        return 1
    print(f"SDK_WORKFLOW_PINS_PASS calls={checked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
