#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "control" / "quantum-wallet-signature-census.json"

REQUIRED = {
    "STEGFIN-EIP1193-USER-WALLET-HANDOFF",
    "STEGID-DEVICE-WALLET-CAPABILITY",
}


def validate() -> dict:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    assert census["schema"] == "stegverse.quantum-wallet-signature-census/v1"
    assert census["goal_id"] == "QUANTUM-RESILIENCE-001"
    assert census["issue"] == "StegVerse-Labs/.github#1013"
    assert census["wallet_signing_authority"] == "USER_ONLY"
    assert census["wallet_broadcast_authority"] == "USER_ONLY"
    assert census["wallet_key_export_authority"] == "NONE"
    assert census["credential_authority"] == "TV/TVC"
    assert census["authority_effect"] == "NONE_CENSUS_ONLY"
    assert census["pqc_deployment_claim"] is False
    assert census["quantum_safe_claim"] is False

    by_id = {row["id"]: row for row in census["surfaces"]}
    assert REQUIRED <= set(by_id)

    wallet = by_id["STEGFIN-EIP1193-USER-WALLET-HANDOFF"]
    assert wallet["signer_execution_location"] == "EXTERNAL_INJECTED_EIP1193_WALLET_PROVIDER"
    assert wallet["stegverse_signs"] is False
    assert wallet["stegverse_broadcasts_automatically"] is False
    assert wallet["private_key_exported_to_stegverse"] is False
    assert wallet["seed_exported_to_stegverse"] is False
    assert wallet["signature_algorithm"] == "NOT_ESTABLISHED_BY_STEGVERSE_SOURCE"
    assert wallet["quantum_state"] == "QUANTUM_SAFETY_UNKNOWN"

    capability = by_id["STEGID-DEVICE-WALLET-CAPABILITY"]
    assert capability["signer_execution_location"] == "NO_SIGNING_PERFORMED_BY_CAPABILITY_DECISION"
    assert capability["stegverse_signs"] is False
    assert capability["private_key_exported_to_stegverse"] is False

    refs = census["observed_non_authoritative_references"]
    assert any(row["reference"] == "ecdsa_secp256k1" for row in refs)
    assert all("NOT_PROOF" in row["classification"] or "NOT_RUNTIME_PROOF" in row["classification"] for row in refs)
    assert census["residual_unresolved_scope"]

    return {
        "status": "PASS_QUANTUM_WALLET_SIGNATURE_CENSUS",
        "goal_id": census["goal_id"],
        "surface_count": len(census["surfaces"]),
        "wallet_signing_authority": census["wallet_signing_authority"],
        "wallet_broadcast_authority": census["wallet_broadcast_authority"],
        "quantum_safe_claim": False,
        "pqc_deployment_claim": False,
        "authority_effect": census["authority_effect"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
