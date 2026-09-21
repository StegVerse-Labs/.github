#!/usr/bin/env python3
"""Non-authorizing HB checkpoint commitment over an exact Master Records receipt-set root."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA = "stegverse.hb-master-records-checkpoint-commitment/v1"
PROFILE = "ORDERED_CANONICAL_RECEIPT_SHA256_BOUNDED_RANGE_V1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_checkpoint_commitment(
    *,
    hb_reference: Mapping[str, Any],
    master_records_projection: Mapping[str, Any],
    prior_hb_checkpoint_commitment_sha256: str | None = None,
    anchor_inheritance_floor_hb_reference: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if hb_reference.get("authority_effect") != "NONE_REFERENCE_ONLY":
        raise ValueError("hb_reference_authority_effect_invalid")
    if master_records_projection.get("schema") != "stegverse.master-records.receipt-set-commitment/v1":
        raise ValueError("master_records_projection_schema_invalid")
    if master_records_projection.get("master_records_commitment_profile") != PROFILE:
        raise ValueError("master_records_commitment_profile_invalid")
    root = master_records_projection.get("master_records_receipt_set_root_sha256")
    count = master_records_projection.get("master_records_receipt_count")
    floor = master_records_projection.get("master_records_query_floor")
    ceiling = master_records_projection.get("master_records_query_ceiling")
    if not isinstance(root, str) or len(root) != 64:
        raise ValueError("master_records_root_invalid")
    if not isinstance(count, int) or count < 1:
        raise ValueError("master_records_receipt_count_invalid")
    if not isinstance(floor, int) or not isinstance(ceiling, int) or floor < 1 or ceiling < floor:
        raise ValueError("master_records_query_bounds_invalid")
    if count != ceiling - floor + 1:
        raise ValueError("master_records_query_bounds_not_contiguous")
    body = {
        "schema": SCHEMA,
        "hb_reference": dict(hb_reference),
        "prior_hb_checkpoint_commitment_sha256": prior_hb_checkpoint_commitment_sha256,
        "master_records_commitment_profile": PROFILE,
        "master_records_receipt_set_root_sha256": root,
        "master_records_receipt_count": count,
        "master_records_query_floor": floor,
        "master_records_query_ceiling": ceiling,
        "anchor_inheritance_floor_hb_reference": dict(anchor_inheritance_floor_hb_reference or hb_reference),
        "heartbeat_grants_authority": False,
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE_EVIDENCE_COMMITMENT_ONLY",
    }
    body["checkpoint_commitment_sha256"] = hashlib.sha256(_canonical(body)).hexdigest()
    return body


def verify_checkpoint_commitment(value: Mapping[str, Any]) -> bool:
    if value.get("schema") != SCHEMA:
        return False
    supplied = value.get("checkpoint_commitment_sha256")
    if not isinstance(supplied, str) or len(supplied) != 64:
        return False
    body = dict(value)
    body.pop("checkpoint_commitment_sha256", None)
    return hashlib.sha256(_canonical(body)).hexdigest() == supplied


__all__ = ["SCHEMA", "PROFILE", "build_checkpoint_commitment", "verify_checkpoint_commitment"]
