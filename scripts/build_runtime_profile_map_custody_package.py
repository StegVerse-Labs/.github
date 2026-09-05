#!/usr/bin/env python3
"""Build a non-authorizing custody input package for the canonical runtime-profile map.

This packages exact hashes and references only. It does not perform Master Records
custody, grant runtime authority, advance HB/oscillator state, or mint claim/fence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_rows(directory: Path) -> list[dict[str, str]]:
    require(directory.is_dir(), f"artifact directory missing:{directory}")
    rows: list[dict[str, str]] = []
    for path in sorted(directory.glob("*.json")):
        data = load(path)
        task_id = data.get("task_id")
        require(isinstance(task_id, str) and task_id, f"task_id missing:{path}")
        rows.append({"task_id": task_id, "ref": str(path), "sha256": sha256(path)})
    require(bool(rows), f"no artifacts found:{directory}")
    return rows


def build(root: Path) -> dict[str, Any]:
    map_path = root / "control/runtime-profile-map.json"
    map_receipt = root / "receipts/runtime-profile-map/runtime-profile-map.latest.json"
    registry = root / "data/canonical-task-registry.json"
    resolutions = root / "receipts/runtime-profile-map/task-resolutions"
    readiness = root / "receipts/runtime-profile-map/routing-readiness"
    for path in (map_path, map_receipt, registry):
        require(path.is_file(), f"required artifact missing:{path}")
    runtime_map = load(map_path)
    require(runtime_map.get("schema") == "stegverse.runtime-profile-map/v1", "runtime map schema mismatch")
    require(isinstance(runtime_map.get("generated_at"), str) and runtime_map.get("generated_at"), "runtime map must be generated")
    return {
        "schema": "stegverse.runtime-profile-map-custody-package/v1",
        "task_id": "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001",
        "map_ref": str(map_path),
        "map_generation": runtime_map.get("generation"),
        "map_sha256": sha256(map_path),
        "map_receipt_ref": str(map_receipt),
        "map_receipt_sha256": sha256(map_receipt),
        "task_resolution_receipts": artifact_rows(resolutions),
        "routing_readiness_receipts": artifact_rows(readiness),
        "registry_ref": str(registry),
        "registry_sha256": sha256(registry),
        "generated_at": runtime_map.get("generated_at"),
        "heartbeat_authority_effect": "NONE_REFERENCE_ONLY",
        "worker_claim_authority": "WORKERCOORDINATOR",
        "credential_authority": "TV/TVC",
        "ingress_egress_authority": "INTERLOCK_INTR",
        "observed_reality_authority": "MASTER_RECORDS",
        "authority_effect": "NONE_CUSTODY_INPUT_ONLY",
        "nonclaims": [
            "PACKAGE_DOES_NOT_PERFORM_MASTER_RECORDS_CUSTODY",
            "PACKAGE_DOES_NOT_GRANT_EXECUTION_OR_TASK_ADMISSION",
            "PACKAGE_DOES_NOT_MINT_WORKERCOORDINATOR_CLAIM_OR_FENCE",
            "PACKAGE_DOES_NOT_ADVANCE_HB_OR_OSCILLATOR",
            "PACKAGE_DOES_NOT_PROVE_TASK_COMPLETION"
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    result = build(root)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": "BUILT", "output": str(output), "sha256": sha256(output), "authority_effect": "NONE_CUSTODY_INPUT_ONLY"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
