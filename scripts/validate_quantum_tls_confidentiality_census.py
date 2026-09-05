#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "control" / "quantum-tls-confidentiality-census.json"

REQUIRED_SURFACES = {
    "STEGTALK-ST034-PUBLIC-TLS-CLIENT",
    "TVC-SERVICE-GATEWAY-TLS-MATERIAL",
}


def load() -> dict:
    value = json.loads(CENSUS.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("TLS census must contain an object")
    return value


def validate() -> dict:
    census = load()
    assert census["schema"] == "stegverse.quantum-tls-confidentiality-census/v1"
    assert census["goal_id"] == "QUANTUM-RESILIENCE-001"
    assert census["issue"] == "StegVerse-Labs/.github#1014"
    assert census["inventory_status"] == "PARTIAL_EXPLICIT"
    assert census["authority_effect"] == "NONE_CENSUS_ONLY"
    assert census["credential_authority"] == "TV/TVC"
    assert census["github_token_runtime_authority"] == "NONE"
    assert census["pqc_deployment_claim"] is False
    assert census["quantum_safe_claim"] is False

    surfaces = census["surfaces"]
    by_id = {row["id"]: row for row in surfaces}
    assert REQUIRED_SURFACES <= set(by_id)

    for surface_id in REQUIRED_SURFACES:
        row = by_id[surface_id]
        assert row["production_activation"] is False
        assert row["quantum_state"] == "QUANTUM_SAFETY_UNKNOWN"
        assert row["harvest_now_decrypt_later_relevant"] is True
        assert row["migration_priority"] == "CRITICAL"
        assert row["runtime_evidence_required"]
        assert "UNKNOWN" in row["key_exchange_algorithm"] or "NEGOTIATED" in row["key_exchange_algorithm"]

    stegtalk = by_id["STEGTALK-ST034-PUBLIC-TLS-CLIENT"]
    assert stegtalk["tls_minimum"] == "TLSv1.2"
    assert stegtalk["certificate_chain_verification_required"] is True
    assert stegtalk["hostname_verification_required"] is True
    assert stegtalk["insecure_mode_available"] is False
    assert stegtalk["certificate_algorithm"] == "NEGOTIATED_NOT_PINNED_IN_SOURCE"
    assert stegtalk["key_exchange_algorithm"] == "NEGOTIATED_NOT_PINNED_IN_SOURCE"

    tvc = by_id["TVC-SERVICE-GATEWAY-TLS-MATERIAL"]
    assert tvc["source_status"] == "IMPLEMENTED_TARGET_UNPROVEN_RUNTIME"
    assert tvc["certificate_algorithm"] == "UNKNOWN_UNTIL_AUTHENTIC_CERTIFICATE_METADATA_RECEIPT"

    assert census["residual_unresolved_scope"], "partial census must retain unresolved scope"

    return {
        "status": "PASS_QUANTUM_TLS_CONFIDENTIALITY_CENSUS",
        "goal_id": census["goal_id"],
        "surface_count": len(surfaces),
        "quantum_safe_claim": False,
        "pqc_deployment_claim": False,
        "authority_effect": census["authority_effect"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
