from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Iterable


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
    """Derive an authority-neutral heartbeat carrier envelope.

    The result intentionally does not schedule, dispatch, issue claims, route, or
    grant authority. It only calculates a frequency/phase/capacity reference
    envelope that another admitted runtime may choose to produce.
    """
    signals = list(constraints)
    if not signals:
        raise CarrierEnvelopeError("at least one admitted signal constraint is required")

    sustainable_max_hz = _positive(sustainable_max_hz) or 0.0
    events_per_reference_capacity = _positive(events_per_reference_capacity) or 0.0
    if not 0 <= growth_reserve_ratio < 1:
        raise CarrierEnvelopeError("growth_reserve_ratio must be in [0,1)")
    if not 0 <= bounded_margin_ratio < 0.5:
        raise CarrierEnvelopeError("bounded_margin_ratio must be in [0,0.5)")
    if not 0 < reserve_recalculation_threshold <= 1:
        raise CarrierEnvelopeError("reserve_recalculation_threshold must be in (0,1]")

    lower_bounds = []
    upper_bounds = [sustainable_max_hz]
    current_composite_load = 0.0
    required_event_rate = 0.0
    max_phase_slots = 1

    for signal in signals:
        if not signal.signal_id:
            raise CarrierEnvelopeError("signal_id is required")
        if signal.min_frequency_hz < 0 or signal.required_event_rate_hz < 0 or signal.simultaneous_units <= 0:
            raise CarrierEnvelopeError(f"invalid non-positive constraint for {signal.signal_id}")
        if signal.max_frequency_hz is not None:
            upper_bounds.append(_positive(signal.max_frequency_hz) or 0.0)
        if signal.min_frequency_hz:
            lower_bounds.append(float(signal.min_frequency_hz))
        if signal.deadline_ms is not None:
            lower_bounds.append(1000.0 / (_positive(signal.deadline_ms) or 1.0))
        current_composite_load += float(signal.simultaneous_units)
        required_event_rate += float(signal.required_event_rate_hz)
        max_phase_slots = max(max_phase_slots, int(signal.requested_phase_slots))

    design_composite_load = current_composite_load * (1.0 + growth_reserve_ratio)
    design_event_rate = required_event_rate * (1.0 + growth_reserve_ratio)
    throughput_floor_hz = design_event_rate / events_per_reference_capacity
    lower_bounds.append(throughput_floor_hz)

    f_min_hz = max(lower_bounds or [0.0])
    f_max_hz = min(upper_bounds)
    if f_min_hz <= 0:
        raise CarrierEnvelopeError("derived minimum frequency must be positive")
    if f_min_hz > f_max_hz:
        raise CarrierEnvelopeError("no admissible carrier frequency interval exists")

    width = f_max_hz - f_min_hz
    edge_margin = width * bounded_margin_ratio
    nominal_low = f_min_hz + edge_margin
    nominal_high = f_max_hz - edge_margin
    nominal_frequency_hz = (nominal_low + nominal_high) / 2.0

    phase_slots = max(1, max_phase_slots, ceil(design_composite_load / events_per_reference_capacity))
    phase_offsets_deg = [round((360.0 * index) / phase_slots, 9) for index in range(phase_slots)]

    jitter_tolerance_ms = _strictest_optional(s.max_jitter_ms for s in signals)
    phase_error_tolerance_deg = _strictest_optional(s.max_phase_error_deg for s in signals)
    frequency_drift_tolerance_hz = _strictest_optional(s.max_frequency_drift_hz for s in signals)

    design_capacity_units = max(design_composite_load, events_per_reference_capacity * phase_slots)
    reserve_units = max(0.0, design_capacity_units - current_composite_load)
    reserve_fraction = reserve_units / design_capacity_units if design_capacity_units else 0.0

    return {
        "schema": "stegverse.heartbeat-carrier-envelope/v1",
        "frequency": {
            "rule": "GATE_PASSBAND_DERIVED",
            "admissible_min_hz": f_min_hz,
            "admissible_max_hz": f_max_hz,
            "nominal_hz": nominal_frequency_hz,
            "nominal_period_ms": 1000.0 / nominal_frequency_hz,
            "bounded_edge_margin_hz": edge_margin,
            "throughput_floor_hz": throughput_floor_hz,
        },
        "phase_plan": {
            "primary_phase_deg": 0.0,
            "phase_slots": phase_slots,
            "phase_offsets_deg": phase_offsets_deg,
            "alternate_phases_are_authority_channels": False,
            "purpose": "OFF_BEAT_AND_INTERMITTENT_REFERENCE_OPPORTUNITIES",
        },
        "capacity": {
            "current_composite_load_units": current_composite_load,
            "design_composite_load_units": design_composite_load,
            "design_capacity_units": design_capacity_units,
            "growth_reserve_ratio": growth_reserve_ratio,
            "reserve_units": reserve_units,
            "reserve_fraction": reserve_fraction,
            "events_per_reference_capacity": events_per_reference_capacity,
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
                "GATE_OR_PASSBAND_CHANGED",
                "DEADLINE_OR_RETURN_PATH_CHANGED",
                "SUSTAINABLE_CARRIER_CAPACITY_CHANGED",
                "GROWTH_RESERVE_THRESHOLD_REACHED",
                "PERSISTENT_FREQUENCY_OR_PHASE_DEVIATION",
            ],
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
    """Compare an observed carrier sample with the calculated envelope."""
    frequency = envelope["frequency"]
    tolerances = envelope["tolerances"]
    observed_frequency_hz = float(observed_frequency_hz)
    frequency_error_hz = observed_frequency_hz - float(frequency["nominal_hz"])
    phase_error_deg = ((float(observed_phase_deg) - float(expected_phase_deg) + 180.0) % 360.0) - 180.0

    reasons: list[str] = []
    if not (float(frequency["admissible_min_hz"]) <= observed_frequency_hz <= float(frequency["admissible_max_hz"])):
        reasons.append("FREQUENCY_OUTSIDE_ADMISSIBLE_INTERVAL")
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
        "schema": "stegverse.heartbeat-carrier-deviation-observation/v1",
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
