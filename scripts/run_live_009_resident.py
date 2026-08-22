#!/usr/bin/env python3
"""Resident-only launcher for HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.

This script performs only real local execution: carrier-only native activation,
then the handoff-authorized worker(1) -> carrier(1) -> worker(1) sequence. It
fails closed unless persisted runtime evidence proves the canonical 10 ms /
100 Hz OSCILLATOR_ONLY carrier and terminal LIVE-009 completion.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TASK_ID = "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009"
TERMINAL = "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def run(command: list[str], root: Path) -> None:
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")


def require_runtime_evidence(root: Path) -> None:
    activation = load_json(root / "receipts/sovereign-host/carrier-activation.latest.json")
    required_activation = {
        "carrier_active": True,
        "activation_scope": "CARRIER_ONLY",
        "canonical_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_period_ms": 10.0,
        "heartbeat_reference_frequency_hz": 100.0,
        "network_fetch_required": False,
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "third_party_deployment_required": False,
        "github_runtime_dependency": False,
        "credential_requirement": "NONE",
    }
    for key, expected in required_activation.items():
        if activation.get(key) != expected:
            raise RuntimeError(f"activation evidence mismatch: {key}")

    carrier = load_json(root / "control/heartbeat-carrier-runtime-state.json")
    oscillator = carrier.get("oscillator") or {}
    if carrier.get("frequency_rule") != "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL":
        raise RuntimeError("carrier frequency rule is not oscillator-only")
    if oscillator.get("progression_dependency") != "OSCILLATOR_ONLY":
        raise RuntimeError("carrier progression dependency mismatch")
    if oscillator.get("phase_travel_time_ms") != 10:
        raise RuntimeError("carrier phase travel is not 10 ms")
    if oscillator.get("reference_frequency_hz") != 100:
        raise RuntimeError("carrier reference rate is not 100 Hz")
    if oscillator.get("snapshot_is_observation_only") is not True:
        raise RuntimeError("carrier snapshot is not observation-only")

    observation = load_json(root / "control/heartbeat-carrier-observation.json")
    if observation.get("observation_is_causal") is not False:
        raise RuntimeError("observation incorrectly marked causal")
    if observation.get("authority_effect") != "NONE":
        raise RuntimeError("observation authority effect is not NONE")

    events = root / "events/worker-runtime.jsonl"
    text = events.read_text(encoding="utf-8") if events.exists() else ""
    if TASK_ID not in text or TERMINAL not in text:
        raise RuntimeError("terminal LIVE-009 worker evidence not found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()

    py = sys.executable
    run([py, "scripts/install_sovereign_heartbeat_carrier.py", "--source-root", str(root)], root)
    run([py, "scripts/run_worker_runtime.py", "--root", str(root), "--cycles", "1"], root)
    run([py, "scripts/run_heartbeat_runtime.py", "--root", str(root), "--cycles", "1"], root)
    run([py, "scripts/run_worker_runtime.py", "--root", str(root), "--cycles", "1"], root)
    require_runtime_evidence(root)

    print(json.dumps({
        "schema": "stegverse.heartbeat-live-009-resident-execution/v1",
        "state": "COMPLETED",
        "task_id": TASK_ID,
        "transition_id": TERMINAL,
        "runtime_authority": "StegVerse",
        "credential_authority": "TV/TVC",
        "third_party_runtime_required": False,
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
