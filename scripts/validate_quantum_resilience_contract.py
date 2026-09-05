#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "control" / "quantum-resilience-contract.json"
CENSUS = ROOT / "control" / "quantum-crypto-census.json"

REQUIRED_STATES = {
    "UNINVENTORIED",
    "CLASSICAL_ONLY",
    "HYBRID_MIGRATION_REQUIRED",
    "HYBRID_ACTIVE",
    "PQC_VALIDATED",
    "DEPRECATED_CRYPTO_PRESENT",
    "QUANTUM_SAFETY_UNKNOWN",
}
REQUIRED_PROPERTIES = {
    "CRYPTO_AGILITY",
    "HARVEST_NOW_DECRYPT_LATER_AWARENESS",
    "DOWNGRADE_RESISTANCE",
    "ALGORITHM_EXPLICITNESS",
    "HISTORICAL_VERIFIABILITY",
    "KEY_AND_ALGORITHM_REVOCABILITY",
    "HYBRID_MIGRATION_SUPPORT",
    "UNKNOWN_STATE_PRESERVATION",
    "AUTHORITY_SEPARATION",
    "NO_SELF_EXEMPTION",
}
REQUIRED_ENTITIES = {"StegVerse-001", "StegVerse-002", "SV-011"}
CRITICAL_IDS = {
    "STEGID-CONTINUITY-RECEIPT-SIGNATURE",
    "TVC-SIGNED-POLICY-ED25519",
    "TLS-WEBPKI-ECOSYSTEM",
    "DEVICE-NODE-IDENTITY",
    "WALLET-SIGNATURES",
    "LONG-LIVED-STORED-CONFIDENTIALITY",
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain an object")
    return value


def validate() -> dict:
    contract = load(CONTRACT)
    census = load(CENSUS)

    assert contract["schema"] == "stegverse.quantum-resilience-contract/v1"
    assert contract["goal_id"] == "QUANTUM-RESILIENCE-001"
    authority = contract["authority"]
    assert authority["credential_authority"] == "TV/TVC"
    assert authority["github_token_runtime_authority"] == "NONE"
    assert authority["intr_interlock_transition_boundary"] is True
    assert authority["quantum_capability_confers_authority"] is False
    assert authority["pqc_validity_confers_transition_authority"] is False
    assert authority["second_machine_required"] is False

    baseline = contract["standards_baseline"]
    assert "FIPS-203:ML-KEM" in baseline["key_establishment"]
    assert "FIPS-204:ML-DSA" in baseline["digital_signatures"]
    assert "FIPS-205:SLH-DSA" in baseline["digital_signatures"]
    assert baseline["crypto_agility_required"] is True
    assert baseline["single_algorithm_permanent_freeze_allowed"] is False

    assert REQUIRED_STATES <= set(contract["required_states"])
    assert REQUIRED_PROPERTIES <= set(contract["required_properties"])
    assert {row["entity_id"] for row in contract["entity_roles"]} == REQUIRED_ENTITIES

    claims = contract["claims"]
    for key in (
        "runtime_claim",
        "deployment_claim",
        "pqc_implementation_claim",
        "complete_crypto_inventory_claim",
        "absolute_quantum_security_claim",
    ):
        assert claims[key] is False

    assert census["schema"] == "stegverse.quantum-crypto-census/v1"
    assert census["goal_id"] == contract["goal_id"]
    assert census["inventory_status"] == "INCOMPLETE_EXPLICIT"
    assert census["pqc_validated_surface_count"] == 0
    assert census["runtime_claim"] is False
    assert census["deployment_claim"] is False

    surfaces = census["surfaces"]
    by_id = {row["id"]: row for row in surfaces}
    assert CRITICAL_IDS <= set(by_id)
    assert by_id["STEGID-CONTINUITY-RECEIPT-SIGNATURE"]["primitive"] == "Ed25519"
    assert by_id["STEGID-CONTINUITY-RECEIPT-SIGNATURE"]["quantum_state"] == "CLASSICAL_ONLY"
    assert by_id["TVC-SIGNED-POLICY-ED25519"]["primitive"] == "Ed25519"
    assert by_id["TVC-SIGNED-POLICY-ED25519"]["quantum_state"] == "CLASSICAL_ONLY"

    unresolved_critical = sorted(
        row["id"] for row in surfaces
        if row["migration_priority"] == "CRITICAL" and row["quantum_state"] == "UNINVENTORIED"
    )
    assert unresolved_critical, "initial census must preserve unresolved critical unknowns"

    return {
        "status": "PASS_QUANTUM_RESILIENCE_SOURCE_CONTRACT",
        "goal_id": contract["goal_id"],
        "surface_count": len(surfaces),
        "known_classical_only_count": sum(row["quantum_state"] == "CLASSICAL_ONLY" for row in surfaces),
        "unresolved_critical": unresolved_critical,
        "pqc_validated_surface_count": census["pqc_validated_surface_count"],
        "credential_authority": authority["credential_authority"],
        "runtime_claim": False,
        "deployment_claim": False,
        "authority_effect": "NONE_VALIDATION_ONLY",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
