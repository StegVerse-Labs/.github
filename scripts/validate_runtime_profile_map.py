#!/usr/bin/env python3
"""Fail-closed validator for the canonical runtime profile map."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "control/runtime-profile-map.json"
FORBIDDEN_KEY_FRAGMENTS = ("token", "secret", "password", "private_key", "api_key", "credential_value")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("map object required")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def walk_forbidden(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lower = str(key).lower()
            if any(fragment in lower for fragment in FORBIDDEN_KEY_FRAGMENTS):
                if key in {"credential_authority", "github_token_runtime_authority"}:
                    pass
                else:
                    findings.append(path + "." + str(key))
            findings.extend(walk_forbidden(child, path + "." + str(key)))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            findings.extend(walk_forbidden(child, f"{path}[{idx}]"))
    return findings


def validate(data: dict[str, Any]) -> dict[str, Any]:
    require(data.get("schema") == "stegverse.runtime-profile-map/v1", "schema mismatch")
    require(isinstance(data.get("generation"), int) and data["generation"] >= 1, "generation invalid")
    authority = data.get("authority") or {}
    require(authority.get("map_grants_execution_authority") is False, "map cannot grant execution authority")
    require(authority.get("capability_match_grants_authority") is False, "match cannot grant authority")
    require(authority.get("worker_claim_authority") == "WORKERCOORDINATOR", "claim/fence authority drift")
    require(authority.get("credential_authority") == "TV/TVC", "credential authority drift")
    require(authority.get("ingress_egress_authority") == "INTERLOCK_INTR", "ingress/egress authority drift")
    require(authority.get("observed_reality_authority") == "MASTER_RECORDS", "observed reality authority drift")

    profiles = data.get("profiles")
    require(isinstance(profiles, list), "profiles array required")
    ids: list[str] = []
    for profile in profiles:
        require(isinstance(profile, dict), "profile object required")
        pid = profile.get("profile_id")
        require(isinstance(pid, str) and pid, "profile_id required")
        ids.append(pid)
        declared = profile.get("declared") or {}
        require(isinstance(declared.get("capabilities"), list), f"capabilities required:{pid}")
        require(isinstance(declared.get("mutation_allowed"), bool), f"mutation_allowed required:{pid}")
        require(isinstance(declared.get("deployment_allowed"), bool), f"deployment_allowed required:{pid}")
        pa = profile.get("authority") or {}
        require(pa.get("availability_grants_authority") is False, f"availability authority forbidden:{pid}")
        require(pa.get("match_grants_authority") is False, f"match authority forbidden:{pid}")
        require(pa.get("claim_fence_authority") == "WORKERCOORDINATOR", f"claim authority drift:{pid}")
        require(pa.get("credential_authority") == "TV/TVC", f"credential authority drift:{pid}")
        require(pa.get("hb_grants_authority") is False, f"HB authority forbidden:{pid}")
        provenance = profile.get("provenance") or {}
        refs = provenance.get("source_refs")
        require(isinstance(refs, list) and bool(refs), f"source provenance required:{pid}")
        observed = profile.get("observed") or {}
        require(observed.get("state", "UNKNOWN") in {"UNKNOWN", "DECLARED_ONLY", "OBSERVED", "STALE", "UNAVAILABLE", "CONFLICT"}, f"observed state invalid:{pid}")
    require(len(ids) == len(set(ids)), "duplicate runtime profile identity")
    forbidden = walk_forbidden(data)
    require(not forbidden, "secret-like fields forbidden: " + ",".join(forbidden))
    return {"state": "PASS", "profile_count": len(profiles), "authority_effect": "NONE_VALIDATION_ONLY"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()
    result = validate(load(args.map))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
