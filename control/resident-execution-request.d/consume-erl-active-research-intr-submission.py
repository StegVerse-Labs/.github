#!/usr/bin/env python3
"""Invoke the bounded resident-local ERL loopback InTr submitter from the existing dispatcher."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SUBMITTER = Path("scripts/submit_erl_active_research_intr_binding_local.py")
MATERIALIZER = Path("scripts/materialize_erl_active_research_intr_resident_local_input.py")
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


def run_json(command: list[str], runtime: Path, *, runner=subprocess.run, timeout: int = 30) -> dict:
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError("ERL loopback submission consumer failed: " + (completed.stderr or completed.stdout).strip())
    return parse_last_json(completed.stdout)


def consume(runtime_root: Path, *, runner=subprocess.run) -> dict:
    runtime = runtime_root.expanduser().resolve()
    submitter = runtime / SUBMITTER
    materializer = runtime / MATERIALIZER
    if not submitter.is_file() or not materializer.is_file():
        return {
            "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
            "state": "SOURCE_NOT_MATERIALIZED",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE_WAIT_STATE",
        }
    input_path = runtime / INPUT_REL
    input_materialization = None
    if not input_path.is_file():
        input_materialization = run_json(
            [sys.executable, str(materializer), "--runtime-root", str(runtime)],
            runtime,
            runner=runner,
        )
        if input_materialization.get("input_materialized") is not True:
            return {
                "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
                "state": input_materialization.get("state"),
                "input_materialization": input_materialization,
                "runtime_execution_attempted": False,
                "transport_submission_attempted": False,
                "provider_operation_attempted": False,
                "authority_effect": "NONE_WAIT_STATE",
            }
    result = run_json(
        [sys.executable, str(submitter), "--runtime-root", str(runtime), "--input", str(INPUT_REL)],
        runtime,
        runner=runner,
    )
    return {
        "schema": "stegverse.erl-active-research-intr-submission-dispatch/v1",
        "state": result.get("state"),
        "input_materialization": input_materialization,
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
