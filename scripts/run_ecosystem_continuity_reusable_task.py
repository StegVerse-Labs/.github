#!/usr/bin/env python3
"""Invoke the already-local Healer ECE cycle from the canonical reusable-task path."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def persist_result(value: dict) -> None:
    target = os.getenv("STEGVERSE_REUSABLE_TASK_RESULT_PATH", "").strip()
    manifest_ref = os.getenv("STEGVERSE_REUSABLE_TASK_MANIFEST", "").strip()
    predicates_ref = os.getenv("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "").strip()
    if not target or not manifest_ref or not predicates_ref:
        return
    manifest = json.loads(Path(manifest_ref).read_text(encoding="utf-8"))
    predicates = json.loads(predicates_ref)
    if not isinstance(predicates, list):
        raise SystemExit("completion predicates must be a list")
    result = {
        "schema": "stegverse.reusable-task-runner-result/v1",
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": manifest["reusable_task_id"],
        "manifest_hash": manifest["manifest_hash"],
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "completion_predicates_satisfied": predicates,
        "cycle": {
            "state": value.get("state"),
            "outcome": value.get("outcome"),
            "evaluation_id": value.get("evaluation_id"),
            "sdk_diagnostic_result_sha256": value.get("sdk_diagnostic_result_sha256"),
            "site_projection_sha256": value.get("site_projection_sha256")
        },
        "authority_effect": "NONE"
    }
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    if completed.returncode == 0:
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            return 3
        value = json.loads(lines[-1])
        if value.get("state") != "COMPLETE":
            return 3
        persist_result(value)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
