#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "HEARTBEAT-OSCILLATOR-RESIDENT-START-012"
REQUIRED_CAPS = {"heartbeat_runtime_start", "native_process_supervision", "bounded_repository_mutation"}


def _load_installer():
    path = ROOT / "scripts" / "install_sovereign_heartbeat_service.py"
    spec = importlib.util.spec_from_file_location("install_sovereign_heartbeat_service", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load canonical sovereign heartbeat installer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _response(state: str, transition_id: str, sequence: int, *, blocker=None, evidence_refs=None):
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition_id,
        "transition_sequence": sequence,
        "expected_next_transition": "NONE_TERMINAL" if state == "COMPLETED" else "SOVEREIGN_HEARTBEAT_STARTED",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": "receipts/sovereign-host/activation.latest.json",
        "evidence_refs": evidence_refs or [],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 0,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "resident_heartbeat_start",
        },
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if task.get("task_id") != EXPECTED_TASK:
        return 3
    required = set((handoff.get("execution") or {}).get("required_capabilities") or [])
    if required != REQUIRED_CAPS:
        return 4
    if not isinstance(task.get("claim_id"), str):
        return 5
    fence = (task.get("assignment_timer") or {}).get("fencing_token")
    if fence is None:
        fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(fence, int):
        return 6
    sequence = int((task.get("heartbeat_timing") or {}).get("transition_sequence", 0)) + 1

    try:
        installer = _load_installer()
        target = installer.default_runtime_root()
        receipt = installer.install(ROOT, target)
        if receipt.get("canonical_runtime") != "heartbeat_runtime.engine_v13.HeartbeatRuntime":
            raise RuntimeError("installer did not bind canonical v13 carrier")
        if receipt.get("heartbeat_production_mode") != "OSCILLATOR_PHASE_DRIVEN":
            raise RuntimeError("installer did not bind oscillator phase-driven production")
        if receipt.get("heartbeat_progression_dependency") != "OSCILLATOR_ONLY":
            raise RuntimeError("installer did not preserve oscillator-only progression")
        if receipt.get("heartbeat_period_ms") != 10.0:
            raise RuntimeError("resident carrier period is not 10 ms")
        if receipt.get("heartbeat_grants_execution_authority") is not False:
            raise RuntimeError("carrier incorrectly grants execution authority")
        if receipt.get("github_runtime_dependency") is not False:
            raise RuntimeError("GitHub runtime dependency is not allowed")
        if receipt.get("credential_requirement") != "NONE":
            raise RuntimeError("resident heartbeat startup unexpectedly requires credentials")
        if receipt.get("carrier_active") is not True:
            raise RuntimeError("native carrier process did not become active")
    except Exception as exc:
        blocker = {
            "dependency_class": "RESIDENT_PROCESS_HOST",
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "START_CANONICAL_NATIVE_CARRIER_ON_ADMITTED_RESIDENT_HOST",
            "machine_observable_release_condition": "activation.latest.json records carrier_active=true for canonical engine_v13 oscillator phase-driven service",
            "github_token_required": False,
            "third_party_blocker": False,
        }
        json.dump(_response("BLOCKED", "SOVEREIGN_HEARTBEAT_START_BLOCKED", sequence, blocker=blocker), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    evidence = [
        "scripts/install_sovereign_heartbeat_service.py",
        "heartbeat_runtime/oscillator_producer.py",
        "heartbeat_runtime/engine_v13.py",
        "receipts/sovereign-host/activation.latest.json",
    ]
    json.dump(_response("COMPLETED", "SOVEREIGN_HEARTBEAT_STARTED", sequence, evidence_refs=evidence), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
