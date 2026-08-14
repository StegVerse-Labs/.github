from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_heartbeat_control_plane_separation.py"

spec = importlib.util.spec_from_file_location("heartbeat_control_plane_validator", VALIDATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_canonical_heartbeat_control_plane_separation() -> None:
    module.validate()


def test_carrier_schema_does_not_own_worker_control_fields() -> None:
    carrier = module.load(ROOT / "schemas" / "heartbeat-carrier-signal.schema.json")
    text = __import__("json").dumps(carrier, sort_keys=True)
    for forbidden in ["claim_id", "fencing_token", "active_workers", "transport_leases"]:
        assert forbidden not in text


def test_expired_worker_history_is_non_authorizing() -> None:
    expired = module.load(ROOT / "schemas" / "expired-worker-history.schema.json")
    data_props = expired["properties"]["data_packet"]["properties"]
    assert data_props["execution_authority"]["const"] is False
    assert data_props["claim_active"]["const"] is False
    assert data_props["lease_active"]["const"] is False
    assert data_props["authority_effect"]["const"] == "NONE"
