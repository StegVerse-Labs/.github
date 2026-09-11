#!/usr/bin/env python3
"""Invoke the already-local Healer ECE cycle from the canonical reusable-task path."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    raw = os.getenv("STEGVERSE_REPO_ROOTS_JSON", "").strip()
    runtime = os.getenv("STEGVERSE_HEARTBEAT_ROOT", "").strip()
    if not raw or not runtime:
        print(json.dumps({"state":"BLOCKED","outcome":"ECE_REUSABLE_RUNTIME_BINDING_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    roots = json.loads(raw)
    if not isinstance(roots, dict):
        raise SystemExit("STEGVERSE_REPO_ROOTS_JSON must be an object")
    healer_raw = roots.get("StegVerse-Labs/StegVerse-Healer")
    if not isinstance(healer_raw, str) or not healer_raw:
        print(json.dumps({"state":"BLOCKED","outcome":"ECE_HEALER_LOCAL_SOURCE_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    healer_root = Path(healer_raw).expanduser().resolve()
    runner = healer_root / "app" / "run_ece_periodic_evaluation.py"
    if not runner.is_file():
        print(json.dumps({"state":"BLOCKED","outcome":"ECE_HEALER_CYCLE_RUNNER_MISSING","authority_effect":"NONE"}, sort_keys=True))
        return 3
    completed = subprocess.run(
        [sys.executable, str(runner)],
        cwd=healer_root,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
