#!/usr/bin/env python3
"""Consume an admitted dependency-resolution event and produce canonical task reevaluation proposals.

The input event must be explicitly admitted by Interlock/InTr. This consumer
never mutates WorkerCoordinator ownership, never advances HB/oscillator state,
and never directly commits the proposed registry state.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("FAIL_CLOSED: object required")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    event = load(Path(args.event))
    require(event.get("schema") == "stegverse.canonical-dependency-resolution-event/v1", "dependency event schema mismatch")
    require(event.get("state") == "INGRESS_ADMITTED", "dependency resolution must be authentically admitted")
    require(event.get("interlock_required") is True, "interlock admission evidence missing")
    require(event.get("transport_protocol") == "InTr", "InTr transport required")
    require(event.get("claim_or_fence_minted") is False, "dependency event must not mint claim/fence")
    require(event.get("authority_effect") == "DEPENDENCY_STATE_TRANSITION_ONLY", "dependency event authority effect mismatch")
    dependency_id = event.get("dependency_id")
    dependency_state = event.get("dependency_state")
    require(isinstance(dependency_id, str) and dependency_id, "dependency_id required")
    require(dependency_state in {"RESOLVED", "UNRESOLVED", "UNKNOWN"}, "dependency_state invalid")

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "reevaluate_canonical_task_dependencies.py"),
        dependency_id,
        "--state", dependency_state,
        "--registry", args.registry,
        "--output", args.output,
    ]
    completed = subprocess.run(cmd, cwd=str(ROOT), stdin=subprocess.DEVNULL, capture_output=True, text=True)
    require(completed.returncode == 0, "dependency fanout failed:" + (completed.stderr.strip() or completed.stdout.strip()))

    result = load(Path(args.output))
    result["admitted_dependency_event_ref"] = str(Path(args.event))
    result["admitted_dependency_event_id"] = event.get("event_id")
    result["dependency_transition_was_admitted"] = True
    result["registry_mutated"] = False
    result["workercoordinator_mutated"] = False
    result["heartbeat_or_oscillator_advanced"] = False
    result["authority_effect"] = "NONE_REEVALUATION_PROPOSAL_ONLY"
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": "stegverse.admitted-dependency-resolution-consumption/v1",
        "state": "DEPENDENTS_REEVALUATED_PROPOSAL_ONLY",
        "dependency_id": dependency_id,
        "affected_count": len(result.get("affected", [])),
        "output": args.output,
        "authority_effect": "NONE_REEVALUATION_PROPOSAL_ONLY"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
