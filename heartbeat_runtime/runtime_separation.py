from __future__ import annotations

from copy import deepcopy


def _subsignals(legacy: dict) -> dict:
    value = legacy.get("subsignals")
    return value if isinstance(value, dict) else {}


def _deviation_observations(deviation: dict | None, source_ref: str) -> list[dict]:
    if not deviation or deviation.get("state") != "DEVIATION":
        return []
    mapping = {
        "FREQUENCY_OUTSIDE_ADMISSIBLE_INTERVAL": "FREQUENCY_DEVIATION",
        "FREQUENCY_DRIFT_EXCEEDED": "FREQUENCY_DEVIATION",
        "PHASE_ERROR_EXCEEDED": "PHASE_DEVIATION",
        "JITTER_EXCEEDED": "JITTER_DEVIATION",
    }
    kinds = []
    for reason in deviation.get("reasons") or []:
        kind = mapping.get(reason)
        if kind and kind not in kinds:
            kinds.append(kind)
    return [
        {
            "signal_id": "carrier_deviation:%s" % kind.lower(),
            "kind": kind,
            "present": True,
            "source_ref": source_ref,
            "authority_effect": "NONE",
        }
        for kind in kinds
    ]


def build_carrier_observation(
    legacy: dict,
    *,
    envelope_ref: str | None = None,
    deviation: dict | None = None,
    deviation_source_ref: str = "runtime:carrier-observation",
) -> dict:
    subsignals = _subsignals(legacy)
    generation = int(legacy.get("generation", 0) or 0)
    reference_frame = "heartbeat_generation:%d" % generation
    observations = []
    for signal_id in sorted(subsignals):
        observations.append(
            {
                "signal_id": signal_id,
                "kind": "SUBSYSTEM_SIGNAL_PRESENCE",
                "present": True,
                "source_ref": "control/heartbeat-subsignals.json#subsignals/%s" % signal_id,
                "authority_effect": "NONE",
            }
        )
    observations.extend(_deviation_observations(deviation, deviation_source_ref))
    carrier = {
        "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
        "reference_frame": reference_frame,
        "frequency_rule": "GATE_PASSBAND_DERIVED",
        "authority_effect": "NONE",
    }
    if envelope_ref:
        carrier.update(
            {
                "envelope_rule": "ADMISSIBLE_FREQUENCY_PHASE_CAPACITY_ENVELOPE",
                "phase_rule": "CALCULATED_MULTI_PHASE_REFERENCE_PLAN",
                "envelope_ref": envelope_ref,
            }
        )
    return {
        "schema": "stegverse.heartbeat-carrier-observation/v1",
        "generation": generation,
        "carrier": carrier,
        "observations": observations,
        "authority": {
            "heartbeat_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
            "master_records_action_authority": False,
        },
    }


def build_control_plane_coordination(legacy: dict, enforcement_signal_refs: list[str] | None = None) -> dict:
    subsignals = _subsignals(legacy)
    generation = int(legacy.get("generation", 0) or 0)
    worker = deepcopy(subsignals.get("worker_coordination") or {})
    federation = deepcopy(subsignals.get("organization_federation"))
    transport_leases = [
        deepcopy(value)
        for _, value in sorted(subsignals.items())
        if isinstance(value, dict) and value.get("kind") == "transport_lease"
    ]
    worker_coordination = {
        "state": worker.get("state", "IDLE"),
        "active_leases": deepcopy(worker.get("active_leases") or []),
        "worker_registry_ref": worker.get("worker_registry_ref", "control/worker-registry.json"),
    }
    return {
        "schema": "stegverse.worker-control-plane-coordination/v1",
        "generation": generation,
        "observed_reference": {
            "carrier_generation": generation,
            "reference_frame": "heartbeat_generation:%d" % generation,
            "heartbeat_is_authority": False,
        },
        "worker_coordination": worker_coordination,
        "transport_leases": transport_leases,
        "organization_federation": federation,
        "enforcement_signal_refs": sorted(set(enforcement_signal_refs or [])),
        "authority": {
            "heartbeat_grants_execution_authority": False,
            "signal_grants_execution_authority": False,
            "master_records_action_authority": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
        },
    }


def project_legacy_registry(legacy: dict, enforcement_signal_refs: list[str] | None = None) -> tuple[dict, dict]:
    """Pure compatibility projection. Never mutates live heartbeat/control-plane state."""
    return (
        build_carrier_observation(legacy),
        build_control_plane_coordination(legacy, enforcement_signal_refs=enforcement_signal_refs),
    )
