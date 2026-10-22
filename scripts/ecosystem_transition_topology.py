"""Device-neutral state-transition admissibility and sovereign receipt verifier.

Reference conformance implementation; no runtime or ledger authority.
Standard library only.  Actual sovereign ledger readback must be supplied by an
authenticated owner-controlled interface, never manufactured here.
"""
from __future__ import annotations
import hashlib
import json
from typing import Mapping, Any

DISPOSITIONS = frozenset({"ALLOW", "DENY", "FAIL_CLOSED"})
CLASSIFICATION = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET", "TOP_SECRET")


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def evaluate(resulting_state: Mapping[str, Any], manifest: Mapping[str, Any],
             evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate *resulting* state; never mint or confer authority."""
    if not all(isinstance(v, Mapping) for v in (resulting_state, manifest, evidence)):
        return {"disposition": "FAIL_CLOSED", "predicate": "INVALID_EVALUATION_INPUT"}
    required = ("classification", "minimum_authority_level", "manifest_id")
    if any(k not in manifest for k in required):
        return {"disposition": "FAIL_CLOSED", "predicate": "MANIFEST_INCOMPLETE"}
    level = manifest["minimum_authority_level"]
    current = resulting_state.get("authority_level")
    if level not in CLASSIFICATION or current not in CLASSIFICATION:
        return {"disposition": "FAIL_CLOSED", "predicate": "AUTHORITY_STATE_UNVERIFIABLE"}
    if resulting_state.get("classification") != manifest["classification"]:
        return {"disposition": "DENY", "predicate": "CLASSIFICATION_MISMATCH"}
    if CLASSIFICATION.index(current) < CLASSIFICATION.index(level):
        return {"disposition": "DENY", "predicate": "MINIMUM_AUTHORITY_NOT_MET"}
    if resulting_state.get("consent_revoked") is True:
        return {"disposition": "DENY", "predicate": "CONSENT_REVOKED"}
    if evidence.get("source_digest_verified") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOURCE_INTEGRITY_UNVERIFIED"}
    if evidence.get("security_exceedance_verified") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SECURITY_EXCEEDANCE_UNVERIFIED"}
    return {"disposition": "ALLOW", "predicate": "MANIFEST_PREDICATES_SATISFIED"}


def verify_organization_readback(transition: Mapping[str, Any],
                                 ledger_readback: Mapping[str, Any] | None) -> dict[str, str]:
    """Verify supplied authenticated ledger evidence, not a local receipt alone."""
    if not isinstance(ledger_readback, Mapping):
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_LEDGER_READBACK_MISSING"}
    if ledger_readback.get("authenticated") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_READBACK_NOT_AUTHENTICATED"}
    if ledger_readback.get("recording_confirmed") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_RECORDING_UNVERIFIED"}
    if ledger_readback.get("transition_digest") != canonical_digest(transition):
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_TRANSITION_DIGEST_MISMATCH"}
    if ledger_readback.get("continuity_verified") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_CONTINUITY_UNVERIFIED"}
    return {"disposition": "ALLOW", "predicate": "SUPPLIED_SOVEREIGN_READBACK_CONSISTENT"}
