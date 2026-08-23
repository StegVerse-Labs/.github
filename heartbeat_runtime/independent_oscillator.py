from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

OSCILLATOR_PERIOD_NS = 10_000_000
OSCILLATOR_PERIOD_MS = 10
REFERENCE_FREQUENCY_HZ = 100
FREQUENCY_RULE = "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
MECHANISM = "INDEPENDENT_PHASE_OSCILLATOR"
PROTOCOL_ANCHOR_EPOCH = 32
PROTOCOL_ANCHOR_UNIX_NS = 1_787_511_600_000_000_000
PROTOCOL_ANCHOR_TIME_UTC = "2026-08-23T19:00:00.000Z"
PROTOCOL_ANCHOR_REF = "control/heartbeat-protocol-anchor.json"


def iso8601_to_unix_ns(value: str | None) -> int | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1_000_000_000)


def unix_ns_to_iso8601(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000_000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _canonical_protocol_oscillator() -> dict[str, Any]:
    return {
        "mechanism": MECHANISM,
        "period_ns": OSCILLATOR_PERIOD_NS,
        "phase_travel_time_ms": OSCILLATOR_PERIOD_MS,
        "reference_increment_interval_ms": OSCILLATOR_PERIOD_MS,
        "reference_frequency_hz": REFERENCE_FREQUENCY_HZ,
        "anchor_epoch": PROTOCOL_ANCHOR_EPOCH,
        "anchor_unix_ns": PROTOCOL_ANCHOR_UNIX_NS,
        "anchor_time_utc": PROTOCOL_ANCHOR_TIME_UTC,
        "anchor_source": PROTOCOL_ANCHOR_REF,
        "protocol_anchor_is_authority": True,
        "progression_dependency": "OSCILLATOR_ONLY",
        "continuous_process_required": False,
        "resident_sampler_required_for_progression": False,
        "downstream_gating": False,
        "observation_is_causal": False,
    }


def normalize_oscillator(state: dict[str, Any], *, now_ns: int) -> dict[str, Any]:
    """Return the heartbeat oscillator used to derive the reference at ``now_ns``.

    At and after the protocol cutover, every observer uses the same durable
    protocol anchor.  No resident process has to remain alive between samples:
    the reference is a pure function of the protocol anchor and elapsed phase.
    Missed references therefore exist independently of observation, exactly as
    required by the heartbeat semantics handoff.

    Samples before the protocol cutover retain the historical migration logic
    solely so immutable HB29/HB30/HB31 evidence and pre-cutover deterministic
    tests remain replayable.  Historical local anchors have no authority over
    references at or after the protocol cutover.
    """
    if now_ns >= PROTOCOL_ANCHOR_UNIX_NS:
        return _canonical_protocol_oscillator()

    oscillator = state.get("oscillator")
    if isinstance(oscillator, dict):
        anchor_epoch = oscillator.get("anchor_epoch")
        anchor_unix_ns = oscillator.get("anchor_unix_ns")
        period_ns = oscillator.get("period_ns")
        if isinstance(anchor_epoch, int) and isinstance(anchor_unix_ns, int) and period_ns == OSCILLATOR_PERIOD_NS:
            return {
                "mechanism": MECHANISM,
                "period_ns": OSCILLATOR_PERIOD_NS,
                "phase_travel_time_ms": OSCILLATOR_PERIOD_MS,
                "reference_increment_interval_ms": OSCILLATOR_PERIOD_MS,
                "reference_frequency_hz": REFERENCE_FREQUENCY_HZ,
                "anchor_epoch": anchor_epoch,
                "anchor_unix_ns": anchor_unix_ns,
                "progression_dependency": "OSCILLATOR_ONLY",
                "downstream_gating": False,
                "observation_is_causal": False,
                "historical_pre_protocol_anchor": True,
            }

    sampled_epoch = int(state.get("epoch", 0))
    legacy_cutover = state.get("legacy_cutover") or {}
    is_initial_hb29_cutover = (
        sampled_epoch == 29
        and int(legacy_cutover.get("legacy_epoch", 29)) == 29
        and legacy_cutover.get("closed") is not True
    )
    if is_initial_hb29_cutover:
        sampled_ns = max(0, now_ns - OSCILLATOR_PERIOD_NS)
    else:
        sampled_ns = iso8601_to_unix_ns(state.get("last_cycle_at"))
        if sampled_ns is None or sampled_ns > now_ns:
            sampled_ns = now_ns
    return {
        "mechanism": MECHANISM,
        "period_ns": OSCILLATOR_PERIOD_NS,
        "phase_travel_time_ms": OSCILLATOR_PERIOD_MS,
        "reference_increment_interval_ms": OSCILLATOR_PERIOD_MS,
        "reference_frequency_hz": REFERENCE_FREQUENCY_HZ,
        "anchor_epoch": sampled_epoch,
        "anchor_unix_ns": sampled_ns,
        "progression_dependency": "OSCILLATOR_ONLY",
        "downstream_gating": False,
        "observation_is_causal": False,
        "historical_pre_protocol_anchor": True,
    }


def derive_reference(oscillator: dict[str, Any], *, now_ns: int) -> dict[str, int]:
    period_ns = int(oscillator["period_ns"])
    anchor_epoch = int(oscillator["anchor_epoch"])
    anchor_ns = int(oscillator["anchor_unix_ns"])
    if period_ns != OSCILLATOR_PERIOD_NS:
        raise RuntimeError("heartbeat oscillator period must remain exactly 10 ms")
    if now_ns < anchor_ns:
        raise RuntimeError("heartbeat oscillator sample precedes anchor")
    elapsed_ns = now_ns - anchor_ns
    elapsed_quanta, phase_offset_ns = divmod(elapsed_ns, period_ns)
    return {
        "epoch": anchor_epoch + elapsed_quanta,
        "generation": anchor_epoch + elapsed_quanta,
        "elapsed_quanta": elapsed_quanta,
        "phase_offset_ns": phase_offset_ns,
        "sampled_unix_ns": now_ns,
    }


def current_reference(*, now_ns: int) -> dict[str, int]:
    """Derive the canonical heartbeat reference without persisted runtime state."""
    if now_ns < PROTOCOL_ANCHOR_UNIX_NS:
        raise RuntimeError("canonical heartbeat protocol anchor is not active yet")
    return derive_reference(_canonical_protocol_oscillator(), now_ns=now_ns)


def sample_state(state: dict[str, Any], *, now_ns: int) -> dict[str, Any]:
    oscillator = normalize_oscillator(state, now_ns=now_ns)
    reference = derive_reference(oscillator, now_ns=now_ns)
    sampled = dict(state)
    sampled["epoch"] = reference["epoch"]
    sampled["generation"] = reference["generation"]
    sampled["reference_frame"] = f"heartbeat_epoch:{reference['epoch']}"
    sampled["frequency_rule"] = FREQUENCY_RULE
    sampled["last_cycle_at"] = unix_ns_to_iso8601(now_ns)
    sampled["activation_state"] = "ACTIVE"
    sampled["authority_effect"] = "NONE"
    sampled["continuous_process_required"] = False
    sampled["resident_sampler_required_for_progression"] = False
    sampled["oscillator"] = {
        **oscillator,
        "sampled_unix_ns": now_ns,
        "sampled_reference_epoch": reference["epoch"],
        "phase_offset_ns": reference["phase_offset_ns"],
        "elapsed_quanta_from_anchor": reference["elapsed_quanta"],
        "snapshot_is_observation_only": True,
    }
    return sampled


__all__ = [
    "OSCILLATOR_PERIOD_NS",
    "OSCILLATOR_PERIOD_MS",
    "REFERENCE_FREQUENCY_HZ",
    "FREQUENCY_RULE",
    "MECHANISM",
    "PROTOCOL_ANCHOR_EPOCH",
    "PROTOCOL_ANCHOR_UNIX_NS",
    "PROTOCOL_ANCHOR_TIME_UTC",
    "PROTOCOL_ANCHOR_REF",
    "current_reference",
    "derive_reference",
    "normalize_oscillator",
    "sample_state",
]
