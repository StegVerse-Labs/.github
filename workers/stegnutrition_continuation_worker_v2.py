#!/usr/bin/env python3
"""StegNutrition continuation worker v2 with unified zero-network proof binding."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import stegnutrition_continuation_worker as base


def _run_unified_validation(stegnutrition_root: Path) -> dict:
    script = stegnutrition_root / "scripts/run_full_validation_no_network.py"
    if not script.is_file():
        return {
            "state": "BLOCKED",
            "reason": "unified zero-network validation orchestrator is absent",
            "returncode": None,
        }
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str((stegnutrition_root / "src").resolve()),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }
    try:
        proc = subprocess.run(
            [sys.executable, str(script.resolve())],
            cwd=stegnutrition_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "state": "RETRY",
            "reason": "unified zero-network validation exceeded 300 seconds",
            "returncode": None,
        }
    tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-8000:]
    try:
        proof = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "state": "FAILED",
            "reason": "unified zero-network validator did not emit JSON",
            "returncode": proc.returncode,
            "output_tail": tail,
        }
    valid = (
        proc.returncode == 0
        and proof.get("schema") == "stegnutrition.zero-network-validation.v1"
        and proof.get("state") == "PASS"
        and proof.get("execution") == "LOCAL_ONLY"
        and proof.get("network_required") is False
        and proof.get("github_token_required") is False
        and proof.get("credential_authority") == "TV/TVC"
        and proof.get("authority_effect") == "NONE"
        and isinstance(proof.get("runtime_custody"), dict)
        and proof["runtime_custody"].get("state") == "PASS"
        and isinstance(proof.get("scenario_provider"), dict)
        and proof["scenario_provider"].get("state") == "PASS"
        and isinstance(proof.get("full_suite"), dict)
        and proof["full_suite"].get("state") == "PASS"
    )
    return {
        "state": "COMPLETE" if valid else "FAILED",
        "reason": "unified zero-network validation passed" if valid else "unified zero-network validation failed contract",
        "returncode": proc.returncode,
        "output_tail": tail,
        "validation_proof": proof,
    }


def main() -> int:
    base._run_full_suite = _run_unified_validation
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
