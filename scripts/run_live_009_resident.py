#!/usr/bin/env python3
"""Resident-only launcher for HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.

This script performs only real local execution: carrier-only native activation,
then the handoff-authorized worker(1) -> carrier(1) -> worker(1) sequence. It
fails closed unless persisted runtime evidence proves the canonical 10 ms /
100 Hz OSCILLATOR_ONLY carrier, a fresh independently admitted fenced claim,
and terminal LIVE-009 completion.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from scripts import install_sovereign_heartbeat_service as sovereign_installer

TASK_ID = "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009"
TERMINAL = "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED"
MINIMUM_FENCE_EXCLUSIVE = 21


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def run(command: list[str], root: Path) -> None:
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")


def resolve_runtime_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    return sovereign_installer.default_runtime_root()


def execution_commands(source_root: Path, runtime_root: Path, python: str) -> list[tuple[list[str], Path]]:
    """Return the exact resident execution sequence."""
    source_root = source_root.resolve()
    runtime_root = runtime_root.resolve()
    return [
        ([
            python,
            str(source_root / "scripts/install_sovereign_heartbeat_carrier.py"),
            "--source-root",
            str(source_root),
            "--runtime-root",
            str(runtime_root),
        ], source_root),
        ([
            python,
            str(runtime_root / "scripts/run_worker_runtime.py"),
            "--root",
            str(runtime_root),
            "--cycles",
            "1",
        ], runtime_root),
        ([
            python,
            str(runtime_root / "scripts/run_heartbeat_runtime.py"),
            "--root",
            str(runtime_root),
            "--cycles",
            "1",
        ], runtime_root),
        ([
            python,
            str(runtime_root / "scripts/run_worker_runtime.py"),
            "--root",
            str(runtime_root),
            "--cycles",
            "1",
        ], runtime_root),
    ]


def _fresh_independent_assignment(root: Path) -> dict:
    records = load_jsonl(root / "events/master-records-worker-assignment.jsonl")
    candidates: list[dict] = []
    for record in records:
        if record.get("task_id") != TASK_ID:
            continue
        claim_id = record.get("claim_id")
        fence = record.get("fencing_token")
        if not isinstance(claim_id, str) or not claim_id:
            continue
        if not isinstance(fence, int) or fence <= MINIMUM_FENCE_EXCLUSIVE:
            continue
        if record.get("source_carrier_event_ref") is not None:
            continue
        if not record.get("source_admission_ref"):
            continue
        candidates.append(record)
    if not candidates:
        raise RuntimeError("fresh independently admitted LIVE-009 fenced claim evidence not found")
    return max(candidates, key=lambda item: int(item["fencing_token"]))


def _terminal_worker_event(root: Path, claim_id: str) -> dict:
    events = load_jsonl(root / "events/worker-runtime.jsonl")
    for event in reversed(events):
        if event.get("task_id") != TASK_ID:
            continue
        if event.get("claim_id") not in (None, claim_id):
            continue
        if event.get("transition_id") == TERMINAL:
            return event
        response = event.get("response")
        if isinstance(response, dict) and response.get("transition_id") == TERMINAL:
            return event
    raise RuntimeError("terminal LIVE-009 worker evidence not found for fresh claim")


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
    if carrier.get("authority_effect") != "NONE":
        raise RuntimeError("carrier authority effect is not NONE")
    if oscillator.get("progression_dependency") != "OSCILLATOR_ONLY":
        raise RuntimeError("carrier progression dependency mismatch")
    if oscillator.get("phase_travel_time_ms") != 10:
        raise RuntimeError("carrier phase travel is not 10 ms")
    if oscillator.get("reference_frequency_hz") != 100:
        raise RuntimeError("carrier reference rate is not 100 Hz")
    if oscillator.get("snapshot_is_observation_only") is not True:
        raise RuntimeError("carrier snapshot is not observation-only")
    if oscillator.get("observation_is_causal") is not False:
        raise RuntimeError("carrier oscillator observation incorrectly marked causal")

    observation = load_json(root / "control/heartbeat-carrier-observation.json")
    if observation.get("observation_is_causal") is not False:
        raise RuntimeError("observation incorrectly marked causal")
    if observation.get("authority_effect") != "NONE":
        raise RuntimeError("observation authority effect is not NONE")

    assignment = _fresh_independent_assignment(root)
    _terminal_worker_event(root, str(assignment["claim_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    runtime_root = resolve_runtime_root(args.runtime_root)
    py = sys.executable

    for command, cwd in execution_commands(source_root, runtime_root, py):
        run(command, cwd)
    require_runtime_evidence(runtime_root)

    print(json.dumps({
        "schema": "stegverse.heartbeat-live-009-resident-execution/v1",
        "state": "COMPLETED",
        "task_id": TASK_ID,
        "transition_id": TERMINAL,
        "runtime_root": str(runtime_root),
        "runtime_authority": "StegVerse",
        "credential_authority": "TV/TVC",
        "third_party_runtime_required": False,
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
