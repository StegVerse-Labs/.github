#!/usr/bin/env python3
"""Install and activate only the native StegVerse heartbeat carrier.

This path deliberately excludes WorkerCoordinator startup. The carrier is
materialized locally, registered only with the host OS process supervisor, and
started from the canonical engine_v13 oscillator runtime. No network fetch,
hosted scheduler, GitHub runtime, third-party process host, or credential is
required.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts import install_sovereign_heartbeat_service as base


def install_carrier(source_root: Path, target_root: Path, runner=subprocess.run, *, system=None, env=None):
    materialization = base.materialize(source_root, target_root)
    service = base.materialize_service(target_root, system=system, env=env)

    carrier_success_index = int(service["carrier_success_index"])
    carrier_commands = list(service["activation_commands"][: carrier_success_index + 1])
    results = []
    for command in carrier_commands:
        completed = runner(command, check=False, capture_output=True, text=True)
        results.append({"command": command, "returncode": completed.returncode})

    carrier_active = (
        len(results) > carrier_success_index
        and results[carrier_success_index]["returncode"] == 0
    )
    receipt = {
        **materialization,
        "schema": "stegverse.sovereign-heartbeat-carrier-activation/v1",
        "activation_scope": "CARRIER_ONLY",
        "carrier_registration_path": service["carrier_registration_path"],
        "carrier_command": service["carrier_command"],
        "carrier_activation_commands": carrier_commands,
        "carrier_activation_results": results,
        "carrier_active": carrier_active,
        "worker_start_attempted": False,
        "worker_active": False,
        "worker_runtime_dependency_for_carrier_start": False,
        "network_fetch_required": False,
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "third_party_deployment_required": False,
        "github_runtime_dependency": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_period_ms": 10.0,
        "heartbeat_reference_frequency_hz": 100.0,
        "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
        "canonical_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
    }
    path = target_root / "receipts" / "sovereign-host" / "carrier-activation.latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()

    target = (args.runtime_root or base.default_runtime_root()).resolve()
    result = install_carrier(args.source_root.resolve(), target)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("carrier_active") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
