#!/usr/bin/env python3
"""Invoke the bounded ERL loopback InTr submitter from the existing dispatcher."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SUBMITTER = Path("scripts/submit_erl_active_research_intr_binding.py")
INPUT_REL = Path("runtime-state/erl-active-research/intr-submission-input.json")


def parse_last_json(stdout: str) -> dict:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    raise RuntimeError("ERL submission result JSON missing")


def consume(runtime_root: Path, *, runner=subprocess.run) -> dict:
    runtime = runtime_root.expanduser().resolve()
    submitter = runtime / SUBMITTER
    if not submitter.is_file():
        return {
            "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
            "state": "SOURCE_NOT_MATERIALIZED",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    command = [sys.executable, str(submitter), "--runtime-root", str(runtime), "--input", str(INPUT_REL)]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, timeout=30)
    if completed.returncode != 0:
        raise RuntimeError("ERL loopback submission consumer failed: " + (completed.stderr or completed.stdout).strip())
    result = parse_last_json(completed.stdout)
    return {
        "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
        "state": result.get("state"),
        "submission_result": result,
        "runtime_execution_attempted": result.get("transport_submission_attempted") is True,
        "provider_operation_attempted": False,
        "authority_effect": "NONE_DISPATCH_ONLY" if result.get("transport_submission_attempted") is not True else "INGRESS_SUBMISSION_DELEGATED_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(consume(args.runtime_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
