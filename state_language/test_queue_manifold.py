"""Deterministic clustered test-queue manifold governance.

This module is an orchestration/planning layer only. Individual tests remain
directly executable without HeartBeat, G18, or WorkerCoordinator. HeartBeat may
be attached as an optional observation reference, but neither it nor this
controller grants execution, credential, claim, or fence authority.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


DESCRIPTOR_SCHEMA = "stegverse.test-queue-manifold-descriptor/v1"
SNAPSHOT_SCHEMA = "stegverse.test-queue-manifold-snapshot/v1"
BUNDLE_SCHEMA = "stegverse.test-queue-manifold-bundle-candidate/v1"
DISPOSITION_SCHEMA = "stegverse.test-queue-manifold-disposition/v1"

TERMINAL_STATES = frozenset({
    "EXECUTED",
    "SUPERSEDED_BY_EVIDENCE",
    "SATISFIED_BY_BUNDLE",
    "NO_LONGER_APPLICABLE",
})
NONTERMINAL_STATES = frozenset({"PENDING", "READY", "CLAIMED", "BLOCKED"})
ALL_STATES = TERMINAL_STATES | NONTERMINAL_STATES
TERMINAL_DISPOSITIONS_REQUIRING_EVIDENCE = TERMINAL_STATES
HEARTBEAT_ALLOWED_AUTHORITY_EFFECTS = frozenset({
    "NONE",
    "NONE_OBSERVATION_ONLY",
})


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _unique_strings(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        value = str(item)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def validate_descriptor(descriptor: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "test_id",
        "canonical_input_hash",
        "goal_transition",
        "source_state",
        "target_state",
        "transition_class",
        "required_capabilities",
        "required_evidence",
        "dependencies",
        "authority_class",
        "cost_capacity",
        "urgency",
        "expected_information_gain",
        "coherency_group",
        "lifecycle_state",
        "execution_claim_ref",
        "person_specific_route",
        "authority_effect",
    }
    missing = sorted(required - set(descriptor))
    if missing:
        raise ValueError("descriptor missing required fields: " + ", ".join(missing))
    if descriptor.get("schema") != DESCRIPTOR_SCHEMA:
        raise ValueError("descriptor schema mismatch")
    if not descriptor.get("test_id"):
        raise ValueError("test_id is required")
    canonical_hash = descriptor.get("canonical_input_hash")
    if (
        not isinstance(canonical_hash, str)
        or not canonical_hash.startswith("sha256:")
        or len(canonical_hash) != 71
    ):
        raise ValueError("canonical_input_hash must be sha256:<64 hex>")
    try:
        int(canonical_hash.split(":", 1)[1], 16)
    except ValueError as exc:
        raise ValueError("canonical_input_hash must be hexadecimal") from exc
    if descriptor.get("lifecycle_state") not in ALL_STATES:
        raise ValueError("unsupported lifecycle state")
    if descriptor.get("person_specific_route") is not False:
        raise ValueError("person-specific test routes are prohibited")
    if descriptor.get("authority_effect") != "NONE":
        raise ValueError("test descriptor cannot grant authority")
    if not isinstance(descriptor.get("required_capabilities"), list):
        raise ValueError("required_capabilities must be an array")
    if not isinstance(descriptor.get("required_evidence"), list):
        raise ValueError("required_evidence must be an array")
    if not isinstance(descriptor.get("dependencies"), list):
        raise ValueError("dependencies must be an array")
    cost = descriptor.get("cost_capacity")
    if not isinstance(cost, Mapping):
        raise ValueError("cost_capacity must be an object")
    if not isinstance(cost.get("cost_units"), (int, float)) or cost["cost_units"] < 0:
        raise ValueError("cost_units must be non-negative")
    if not isinstance(cost.get("capacity_units"), (int, float)) or cost["capacity_units"] <= 0:
        raise ValueError("capacity_units must be positive")
    urgency = descriptor.get("urgency")
    if not isinstance(urgency, int) or not 0 <= urgency <= 100:
        raise ValueError("urgency must be an integer from 0 to 100")
    info = descriptor.get("expected_information_gain")
    if not isinstance(info, (int, float)) or info < 0:
        raise ValueError("expected_information_gain must be non-negative")
    if descriptor.get("lifecycle_state") == "CLAIMED" and not descriptor.get("execution_claim_ref"):
        raise ValueError("CLAIMED test requires independently admitted execution_claim_ref")


def _validate_heartbeat_reference(observation: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if observation is None:
        return None
    authority_effect = observation.get("authority_effect")
    if authority_effect not in HEARTBEAT_ALLOWED_AUTHORITY_EFFECTS:
        raise ValueError("Heartbeat/reference observation cannot grant queue authority")
    if observation.get("execution_authority") not in (None, "NONE", False):
        raise ValueError("Heartbeat/reference observation cannot grant execution authority")
    if observation.get("credential_authority") not in (None, "NONE"):
        raise ValueError("Heartbeat/reference observation cannot grant credential authority")
    return {
        "schema": observation.get("schema"),
        "carrier_epoch": observation.get("carrier_epoch"),
        "carrier_generation": observation.get("carrier_generation"),
        "authority_effect": authority_effect,
        "reference_only": True,
    }


def _descriptor_readiness(
    descriptor: Mapping[str, Any],
    *,
    terminal_test_ids: set[str],
    available_capabilities: set[str],
    available_evidence: set[str],
) -> tuple[str, list[str]]:
    state = str(descriptor["lifecycle_state"])
    if state in TERMINAL_STATES or state == "CLAIMED":
        return state, []

    blockers: list[str] = []
    missing_dependencies = [
        dep for dep in descriptor["dependencies"] if dep not in terminal_test_ids
    ]
    missing_capabilities = [
        cap for cap in descriptor["required_capabilities"] if cap not in available_capabilities
    ]
    missing_evidence = [
        ref for ref in descriptor["required_evidence"] if ref not in available_evidence
    ]
    if missing_dependencies:
        blockers.append("dependencies:" + ",".join(sorted(missing_dependencies)))
    if missing_capabilities:
        blockers.append("capabilities:" + ",".join(sorted(missing_capabilities)))
    if missing_evidence:
        blockers.append("evidence:" + ",".join(sorted(missing_evidence)))
    return ("BLOCKED", blockers) if blockers else ("READY", [])


def build_queue_manifold(
    descriptors: Sequence[Mapping[str, Any]],
    *,
    manifold_version: int,
    available_capabilities: Iterable[str] = (),
    available_evidence: Iterable[str] = (),
    heartbeat_observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an authority-neutral, deterministic queue-manifold snapshot."""

    if not isinstance(manifold_version, int) or manifold_version < 1:
        raise ValueError("manifold_version must be a positive integer")

    by_id: dict[str, dict[str, Any]] = {}
    for raw in descriptors:
        descriptor = dict(raw)
        validate_descriptor(descriptor)
        test_id = str(descriptor["test_id"])
        if test_id in by_id:
            raise ValueError("duplicate test_id in queue manifold")
        by_id[test_id] = descriptor

    terminal_ids = {
        test_id
        for test_id, descriptor in by_id.items()
        if descriptor["lifecycle_state"] in TERMINAL_STATES
    }
    capabilities = set(_unique_strings(available_capabilities))
    evidence = set(_unique_strings(available_evidence))

    projected: list[dict[str, Any]] = []
    for test_id in sorted(by_id):
        descriptor = by_id[test_id]
        projected_state, blockers = _descriptor_readiness(
            descriptor,
            terminal_test_ids=terminal_ids,
            available_capabilities=capabilities,
            available_evidence=evidence,
        )
        projected.append({
            "test_id": test_id,
            "canonical_input_hash": descriptor["canonical_input_hash"],
            "goal_transition": descriptor["goal_transition"],
            "source_state": descriptor["source_state"],
            "target_state": descriptor["target_state"],
            "transition_class": descriptor["transition_class"],
            "required_capabilities": list(descriptor["required_capabilities"]),
            "required_evidence": list(descriptor["required_evidence"]),
            "dependencies": list(descriptor["dependencies"]),
            "authority_class": descriptor["authority_class"],
            "cost_capacity": dict(descriptor["cost_capacity"]),
            "urgency": descriptor["urgency"],
            "expected_information_gain": descriptor["expected_information_gain"],
            "coherency_group": descriptor["coherency_group"],
            "declared_lifecycle_state": descriptor["lifecycle_state"],
            "projected_lifecycle_state": projected_state,
            "execution_claim_ref": descriptor["execution_claim_ref"],
            "readiness_blockers": blockers,
            "authority_effect": "NONE",
        })

    groups: dict[str, list[str]] = {}
    for row in projected:
        groups.setdefault(row["coherency_group"], []).append(row["test_id"])

    heartbeat_ref = _validate_heartbeat_reference(heartbeat_observation)
    basis = {
        "manifold_version": manifold_version,
        "tests": projected,
        "available_capabilities": sorted(capabilities),
        "available_evidence": sorted(evidence),
    }
    manifold_hash = _digest(basis)

    return {
        "schema": SNAPSHOT_SCHEMA,
        "manifold_version": manifold_version,
        "manifold_hash": manifold_hash,
        "tests": projected,
        "coherency_groups": {
            group: sorted(test_ids) for group, test_ids in sorted(groups.items())
        },
        "available_capabilities": sorted(capabilities),
        "available_evidence": sorted(evidence),
        "heartbeat_observation": heartbeat_ref,
        "direct_test_execution_heartbeat_dependency": False,
        "execution_authority": "INDEPENDENT_ADMITTED_CLAIM_FENCE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    }


def _distinguishing_signature(row: Mapping[str, Any]) -> str:
    return _digest({
        "canonical_input_hash": row["canonical_input_hash"],
        "goal_transition": row["goal_transition"],
        "source_state": row["source_state"],
        "target_state": row["target_state"],
        "transition_class": row["transition_class"],
        "required_capabilities": sorted(row["required_capabilities"]),
        "required_evidence": sorted(row["required_evidence"]),
        "authority_class": row["authority_class"],
        "coherency_group": row["coherency_group"],
    })


def select_candidate_bundle(
    snapshot: Mapping[str, Any],
    *,
    capacity_units: float,
) -> dict[str, Any]:
    """Select a deterministic, non-authorizing minimum-distinguishing candidate set.

    Equivalent READY tests are not dropped or terminalized. One representative
    can be selected for a distinguishing signature while equivalent tests remain
    explicitly deferred pending bundle evidence.
    """

    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError("queue manifold snapshot schema mismatch")
    if not isinstance(capacity_units, (int, float)) or capacity_units <= 0:
        raise ValueError("capacity_units must be positive")

    ready = [
        dict(row)
        for row in snapshot.get("tests", [])
        if row.get("projected_lifecycle_state") == "READY"
    ]
    ready.sort(
        key=lambda row: (
            -int(row["urgency"]),
            -float(row["expected_information_gain"]),
            float(row["cost_capacity"]["cost_units"]),
            str(row["test_id"]),
        )
    )

    signatures_seen: set[str] = set()
    selected: list[str] = []
    deferred_equivalent: list[dict[str, str]] = []
    consumed = 0.0

    for row in ready:
        signature = _distinguishing_signature(row)
        if signature in signatures_seen:
            deferred_equivalent.append({
                "test_id": row["test_id"],
                "reason": "AWAIT_BUNDLE_EVIDENCE_FOR_EQUIVALENT_DISTINGUISHING_SIGNATURE",
                "distinguishing_signature": signature,
            })
            continue

        units = float(row["cost_capacity"]["capacity_units"])
        if consumed + units > float(capacity_units):
            continue
        signatures_seen.add(signature)
        selected.append(row["test_id"])
        consumed += units

    unselected_ready = sorted(
        set(row["test_id"] for row in ready)
        - set(selected)
        - set(item["test_id"] for item in deferred_equivalent)
    )

    bundle_basis = {
        "manifold_version": snapshot["manifold_version"],
        "manifold_hash": snapshot["manifold_hash"],
        "selected_test_ids": selected,
        "deferred_equivalent": deferred_equivalent,
        "capacity_units": float(capacity_units),
    }
    return {
        "schema": BUNDLE_SCHEMA,
        "bundle_id": "bundle-" + _digest(bundle_basis).split(":", 1)[1][:24],
        "manifold_version": snapshot["manifold_version"],
        "manifold_hash": snapshot["manifold_hash"],
        "selected_test_ids": selected,
        "deferred_equivalent_tests": deferred_equivalent,
        "unselected_ready_test_ids": unselected_ready,
        "capacity_units_available": float(capacity_units),
        "capacity_units_selected": consumed,
        "execution_authority_granted": False,
        "claim_or_fence_minted": False,
        "heartbeat_authority_granted": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    }


def validate_bundle_instruction(
    bundle: Mapping[str, Any],
    current_snapshot: Mapping[str, Any],
) -> None:
    """Reject stale queue instructions after any manifold state change."""

    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise ValueError("bundle schema mismatch")
    if current_snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError("current snapshot schema mismatch")
    if bundle.get("manifold_version") != current_snapshot.get("manifold_version"):
        raise ValueError("STALE_MANIFOLD_VERSION")
    if bundle.get("manifold_hash") != current_snapshot.get("manifold_hash"):
        raise ValueError("STALE_MANIFOLD_HASH")
    if bundle.get("execution_authority_granted") is not False:
        raise ValueError("bundle cannot grant execution authority")
    if bundle.get("claim_or_fence_minted") is not False:
        raise ValueError("bundle cannot mint claim or fence")
    if bundle.get("heartbeat_authority_granted") is not False:
        raise ValueError("bundle cannot grant HeartBeat authority")
    if bundle.get("credential_authority") != "TV/TVC":
        raise ValueError("bundle cannot replace TV/TVC credential authority")
    if bundle.get("authority_effect") != "NONE":
        raise ValueError("bundle cannot grant authority")


def apply_test_disposition(
    descriptor: Mapping[str, Any],
    *,
    new_state: str,
    evidence_refs: Sequence[str],
    bundle_id: str | None = None,
) -> dict[str, Any]:
    """Create an explicit lifecycle disposition; never silently remove a test."""

    validate_descriptor(descriptor)
    if new_state not in ALL_STATES:
        raise ValueError("unsupported disposition state")
    evidence = _unique_strings(evidence_refs)
    if new_state in TERMINAL_DISPOSITIONS_REQUIRING_EVIDENCE and not evidence:
        raise ValueError("terminal queue disposition requires evidence")
    if new_state == "SATISFIED_BY_BUNDLE" and not bundle_id:
        raise ValueError("SATISFIED_BY_BUNDLE requires bundle_id")
    if new_state == "CLAIMED" and not descriptor.get("execution_claim_ref"):
        raise ValueError("CLAIMED disposition requires independent execution_claim_ref")

    disposition_basis = {
        "test_id": descriptor["test_id"],
        "prior_state": descriptor["lifecycle_state"],
        "new_state": new_state,
        "evidence_refs": evidence,
        "bundle_id": bundle_id,
    }
    return {
        "schema": DISPOSITION_SCHEMA,
        "disposition_id": "disposition-" + _digest(disposition_basis).split(":", 1)[1][:24],
        **disposition_basis,
        "silent_drop": False,
        "execution_authority_granted": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    }


__all__ = [
    "DESCRIPTOR_SCHEMA",
    "SNAPSHOT_SCHEMA",
    "BUNDLE_SCHEMA",
    "DISPOSITION_SCHEMA",
    "TERMINAL_STATES",
    "validate_descriptor",
    "build_queue_manifold",
    "select_candidate_bundle",
    "validate_bundle_instruction",
    "apply_test_disposition",
]
