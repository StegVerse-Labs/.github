from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .intr_derived_carrier import (
    DerivedCarrierError,
    derive_intr_carrier_signal,
    recover_intr_packet_bytes,
)

SIGNAL_DIR_REL = Path("control/heartbeat-derived-signals.d")
EVENT_LOG_REL = Path("events/heartbeat-derived-carrier.jsonl")
SIGNAL_SCHEMA = "stegverse.heartbeat-intr-derived-carrier/v1"
EVENT_SCHEMA = "stegverse.heartbeat-intr-derived-carrier-event/v1"


class LocalDerivedCarrierError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def signal_sha256(signal: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(dict(signal))).hexdigest()


def _safe_name(signal_id: str) -> str:
    digest = hashlib.sha256(signal_id.encode("utf-8")).hexdigest()
    return f"{digest}.json"


def propagate_local_intr_subsignal(
    *,
    root: Path,
    packet_id: str,
    payload_hash: str,
    sampled_unix_ms: int,
    packet_bytes: bytes,
    intr_transport_profile: str,
    boundary_from: str,
    boundary_to: str,
    packet_receipt_hash: str,
) -> dict[str, Any]:
    """Persist one deterministic HB-derived InTr carrier signal locally.

    This is a carrier/materialization operation only. It never advances HB and
    never invokes task-control, routing, admission, execution, receipt, claim,
    fence, credential, transition, or receiving authority.
    """
    runtime_root = root.expanduser().resolve()
    runtime_root.mkdir(parents=True, exist_ok=True)
    try:
        signal = derive_intr_carrier_signal(
            packet_id=packet_id,
            payload_hash=payload_hash,
            sampled_unix_ms=sampled_unix_ms,
            packet_bytes=packet_bytes,
            intr_transport_profile=intr_transport_profile,
            boundary_from=boundary_from,
            boundary_to=boundary_to,
            packet_receipt_hash=packet_receipt_hash,
        )
    except DerivedCarrierError as exc:
        raise LocalDerivedCarrierError(str(exc)) from exc

    signal_digest = signal_sha256(signal)
    signal_dir = runtime_root / SIGNAL_DIR_REL
    signal_dir.mkdir(parents=True, exist_ok=True)
    signal_path = signal_dir / _safe_name(str(signal["signal_id"]))
    serialized = json.dumps(signal, sort_keys=True, indent=2) + "\n"

    newly_materialized = False
    if signal_path.exists():
        existing = signal_path.read_text(encoding="utf-8")
        if existing != serialized:
            raise LocalDerivedCarrierError("derived_carrier_write_once_collision")
    else:
        temporary = signal_path.with_suffix(".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(signal_path)
        newly_materialized = True

    # Re-read and reconstruct before any event evidence is emitted.
    persisted = json.loads(signal_path.read_text(encoding="utf-8"))
    try:
        recovered = recover_intr_packet_bytes(persisted)
    except DerivedCarrierError as exc:
        raise LocalDerivedCarrierError(str(exc)) from exc
    if recovered != packet_bytes:
        raise LocalDerivedCarrierError("derived_carrier_exact_packet_recovery_failed")
    if signal_sha256(persisted) != signal_digest:
        raise LocalDerivedCarrierError("derived_carrier_persisted_signal_digest_mismatch")

    event = {
        "schema": EVENT_SCHEMA,
        "event": "HB_DERIVED_INTR_SUBSIGNAL_PROPAGATED_LOCAL",
        "signal_id": signal["signal_id"],
        "signal_sha256": signal_digest,
        "signal_ref": str(signal_path.relative_to(runtime_root)),
        "heartbeat_epoch": signal["carrier"]["heartbeat_epoch"],
        "heartbeat_reference": signal["carrier"]["heartbeat_reference"],
        "carrier_channel_id": signal["carrier"]["channel_id"],
        "carrier_binding_sha256": signal["carrier"]["carrier_binding_sha256"],
        "packet_id": signal["intr"]["packet_id"],
        "packet_sha256": signal["intr"]["packet_sha256"],
        "packet_receipt_hash": signal["intr"]["packet_receipt_hash"],
        "exact_packet_recovered": True,
        "heartbeat_progression_effect": "NONE",
        "worker_coordinator_invoked": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_CARRIER_OBSERVATION_ONLY",
    }

    if newly_materialized:
        event_path = runtime_root / EVENT_LOG_REL
        event_path.parent.mkdir(parents=True, exist_ok=True)
        with event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    return {
        "schema": "stegverse.heartbeat-intr-local-propagation-result/v1",
        "state": "PROPAGATED_LOCAL" if newly_materialized else "ALREADY_PROPAGATED_IDENTICAL",
        "signal_ref": str(signal_path.relative_to(runtime_root)),
        "event_log_ref": str(EVENT_LOG_REL),
        "signal_sha256": signal_digest,
        "heartbeat_epoch": signal["carrier"]["heartbeat_epoch"],
        "heartbeat_reference": signal["carrier"]["heartbeat_reference"],
        "carrier_channel_id": signal["carrier"]["channel_id"],
        "packet_id": signal["intr"]["packet_id"],
        "packet_sha256": signal["intr"]["packet_sha256"],
        "exact_packet_recovered": True,
        "heartbeat_progression_effect": "NONE",
        "worker_coordinator_invoked": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_CARRIER_ONLY",
    }


def recover_local_intr_subsignal(*, root: Path, signal_ref: str) -> bytes:
    runtime_root = root.expanduser().resolve()
    path = (runtime_root / signal_ref).resolve()
    try:
        path.relative_to(runtime_root)
    except ValueError as exc:
        raise LocalDerivedCarrierError("derived_carrier_signal_ref_outside_runtime") from exc
    if not path.is_file():
        raise LocalDerivedCarrierError("derived_carrier_signal_missing")
    try:
        signal = json.loads(path.read_text(encoding="utf-8"))
        return recover_intr_packet_bytes(signal)
    except (json.JSONDecodeError, DerivedCarrierError) as exc:
        raise LocalDerivedCarrierError(str(exc)) from exc


__all__ = [
    "SIGNAL_DIR_REL",
    "EVENT_LOG_REL",
    "LocalDerivedCarrierError",
    "propagate_local_intr_subsignal",
    "recover_local_intr_subsignal",
    "signal_sha256",
]
