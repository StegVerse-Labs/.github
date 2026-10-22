"""Device-neutral state-transition admissibility and sovereign receipt verifier.

Reference conformance implementation; no runtime or ledger authority.
Standard library only.  Actual sovereign ledger readback must be supplied by an
authenticated owner-controlled interface, never manufactured here.
"""
from __future__ import annotations
import hashlib
import json
from typing import Mapping, Any, Callable

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
                                 ledger_readback: Mapping[str, Any] | None,
                                 authenticate: Callable[[Mapping[str, Any]], bool] | None = None) -> dict[str, str]:
    """Verify supplied authenticated ledger evidence, not a local receipt alone."""
    if not isinstance(ledger_readback, Mapping):
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_LEDGER_READBACK_MISSING"}
    # A JSON boolean is NOT authentication. Require a caller-supplied trusted
    # verification interface; absent interface is always non-ALLOW.
    if authenticate is None:
        return {"disposition": "FAIL_CLOSED", "predicate": "AUTHENTIC_SOVEREIGN_VERIFIER_UNAVAILABLE"}
    try:
        verified = authenticate(ledger_readback) is True
    except Exception:
        verified = False
    if not verified:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_READBACK_NOT_AUTHENTICATED"}
    if ledger_readback.get("recording_confirmed") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_RECORDING_UNVERIFIED"}
    if ledger_readback.get("transition_digest") != canonical_digest(transition):
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_TRANSITION_DIGEST_MISMATCH"}
    if ledger_readback.get("continuity_verified") is not True:
        return {"disposition": "FAIL_CLOSED", "predicate": "SOVEREIGN_CONTINUITY_UNVERIFIED"}
    return {"disposition": "ALLOW", "predicate": "SUPPLIED_SOVEREIGN_READBACK_CONSISTENT"}


def verify_native_organization_transition(
    state_receipt_result: Mapping[str, Any],
    *,
    expected_transition_id: str,
    expected_predecessor: str | None = None,
    root: Any = None,
) -> dict[str, Any]:
    """Use the installed sovereign Organization receipt readback gate.

    The caller must supply the actual receipt result of a canonical transition.
    No synthetic transition or ledger append is performed by this verifier.
    The native gate independently checks the organization ledger's record,
    state-receipt digest and expected transition/predecessor.
    """
    if (not isinstance(state_receipt_result, Mapping) or not expected_transition_id
            or not isinstance(state_receipt_result.get("receipt_sha256"), str)
            or not state_receipt_result.get("receipt_sha256")):
        return {"disposition": "FAIL_CLOSED", "predicate": "STATE_RECEIPT_OR_TRANSITION_ID_MISSING"}
    try:
        from workers.canonical_state_transition_custody import organization_receipt_gate
        gate = organization_receipt_gate(
            state_receipt_result, root=root,
            expected_transition_id=expected_transition_id,
            expected_predecessor=expected_predecessor,
            record_refusal=False,
        )
    except Exception as exc:
        # A native verifier failure cannot propagate as an accidental success.
        return {"disposition": "FAIL_CLOSED", "predicate": "NATIVE_ORGANIZATION_READBACK_UNAVAILABLE",
                "error_type": type(exc).__name__}
    if not isinstance(gate, Mapping) or gate.get("verified") is not True:
        refusal = gate.get("refusal") if isinstance(gate, Mapping) else None
        return {"disposition": "FAIL_CLOSED", "predicate": "NATIVE_ORGANIZATION_RECEIPT_NOT_VERIFIED",
                "native_refusal": refusal}
    # Only the native ledger gate may attest the readback. This is NOT the
    # governance decision disposition; a recorded DENY remains DENY.
    digest = gate.get("organization_receipt_sha256")
    if not isinstance(digest, str) or not digest:
        return {"disposition": "FAIL_CLOSED", "predicate": "NATIVE_ORGANIZATION_RECEIPT_DIGEST_MISSING"}
    return {"disposition": "ALLOW", "predicate": "NATIVE_ORGANIZATION_READBACK_VERIFIED",
            "organization_receipt_sha256": digest,
            "verification_scope": "ORGANIZATION_RECORDING_ONLY_NOT_GOVERNANCE_ADMISSIBILITY"}


def verify_published_organization_chain(
    fresh_ref_location: str, *, expected_receipt_sha256: str
) -> dict[str, Any]:
    """Read an already-published sovereign ref using the existing native chain reader.

    A caller must independently fetch the designated Git ref into a separate
    repository before invoking this read-only function. No new transition occurs.
    """
    if not fresh_ref_location or not expected_receipt_sha256:
        return {"disposition": "FAIL_CLOSED", "predicate": "FRESH_REF_OR_RECEIPT_NOT_BOUND"}
    try:
        import importlib.util
        from pathlib import Path
        module_path = Path(__file__).resolve().parents[1] / "resident-runtime" / "organization_ledger_readback.py"
        spec = importlib.util.spec_from_file_location("stegverse_native_org_readback", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("native reader unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        observed = module.readback(fresh_ref_location)
    except Exception as exc:
        return {"disposition": "FAIL_CLOSED", "predicate": "PUBLISHED_ORGANIZATION_CHAIN_READBACK_FAILED",
                "error_type": type(exc).__name__}
    if observed.get("disposition") != "ALLOW" or not all(
        observed.get(key) is True for key in
        ("every_receipt_verifies_against_its_body", "every_source_receipt_retained_and_verifies")
    ):
        return {"disposition": "FAIL_CLOSED", "predicate": "ORGANIZATION_CHAIN_INTEGRITY_UNVERIFIED"}
    matches = [row for row in observed.get("chain", [])
               if row.get("receipt_sha256") == expected_receipt_sha256]
    if len(matches) != 1:
        return {"disposition": "FAIL_CLOSED", "predicate": "EXPECTED_SOVEREIGN_RECEIPT_NOT_IN_CHAIN"}
    return {"disposition": "ALLOW", "predicate": "PUBLISHED_ORGANIZATION_CHAIN_AND_RECEIPT_VERIFIED",
            "verification_scope": "ORGANIZATION_RECORDING_ONLY_NOT_GOVERNANCE_ADMISSIBILITY",
            "receipt_sha256": expected_receipt_sha256,
            "head_receipt_sha256": observed["head_receipt_sha256"],
            "chain_length": observed["chain_length"]}
