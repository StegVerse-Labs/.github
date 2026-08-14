#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.runtime_separation import project_legacy_registry

LEGACY = ROOT / "control" / "heartbeat-subsignals.json"
CONTRACT = ROOT / "control" / "runtime-separation-contract.json"
CARRIER_SCHEMA = ROOT / "schemas" / "heartbeat-carrier-observation.schema.json"
CONTROL_SCHEMA = ROOT / "schemas" / "worker-control-plane-coordination.schema.json"
EXPIRED_WORKER_SCHEMA = ROOT / "schemas" / "expired-worker-history.schema.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


def main() -> int:
    errors: list[str] = []
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    json.loads(CARRIER_SCHEMA.read_text(encoding="utf-8"))
    json.loads(CONTROL_SCHEMA.read_text(encoding="utf-8"))
    expired_schema = json.loads(EXPIRED_WORKER_SCHEMA.read_text(encoding="utf-8"))

    carrier, control = project_legacy_registry(
        legacy,
        enforcement_signal_refs=["StegVerse-Labs/StegBrain#860:WORKER_CLOSURE_MISSING"],
    )

    require(carrier.get("schema") == "stegverse.heartbeat-carrier-observation/v1", "carrier schema mismatch", errors)
    require(control.get("schema") == "stegverse.worker-control-plane-coordination/v1", "control schema mismatch", errors)
    require(carrier.get("generation") == legacy.get("generation"), "carrier generation mismatch", errors)
    require(control.get("generation") == legacy.get("generation"), "control generation mismatch", errors)

    forbidden = set(contract.get("forbidden_carrier_fields") or [])
    carrier_keys = set(walk_keys(carrier))
    for key in sorted(forbidden):
        require(key not in carrier_keys, f"carrier leaked control-plane field: {key}", errors)

    authority = carrier.get("authority") or {}
    require(authority.get("heartbeat_grants_execution_authority") is False, "heartbeat authority must be false", errors)
    require(authority.get("credential_authority") == "TV/TVC", "credential authority must be TV/TVC", errors)
    require(authority.get("github_token_runtime_authority") is False, "GitHub token runtime authority must be false", errors)
    require(authority.get("master_records_action_authority") is False, "Master Records action authority must be false", errors)

    control_authority = control.get("authority") or {}
    require(control_authority.get("heartbeat_grants_execution_authority") is False, "control must not derive authority from heartbeat", errors)
    require(control_authority.get("signal_grants_execution_authority") is False, "StegBrain signal must not grant execution authority", errors)
    require(control_authority.get("master_records_action_authority") is False, "Master Records must remain passive", errors)
    require(control_authority.get("credential_authority") == "TV/TVC", "control credential authority must be TV/TVC", errors)
    require(control_authority.get("github_token_runtime_authority") is False, "control GitHub token authority must be false", errors)

    legacy_worker = ((legacy.get("subsignals") or {}).get("worker_coordination") or {})
    projected_worker = control.get("worker_coordination") or {}
    require(projected_worker.get("active_leases") == legacy_worker.get("active_leases"), "worker leases must be preserved in control-plane projection", errors)
    if legacy_worker.get("active_leases"):
        require("claim_id" in set(walk_keys(projected_worker)), "control-plane projection must retain claim_id", errors)
        require("fencing_token" in set(walk_keys(projected_worker)), "control-plane projection must retain fencing_token", errors)

    required_domains = set(contract.get("required_domains") or [])
    require(required_domains == {"StegVerse-Labs", "DEMO", "TEST", "StegVerse-org", "StegGhost"}, "required transition-domain parity mismatch", errors)
    require(contract.get("nervous_system_owner") == "StegVerse-Labs/StegBrain#860", "StegBrain nervous-system owner mismatch", errors)
    require(contract.get("master_records_role") == "PASSIVE_CUSTODY_AND_QUERYABLE_EVIDENCE", "Master Records passive role mismatch", errors)
    require((contract.get("authority") or {}).get("non_tv_tvc_secret_or_token_required") is False, "non-TV/TVC secret/token requirement must be false", errors)

    require(expired_schema.get("properties", {}).get("schema", {}).get("const") == "stegverse.expired-worker-history/v1", "expired-worker schema id mismatch", errors)
    wrapper = (expired_schema.get("properties") or {}).get("expiration_wrapper") or {}
    wrapper_props = wrapper.get("properties") or {}
    require(
        (wrapper_props.get("closure_deadline_rule") or {}).get("const") == "NEXT_ADMISSIBLE_CARRIER_OR_EQUIVALENT_RETURN_REFERENCE",
        "expired-worker closure deadline must be next admissible reference",
        errors,
    )
    data_props = (((expired_schema.get("properties") or {}).get("data_packet") or {}).get("properties") or {})
    require((data_props.get("authority_effect") or {}).get("const") == "NONE", "expired-worker authority_effect must be NONE", errors)
    require((data_props.get("execution_authority") or {}).get("const") is False, "expired-worker execution authority must be false", errors)
    require((data_props.get("claim_active") or {}).get("const") is False, "expired-worker claim must be inactive", errors)
    require((data_props.get("lease_active") or {}).get("const") is False, "expired-worker lease must be inactive", errors)
    expired_auth = (((expired_schema.get("properties") or {}).get("authority") or {}).get("properties") or {})
    require((expired_auth.get("credential_authority") or {}).get("const") == "TV/TVC", "expired-worker credential authority must be TV/TVC", errors)
    require((expired_auth.get("github_token_runtime_authority") or {}).get("const") is False, "expired-worker GitHub token authority must be false", errors)
    require((expired_auth.get("heartbeat_grants_authority") or {}).get("const") is False, "heartbeat must not grant expired-worker authority", errors)
    require((expired_auth.get("reactivates_expired_worker") or {}).get("const") is False, "history must not reactivate expired worker", errors)
    require((expired_auth.get("master_records_action_authority") or {}).get("const") is False, "Master Records action authority must remain false", errors)

    if errors:
        for error in errors:
            print(f"HEARTBEAT_RUNTIME_SEPARATION_INVALID:{error}")
        return 1

    print(
        "HEARTBEAT_RUNTIME_SEPARATION_PASS "
        "carrier=regulatory_reference control_plane=separate nervous_system=StegBrain "
        "expired_worker=terminal_history master_records=passive credential_authority=TV/TVC"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
