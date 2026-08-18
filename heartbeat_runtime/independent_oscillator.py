from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

OSCILLATOR_PERIOD_NS = 10_000_000
OSCILLATOR_PERIOD_MS = 10
REFERENCE_FREQUENCY_HZ = 100
FREQUENCY_RULE = "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
MECHANISM = "INDEPENDENT_PHASE_OSCILLATOR"


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


def normalize_oscillator(state: dict[str, Any], *, now_ns: int) -> dict[str, Any]:
    """Return a stable oscillator anchor without making observation causal.

    Existing pre-fix carrier snapshots are migrated by treating their persisted
    epoch and observation timestamp as the last known sample of an oscillator
    that continued independently after that sample. No worker/task state is
    consulted.
    """
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
            }

    sampled_epoch = int(state.get("epoch", 0))
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
    "derive_reference",
    "normalize_oscillator",
    "sample_state",
]
