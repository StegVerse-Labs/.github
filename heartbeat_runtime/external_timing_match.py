from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ExternalTimingMatchError(ValueError):
    pass


@dataclass(frozen=True)
class ExternalTimingCapability:
    source_id: str
    source_class: str
    monotonic_resolution_ns: int
    timer_floor_ms: float
    observed_jitter_ms: float
    sustainable_period_min_ms: float
    sustainable_period_max_ms: float
    phase_capacity: int
    waveform_family: str
    waveform_signature: str
    workload_capacity_per_pulse: float
    deployment_class: str | None = None


def _positive(name: str, value: float) -> float:
    value = float(value)
    if value <= 0:
        raise ExternalTimingMatchError(f"{name} must be positive")
    return value


def _validate_capability(cap: ExternalTimingCapability) -> None:
    if not cap.source_id or not cap.source_class:
        raise ExternalTimingMatchError("source identity and class are required")
    if cap.monotonic_resolution_ns <= 0:
        raise ExternalTimingMatchError("monotonic_resolution_ns must be positive")
    _positive("timer_floor_ms", cap.timer_floor_ms)
    if cap.observed_jitter_ms < 0:
        raise ExternalTimingMatchError("observed_jitter_ms must be non-negative")
    minimum = _positive("sustainable_period_min_ms", cap.sustainable_period_min_ms)
    maximum = _positive("sustainable_period_max_ms", cap.sustainable_period_max_ms)
    if minimum > maximum:
        raise ExternalTimingMatchError("sustainable period interval is empty")
    if cap.phase_capacity < 1:
        raise ExternalTimingMatchError("phase_capacity must be >= 1")
    if not cap.waveform_family or not cap.waveform_signature:
        raise ExternalTimingMatchError("waveform family and signature are required")
    _positive("workload_capacity_per_pulse", cap.workload_capacity_per_pulse)
    if cap.deployment_class not in {None, "S", "NS"}:
        raise ExternalTimingMatchError("deployment_class must be S, NS, or absent")


def capability_profile(cap: ExternalTimingCapability) -> dict[str, Any]:
    """Normalize an exterior timing source without creating StegVerse authority."""
    _validate_capability(cap)
    return {
        "schema": "stegverse.external-timing-capability/v1",
        "source": {
            "source_id": cap.source_id,
            "source_class": cap.source_class,
            "deployment_class": cap.deployment_class,
            "deployment_class_inferred_from_frequency": False,
        },
        "clock": {
            "monotonic_resolution_ns": int(cap.monotonic_resolution_ns),
            "timer_floor_ms": float(cap.timer_floor_ms),
            "observed_jitter_ms": float(cap.observed_jitter_ms),
            "sustainable_period_min_ms": float(cap.sustainable_period_min_ms),
            "sustainable_period_max_ms": float(cap.sustainable_period_max_ms),
        },
        "waveform": {
            "family": cap.waveform_family,
            "signature": cap.waveform_signature,
            "phase_capacity": int(cap.phase_capacity),
        },
        "workload": {
            "capacity_per_pulse": float(cap.workload_capacity_per_pulse),
        },
        "authority": {
            "authority_effect": "NONE",
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "external_timing_source_grants_authority": False,
            "waveform_match_grants_authority": False,
            "phase_lock_grants_authority": False,
        },
    }


def select_fixed_logical_period(
    profile: dict[str, Any],
    *,
    requested_period_ms: float | None = None,
) -> dict[str, Any]:
    """Select one fixed StegVerse period from the exterior capability interval.

    Once selected, workload does not modify this period. A material timing-source
    change requires an explicit bounded re-profile/re-lock operation.
    """
    clock = profile["clock"]
    minimum = float(clock["sustainable_period_min_ms"])
    maximum = float(clock["sustainable_period_max_ms"])
    floor = float(clock["timer_floor_ms"])
    minimum = max(minimum, floor)
    if minimum > maximum:
        raise ExternalTimingMatchError("host timer floor leaves no sustainable fixed period")

    if requested_period_ms is None:
        selected = (minimum + maximum) / 2.0
        selection_basis = "MIDPOINT_OF_SUSTAINABLE_FIXED_INTERVAL"
    else:
        selected = _positive("requested_period_ms", requested_period_ms)
        if not minimum <= selected <= maximum:
            raise ExternalTimingMatchError("requested fixed period is outside exterior capability")
        selection_basis = "EXPLICIT_COMPATIBLE_FIXED_PERIOD"

    return {
        "schema": "stegverse.external-timing-lock/v1",
        "state": "LOCK_PROFILE_READY",
        "source_id": profile["source"]["source_id"],
        "fixed_logical_period_ms": selected,
        "fixed_logical_frequency_hz": 1000.0 / selected,
        "selection_basis": selection_basis,
        "period_changes_with_workload": False,
        "reprofile_required_for_period_change": True,
        "phase_capacity": int(profile["waveform"]["phase_capacity"]),
        "waveform_family": profile["waveform"]["family"],
        "waveform_signature": profile["waveform"]["signature"],
        "deployment_class": profile["source"].get("deployment_class"),
        "deployment_class_inferred_from_frequency": False,
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }


