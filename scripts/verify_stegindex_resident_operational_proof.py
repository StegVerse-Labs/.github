#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ONE_SHOT_REL = Path("receipts/sovereign-host/one-shot-resident-stack-activation-request-consumption.latest.json")
PREFLIGHT_DIR = Path("receipts/stegindex-preflight")
OUT_REL = Path("receipts/sovereign-host/stegindex-resident-operational-proof.latest.json")

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected JSON object")
    return value

def select_preflight(runtime_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    root = runtime_root / PREFLIGHT_DIR
    if not root.is_dir():
        return None, None
    candidates = sorted(root.glob("*.json"), key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
    for path in candidates:
        try:
            row = load(path)
        except Exception:
            continue
        if row.get("schema") != "stegverse.stegindex-resolution-admission-preflight/v1":
            continue
        preflight = row.get("preflight")
        if not isinstance(preflight, dict):
            continue
        if preflight.get("state") == "PREFLIGHT_UNAVAILABLE":
            continue
        if preflight.get("canonical_resolver_invoked") is not True:
            continue
        if row.get("network_fetch_performed") is not False:
            continue
        if row.get("github_token_required") is not False:
            continue
        if row.get("credential_authority") != "TV/TVC":
            continue
        return path, row
    return None, None

def verify(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    one_shot_path = runtime / ONE_SHOT_REL
    one_shot = load(one_shot_path) if one_shot_path.is_file() else None

    root_resolved = bool(
        isinstance(one_shot, dict)
        and one_shot.get("source_root_resolution_observed") is True
        and one_shot.get("stegindex_source_root_resolved") is True
        and "stegindex" in (one_shot.get("resolved_source_roots") or [])
        and one_shot.get("network_source_fetch_performed") is False
        and one_shot.get("github_token_runtime_authority") == "NONE"
        and one_shot.get("credential_authority") == "TV/TVC"
    )

    preflight_path, preflight_receipt = select_preflight(runtime)
    preflight_observed = preflight_receipt is not None

    predicates = {
        "stegindex_resident_source_root_resolved": root_resolved,
        "stegindex_resolution_admission_preflight_receipt_observed": preflight_observed,
    }
    complete = all(predicates.values())

    out = {
        "schema": "stegverse.stegindex-resident-operational-proof/v1",
        "state": "COMPLETE" if complete else "INCOMPLETE",
        "runtime_root": str(runtime),
        "predicates": predicates,
        "one_shot_receipt_ref": str(one_shot_path.relative_to(runtime)) if one_shot_path.is_file() else None,
        "preflight_receipt_ref": str(preflight_path.relative_to(runtime)) if preflight_path else None,
        "preflight_parent_task_id": preflight_receipt.get("parent_task_id") if preflight_receipt else None,
        "preflight_heartbeat_epoch": preflight_receipt.get("heartbeat_epoch") if preflight_receipt else None,
        "runtime_activation_claimed": False,
        "network_fetch_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_EVIDENCE_VERIFICATION_ONLY",
    }
    return out

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.runtime_root)
    output = args.output or (args.runtime_root.expanduser().resolve() / OUT_REL)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "COMPLETE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
