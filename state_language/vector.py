from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

VECTOR_SCHEMA = "stegverse.semantic-state-vector/v1"
DELTA_SCHEMA = "stegverse.semantic-state-delta/v1"


def canonical_json(value: Any) -> str:
    """Return deterministic UTF-8 JSON text suitable for governance hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _validate_dimension(name: str, dimension: dict[str, Any]) -> None:
    if not isinstance(dimension, dict):
        raise ValueError(f"dimension {name!r} must be an object")
    if "type" not in dimension or "value" not in dimension:
        raise ValueError(f"dimension {name!r} requires type and value")
    allowed = {"string", "integer", "number", "boolean", "enum", "set", "object", "unknown"}
    if dimension["type"] not in allowed:
        raise ValueError(f"dimension {name!r} has unsupported type")
    if dimension["type"] == "unknown" and dimension["value"] is not None:
        raise ValueError(f"unknown dimension {name!r} must use null value")


def normalize_vector(vector: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a semantic state vector without interpreting prose."""
    value = deepcopy(vector)
    if value.get("schema") != VECTOR_SCHEMA:
        raise ValueError("unsupported semantic state vector schema")
    if not isinstance(value.get("subject"), str) or not value["subject"]:
        raise ValueError("state vector subject is required")
    if not isinstance(value.get("resolution"), str) or not value["resolution"]:
        raise ValueError("state vector resolution is required")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("state vector dimensions must be an object")
    for name, dimension in dimensions.items():
        if not isinstance(name, str) or not name:
            raise ValueError("state dimension names must be non-empty strings")
        _validate_dimension(name, dimension)
    evidence = value.setdefault("evidence_refs", [])
    if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
        raise ValueError("evidence_refs must be a string array")
    value["evidence_refs"] = sorted(set(evidence))
    authority = value.get("authority")
    if not isinstance(authority, dict) or not authority.get("effect") or not authority.get("domain"):
        raise ValueError("authority effect and domain are required")
    return value


def derive_delta(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    affected_scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Derive a typed semantic delta from two vectors.

    Only dimension changes are semantic. Metadata-only/prose-only revision changes therefore
    produce an empty `changes` object and cannot silently reprogram worker execution.
    """
    source = normalize_vector(before)
    target = normalize_vector(after)
    if source["subject"] != target["subject"]:
        raise ValueError("cannot derive delta across different state subjects")

    changes: dict[str, Any] = {}
    dimension_names = sorted(set(source["dimensions"]) | set(target["dimensions"]))
    for name in dimension_names:
        old = source["dimensions"].get(name)
        new = target["dimensions"].get(name)
        if canonical_json(old) == canonical_json(new):
            continue
        criticality = "MODERATE"
        if isinstance(new, dict) and new.get("criticality"):
            criticality = new["criticality"]
        elif isinstance(old, dict) and old.get("criticality"):
            criticality = old["criticality"]
        changes[name] = {"before": old, "after": new, "criticality": criticality}

    evidence = sorted(set(source.get("evidence_refs", []) + target.get("evidence_refs", [])))
    return {
        "schema": DELTA_SCHEMA,
        "subject": source["subject"],
        "source_state_hash": canonical_hash(source),
        "target_state_hash": canonical_hash(target),
        "source_ref": target.get("source_ref") or source.get("source_ref"),
        "source_revision": target.get("revision"),
        "changes": changes,
        "affected_scopes": sorted(set(affected_scopes or [])),
        "authority_effect": target["authority"].get("effect", "NONE"),
        "evidence_refs": evidence,
    }
