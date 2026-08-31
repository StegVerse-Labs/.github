from __future__ import annotations

import base64
import hashlib
import math
import re
from typing import Any, Mapping

from .intr_carrier_profile import (
    CHANNEL_COUNT,
    PROFILE_SCHEMA,
    build_carrier_binding,
    validate_carrier_binding,
)

SCHEMA = "stegverse.heartbeat-intr-derived-carrier/v1"
CREDENTIAL_AUTHORITY = "TV/TVC"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class DerivedCarrierError(ValueError):
    pass


def _require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise DerivedCarrierError(f"{name}_required")
    return value


def _receipt_hash(value: Any) -> str:
    text = _require_text("packet_receipt_hash", value).lower()
    if text.startswith("sha256:"):
        text = text[7:]
    if not _HEX64.fullmatch(text):
        raise DerivedCarrierError("packet_receipt_hash_invalid")
    return text


def derive_intr_carrier_signal(
    *,
    packet_id: str,
    payload_hash: str,
    sampled_unix_ms: int,
    packet_bytes: bytes,
    intr_transport_profile: str,
    boundary_from: str,
    boundary_to: str,
    packet_receipt_hash: str,
) -> dict[str, Any]:
    """Materialize exact governed InTr bytes on the canonical HB-derived channel.

    Channel/reference derivation is delegated to intr_carrier_profile so the
    exact-byte carrier and the Universal InTr ingress advertise one canonical
    formula. This function creates no routing, admission, execution, transition,
    receiving, credential, claim/fence, or governance authority.
    """
    packet = _require_text("packet_id", packet_id)
    profile = _require_text("intr_transport_profile", intr_transport_profile)
    source = _require_text("boundary_from", boundary_from)
    destination = _require_text("boundary_to", boundary_to)
    receipt_hash = _receipt_hash(packet_receipt_hash)
    if not isinstance(packet_bytes, bytes) or not packet_bytes:
        raise DerivedCarrierError("packet_bytes_required")

    try:
        binding = build_carrier_binding(
            packet_id=packet,
            payload_hash=payload_hash,
            sampled_unix_ms=sampled_unix_ms,
        )
    except ValueError as exc:
        raise DerivedCarrierError(str(exc)) from exc

    reference = binding["heartbeat_reference"]
    channel = binding["channel"]
    packet_sha256 = hashlib.sha256(packet_bytes).hexdigest()
    phase_offset_deg = round(math.degrees(float(channel["phase_radians"])) % 360.0, 9)
    signal_id = (
        f"hb-intr:{reference['heartbeat_epoch']}:{channel['phase_slot']}:"
        f"{binding['binding_sha256'][7:23]}:{packet_sha256[:16]}"
    )

    return {
        "schema": SCHEMA,
        "signal_id": signal_id,
        "kind": "INTR_PACKET_DERIVED_CARRIER",
        "carrier_binding": binding,
        "carrier": {
            "primary": "STEGVERSE_HEARTBEAT",
            "carrier_profile": PROFILE_SCHEMA,
            "carrier_binding_sha256": binding["binding_sha256"],
            "heartbeat_epoch": reference["heartbeat_epoch"],
            "heartbeat_reference": reference["heartbeat_id"],
            "sampled_unix_ms": reference["sampled_unix_ms"],
            "intra_reference_phase_offset_ms": reference["phase_offset_ms"],
            "reference_rate_hz": 100.0,
            "reference_period_ms": 10.0,
            "progression_dependency": "OSCILLATOR_ONLY",
            "channel_id": channel["channel_id"],
            "phase_slots": channel["phase_slot_count"],
            "channel_slot": channel["phase_slot"],
            "phase_offset_deg": phase_offset_deg,
            "channel_derivation": channel["derivation"],
            "phase_plan_changes_reference_interval": False,
        },
        "intr": {
            "packet_id": packet,
            "payload_hash": payload_hash,
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


def recover_intr_packet_bytes(signal: Mapping[str, Any]) -> bytes:
    if signal.get("schema") != SCHEMA:
        raise DerivedCarrierError("derived_carrier_schema_invalid")
    binding = signal.get("carrier_binding")
    carrier = signal.get("carrier")
    intr = signal.get("intr")
    if not isinstance(binding, Mapping):
        raise DerivedCarrierError("derived_carrier_binding_missing")
    if not isinstance(carrier, Mapping):
        raise DerivedCarrierError("derived_carrier_carrier_missing")
    if not isinstance(intr, Mapping) or intr.get("packet_encoding") != "base64":
        raise DerivedCarrierError("derived_carrier_packet_encoding_invalid")

    try:
        validated = validate_carrier_binding(
            binding,
            packet_id=str(intr.get("packet_id") or ""),
            payload_hash=str(intr.get("payload_hash") or ""),
        )
    except ValueError as exc:
        raise DerivedCarrierError(str(exc)) from exc

    reference = validated["heartbeat_reference"]
    channel = validated["channel"]
    expected_carrier = {
        "carrier_profile": validated["carrier_profile"],
        "carrier_binding_sha256": validated["binding_sha256"],
        "heartbeat_epoch": reference["heartbeat_epoch"],
        "heartbeat_reference": reference["heartbeat_id"],
        "sampled_unix_ms": reference["sampled_unix_ms"],
        "intra_reference_phase_offset_ms": reference["phase_offset_ms"],
        "channel_id": channel["channel_id"],
        "phase_slots": channel["phase_slot_count"],
        "channel_slot": channel["phase_slot"],
        "channel_derivation": channel["derivation"],
    }
    for key, expected in expected_carrier.items():
        if carrier.get(key) != expected:
            raise DerivedCarrierError(f"derived_carrier_{key}_mismatch")

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


__all__ = [
    "SCHEMA",
    "DerivedCarrierError",
    "derive_intr_carrier_signal",
    "recover_intr_packet_bytes",
    "CHANNEL_COUNT",
]
