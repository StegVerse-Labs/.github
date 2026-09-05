#!/usr/bin/env python3
"""Deterministically match declared runtime profiles to explicit task requirements.

A match is routing/discovery evidence only. It never grants admission, execution,
claim/fence, credential, deployment, transition, or consequence authority.
"""
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


def evaluate(profile: dict[str, Any], required: set[str], environment: str | None, direction: str | None,
             mutation_required: bool, deployment_required: bool, require_observed: bool) -> dict[str, Any]:
    declared = profile.get("declared") or {}
    available = set(declared.get("capabilities", []))
    missing = sorted(required - available)
    reasons: list[str] = []
    if missing:
        reasons.append("MISSING_CAPABILITIES:" + ",".join(missing))
    envs = set(declared.get("environment_classes", []))
    if environment and environment not in envs:
        reasons.append("ENVIRONMENT_NOT_DECLARED:" + environment)
    directions = set(declared.get("directions", []))
    if direction and direction not in directions:
        reasons.append("DIRECTION_NOT_DECLARED:" + direction)
    if mutation_required and declared.get("mutation_allowed") is not True:
        reasons.append("MUTATION_NOT_ALLOWED_BY_PROFILE")
    if deployment_required and declared.get("deployment_allowed") is not True:
        reasons.append("DEPLOYMENT_NOT_ALLOWED_BY_PROFILE")
    observed = (profile.get("observed") or {}).get("state", "UNKNOWN")
    if require_observed and observed != "OBSERVED":
        reasons.append("CURRENT_OBSERVATION_REQUIRED:" + observed)
    compatible = not reasons
    return {
        "profile_id": profile.get("profile_id"),
        "compatible": compatible,
        "reasons": reasons,
        "observed_state": observed,
        "capabilities_satisfied": sorted(required & available),
        "missing_capabilities": missing,
        "authority_effect": "NONE_CANDIDATE_MATCH_ONLY"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--environment")
    parser.add_argument("--direction")
    parser.add_argument("--mutation-required", action="store_true")
    parser.add_argument("--deployment-required", action="store_true")
    parser.add_argument("--require-observed", action="store_true")
    args = parser.parse_args()

    data = load(args.map)
    required = set(args.capability)
    evaluated = [evaluate(p, required, args.environment, args.direction, args.mutation_required,
                          args.deployment_required, args.require_observed) for p in data.get("profiles", [])]
    candidates = [row for row in evaluated if row["compatible"]]
    candidates.sort(key=lambda row: str(row["profile_id"]))
    print(json.dumps({
        "schema": "stegverse.runtime-profile-match/v1",
        "requirements": {
            "capabilities": sorted(required),
            "environment": args.environment,
            "direction": args.direction,
            "mutation_required": args.mutation_required,
            "deployment_required": args.deployment_required,
            "current_observation_required": args.require_observed
        },
        "candidate_profile_ids": [row["profile_id"] for row in candidates],
        "candidate_count": len(candidates),
        "evaluated": evaluated,
        "selection_is_authorization": False,
        "workercoordinator_admission_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_DISCOVERY_ONLY"
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
