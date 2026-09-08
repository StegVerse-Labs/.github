#!/usr/bin/env python3
"""Durable federation observation retention for organization resident kernels.

This module deliberately does not infer runtime authority or task completion. It only
retains evidence produced by the canonical org-kernel when an addressed frame is
actually consumed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

_spec = importlib.util.spec_from_file_location("stegverse_org_kernel", Path(__file__).with_name("kernel.py"))
_kernel = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_kernel)

OBSERVATION_SCHEMA = "stegverse.org-federation-observation/v1"


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _sha(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else _canon(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def _write_once_json(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text())
        if existing != value:
            raise ValueError("federation_observation_write_once_collision")
        return path
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def retain_consumed_observation(repo_root: Path, consumed_item: dict[str, Any]) -> dict[str, Any]:
    """Persist one actually consumed federation frame as immutable local evidence."""
    result = consumed_item.get("result") or {}
    if result.get("status") != "CONSUMED":
        raise ValueError("observation_requires_consumed_result")

    packet = result.get("packet") or {}
    execution = result.get("execution_result") or {}
    receipts = execution.get("receipts") or []
    reconstruction = execution.get("reconstruction") or {}

    required_kinds = ["INGRESS_ACCEPTED", "DISPATCHED", "CONSUMED", "RESULT_BOUND", "EGRESS_EMITTED"]
    actual_kinds = [item.get("kind") for item in receipts]
    if actual_kinds != required_kinds:
        raise ValueError("observation_receipt_chain_incomplete")
    if reconstruction.get("status") != "RECONSTRUCTED":
        raise ValueError("observation_reconstruction_incomplete")

    registry = _kernel.load_registry(repo_root)
    organization = registry["organization"]
    if packet.get("destination", {}).get("org") != organization:
        raise ValueError("observation_destination_mismatch")

    terminal_receipt_id = reconstruction.get("terminal_receipt_id")
    if not terminal_receipt_id or terminal_receipt_id != receipts[-1].get("receipt_id"):
        raise ValueError("observation_terminal_receipt_mismatch")

    body = {
        "schema": OBSERVATION_SCHEMA,
        "organization": organization,
        "packet_id": packet.get("packet_id"),
        "frame_path": consumed_item.get("path"),
        "origin": packet.get("origin"),
        "destination": packet.get("destination"),
        "intr_profile": packet.get("intr_profile"),
        "transition": packet.get("transition"),
        "authority_effect": execution.get("authority_effect"),
        "receipt_chain": receipts,
        "reconstruction": reconstruction,
        "authenticity_claim": "OBSERVED_FROM_CONSUMED_CANONICAL_FRAME",
        "activation_inferred": False,
        "task_completion_inferred": False,
    }
    observation = {**body, "observation_hash": _sha(body)}
    filename = hashlib.sha256((organization + "|" + str(packet.get("packet_id"))).encode()).hexdigest() + ".json"
    path = repo_root / "resident-runtime" / "federation" / "observations" / filename
    _write_once_json(path, observation)
    return {"path": str(path), "observation": observation}


def consume_and_retain(repo_root: Path, *, mesh_root: Path | None = None, seen: set[str] | None = None) -> list[dict[str, Any]]:
    """Consume canonical addressed frames and durably retain only successful observations."""
    consumed = _kernel.consume_addressed_frames(repo_root, mesh_root=mesh_root, seen=seen)
    retained = []
    for item in consumed:
        result = item.get("result") or {}
        if result.get("status") == "CONSUMED":
            retained.append(retain_consumed_observation(repo_root, item))
    return retained


__all__ = ["OBSERVATION_SCHEMA", "retain_consumed_observation", "consume_and_retain"]
