"""Deterministic non-authorizing HeartBeat-derived carrier binding for InTr packets."""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from .independent_oscillator import (
    OSCILLATOR_PERIOD_MS,
    PROTOCOL_ANCHOR_EPOCH,
    PROTOCOL_ANCHOR_UNIX_NS,
    REFERENCE_FREQUENCY_HZ,
    encode_heartbeat_id,
)

PROFILE_SCHEMA = "stegverse.intr.hb-derived-carrier-profile/v1"
BINDING_SCHEMA = "stegverse.intr.hb-derived-carrier-binding/v1"
CHANNEL_COUNT = 16
CHANNEL_FAMILY = "H1_PHASE_SLOTS"
AUTHORITY_EFFECT = "NONE_CARRIER_ONLY"


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical_json(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def derive_reference_from_unix_ms(sampled_unix_ms: int) -> dict[str, Any]:
    _require(isinstance(sampled_unix_ms, int) and not isinstance(sampled_unix_ms, bool), "sampled_unix_ms_required")
    anchor_ms = PROTOCOL_ANCHOR_UNIX_NS // 1_000_000
    _require(sampled_unix_ms >= anchor_ms, "sample_precedes_hb32_anchor")
    elapsed_ms = sampled_unix_ms - anchor_ms
    elapsed_quanta, phase_offset_ms = divmod(elapsed_ms, OSCILLATOR_PERIOD_MS)
    epoch = PROTOCOL_ANCHOR_EPOCH + elapsed_quanta
    return {
        "heartbeat_epoch": epoch,
        "heartbeat_id": encode_heartbeat_id(epoch),
        "sampled_unix_ms": sampled_unix_ms,
        "phase_offset_ms": phase_offset_ms,
        "reference_frequency_hz": REFERENCE_FREQUENCY_HZ,
        "progression_dependency": "OSCILLATOR_ONLY",
    }


def derive_channel(payload_hash: str) -> dict[str, Any]:
    _require(
        isinstance(payload_hash, str)
        and len(payload_hash) == 71
        and payload_hash.startswith("sha256:")
        and all(ch in "0123456789abcdef" for ch in payload_hash[7:]),
        "payload_hash_invalid",
    )
    digest = payload_hash[7:]
    slot = int(digest[:16], 16) % CHANNEL_COUNT
    return {
        "channel_id": f"HB:H1:P{slot}",
        "channel_family": CHANNEL_FAMILY,
        "frequency_ratio": 1.0,
        "phase_slot": slot,
        "phase_slot_count": CHANNEL_COUNT,
        "phase_radians": round(2.0 * math.pi * slot / CHANNEL_COUNT, 12),
        "amplitude_ratio": 1.0,
        "derivation": "PAYLOAD_SHA256_FIRST64_MOD_16",
    }


def build_carrier_binding(*, packet_id: str, payload_hash: str, sampled_unix_ms: int) -> dict[str, Any]:
    _require(isinstance(payload_hash, str) and len(payload_hash) == 71 and payload_hash.startswith("sha256:"), "payload_hash_invalid")
    reference = derive_reference_from_unix_ms(sampled_unix_ms)
    channel = derive_channel(payload_hash)
    body = {
        "schema": BINDING_SCHEMA,
        "carrier_profile": PROFILE_SCHEMA,
        "fundamental_mode": "HB",
        "packet_id": packet_id,
        "payload_hash": payload_hash,
        "heartbeat_reference": reference,
        "channel": channel,
        "carrier_grants_admission_authority": False,
        "carrier_grants_execution_authority": False,
        "carrier_grants_credential_authority": False,
        "carrier_grants_routing_authority": False,
        "carrier_grants_transition_authority": False,
        "carrier_grants_receiving_authority": False,
        "credential_authority": "TV/TVC",
        "authority_effect": AUTHORITY_EFFECT,
    }
    return {**body, "binding_sha256": sha256_uri(body)}


def validate_carrier_binding(binding: Mapping[str, Any], *, packet_id: str, payload_hash: str) -> dict[str, Any]:
    _require(isinstance(binding, Mapping), "carrier_binding_object_required")
    _require(binding.get("schema") == BINDING_SCHEMA, "carrier_binding_schema_mismatch")
    _require(binding.get("carrier_profile") == PROFILE_SCHEMA, "carrier_profile_mismatch")
    _require(binding.get("fundamental_mode") == "HB", "carrier_fundamental_mismatch")
    _require(binding.get("packet_id") == packet_id, "carrier_packet_id_mismatch")
    _require(binding.get("payload_hash") == payload_hash, "carrier_payload_hash_mismatch")
    _require(binding.get("credential_authority") == "TV/TVC", "carrier_credential_authority_mismatch")
    _require(binding.get("authority_effect") == AUTHORITY_EFFECT, "carrier_authority_effect_mismatch")
    for field in (
        "carrier_grants_admission_authority",
        "carrier_grants_execution_authority",
        "carrier_grants_credential_authority",
        "carrier_grants_routing_authority",
        "carrier_grants_transition_authority",
        "carrier_grants_receiving_authority",
    ):
        _require(binding.get(field) is False, field + "_must_be_false")

    reference = binding.get("heartbeat_reference")
    _require(isinstance(reference, Mapping), "heartbeat_reference_required")
    expected_reference = derive_reference_from_unix_ms(reference.get("sampled_unix_ms"))
    _require(dict(reference) == expected_reference, "heartbeat_reference_derivation_mismatch")
    channel = binding.get("channel")
    _require(isinstance(channel, Mapping), "carrier_channel_required")
    expected_channel = derive_channel(payload_hash)
    _require(dict(channel) == expected_channel, "carrier_channel_derivation_mismatch")

    body = dict(binding)
    claimed = body.pop("binding_sha256", None)
    _require(claimed == sha256_uri(body), "carrier_binding_sha256_mismatch")
    return dict(binding)


def carrier_profile() -> dict[str, Any]:
    return {
        "schema": PROFILE_SCHEMA,
        "state": "SUPPORTED_MIGRATION_OPTIONAL",
        "fundamental_mode": "HB",
        "reference_frequency_hz": REFERENCE_FREQUENCY_HZ,
        "heartbeat_period_ms": OSCILLATOR_PERIOD_MS,
        "progression_dependency": "OSCILLATOR_ONLY",
        "reference_derivation": "HB32_PROTOCOL_ANCHOR_PLUS_ELAPSED_10MS_QUANTA",
        "binding_schema": BINDING_SCHEMA,
        "channel_family": CHANNEL_FAMILY,
        "channel_count": CHANNEL_COUNT,
        "channel_selection": "PAYLOAD_SHA256_FIRST64_MOD_16",
        "carrier_binding_required": False,
        "legacy_unbound_packets_temporarily_accepted": True,
        "carrier_presence_grants_admission_authority": False,
        "carrier_presence_grants_execution_authority": False,
        "carrier_presence_grants_credential_authority": False,
        "carrier_presence_grants_routing_authority": False,
        "carrier_presence_grants_transition_authority": False,
        "carrier_presence_grants_receiving_authority": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }


__all__ = [
    "PROFILE_SCHEMA", "BINDING_SCHEMA", "CHANNEL_COUNT", "CHANNEL_FAMILY",
    "derive_reference_from_unix_ms", "derive_channel", "build_carrier_binding",
    "validate_carrier_binding", "carrier_profile",
]
