#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_RECEIPT = Path("receipts/sovereign-host/carrier-activation.latest.json")

EXPECTED = {
    "carrier_active": True,
    "activation_scope": "CARRIER_ONLY",
    "worker_start_attempted": False,
    "worker_runtime_dependency_for_carrier_start": False,
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
    "credential_authority": "TV/TVC",
}


def verify_receipt(receipt: Any) -> list[str]:
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]

    failures: list[str] = []
    for key, expected in EXPECTED.items():
        if key not in receipt:
            failures.append(f"missing required field: {key}")
            continue
        actual = receipt[key]
        if isinstance(expected, float):
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or float(actual) != expected:
                failures.append(f"{key}: expected {expected!r}, got {actual!r}")
        elif actual != expected:
            failures.append(f"{key}: expected {expected!r}, got {actual!r}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the sovereign resident heartbeat carrier activation receipt without granting runtime authority."
    )
    parser.add_argument("receipt", nargs="?", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args(argv)

    try:
        with args.receipt.open("r", encoding="utf-8") as handle:
            receipt = json.load(handle)
    except FileNotFoundError:
        print(json.dumps({
            "verified": False,
            "receipt": str(args.receipt),
            "failures": ["activation receipt is absent"],
            "authority_effect": "NONE",
        }, sort_keys=True))
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "verified": False,
            "receipt": str(args.receipt),
            "failures": [f"unable to read valid JSON receipt: {exc}"],
            "authority_effect": "NONE",
        }, sort_keys=True))
        return 1

    failures = verify_receipt(receipt)
    result = {
        "verified": not failures,
        "receipt": str(args.receipt),
        "failures": failures,
        "authority_effect": "NONE",
        "runtime_authority_granted": False,
        "credential_authority": "TV/TVC",
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