def assess_timing_observation(
    lock: dict[str, Any],
    *,
    expected_reference_ms: float,
    observed_reference_ms: float,
    expected_phase_deg: float,
    observed_phase_deg: float,
    observed_period_ms: float,
    observed_jitter_ms: float,
    max_clock_offset_ms: float,
    max_phase_error_deg: float,
    max_period_drift_ms: float,
    max_jitter_ms: float,
) -> dict[str, Any]:
    """Evaluate timing residuals without conflating workload with carrier health."""
    fixed_period = float(lock["fixed_logical_period_ms"])
    clock_offset = float(observed_reference_ms) - float(expected_reference_ms)
    phase_error = ((float(observed_phase_deg) - float(expected_phase_deg) + 180.0) % 360.0) - 180.0
    period_drift = float(observed_period_ms) - fixed_period
    jitter = abs(float(observed_jitter_ms))

    reasons: list[str] = []
    if abs(clock_offset) > _positive("max_clock_offset_ms", max_clock_offset_ms):
        reasons.append("CLOCK_OFFSET_EXCEEDED")
    if abs(phase_error) > _positive("max_phase_error_deg", max_phase_error_deg):
        reasons.append("PHASE_ERROR_EXCEEDED")
    if abs(period_drift) > _positive("max_period_drift_ms", max_period_drift_ms):
        reasons.append("PERIOD_DRIFT_EXCEEDED")
    if jitter > _positive("max_jitter_ms", max_jitter_ms):
        reasons.append("JITTER_EXCEEDED")

    return {
        "schema": "stegverse.external-timing-residual/v1",
        "state": "LOSS_OF_LOCK" if reasons else "LOCKED",
        "source_id": lock["source_id"],
        "fixed_logical_period_ms": fixed_period,
        "clock_offset_ms": clock_offset,
        "phase_error_deg": phase_error,
        "period_drift_ms": period_drift,
        "observed_jitter_ms": jitter,
        "reasons": reasons,
        "workload_activity_considered_timing_deviation": False,
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
    }


def assess_workload_health(
    profile: dict[str, Any],
    *,
    work_units_per_pulse: float,
    underload_ratio: float = 0.10,
    elevated_ratio: float = 0.75,
    saturated_ratio: float = 0.95,
) -> dict[str, Any]:
    """Classify workload health independently from heartbeat cadence."""
    capacity = float(profile["workload"]["capacity_per_pulse"])
    work = max(0.0, float(work_units_per_pulse))
    if not (0 <= underload_ratio < elevated_ratio < saturated_ratio <= 1.0):
        raise ExternalTimingMatchError("workload thresholds must be ordered within [0,1]")
    ratio = work / capacity
    if ratio > 1.0:
        state = "OVERLOADED"
    elif ratio >= saturated_ratio:
        state = "SATURATED"
    elif ratio >= elevated_ratio:
        state = "ELEVATED"
    elif ratio <= underload_ratio:
        state = "UNDERLOAD"
    else:
        state = "NORMAL"
    return {
        "schema": "stegverse.heartbeat-workload-health/v1",
        "state": state,
        "work_units_per_pulse": work,
        "capacity_per_pulse": capacity,
        "load_ratio": ratio,
        "heartbeat_period_changes_with_load": False,
        "timing_lock_state_derived_from_workload": False,
        "authority_effect": "NONE",
    }
