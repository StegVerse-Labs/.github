#!/usr/bin/env python3
"""Emit an integrity/evidence receipt for a validated runtime-profile projection.

The receipt proves only exact bytes plus validation outcome. It grants no runtime,
execution, admission, claim/fence, credential, deployment, or transition authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "control/runtime-profile-map.json"
DEFAULT_OUTPUT = ROOT / "receipts/runtime-profile-map/runtime-profile-map.latest.json"


def load_validator():
    path = ROOT / "scripts/validate_runtime_profile_map.py"
    spec = importlib.util.spec_from_file_location("runtime_profile_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw = args.map.read_bytes()
    data: Any = json.loads(raw.decode("utf-8"))
    validator = load_validator()
    validation = validator.validate(data)
    receipt = {
        "schema": "stegverse.runtime-profile-map-projection-receipt/v1",
        "state": "VALIDATED_PROJECTION",
        "map_ref": str(args.map),
        "map_sha256": hashlib.sha256(raw).hexdigest(),
        "map_generation": data.get("generation"),
        "map_status": data.get("status"),
        "profile_count": len(data.get("profiles", [])),
        "validation": validation,
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "execution_authority_granted": False,
        "task_admission_granted": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_or_oscillator_advanced": False,
        "authority_effect": "NONE_EVIDENCE_ONLY"
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
