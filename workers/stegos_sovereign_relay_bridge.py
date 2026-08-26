from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping

REQUIRED_STEGOS_SURFACES = (
    "stegos/network_capacity_esrl_runtime.py",
    "stegos/network_capacity_esrl_binding.py",
    "stegos/sovereign_ephemeral_node_adapter.py",
    "stegos/ephemeral_relay_service.py",
)


def _complete_stegos_root(path: Path) -> bool:
    return path.is_dir() and all((path / rel).is_file() for rel in REQUIRED_STEGOS_SURFACES)


def find_stegos_root(control_root: Path, env: Mapping[str, str] | None = None) -> Path | None:
    values = os.environ if env is None else env
    candidates: list[Path] = []
    explicit = values.get("STEGVERSE_STEGOS_ROOT")
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(
        [
            control_root.parent / "StegOS",
            control_root.parent.parent / "StegOS",
            Path.home() / "StegVerse-Labs" / "StegOS",
            Path.home() / "stegverse" / "StegOS",
            Path.home() / ".stegverse" / "source" / "StegOS",
        ]
    )
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        if _complete_stegos_root(resolved):
            return resolved
    return None


def materialize_relay(
    *,
    control_root: Path,
    stegos_root: Path,
    runtime_base: Path,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    if not _complete_stegos_root(stegos_root):
        raise RuntimeError("stegos_relay_source_surface_incomplete")
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))

    from stegos.network_capacity_esrl_binding import build_ephemeral_relay_lease_binding
    from stegos.network_capacity_esrl_runtime import materialize_ephemeral_relay, validate_runtime_materialization_evidence
    from stegos.sovereign_ephemeral_node_adapter import SovereignEphemeralNodeAdapter
    from stegos.sovereign_network_capacity import ExpansionAssessment

    if request.get("schema") != "stegverse.sovereign-relay-materialization-request/v1":
        raise RuntimeError("unsupported_relay_materialization_request_schema")
    if request.get("admission_state") != "ADMITTED":
        raise RuntimeError("relay_materialization_request_not_admitted")
    if request.get("credential_authority") != "TV/TVC":
        raise RuntimeError("credential_authority_must_remain_tv_tvc")
    if request.get("route_admitted") is not False or request.get("outbound_egress_authorized") is not False:
        raise RuntimeError("relay_materialization_request_cannot_admit_route_or_egress")

    assessment = ExpansionAssessment(
        eligible=True,
        blockers=(),
        pressure_score=float(request["pressure_score"]),
        regional_spare_ratio=float(request["regional_spare_ratio"]),
        requested_additional_capacity=float(request["requested_additional_capacity"]),
        authority_effect="NONE",
    )
    binding = build_ephemeral_relay_lease_binding(
        assessment=assessment,
        capacity_event_id=str(request["capacity_event_id"]),
        region_id=str(request["region_id"]),
        source_receipt_id=str(request["source_receipt_id"]),
        consequence_id=str(request["consequence_id"]),
        consequence_registry_hash=str(request["consequence_registry_hash"]),
        implementation_ref=str(request["implementation_ref"]),
        node_kv_state_root=str(request["node_kv_state_root"]),
        generation=int(request["generation"]),
        max_transport_operations=int(request.get("max_transport_operations", 1)),
    )
    adapter = SovereignEphemeralNodeAdapter(
        sovereign_source_root=control_root,
        runtime_base=runtime_base,
        stegos_source_root=stegos_root,
    )
    result = materialize_ephemeral_relay(
        binding=binding,
        compute=adapter,
        materializer=adapter,
        identity=adapter,
        rendezvous_adapter=adapter,
    )
    validate_runtime_materialization_evidence(result.evidence)
    return {
        "evidence": dict(result.evidence),
        "runtime": dict(result.runtime),
        "rendezvous": dict(result.rendezvous),
    }
