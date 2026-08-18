from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Iterable

OSCILLATOR_FREQUENCY_HZ = 100.0
OSCILLATOR_PERIOD_MS = 10.0


@dataclass(frozen=True)
class SignalConstraint:
    signal_id: str
    min_frequency_hz: float = 0.0
    max_frequency_hz: float | None = None
    required_event_rate_hz: float = 0.0
    deadline_ms: float | None = None
    simultaneous_units: float = 1.0
    requested_phase_slots: int = 1
    max_jitter_ms: float | None = None
    max_phase_error_deg: float | None = None
    max_frequency_drift_hz: float | None = None


class CarrierEnvelopeError(ValueError):
    pass


def _positive(value: float | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    if value <= 0:
        raise CarrierEnvelopeError("carrier constraints must be positive where specified")
    return value


def _strictest_optional(values: Iterable[float | None]) -> float | None:
    material = [float(v) for v in values if v is not None]
    return min(material) if material else None


def derive_carrier_envelope(
    constraints: Iterable[SignalConstraint],
    *,
    sustainable_max_hz: float,
    events_per_reference_capacity: float,
    growth_reserve_ratio: float = 0.25,
    bounded_margin_ratio: float = 0.10,
    reserve_recalculation_threshold: float = 0.80,
) -> dict[str, Any]:
    """Assess downstream capacity around the fixed independent heartbeat.

    The heartbeat oscillator is not derived here. It is fixed at one reference
    per 10 ms (100 Hz). Signal constraints may be compatible or incompatible
    with that independent carrier, but they may not change, slow, accelerate,
    gate, or authorize it.
    """
    signals = list(constraints)
    if not signals:
        raise CarrierEnvelopeError("at least one signal constraint is required")

    sustainable_max_hz = _positive(sustainable_max_hz) or 0.0
    events_per_reference_capacity = _positive(events_per_reference_capacity) or 0.0
    if sustainable_max_hz < OSCILLATOR_FREQUENCY_HZ:
        raise CarrierEnvelopeError("downstream surface cannot sustain independent 100 Hz heartbeat")
    if not 0 <= growth_reserve_ratio < 1:
        raise CarrierEnvelopeError("growth_reserve_ratio must be in [0,1)")
    if not 0 <= bounded_margin_ratio < 0.5:
        raise CarrierEnvelopeError("bounded_margin_ratio must be in [0,0.5)")
    if not 0 < reserve_recalculation_threshold <= 1:
        raise CarrierEnvelopeError("reserve_recalculation_threshold must be in (0,1]")

    current_composite_load = 0.0
    required_event_rate = 0.0
    max_phase_slots = 1

    for signal in signals:
        if not signal.signal_id:
            raise CarrierEnvelopeError("signal_id is required")
        if signal.min_frequency_hz < 0 or signal.required_event_rate_hz < 0 or signal.simultaneous_units <= 0:
            raise CarrierEnvelopeError(f"invalid non-positive constraint for {signal.signal_id}")
        if signal.min_frequency_hz and float(signal.min_frequency_hz) > OSCILLATOR_FREQUENCY_HZ:
            raise CarrierEnvelopeError(f"{signal.signal_id} requires a carrier faster than independent 100 Hz heartbeat")
        if signal.max_frequency_hz is not None and float(signal.max_frequency_hz) < OSCILLATOR_FREQUENCY_HZ:
            raise CarrierEnvelopeError(f"{signal.signal_id} cannot accept independent 100 Hz heartbeat")
        if signal.deadline_ms is not None and (_positive(signal.deadline_ms) or 1.0) < OSCILLATOR_PERIOD_MS:
            raise CarrierEnvelopeError(f"{signal.signal_id} deadline is shorter than 10 ms heartbeat reference interval")
        current_composite_load += float(signal.simultaneous_units)
        required_event_rate += float(signal.required_event_rate_hz)
        max_phase_slots = max(max_phase_slots, int(signal.requested_phase_slots))

    design_composite_load = current_composite_load * (1.0 + growth_reserve_ratio)
    design_event_rate = required_event_rate * (1.0 + growth_reserve_ratio)
    throughput_capacity_hz = OSCILLATOR_FREQUENCY_HZ * events_per_reference_capacity
    if design_event_rate > throughput_capacity_hz:
        raise CarrierEnvelopeError("downstream event demand exceeds capacity at independent 100 Hz heartbeat")

    phase_slots = max(1, max_phase_slots, ceil(design_composite_load / events_per_reference_capacity))
    phase_offsets_deg = [round((360.0 * index) / phase_slots, 9) for index in range(phase_slots)]

    jitter_tolerance_ms = _strictest_optional(s.max_jitter_ms for s in signals)
    phase_error_tolerance_deg = _strictest_optional(s.max_phase_error_deg for s in signals)
    frequency_drift_tolerance_hz = _strictest_optional(s.max_frequency_drift_hz for s in signals)
    drift = 0.0 if frequency_drift_tolerance_hz is None else float(frequency_drift_tolerance_hz)

    design_capacity_units = max(design_composite_load, events_per_reference_capacity * phase_slots)
    reserve_units = max(0.0, design_capacity_units - current_composite_load)
    reserve_fraction = reserve_units / design_capacity_units if design_capacity_units else 0.0

    return {
        "schema": "stegverse.heartbeat-carrier-envelope/v2",
        "frequency": {
            "rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL",
            "nominal_hz": OSCILLATOR_FREQUENCY_HZ,
            "nominal_period_ms": OSCILLATOR_PERIOD_MS,
            "admissible_min_hz": OSCILLATOR_FREQUENCY_HZ - drift,
            "admissible_max_hz": OSCILLATOR_FREQUENCY_HZ + drift,
            "progression_dependency": "OSCILLATOR_ONLY",
            "downstream_constraints_may_change_frequency": False,
        },
        "phase_plan": {
            "primary_phase_deg": 0.0,
            "phase_slots": phase_slots,
            "phase_offsets_deg": phase_offsets_deg,
            "alternate_phases_are_authority_channels": False,
            "phase_plan_changes_reference_interval": False,
            "purpose": "DOWNSTREAM_REFERENCE_UTILIZATION_ONLY",
        },
        "capacity": {
            "current_composite_load_units": current_composite_load,
            "design_composite_load_units": design_composite_load,
            "design_capacity_units": design_capacity_units,
            "growth_reserve_ratio": growth_reserve_ratio,
            "reserve_units": reserve_units,
            "reserve_fraction": reserve_fraction,
            "events_per_reference_capacity": events_per_reference_capacity,
            "reference_rate_hz": OSCILLATOR_FREQUENCY_HZ,
            "event_capacity_per_second": throughput_capacity_hz,
        },
        "tolerances": {
            "max_jitter_ms": jitter_tolerance_ms,
            "max_phase_error_deg": phase_error_tolerance_deg,
            "max_frequency_drift_hz": frequency_drift_tolerance_hz,
        },
        "recalculation": {
            "reserve_recalculation_threshold": reserve_recalculation_threshold,
            "recalculate_when_reserve_fraction_lte": 1.0 - reserve_recalculation_threshold,
            "triggers": [
                "ADMITTED_SIGNAL_SET_CHANGED",
                "DEADLINE_OR_RETURN_PATH_CHANGED",
                "SUSTAINABLE_CONSUMER_CAPACITY_CHANGED",
                "GROWTH_RESERVE_THRESHOLD_REACHED",
                "PERSISTENT_OBSERVED_FREQUENCY_OR_PHASE_DEVIATION",
            ],
            "recalculation_changes_heartbeat_frequency": False,
        },
        "authority": {
            "heartbeat_grants_execution_authority": False,
            "alternate_phase_grants_execution_authority": False,
            "signal_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "master_records_action_authority": False,
        },
    }


def assess_carrier_observation(
    envelope: dict[str, Any],
    *,
    observed_frequency_hz: float,
    observed_phase_deg: float,
    expected_phase_deg: float = 0.0,
    observed_jitter_ms: float | None = None,
) -> dict[str, Any]:
    """Compare an observed carrier sample with the independent oscillator expectation."""
    frequency = envelope["frequency"]
    tolerances = envelope["tolerances"]
    observed_frequency_hz = float(observed_frequency_hz)
    frequency_error_hz = observed_frequency_hz - float(frequency["nominal_hz"])
    phase_error_deg = ((float(observed_phase_deg) - float(expected_phase_deg) + 180.0) % 360.0) - 180.0

    reasons: list[str] = []
    drift_tol = tolerances.get("max_frequency_drift_hz")
    if drift_tol is not None and abs(frequency_error_hz) > float(drift_tol):
        reasons.append("FREQUENCY_DRIFT_EXCEEDED")
    phase_tol = tolerances.get("max_phase_error_deg")
    if phase_tol is not None and abs(phase_error_deg) > float(phase_tol):
        reasons.append("PHASE_ERROR_EXCEEDED")
    jitter_tol = tolerances.get("max_jitter_ms")
    if observed_jitter_ms is not None and jitter_tol is not None and abs(float(observed_jitter_ms)) > float(jitter_tol):
        reasons.append("JITTER_EXCEEDED")

    return {
        "schema": "stegverse.heartbeat-carrier-deviation-observation/v2",
        "state": "DEVIATION" if reasons else "WITHIN_ENVELOPE",
        "observed_frequency_hz": observed_frequency_hz,
        "expected_nominal_frequency_hz": float(frequency["nominal_hz"]),
        "frequency_error_hz": frequency_error_hz,
        "observed_phase_deg": float(observed_phase_deg),
        "expected_phase_deg": float(expected_phase_deg),
        "phase_error_deg": phase_error_deg,
        "observed_jitter_ms": None if observed_jitter_ms is None else float(observed_jitter_ms),
        "reasons": reasons,
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "heartbeat_grants_execution_authority": False,
    }
