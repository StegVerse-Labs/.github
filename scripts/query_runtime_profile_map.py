#!/usr/bin/env python3
"""Query the canonical runtime profile map without granting any authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "control/runtime-profile-map.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("map object required")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--profile-id")
    parser.add_argument("--profile-class")
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--observed-state")
    args = parser.parse_args()

    profiles = load(args.map).get("profiles", [])
    rows = []
    for p in profiles:
        if args.profile_id and p.get("profile_id") != args.profile_id:
            continue
        if args.profile_class and p.get("profile_class") != args.profile_class:
            continue
        capabilities = set((p.get("declared") or {}).get("capabilities", []))
        if any(cap not in capabilities for cap in args.capability):
            continue
        if args.observed_state and (p.get("observed") or {}).get("state") != args.observed_state:
            continue
        rows.append(p)

    print(json.dumps({
        "schema": "stegverse.runtime-profile-query-result/v1",
        "match_count": len(rows),
        "profiles": rows,
        "execution_authority_granted": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_DISCOVERY_ONLY"
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
