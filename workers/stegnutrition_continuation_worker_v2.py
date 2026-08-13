#!/usr/bin/env python3
"""StegNutrition continuation worker v2 with unified zero-network proof binding."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import stegnutrition_continuation_worker as base


def _local_env(stegnutrition_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str((stegnutrition_root / "src").resolve()),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
    }


def _run_real_data_candidate(stegnutrition_root: Path) -> dict:
    script = stegnutrition_root / "scripts/run_real_data_qualification_no_network.py"
    if not script.is_file():
        return {
            "state": "FAILED",
            "reason": "real-data qualification candidate runner is absent",
            "returncode": None,
        }
    try:
        proc = subprocess.run(
            [sys.executable, str(script.resolve())],
            cwd=stegnutrition_root,
            env=_local_env(stegnutrition_root),
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "state": "RETRY",
            "reason": "real-data qualification candidate runner exceeded 120 seconds",
            "returncode": None,
        }
    tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-8000:]
    try:
        proof = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "state": "FAILED",
            "reason": "real-data qualification candidate runner did not emit JSON",
            "returncode": proc.returncode,
            "output_tail": tail,
        }
    valid_shape = (
        proc.returncode == 0
        and proof.get("schema") == "stegnutrition.real-data-qualification-candidate.v1"
        and proof.get("execution") == "LOCAL_ONLY"
        and proof.get("network_required") is False
        and proof.get("github_token_required") is False
        and proof.get("credential_authority") == "TV/TVC"
        and proof.get("authority_effect") == "NONE"
        and proof.get("state") in {
            "ACTIVE_WAITING_FOR_REAL_EVIDENCE",
            "PARTIAL_CANDIDATE_QUALIFIED",
            "CANDIDATES_QUALIFIED",
        }
    )
    return {
        "state": "COMPLETE" if valid_shape else "FAILED",
        "reason": "real-data qualification candidate projection completed" if valid_shape else "real-data qualification candidate contract failed",
        "returncode": proc.returncode,
        "output_tail": tail,
        "candidate_proof": proof,
    }


def _run_unified_validation(stegnutrition_root: Path) -> dict:
    script = stegnutrition_root / "scripts/run_full_validation_no_network.py"
    if not script.is_file():
        return {
            "state": "FAILED",
            "reason": "unified zero-network validation orchestrator is absent",
            "returncode": None,
        }
    try:
        proc = subprocess.run(
            [sys.executable, str(script.resolve())],
            cwd=stegnutrition_root,
            env=_local_env(stegnutrition_root),
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
    candidate = _run_real_data_candidate(stegnutrition_root) if valid else {
        "state": "FAILED",
        "reason": "real-data candidate projection requires unified validation PASS",
        "returncode": None,
    }
    return {
        "state": "COMPLETE" if valid and candidate.get("state") == "COMPLETE" else "FAILED",
        "reason": (
            "unified zero-network validation and real-data candidate projection completed"
            if valid and candidate.get("state") == "COMPLETE"
            else "unified validation or real-data candidate projection failed contract"
        ),
        "returncode": proc.returncode,
        "output_tail": tail,
        "validation_proof": proof,
        "real_data_qualification": candidate,
    }


def main() -> int:
    base._run_full_suite = _run_unified_validation
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
