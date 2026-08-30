#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

POLICY_ID = "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001"
TRANSPORT_PROFILE = "stegverse.universal-intr.adjacent-hop/v1"
ROUTE_ID = "SV-DN-1-HF-PUBLIC"
RESIDENT_TRANSITION = "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE"
INTR_TRANSITION = "SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE"


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_ref(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def verify(resident_receipt: Mapping[str, Any], capture: Mapping[str, Any], exchange: Mapping[str, Any], intr_receipt: Mapping[str, Any]) -> dict[str, Any]:
    if resident_receipt.get("state") != "COMPLETE" or resident_receipt.get("transition_id") != RESIDENT_TRANSITION:
        raise RuntimeError("resident observation is not complete")
    if not resident_receipt.get("runtime_source_pin_verified"):
        raise RuntimeError("resident runtime source pin is not verified")
    if resident_receipt.get("credential_used") or resident_receipt.get("github_token_used"):
        raise RuntimeError("resident observation used prohibited credentials")
    if resident_receipt.get("repository_writeback_performed"):
        raise RuntimeError("resident observation performed repository writeback")

    raw_sha = capture.get("raw_sha256")
    if not raw_sha or raw_sha != resident_receipt.get("raw_response_sha256"):
        raise RuntimeError("resident raw digest mismatch")
    exchange_id = exchange.get("exchange_id")
    if not exchange_id or exchange_id != resident_receipt.get("semantic_exchange_id"):
        raise RuntimeError("resident semantic exchange identity mismatch")
    if exchange.get("raw_evidence", {}).get("preserved_native_fields") != capture.get("parsed_json"):
        raise RuntimeError("captured native fields do not match semantic exchange")

    if intr_receipt.get("state") != "COMPLETE" or intr_receipt.get("transition_id") != INTR_TRANSITION:
        raise RuntimeError("Universal InTr hop is not complete")
    if intr_receipt.get("route_id") != ROUTE_ID:
        raise RuntimeError("unexpected InTr route")
    if intr_receipt.get("transport_profile") != TRANSPORT_PROFILE:
        raise RuntimeError("non-canonical InTr transport profile")
    if intr_receipt.get("exchange_id") != exchange_id:
        raise RuntimeError("InTr exchange identity mismatch")
    if intr_receipt.get("destination_validation") != "PASS" or not intr_receipt.get("lineage_verified"):
        raise RuntimeError("InTr destination validation or lineage failed")

    claims = intr_receipt.get("claims") or {}
    required = {
        "canonical_protocol_adopted": True,
        "universal_intr_policy_id": POLICY_ID,
        "boundary_from": "EXTERNAL_SYSTEM",
        "boundary_to": "STEGOS_ECOSYSTEM",
        "interlock_required_per_hop": True,
        "receipt_hash_chain_required": True,
        "runtime_activation_claimed": False,
        "production_interlock_runtime_activated": False,
        "sdk_admitted": False,
        "authority_effect": "NONE",
    }
    for key, expected in required.items():
        if claims.get(key) != expected:
            raise RuntimeError(f"InTr claim mismatch: {key}")

    previous = exchange.get("intr", {}).get("previous_receipt_hash")
    if not previous or intr_receipt.get("previous_receipt_hash") != previous:
        raise RuntimeError("InTr previous receipt hash mismatch")
    source_transform = exchange.get("far_side_receipt", {}).get("transformation_hash")
    if not source_transform or intr_receipt.get("source_transform_hash") != source_transform:
        raise RuntimeError("InTr source transformation hash mismatch")

    receipt_hash = intr_receipt.get("receipt_hash")
    body = {k: v for k, v in intr_receipt.items() if k != "receipt_hash"}
    if receipt_hash != sha256_ref(body):
        raise RuntimeError("InTr deterministic receipt hash mismatch")

    return {
        "schema": "stegverse.sv-dn1.runtime-observation-verification/v1",
        "state": "OBSERVED",
        "resident_source_capture": "OBSERVED",
        "hf_semantic_exchange": "OBSERVED",
        "universal_intr_hop": "OBSERVED",
        "exchange_id": exchange_id,
        "intr_receipt_hash": receipt_hash,
        "policy_id": POLICY_ID,
        "transport_profile": TRANSPORT_PROFILE,
        "runtime_activation_claimed": False,
        "sdk_admitted": False,
        "authority_effect": "NONE",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resident-receipt", required=True)
    ap.add_argument("--source-capture", required=True)
    ap.add_argument("--exchange", required=True)
    ap.add_argument("--intr-receipt", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()

    result = verify(
        load_json(Path(args.resident_receipt)),
        load_json(Path(args.source_capture)),
        load_json(Path(args.exchange)),
        load_json(Path(args.intr_receipt)),
    )
    rendered = json.dumps(result, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
