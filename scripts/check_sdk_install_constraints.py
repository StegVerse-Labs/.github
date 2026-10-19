#!/usr/bin/env python3
"""Every workflow step that pip-installs the StegVerse SDK pins its transitive set.

A step installs the SDK when a ``pip install`` line names the SDK (a ``StegVerse-SDK``
URL or a ``stegverse-sdk`` path). Such a step must, before that line:

* fix the commit as ``SDK_SHA=<40 hex>`` and fetch ``StegVerse-SDK/archive/${SDK_SHA}``;
* set ``PIP_CONSTRAINT`` to ``constraints/sdk-install.txt`` of that same commit: the file
  inside the directory the archive is extracted to, or the raw file at ``${SDK_SHA}`` or
  at the literal SHA.

Reads workflow text only (no YAML library, network or clock). Exits 0 with a PASS line
naming the steps checked, or 1 with FAIL_CLOSED lines.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
STEP = re.compile(r"^\s*- (?:name|uses|run):", re.M)
SDK_INSTALL = re.compile(r"pip install\b[^\n]*(StegVerse-SDK|stegverse-sdk)", re.I)
SHA = re.compile(r"\bSDK_SHA=([0-9a-f]{40})\b")
EXTRACT = re.compile(r"tar -xzf \S*\s+-C\s+(\S+)")
RAW = "https://raw.githubusercontent.com/StegVerse-org/StegVerse-SDK/{}/constraints/sdk-install.txt"


def steps(text: str) -> list[str]:
    starts = [m.start() for m in STEP.finditer(text)] + [len(text)]
    return [text[a:b] for a, b in zip(starts, starts[1:])]


def step_defects(step: str) -> list[str]:
    install = SDK_INSTALL.search(step)
    if not install:
        return []
    before = step[:install.start()]
    sha = SHA.search(before)
    if not sha:
        return ["the SDK commit is fixed as SDK_SHA=<40 hex> before the install"]
    if "StegVerse-SDK/archive/${SDK_SHA}" not in before:
        return ["the installed archive is StegVerse-SDK/archive/${SDK_SHA}"]
    allowed = {RAW.format("${SDK_SHA}"), RAW.format(sha.group(1))}
    allowed |= {f"{d.rstrip('/')}/constraints/sdk-install.txt" for d in EXTRACT.findall(before)}
    constraint = re.findall(r"PIP_CONSTRAINT=\"?([^\s\"]+)", before)
    if not constraint:
        return ["PIP_CONSTRAINT is set before the SDK install"]
    if constraint[-1] not in allowed:
        return [f"PIP_CONSTRAINT {constraint[-1]} is constraints/sdk-install.txt at the installed commit"]
    return []


def check(root: Path = WORKFLOWS) -> tuple[int, list[str]]:
    checked, failures = 0, []
    for path in sorted(root.glob("*.y*ml")):
        for step in steps(path.read_text(encoding="utf-8")):
            if SDK_INSTALL.search(step):
                checked += 1
                failures += [f"FAIL_CLOSED {path.name}: {d}" for d in step_defects(step)]
    return checked, failures


def main() -> int:
    checked, failures = check()
    if failures or not checked:
        print("\n".join(failures or ["FAIL_CLOSED: no SDK install step found; the guard would be vacuous"]))
        return 1
    print(f"SDK_INSTALL_CONSTRAINTS_PASS steps={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
