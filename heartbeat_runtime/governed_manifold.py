from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


GOVERNED_MANIFOLD_SCHEMA = "stegverse.heartbeat-governed-manifold-observation/v1"


@dataclass(frozen=True)
class GovernedProjectionDimension:
    """Authority-neutral dimension included in an HB governed-state projection."""

    name: str
    value: Any
    source_ref: str
    observed: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "source_ref": self.source_ref,
            "observed": bool(self.observed),
        }


def governed_manifold_observation(
    *,
    carrier_epoch: int,
    carrier_generation: int,
    dimensions: Iterable[GovernedProjectionDimension | dict[str, Any]],
    transition_refs: Iterable[str] = (),
    authority_boundary_refs: Iterable[str] = (),
) -> dict[str, Any]:
    """Build the canonical HB projection over concurrently changing governed state.

    HB does not serialize the underlying system into a single human decision path.
    It observes a reviewable projection of state and transition evidence while
    remaining non-authorizing. Wall-clock time and carrier cadence are observables,
    not governance authority. Human authority remains attached to the applicable
    transition/admissibility boundary outside the carrier.
    """

    if not isinstance(carrier_epoch, int) or carrier_epoch < 0:
        raise ValueError("carrier_epoch must be a non-negative integer")
    if not isinstance(carrier_generation, int) or carrier_generation < 0:
        raise ValueError("carrier_generation must be a non-negative integer")

    projected: list[dict[str, Any]] = []
    for item in dimensions:
        if isinstance(item, GovernedProjectionDimension):
            row = item.as_dict()
        elif isinstance(item, dict):
            row = dict(item)
        else:
            raise TypeError("dimensions must contain GovernedProjectionDimension or dict values")
        name = row.get("name")
        source_ref = row.get("source_ref")
        if not isinstance(name, str) or not name:
            raise ValueError("projection dimension name is required")
        if not isinstance(source_ref, str) or not source_ref:
            raise ValueError("projection dimension source_ref is required")
        row["observed"] = bool(row.get("observed", True))
        projected.append(row)

    transitions = [str(ref) for ref in transition_refs if str(ref)]
    boundaries = [str(ref) for ref in authority_boundary_refs if str(ref)]

    return {
        "schema": GOVERNED_MANIFOLD_SCHEMA,
        "carrier_epoch": carrier_epoch,
        "carrier_generation": carrier_generation,
        "projection_role": "GOVERNED_MANIFOLD_OBSERVATION",
        "state_model": "MULTI_VARIABLE_CONCURRENT_TRANSITION_SPACE",
        "human_governance_model": "AUTHORITY_OVER_ADMISSIBLE_BOUNDARIES_NOT_PER_TRANSITION_TIMING",
        "dimensions": projected,
        "transition_evidence_refs": transitions,
        "authority_boundary_refs": boundaries,
        "invariants": {
            "heartbeat_is_clock_only": False,
            "heartbeat_is_governance_authority": False,
            "wall_clock_is_governance_authority": False,
            "human_review_is_required_per_machine_transition": False,
            "observation_causes_transition": False,
            "projection_may_be_reviewed_without_advancing_governed_state": True,
            "machine_speed_internal_transitions_may_continue_inside_existing_authority": True,
            "protected_boundary_crossing_requires_external_authority": True,
        },
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


__all__ = [
    "GOVERNED_MANIFOLD_SCHEMA",
    "GovernedProjectionDimension",
    "governed_manifold_observation",
]
