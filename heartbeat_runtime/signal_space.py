from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any, Iterable


@dataclass(frozen=True)
class SignalCoordinate:
    """Authority-neutral coordinate in the coherent carrier signal space.

    `frequency_ratio` is relative to the current fundamental carrier mode. It is
    intentionally dimensionless so the coordinate system does not assume that
    physical wall-clock time is primitive. `phase_radians` locates the mode
    within the coherent family.
    """

    mode_id: str
    frequency_ratio: float = 1.0
    phase_radians: float = 0.0
    amplitude_ratio: float = 1.0

    def __post_init__(self) -> None:
        if not self.mode_id:
            raise ValueError("mode_id is required")
        if self.frequency_ratio <= 0:
            raise ValueError("frequency_ratio must be positive")
        if self.amplitude_ratio < 0:
            raise ValueError("amplitude_ratio must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "frequency_ratio": float(self.frequency_ratio),
            "phase_radians": float(self.phase_radians),
            "amplitude_ratio": float(self.amplitude_ratio),
            "coordinate_role": "STATE_TRANSITION_PROBE",
            "authority_effect": "NONE",
        }


def harmonic_family(
    *,
    harmonics: Iterable[int] = (1, 2, 3),
    phase_slots: int = 1,
    include_subharmonic_half: bool = False,
) -> list[SignalCoordinate]:
    """Construct a finite coherent basis candidate around the HB fundamental."""
    if phase_slots < 1:
        raise ValueError("phase_slots must be >= 1")
    modes: list[SignalCoordinate] = []
    ratios: list[tuple[str, float]] = []
    for harmonic in harmonics:
        if not isinstance(harmonic, int) or harmonic < 1:
            raise ValueError("harmonics must be positive integers")
        ratios.append((f"H{harmonic}", float(harmonic)))
    if include_subharmonic_half:
        ratios.append(("H1/2", 0.5))

    for mode_name, ratio in ratios:
        for slot in range(phase_slots):
            phase = 2.0 * pi * slot / phase_slots
            modes.append(
                SignalCoordinate(
                    mode_id=f"{mode_name}:P{slot}",
                    frequency_ratio=ratio,
                    phase_radians=phase,
                )
            )
    return modes


def coherent_signal_space_candidate(
    *,
    harmonics: Iterable[int] = (1, 2, 3),
    phase_slots: int = 4,
    include_subharmonic_half: bool = True,
) -> dict[str, Any]:
    """Return the currently implemented coordinate-system candidate.

    This is deliberately a candidate rather than a completeness claim. The
    evidence may require additional coordinates or a different operator family.
    """
    modes = harmonic_family(
        harmonics=harmonics,
        phase_slots=phase_slots,
        include_subharmonic_half=include_subharmonic_half,
    )
    return {
        "schema": "stegverse.coherent-signal-space/v0.1",
        "fundamental_mode": "HB",
        "coordinate_hypothesis": ["frequency_ratio", "phase_radians", "amplitude_ratio"],
        "state_transform_candidate": "S_prime = T_alpha(S), alpha in coherent_signal_space",
        "operator_family_hypothesis": True,
        "operator_family_proved": False,
        "coordinate_system_complete": False,
        "modes": [mode.as_dict() for mode in modes],
        "interpretation": {
            "heartbeat_is_fundamental_mode_not_whole_mechanism": True,
            "frequency_parameterizes_state_transformation": True,
            "many_state_transition_manifold_target": True,
            "physical_time_is_not_assumed_primitive": True,
        },
        "authority": {
            "signal_grants_execution_authority": False,
            "frequency_grants_execution_authority": False,
            "phase_grants_execution_authority": False,
            "master_records_role": "RETAIN_OBSERVED_STATE_TRANSITIONS",
        },
    }


__all__ = ["SignalCoordinate", "harmonic_family", "coherent_signal_space_candidate"]
