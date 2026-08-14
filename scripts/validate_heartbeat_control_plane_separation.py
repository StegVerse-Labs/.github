#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "control" / "heartbeat-documentation-semantics-audit.json"
CARRIER = ROOT / "schemas" / "heartbeat-carrier-signal.schema.json"
CONTROL = ROOT / "schemas" / "worker-control-plane.schema.json"
EXPIRED = ROOT / "schemas" / "expired-worker-history.schema.json"
LEGACY_SCHEMA = ROOT / "schemas" / "heartbeat-subsignal.schema.json"
LEGACY_STATE = ROOT / "control" / "heartbeat-subsignals.json"


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> None:
    audit = load(AUDIT)
    carrier = load(CARRIER)
    control = load(CONTROL)
    expired = load(EXPIRED)
    load(LEGACY_SCHEMA)
    load(LEGACY_STATE)

    require(audit.get("schema") == "stegverse.heartbeat-documentation-semantics-audit/v3", "audit schema must be v3")
    require(audit.get("credential_authority") == "TV/TVC", "audit credential authority must be TV/TVC")
    require(audit.get("github_token_runtime_authority") is False, "GitHub token runtime authority must be false")

    contracts = audit.get("canonical_runtime_contracts") or {}
    require(contracts.get("heartbeat_carrier_schema") == "schemas/heartbeat-carrier-signal.schema.json", "carrier schema binding missing")
    require(contracts.get("worker_control_plane_schema") == "schemas/worker-control-plane.schema.json", "control-plane schema binding missing")
    require(contracts.get("expired_worker_history_schema") == "schemas/expired-worker-history.schema.json", "expired worker schema binding missing")

    carrier_props = carrier.get("properties") or {}
    authority_props = ((carrier_props.get("authority") or {}).get("properties") or {})
    require((carrier_props.get("schema") or {}).get("const") == "stegverse.heartbeat-carrier-signal/v1", "carrier schema identity invalid")
    require((authority_props.get("credential_authority") or {}).get("const") == "TV/TVC", "carrier credential authority invalid")
    for field in ["github_token_runtime_authority", "grants_execution_authority", "dispatches_tasks", "issues_claims_or_fences", "routes_communications", "is_master_records_transport"]:
        require((authority_props.get(field) or {}).get("const") is False, f"carrier authority field must be false: {field}")
    carrier_text = json.dumps(carrier, sort_keys=True)
    for forbidden in ["claim_id", "fencing_token", "active_workers", "transport_leases"]:
        require(forbidden not in carrier_text, f"carrier schema must not own control-plane field: {forbidden}")

    control_props = control.get("properties") or {}
    require((control_props.get("schema") or {}).get("const") == "stegverse.worker-control-plane/v1", "control-plane schema identity invalid")
    worker_props = ((((control.get("$defs") or {}).get("worker") or {}).get("properties")) or {})
    for required_field in ["claim_id", "fencing_token", "lease", "task_id", "worker_id"]:
        require(required_field in worker_props, f"control-plane worker missing field: {required_field}")
    control_authority = ((control_props.get("authority") or {}).get("properties") or {})
    require((control_authority.get("credential_authority") or {}).get("const") == "TV/TVC", "control-plane credential authority invalid")
    require((control_authority.get("github_token_runtime_authority") or {}).get("const") is False, "control-plane GitHub authority must be false")
    require((control_authority.get("carrier_grants_execution_authority") or {}).get("const") is False, "carrier must not grant control-plane authority")

    expired_props = expired.get("properties") or {}
    require((expired_props.get("schema") or {}).get("const") == "stegverse.expired-worker-history/v1", "expired worker schema identity invalid")
    data_props = ((expired_props.get("data_packet") or {}).get("properties") or {})
    for field in ["execution_authority", "claim_active", "lease_active"]:
        require((data_props.get(field) or {}).get("const") is False, f"expired worker field must be false: {field}")
    require((data_props.get("authority_effect") or {}).get("const") == "NONE", "expired worker authority effect must be NONE")
    expired_authority = ((expired_props.get("authority") or {}).get("properties") or {})
    require((expired_authority.get("credential_authority") or {}).get("const") == "TV/TVC", "expired worker credential authority invalid")
    require((expired_authority.get("heartbeat_grants_authority") or {}).get("const") is False, "heartbeat must not grant expired worker authority")
    require((expired_authority.get("reactivates_expired_worker") or {}).get("const") is False, "expired worker reactivation must be forbidden")

    compatibility = {item.get("path"): item for item in audit.get("compatibility_surfaces") or [] if isinstance(item, dict)}
    require(compatibility.get("schemas/heartbeat-subsignal.schema.json", {}).get("state") == "LEGACY_COMPATIBILITY_ONLY", "legacy schema must be compatibility-only")
    require(compatibility.get("control/heartbeat-subsignals.json", {}).get("manual_mutation_allowed_by_schema_lane") is False, "schema lane must not mutate live legacy projection")

    separation = audit.get("separation_rules") or {}
    require(separation.get("worker_claims_fences_leases_belong_to") == "WORKER_CONTROL_PLANE", "claims/fences/leases ownership invalid")
    require(separation.get("heartbeat_observation_belongs_to") == "HEARTBEAT_CARRIER", "heartbeat ownership invalid")
    require(separation.get("carrier_continuity_is_capability_activation_proof") is False, "carrier continuity cannot prove AE activation")

    print("HEARTBEAT_CONTROL_PLANE_SEPARATION_PASS carrier=carrier_only control=worker_claims_fences_leases expired_worker=non_authorizing credential_authority=TV/TVC legacy_projection=machine_migration_pending")


if __name__ == "__main__":
    try:
        validate()
    except Exception as exc:
        print(f"HEARTBEAT_CONTROL_PLANE_SEPARATION_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
