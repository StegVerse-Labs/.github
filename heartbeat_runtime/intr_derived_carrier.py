from __future__ import annotations

import base64
import hashlib
import re
from typing import Any

SCHEMA = "stegverse.heartbeat-intr-derived-carrier/v1"
CREDENTIAL_AUTHORITY = "TV/TVC"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class DerivedCarrierError(ValueError):
    pass


def _require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise DerivedCarrierError(f"{name}_required")
    return value


def _require_epoch(value: Any) -> int:
    if not isinstance(value, int) or value < 0:
        raise DerivedCarrierError("heartbeat_epoch_invalid")
    return value


def derive_intr_carrier_signal(
    *,
    heartbeat_epoch: int,
    heartbeat_reference: str,
    phase_slots: int,
    packet_bytes: bytes,
    intr_transport_profile: str,
    boundary_from: str,
    boundary_to: str,
    packet_receipt_hash: str,
) -> dict[str, Any]:
    """Bind exact governed InTr bytes to a deterministic HB-derived carrier signal.

    This function creates no routing, admission, execution, transition, receiving,
    credential, or governance authority. It only derives synchronization/channel
    coordinates from the existing HB reference and preserves exact packet bytes.
    """
    epoch = _require_epoch(heartbeat_epoch)
    reference = _require_text("heartbeat_reference", heartbeat_reference)
    profile = _require_text("intr_transport_profile", intr_transport_profile)
    source = _require_text("boundary_from", boundary_from)
    destination = _require_text("boundary_to", boundary_to)
    receipt_hash = _require_text("packet_receipt_hash", packet_receipt_hash).lower()
    if not _HEX64.fullmatch(receipt_hash):
        raise DerivedCarrierError("packet_receipt_hash_invalid")
    if not isinstance(phase_slots, int) or phase_slots < 1:
        raise DerivedCarrierError("phase_slots_invalid")
    if not isinstance(packet_bytes, bytes) or not packet_bytes:
        raise DerivedCarrierError("packet_bytes_required")

    packet_sha256 = hashlib.sha256(packet_bytes).hexdigest()
    slot = int(packet_sha256[:16], 16) % phase_slots
    phase_offset_deg = round((360.0 * slot) / phase_slots, 9)
    signal_id = f"hb-intr:{epoch}:{slot}:{packet_sha256[:16]}"

    return {
        "schema": SCHEMA,
        "signal_id": signal_id,
        "kind": "INTR_PACKET_DERIVED_CARRIER",
        "carrier": {
            "primary": "STEGVERSE_HEARTBEAT",
            "heartbeat_epoch": epoch,
            "heartbeat_reference": reference,
            "reference_rate_hz": 100.0,
            "reference_period_ms": 10.0,
            "progression_dependency": "OSCILLATOR_ONLY",
            "phase_slots": phase_slots,
            "channel_slot": slot,
            "phase_offset_deg": phase_offset_deg,
            "phase_plan_changes_reference_interval": False,
        },
        "intr": {
            "transport_profile": profile,
            "boundary_from": source,
            "boundary_to": destination,
            "packet_receipt_hash": receipt_hash,
            "packet_sha256": packet_sha256,
            "packet_encoding": "base64",
            "packet_base64": base64.b64encode(packet_bytes).decode("ascii"),
            "packet_semantics_interpreted_by_heartbeat": False,
            "packet_governance_external_to_heartbeat": True,
        },
        "authority": {
            "heartbeat_grants_admission_authority": False,
            "heartbeat_grants_execution_authority": False,
            "heartbeat_grants_credential_authority": False,
            "heartbeat_grants_routing_authority": False,
            "heartbeat_grants_transition_authority": False,
            "heartbeat_grants_receiving_authority": False,
            "derived_carrier_grants_admission_authority": False,
            "derived_carrier_grants_execution_authority": False,
            "derived_carrier_grants_credential_authority": False,
            "derived_carrier_grants_routing_authority": False,
            "derived_carrier_grants_transition_authority": False,
            "derived_carrier_grants_receiving_authority": False,
            "credential_authority": CREDENTIAL_AUTHORITY,
            "authority_effect": "NONE_CARRIER_ONLY",
        },
    }


def recover_intr_packet_bytes(signal: dict[str, Any]) -> bytes:
    if signal.get("schema") != SCHEMA:
        raise DerivedCarrierError("derived_carrier_schema_invalid")
    intr = signal.get("intr")
    if not isinstance(intr, dict) or intr.get("packet_encoding") != "base64":
        raise DerivedCarrierError("derived_carrier_packet_encoding_invalid")
    encoded = intr.get("packet_base64")
    if not isinstance(encoded, str):
        raise DerivedCarrierError("derived_carrier_packet_missing")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as exc:
        raise DerivedCarrierError("derived_carrier_packet_base64_invalid") from exc
    expected = intr.get("packet_sha256")
    if not isinstance(expected, str) or hashlib.sha256(raw).hexdigest() != expected:
        raise DerivedCarrierError("derived_carrier_packet_hash_mismatch")
    return raw
