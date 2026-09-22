#!/usr/bin/env python3
"""Observe the first authentic HB-bound Master Records successor and commit it to HB evidence.

This is a resident observation consumer on the existing dispatcher. It creates no
runtime, scheduler, claim/fence, transition authority, custody authority, or
credential path. It emits no checkpoint until canonical Master Records already
contains a reconstructable HB-bound successor receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from heartbeat_runtime.master_records_checkpoint_commitment import build_checkpoint_commitment
from workers.canonical_state_transition_custody import (
    build_master_records_receipt_set_commitment,
    current_hb_creation_reference,
    reconstruct_state_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
DEST_REL = Path("receipts/sovereign-host/ecosystem-receipt-hb-first-successor-checkpoint.latest.json")
FIRST_SUCCESSOR_ORDINAL = 1


def _write(runtime: Path, value: dict[str, Any]) -> dict[str, Any]:
    destination = runtime / DEST_REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def observe(runtime_root: Path) -> dict[str, Any]:
    runtime = runtime_root.expanduser().resolve()
    projection = build_master_records_receipt_set_commitment(FIRST_SUCCESSOR_ORDINAL, FIRST_SUCCESSOR_ORDINAL)
    if projection.get("state") != "PASS":
        return _write(runtime, {
            "schema": "stegverse.ecosystem-receipt-hb-first-successor-observation/v1",
            "state": "WAITING_FOR_MASTER_RECORDS_HB_SUCCESSOR",
            "reason": projection.get("reason"),
            "runtime_checkpoint_created": False,
            "node_kv_witness_advanced": False,
            "external_anchor_advanced": False,
            "authority_effect": "NONE_OBSERVATION_ONLY",
        })

    identities = projection.get("ordered_receipt_identities")
    if not isinstance(identities, list) or len(identities) != 1:
        raise RuntimeError("first successor projection must contain exactly one receipt")
    receipt_sha256 = identities[0].get("receipt_sha256")
    if not isinstance(receipt_sha256, str) or len(receipt_sha256) != 64:
        raise RuntimeError("first successor receipt identity invalid")

    reconstructed = reconstruct_state_receipt(receipt_sha256)
    if reconstructed.get("state") != "PASS":
        raise RuntimeError("first successor reconstruction not PASS")
    if reconstructed.get("receipt_sha256") != receipt_sha256 or reconstructed.get("reconstructed_receipt_sha256") != receipt_sha256:
        raise RuntimeError("first successor receipt/reconstruction digest mismatch")
    if reconstructed.get("required_evidence_validation_status") != "PASS":
        raise RuntimeError("first successor required evidence not PASS")
    receipt = reconstructed.get("receipt")
    if not isinstance(receipt, dict):
        raise RuntimeError("first successor receipt missing")
    creation = receipt.get("hb_creation_reference")
    recording = reconstructed.get("hb_recording_reference")
    if not isinstance(creation, dict) or creation.get("authority_effect") != "NONE_REFERENCE_ONLY":
        raise RuntimeError("first successor creation HB reference missing")
    if not isinstance(recording, dict) or recording.get("authority_effect") != "NONE_REFERENCE_ONLY":
        raise RuntimeError("first successor recording HB reference missing")
    if reconstructed.get("recorded_receipt_sha256") != receipt_sha256:
        raise RuntimeError("first successor recording identity mismatch")
    if reconstructed.get("master_records_custody_ordinal") != FIRST_SUCCESSOR_ORDINAL:
        raise RuntimeError("first successor custody ordinal mismatch")
    if reconstructed.get("hb_evidence_class") != "HB_BOUND_SUCCESSOR":
        raise RuntimeError("first successor evidence class mismatch")

    checkpoint_hb = current_hb_creation_reference()
    checkpoint = build_checkpoint_commitment(
        hb_reference=checkpoint_hb,
        master_records_projection=projection,
        anchor_inheritance_floor_hb_reference=creation,
    )
    result = {
        "schema": "stegverse.ecosystem-receipt-hb-first-successor-observation/v1",
        "state": "AUTHENTIC_FIRST_SUCCESSOR_CHECKPOINT_COMMITTED",
        "first_successor_ordinal": FIRST_SUCCESSOR_ORDINAL,
        "receipt_sha256": receipt_sha256,
        "reconstructed_receipt_sha256": reconstructed.get("reconstructed_receipt_sha256"),
        "master_record_ref": reconstructed.get("master_record_ref"),
        "hb_creation_reference": creation,
        "hb_recording_reference": recording,
        "master_records_receipt_set_commitment": projection,
        "hb_checkpoint_commitment": checkpoint,
        "runtime_checkpoint_created": True,
        "node_kv_witness_advanced": False,
        "external_anchor_advanced": False,
        "master_records_grants_transition_authority": False,
        "heartbeat_grants_authority": False,
        "authority_effect": "NONE_EVIDENCE_COMMITMENT_ONLY",
    }
    return _write(runtime, result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
