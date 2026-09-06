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
import sys
import time
from pathlib import Path
from typing import Callable

# Canonical handoffs invoke this file directly from the repository root.
# Direct execution places scripts/ rather than the repository root on sys.path,
# so make the existing package import resolvable without caller configuration.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import install_sovereign_heartbeat_service as base


def _observe_carrier_progress(target_root: Path, *, timeout_seconds: float = 5.0) -> dict:
    """Require two oscillator-backed carrier observations with increasing epochs."""
    path = target_root / "control" / "heartbeat-carrier-runtime-state.json"
    deadline = time.monotonic() + timeout_seconds
    first_epoch = None
    last_error = "carrier state not observed"
    while time.monotonic() < deadline:
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            oscillator = state.get("oscillator") or {}
            epoch = state.get("epoch")
            valid = (
                isinstance(epoch, int)
                and state.get("frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
                and oscillator.get("progression_dependency") == "OSCILLATOR_ONLY"
                and oscillator.get("phase_travel_time_ms") == 10
                and oscillator.get("reference_frequency_hz") == 100
                and oscillator.get("snapshot_is_observation_only") is True
                and oscillator.get("observation_is_causal") is False
            )
            if valid:
                if first_epoch is not None and epoch > first_epoch:
                    return {
                        "observed": True,
                        "first_epoch": first_epoch,
                        "last_epoch": epoch,
                        "state_ref": "control/heartbeat-carrier-runtime-state.json",
                    }
                first_epoch = epoch
            else:
                last_error = "carrier state did not satisfy oscillator invariants"
        except (OSError, ValueError, TypeError) as exc:
            last_error = str(exc)
        time.sleep(0.05)
    return {
        "observed": False,
        "first_epoch": first_epoch,
        "last_epoch": first_epoch,
        "state_ref": "control/heartbeat-carrier-runtime-state.json",
        "failure": last_error,
    }


def install_carrier(
    source_root: Path,
    target_root: Path,
    runner=subprocess.run,
    *,
    system=None,
    env=None,
    carrier_observer: Callable[[Path], dict] = _observe_carrier_progress,
):
    materialization = base.materialize(source_root, target_root)
    service = base.materialize_service(target_root, system=system, env=env)

    carrier_success_index = int(service["carrier_success_index"])
    carrier_commands = list(service["activation_commands"][: carrier_success_index + 1])
    results = []
    for command in carrier_commands:
        completed = runner(command, check=False, capture_output=True, text=True)
        results.append({"command": command, "returncode": completed.returncode})

    carrier_start_reported = (
        len(results) > carrier_success_index
        and results[carrier_success_index]["returncode"] == 0
    )

    # Windows scheduled-task registration does not itself start an ONLOGON task.
    # Require an explicit immediate launch before claiming carrier_active=true.
    # This prevents a successful `schtasks /Create` from being misreported as
    # evidence that the heartbeat process is actually resident.
    if service.get("registration_kind") == "scheduled-task-separated":
        run_command = ["schtasks", "/Run", "/TN", "StegVerse Heartbeat"]
        completed = runner(run_command, check=False, capture_output=True, text=True)
        results.append({"command": run_command, "returncode": completed.returncode})
        carrier_start_reported = carrier_start_reported and completed.returncode == 0

    carrier_observation = carrier_observer(target_root) if carrier_start_reported else {
        "observed": False,
        "failure": "native carrier start command failed",
        "state_ref": "control/heartbeat-carrier-runtime-state.json",
    }
    carrier_active = carrier_start_reported and carrier_observation.get("observed") is True

    receipt = {
        **materialization,
        "schema": "stegverse.sovereign-heartbeat-carrier-activation/v1",
        "activation_scope": "CARRIER_ONLY",
        "carrier_registration_path": service["carrier_registration_path"],
        "carrier_command": service["carrier_command"],
        "carrier_activation_commands": [item["command"] for item in results],
        "carrier_activation_results": results,
        "carrier_start_reported": carrier_start_reported,
        "carrier_progression_observation": carrier_observation,
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
