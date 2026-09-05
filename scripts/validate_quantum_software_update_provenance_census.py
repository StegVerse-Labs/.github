#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "control" / "quantum-software-update-provenance-census.json"


def validate() -> dict[str, object]:
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    assert data["schema"] == "stegverse.quantum-software-update-provenance-census/v1"
    assert data["goal_id"] == "QUANTUM-RESILIENCE-001"
    assert data["authority_effect"] == "NONE_CENSUS_ONLY"
    assert data["credential_authority"] == "TV/TVC"
    assert data["github_token_runtime_authority"] == "NONE"
    rules = data["rules"]
    for key in (
        "sha256_is_integrity_not_authenticity",
        "manifest_is_integrity_not_signer_identity",
        "github_release_presence_is_not_cryptographic_provenance",
        "ci_success_is_not_cryptographic_provenance",
        "source_merge_is_not_runtime_or_release_authority",
        "pqc_claim_requires_real_crypto_evidence",
    ):
        assert rules[key] is True
    surfaces = data["surfaces"]
    assert {s["id"] for s in surfaces} == {"CVK-RELEASE-V0.1.9", "STEGCORE-PORTABLE-RELEASE"}
    for surface in surfaces:
        assert surface["authenticity_state"] == "HASH_MANIFEST_ONLY_AUTHENTICITY_UNPROVEN"
        assert surface["quantum_state"] == "QUANTUM_SAFETY_UNKNOWN"
        assert surface["observed_authenticated_signing"] == "NOT_FOUND_IN_SCOPED_SOURCE_SEARCH"
        assert surface["rollback_relevance"] is True
    assert data["pqc_validated_surface_count"] == 0
    assert data["runtime_claim"] is False
    assert data["deployment_claim"] is False
    return {"state": "PASS", "surface_count": len(surfaces), "authority_effect": data["authority_effect"]}


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (AssertionError, KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
