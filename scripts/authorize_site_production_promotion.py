#!/usr/bin/env python3
"""Site production-promotion authorization transition (SPPA).

A production promotion of StegVerse-Labs/Site is a state transition of the
organization, so it is authorized only by a manifest-bound transition with an
Organization receipt (ORRD: EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_
ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT; standard 1, standard 5). CI and a
provider build are evidence, never authority (ORRD §Validation; SV-DN1 handoff
L141: Actions cannot become publication-decision or runtime authority).

This module is the pure transition. It evaluates predicates P1-P8 over the
evidence it is handed and, when ledger roots are supplied, appends a
SITE_PRODUCTION_PROMOTION_{AUTHORIZED,REFUSED,FAIL_CLOSED} receipt through the
EXISTING emitters (.stegverse/transition-ledger/emit.py, then
resident-runtime/aggregate_repo_transition.py) and reads it back through the
EXISTING verifier (organization_batch_custody.verified_organization_receipt),
the same pattern the org claim allocator consumer uses. It contacts no
provider, changes no provider setting, fetches nothing from the network and
dispatches nothing. It reads no clock: an AUTHORIZED receipt carries the
carrier-supplied heartbeat epoch or is not written.

Modes:
  PROMOTE         decide whether a candidate build may be promoted.
  RETRO_CLASSIFY  classify a provider deploy already observed; a deploy without
                  an AUTHORIZED receipt is FAIL_CLOSED
                  (PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT classification).
Authority effect: NONE. The allocator stays claim and fence authority; InTr
stays transition authority; this transition records, it does not deploy.

Fail-open correction (StegVerse-org/.github#167 c6249647656, against #3244):
caller-supplied evidence may refuse a promotion, never authorize one. Every
authorizing predicate (P1, P3-P7) PASSes only on an organization receipt that
is on the verified organization chain, was emitted by the repository the
existing declarations name as that evidence's issuer, binds the exact sha, and
whose readback custody basis authenticates. Evidence that is absent, off the
chain, or on a chain whose custody basis does not authenticate is UNKNOWN, and
decide() never turns UNKNOWN into AUTHORIZED: anything short of every predicate
PASS at its required authenticity is at most FAIL_CLOSED. No custody basis the
existing verifier reports authenticates today (organization_batch_custody
Q74-01: a verified readback never proves authentic custody, InTr admission or
an authorized ALLOW), so AUTHORIZED is unreachable until one is declared.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

REQUEST_SCHEMA = "stegverse.site-production-promotion-request/v1"
MANIFEST_SCHEMA = "stegverse.site-production-promotion-manifest/v1"
RESULT_SCHEMA = "stegverse.site-production-promotion-result/v1"
AUTHORIZED = "SITE_PRODUCTION_PROMOTION_AUTHORIZED"
REFUSED = "SITE_PRODUCTION_PROMOTION_REFUSED"
FAIL_CLOSED = "SITE_PRODUCTION_PROMOTION_FAIL_CLOSED"
DISPOSITION = {AUTHORIZED: "ALLOW", REFUSED: "DENY", FAIL_CLOSED: "FAIL_CLOSED"}
PROMOTE, RETRO = "PROMOTE", "RETRO_CLASSIFY"
SITE_REPOSITORY = "StegVerse-Labs/Site"
DEPENDENCY_SURFACE = "site:production-deploy"
CLAIM_AUTHORITY = "ORGANIZATION_CLAIM_ALLOCATOR"
CREDENTIAL_AUTHORITY = "TV/TVC"
OWNING_EXISTING_GOAL = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"
RETRY_ENTRYPOINT = "scripts/authorize_site_production_promotion.py"
UNKNOWN = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
GRANTED_CLASS = "ORGANIZATION_WORKER_CLAIM_GRANTED"
# A compare of <promotion ref>...<sha> reports the sha reachable from the ref
# only when the sha is the ref tip or one of its ancestors.
REACHABLE_COMPARE_STATUSES = ("identical", "behind")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

UNKNOWN_STATE = "UNKNOWN"
AUTHENTICATED = "AUTHENTICATED"
DECLARATION_BOUND = "DECLARATION_BOUND"
# Readback custody bases that authenticate an evidence receipt. Empty: every
# basis organization_batch_custody.readback_custody_basis reports today is
# "NO_CUSTODY_AUTHORITY_CLAIMED" (Q74-01), and CUSTODY_AUTHENTICATION on the
# chain is HASH_CHAIN_CONTINUITY_ONLY. Adding a basis here is its own reviewed
# transition; no request, manifest or caller can supply one.
AUTHENTICATING_CUSTODY_BASES: frozenset[str] = frozenset()
# Issuer declarations read from the source tree (never from the request).
INTR_BOUNDARY_DECLARATION = "org-runtime/interlock-intr.json"            # owner_repository: org ingress/egress + InTr
TVC_ISSUER_DECLARATION = "control/formalism-tvc-repository-transport.json"  # tvc_broker.repository: TV/TVC
# Organization receipt operations each predicate consumes (boundary_evidence.operation).
OP_SOURCE_REACHABILITY = "SITE_SOURCE_REACHABILITY_OBSERVED"
OP_EXACT_HEAD_CHECKS = "SITE_EXACT_HEAD_CHECKS_OBSERVED"
OP_INTR_ADMITTED = "SITE_PRODUCTION_PROMOTION_INTR_ADMITTED"   # <SUBJECT>_INTR_ADMITTED, as SDK_MANIFEST_INTR_ADMITTED
OP_TVC_ISSUED = "TVC_CREDENTIAL_ISSUED"
OP_PROVIDER_BUILD = "SITE_PROVIDER_BUILD_OBSERVED"
# Check conclusions, reconciled with scripts/evaluate_pr_precreation_gate.py and the
# INDEX exact-head rule (12:09Z): a required check that did not run and pass is not satisfied.
CHECK_FAILED_CONCLUSIONS = frozenset({"failure", "failed", "cancelled", "timed_out", "action_required",
                                      "startup_failure", "stale"})

# Refusal codes (lane file §18.3). FENCE_GENERATION_BEHIND_ISSUED_FENCES is the existing allocator code.
SOURCE_NOT_ON_REF = "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF"
MANIFEST_MISSING = "PROMOTION_MANIFEST_MISSING"
MANIFEST_SHA_MISMATCH = "PROMOTION_MANIFEST_SHA_MISMATCH"
CLAIM_MISSING = "PROMOTION_CLAIM_OR_FENCE_MISSING"
FENCE_BEHIND = "FENCE_GENERATION_BEHIND_ISSUED_FENCES"
INTR_MISSING = "PROMOTION_INTR_ADMISSION_MISSING"
CREDENTIAL_NOT_TVC = "PROMOTION_CREDENTIAL_AUTHORITY_NOT_TVC"
IDENTITY_MISMATCH = "PROVIDER_DEPLOY_IDENTITY_MISMATCH"
WITHOUT_RECEIPT = "PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT"
READBACK_NOT_VERIFIED = "PROMOTION_READBACK_NOT_VERIFIED"
# Fail-open correction codes (#167 c6249647656).
SOURCE_UNAUTHENTICATED = "PROMOTION_SOURCE_REACHABILITY_NOT_AUTHENTICALLY_OBSERVED"
CHECKS_UNAUTHENTICATED = "PROMOTION_EXACT_HEAD_CHECKS_NOT_AUTHENTICALLY_OBSERVED"
REQUIRED_CHECK_FAILED = "PROMOTION_REQUIRED_CHECK_FAILED"
REQUIRED_CHECK_NOT_PASSED = "PROMOTION_REQUIRED_CHECK_PENDING_SKIPPED_OR_MISSING"
REQUIRED_CHECK_POLICY_UNOBSERVED = "PROMOTION_REQUIRED_CHECK_POLICY_NOT_OBSERVED"
INTR_UNAUTHENTICATED = "PROMOTION_INTR_ADMISSION_NOT_AUTHENTICATED"
ISSUER_UNVERIFIED = "PROMOTION_CREDENTIAL_ISSUER_UNVERIFIABLE"
ISSUER_NOT_TVC = "PROMOTION_CREDENTIAL_ISSUER_NOT_TVC"
BUILD_UNAUTHENTICATED = "PROVIDER_BUILD_IDENTITY_NOT_AUTHENTICALLY_OBSERVED"
EVIDENCE_CUSTODY_UNAUTHENTICATED = "PROMOTION_EVIDENCE_CUSTODY_NOT_AUTHENTICATED"
PREDICATE_SET_INCOMPLETE = "PROMOTION_PREDICATE_SET_INCOMPLETE"
REFUSAL_CODES = (SOURCE_NOT_ON_REF, MANIFEST_MISSING, MANIFEST_SHA_MISMATCH, CLAIM_MISSING, FENCE_BEHIND,
                 INTR_MISSING, CREDENTIAL_NOT_TVC, IDENTITY_MISMATCH, WITHOUT_RECEIPT, READBACK_NOT_VERIFIED,
                 SOURCE_UNAUTHENTICATED, CHECKS_UNAUTHENTICATED, REQUIRED_CHECK_FAILED, REQUIRED_CHECK_NOT_PASSED,
                 REQUIRED_CHECK_POLICY_UNOBSERVED, INTR_UNAUTHENTICATED, ISSUER_UNVERIFIED, ISSUER_NOT_TVC,
                 BUILD_UNAUTHENTICATED, EVIDENCE_CUSTODY_UNAUTHENTICATED, PREDICATE_SET_INCOMPLETE)
# Evidence that is present and contradicts the promotion is a DENY in PROMOTE
# mode; absent or unverifiable evidence is FAIL_CLOSED. A deploy that already
# happened (RETRO_CLASSIFY) is always FAIL_CLOSED: nothing can be refused after the fact.
DENY_CODES = frozenset({SOURCE_NOT_ON_REF, MANIFEST_SHA_MISMATCH, CREDENTIAL_NOT_TVC, IDENTITY_MISMATCH,
                        REQUIRED_CHECK_FAILED, ISSUER_NOT_TVC})

PREDICATES = (
    ("P1", "PROMOTION_SOURCE_ON_PROMOTION_REF"),
    ("P2", "PROMOTION_MANIFEST_BINDS_SHA"),
    ("P3", "PROMOTION_CLAIM_AND_FENCE_ISSUED"),
    ("P4", "EXACT_SHA_REQUIRED_CHECKS_SUCCESS"),
    ("P5", "INTR_ADMISSION_AUTHENTICATED"),
    ("P6", "CREDENTIAL_ISSUED_BY_TVC"),
    ("P7", "PROVIDER_BUILD_MATCHES_MANIFEST"),
    ("P8", "FRESH_FETCH_READBACK_VERIFIED"),
)
PREDICATE_NAME = dict(PREDICATES)
# The authenticity each predicate must carry for AUTHORIZED. P2 binds the caller's
# own declaration (the manifest) by recomputation; every other predicate needs an
# authenticated organization receipt.
REQUIRED_AUTHENTICITY = {"P1": AUTHENTICATED, "P2": DECLARATION_BOUND, "P3": AUTHENTICATED, "P4": AUTHENTICATED,
                         "P5": AUTHENTICATED, "P6": AUTHENTICATED, "P7": AUTHENTICATED}
MANIFEST_REQUIRED = ("schema", "repository", "sha", "promotion_ref", "environment", "route", "service",
                     "worker_main", "assets_directory", "d1_bindings", "wrangler_config_sha256",
                     "dependency_surface", "claim_task_id", "claim_scope", "owning_existing_goal")
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
              "owning_existing_goal", "next_attempt")

REPAIR = {
    SOURCE_NOT_ON_REF: "merge the exact sha into the promotion ref through its own reviewed transition, then promote that sha",
    MANIFEST_MISSING: "supply a " + MANIFEST_SCHEMA + " manifest binding the sha, environment, route and wrangler config",
    MANIFEST_SHA_MISMATCH: "supply a manifest whose sha, repository, ref and wrangler_config_sha256 equal the promoted source",
    CLAIM_MISSING: ("supply the ORGANIZATION_WORKER_CLAIM_GRANTED receipt for dependency surface " + DEPENDENCY_SURFACE
                    + " issued by the organization claim allocator; a session claim is never claim authority"),
    FENCE_BEHIND: "obtain a fresh allocator grant whose fence exceeds every issued fence for the task and the floor",
    INTR_MISSING: "supply the InTr admission reference that admits this exact sha for SITE_PRODUCTION_PROMOTION",
    CREDENTIAL_NOT_TVC: "supply the TV/TVC credential reference; GitHub token runtime authority stays NONE",
    IDENTITY_MISMATCH: "promote the provider build whose service, environment and commit equal the manifest",
    WITHOUT_RECEIPT: "record a SITE_PRODUCTION_PROMOTION_AUTHORIZED receipt before any production promotion",
    READBACK_NOT_VERIFIED: "re-read the appended receipt from a fresh fetch of the organization ledger; do not promote until it verifies",
    SOURCE_UNAUTHENTICATED: ("supply the organization receipt (" + OP_SOURCE_REACHABILITY + ") recording an authenticated "
                             "compare of the promotion ref to the exact sha; a caller-supplied compare can only refuse"),
    CHECKS_UNAUTHENTICATED: ("supply the organization receipt (" + OP_EXACT_HEAD_CHECKS + ") recording the required-check "
                             "policy and the check runs observed at the exact sha"),
    REQUIRED_CHECK_FAILED: "fix the failing required check at the exact sha and observe it again; a failed required check refuses",
    REQUIRED_CHECK_NOT_PASSED: "every required check must have run and concluded success at the exact sha (pending, skipped or missing is not success)",
    REQUIRED_CHECK_POLICY_UNOBSERVED: "observe the promotion ref's required-check policy into the checks receipt; an empty or absent policy is never satisfied",
    INTR_UNAUTHENTICATED: ("supply the InTr admission organization receipt (" + OP_INTR_ADMITTED + ") emitted at the InTr "
                           "boundary declared in " + INTR_BOUNDARY_DECLARATION + " for this exact sha"),
    ISSUER_UNVERIFIED: ("supply the TV/TVC issuance organization receipt (" + OP_TVC_ISSUED + ") emitted by the issuer "
                        "declared in " + TVC_ISSUER_DECLARATION + " for this credential reference and surface"),
    ISSUER_NOT_TVC: "obtain the credential from the TV/TVC issuer declared in " + TVC_ISSUER_DECLARATION + "; any other or self-issued credential refuses",
    BUILD_UNAUTHENTICATED: ("supply the provider build organization receipt (" + OP_PROVIDER_BUILD + "); the build identity "
                            "must not come from the same caller input as the manifest"),
    EVIDENCE_CUSTODY_UNAUTHENTICATED: ("the evidence receipt is on the verified chain but its readback custody basis does "
                                       "not authenticate (Q74-01); declare an authenticating custody basis by its own transition"),
    PREDICATE_SET_INCOMPLETE: "evaluate every predicate P1-P7; a missing predicate is never satisfied",
}


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result(pid: str, state: str, code: str | None = None, detail: str = "", **extra: Any) -> dict[str, Any]:
    return {"predicate": pid, "name": PREDICATE_NAME[pid], "state": state, "failure_code": code,
            "detail": detail, **extra}


def _unknown(pid: str, code: str, detail: str, **extra: Any) -> dict[str, Any]:
    """Not authentically observed: never PASS, at most FAIL_CLOSED (decide())."""
    return _result(pid, UNKNOWN_STATE, code, detail, authenticity=UNKNOWN, **extra)


def declared_issuers(source: Path) -> dict[str, str | None]:
    """Issuer repositories read from the existing declarations in the source tree, never from the request.

    boundary: org-runtime/interlock-intr.json owner_repository, where all organization
              ingress/egress and InTr admission are generated (observations P1/P4/P7, admission P5).
    tvc:      control/formalism-tvc-repository-transport.json tvc_broker.repository, the TV/TVC
              credential authority (canonical task TVC-CREDENTIAL-MODEL-CONSISTENCY-20260826).
    An unreadable declaration leaves its issuer None, so evidence it would vouch for stays UNKNOWN.
    """
    issuers: dict[str, str | None] = {"boundary": None, "tvc": None}
    try:
        value = json.loads((source / INTR_BOUNDARY_DECLARATION).read_text(encoding="utf-8")).get("owner_repository")
        issuers["boundary"] = value if isinstance(value, str) and "/" in value else None
    except (OSError, ValueError, AttributeError):
        pass
    try:
        broker = json.loads((source / TVC_ISSUER_DECLARATION).read_text(encoding="utf-8")).get("tvc_broker") or {}
        value = broker.get("repository") if isinstance(broker, Mapping) else None
        issuers["tvc"] = value if isinstance(value, str) and "/" in value else None
    except (OSError, ValueError, AttributeError):
        pass
    return issuers


def evidence_custody_basis(custody: Mapping[str, Any] | None, row: Mapping[str, Any]) -> str | None:
    """The existing verifier's readback custody basis for an evidence receipt (never custody authority)."""
    if custody is None:
        return None
    return custody["organization_receipt_custody"].readback_custody_basis(row)


def _context(chain_rows: list[dict[str, Any]] | None = None, *, issuers: Mapping[str, str | None] | None = None,
             basis_of=None) -> dict[str, Any]:
    return {"chain_rows": chain_rows, "issuers": dict(issuers or {}), "basis_of": basis_of or (lambda row: None)}


def _authenticated(ctx: Mapping[str, Any], row: Mapping[str, Any]) -> tuple[bool, str | None]:
    basis = ctx["basis_of"](row)
    return basis in AUTHENTICATING_CUSTODY_BASES, basis


def chain_evidence(ctx: Mapping[str, Any], pid: str, digest: Any, *, operation: str, issuer_key: str,
                   unverified_code: str, subject: Mapping[str, Any], wrong_issuer_code: str | None = None):
    """(row, None) when `digest` names a receipt on the verified chain, from the declared issuer, recording
    `operation` for exactly `subject`; (None, result) otherwise. Authenticity is decided by the caller."""
    if not isinstance(digest, str) or not digest:
        return None, _unknown(pid, unverified_code, "no organization receipt referenced; caller-supplied evidence "
                                                   "may refuse a promotion, never authorize one")
    rows = ctx["chain_rows"]
    if rows is None:
        return None, _unknown(pid, unverified_code, "no verified organization chain to read " + operation + " from")
    row = next((r for r in rows if r.get("receipt_sha256") == digest), None)
    if row is None:
        return None, _unknown(pid, unverified_code, f"{digest} is not on the verified organization chain")
    issuer = ctx["issuers"].get(issuer_key)
    if not issuer:
        return None, _unknown(pid, unverified_code, f"{issuer_key} issuer declaration unreadable")
    if row.get("source_repository") != issuer:
        detail = f"receipt emitted by {row.get('source_repository')!r}, not the declared issuer {issuer!r}"
        if wrong_issuer_code is not None:
            return None, _result(pid, "FAIL", wrong_issuer_code, detail, authenticity=UNKNOWN)
        return None, _unknown(pid, unverified_code, detail)
    evidence = row.get("boundary_evidence") or {}
    if evidence.get("operation") != operation:
        # Also refuses the SPPA's own receipts (which carry caller input) as observations.
        return None, _unknown(pid, unverified_code, f"receipt operation {evidence.get('operation')!r} is not {operation}")
    for key, expected in subject.items():
        if expected in (None, "") or evidence.get(key) != expected:
            return None, _unknown(pid, unverified_code, f"receipt {key} {evidence.get(key)!r} does not observe {expected!r}")
    return row, None


def _custody_unknown(ctx: Mapping[str, Any], pid: str, row: Mapping[str, Any], code: str):
    ok, basis = _authenticated(ctx, row)
    if ok:
        return None
    return _unknown(pid, code, f"receipt {row.get('receipt_sha256')} custody basis {basis!r} does not authenticate "
                               "(organization_batch_custody Q74-01)", evidence_receipt_sha256=row.get("receipt_sha256"))


def p1_source_on_ref(request: Mapping[str, Any], ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or _context()
    sha, ref = request.get("sha"), request.get("promotion_ref")
    supplied = request.get("source_reachability")
    if isinstance(supplied, Mapping) and supplied.get("head_sha") == sha and supplied.get("base_ref") == ref \
            and supplied.get("compare_status") not in REACHABLE_COMPARE_STATUSES:
        # Unauthenticated evidence against the promotion may refuse it.
        return _result("P1", "FAIL", SOURCE_NOT_ON_REF,
                       f"{sha} is not reachable from {ref} at {supplied.get('base_sha')} (supplied compare status "
                       f"{supplied.get('compare_status')}, ahead_by {supplied.get('ahead_by')}, "
                       f"behind_by {supplied.get('behind_by')})", authenticity=UNKNOWN)
    row, unknown = chain_evidence(ctx, "P1", (request.get("source_observation") or {}).get("organization_receipt_sha256"),
                                  operation=OP_SOURCE_REACHABILITY, issuer_key="boundary",
                                  unverified_code=SOURCE_UNAUTHENTICATED,
                                  subject={"repository": request.get("repository"), "head_sha": sha, "base_ref": ref})
    if unknown is not None:
        return unknown
    observed = row["boundary_evidence"]
    if observed.get("compare_status") not in REACHABLE_COMPARE_STATUSES:
        return _result("P1", "FAIL", SOURCE_NOT_ON_REF, f"{sha} is not reachable from {ref} (observed compare status "
                                                        f"{observed.get('compare_status')})", authenticity=UNKNOWN)
    unknown = _custody_unknown(ctx, "P1", row, SOURCE_UNAUTHENTICATED)
    if unknown is not None:
        return unknown
    return _result("P1", "PASS", detail=f"{sha} reachable from {ref} ({observed.get('compare_status')})",
                   authenticity=AUTHENTICATED, evidence_receipt_sha256=row["receipt_sha256"])


def p2_manifest_binds_sha(request: Mapping[str, Any]) -> dict[str, Any]:
    manifest = request.get("manifest")
    if not isinstance(manifest, Mapping):
        return _result("P2", "FAIL", MANIFEST_MISSING, "no promotion manifest")
    missing = [key for key in MANIFEST_REQUIRED if key not in manifest]
    if manifest.get("schema") != MANIFEST_SCHEMA or missing:
        return _result("P2", "FAIL", MANIFEST_MISSING, "manifest incomplete: " + ", ".join(missing or ["schema"]))
    declared = request.get("manifest_sha256")
    if declared != stable_hash(manifest):
        return _result("P2", "FAIL", MANIFEST_SHA_MISMATCH, "declared manifest_sha256 does not recompute")
    for key, expected in (("repository", request.get("repository")), ("sha", request.get("sha")),
                          ("promotion_ref", request.get("promotion_ref")),
                          ("wrangler_config_sha256", request.get("wrangler_config_sha256")),
                          ("dependency_surface", DEPENDENCY_SURFACE)):
        if manifest.get(key) != expected:
            return _result("P2", "FAIL", MANIFEST_SHA_MISMATCH, f"manifest {key} {manifest.get(key)!r} != {expected!r}")
    if not SHA256.match(str(manifest.get("wrangler_config_sha256"))):
        return _result("P2", "FAIL", MANIFEST_SHA_MISMATCH, "wrangler_config_sha256 is not a sha256")
    # The manifest is the request's own declaration: it binds, it does not authenticate.
    return _result("P2", "PASS", detail="manifest " + declared + " binds the sha", authenticity=DECLARATION_BOUND)


def p3_claim_and_fence(request: Mapping[str, Any], grants: list[dict[str, Any]] | None,
                       floor_fence: int | None, ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or _context()
    claim, manifest = request.get("claim"), request.get("manifest") or {}
    if not isinstance(claim, Mapping):
        return _result("P3", "FAIL", CLAIM_MISSING, "no claim or fence supplied")
    if claim.get("claim_authority") != CLAIM_AUTHORITY:
        # TRCI worker-claim invariant: a chat or agent session is never claim authority.
        return _result("P3", "FAIL", CLAIM_MISSING,
                       f"claim authority {claim.get('claim_authority')!r} is not the organization claim allocator")
    if grants is None or floor_fence is None:
        return _result("P3", "FAIL", CLAIM_MISSING, "no verified organization chain to read the grant from")
    digest = claim.get("organization_receipt_sha256")
    row = next((g for g in grants if g.get("receipt_sha256") == digest), None)
    if row is None:
        return _result("P3", "FAIL", CLAIM_MISSING, f"grant {digest} is not on the verified organization chain")
    evidence = row.get("boundary_evidence") or {}
    fence = evidence.get("fencing_token")
    if fence != claim.get("fencing_token") or evidence.get("task_id") != manifest.get("claim_task_id"):
        return _result("P3", "FAIL", CLAIM_MISSING, "grant fence or task does not match the claim and manifest")
    if evidence.get("claim_scope_sha256") != stable_hash(manifest.get("claim_scope")) or \
            DEPENDENCY_SURFACE not in json.dumps(manifest.get("claim_scope"), sort_keys=True):
        return _result("P3", "FAIL", CLAIM_MISSING, "grant scope does not cover " + DEPENDENCY_SURFACE)
    later = [g for g in grants if (g.get("boundary_evidence") or {}).get("task_id") == evidence.get("task_id")
             and (g.get("boundary_evidence") or {}).get("fencing_token", 0) > fence]
    if fence <= floor_fence or later:
        return _result("P3", "FAIL", FENCE_BEHIND,
                       f"fence {fence} is not beyond the issued floor {floor_fence} or a later grant superseded it")
    unknown = _custody_unknown(ctx, "P3", row, EVIDENCE_CUSTODY_UNAUTHENTICATED)
    if unknown is not None:
        unknown["fencing_token"] = fence
        return unknown
    return _result("P3", "PASS", detail=f"allocator grant {digest} fence {fence} > floor {floor_fence}",
                   fencing_token=fence, authenticity=AUTHENTICATED, evidence_receipt_sha256=digest)


def p4_checks(request: Mapping[str, Any], ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Required checks at the exact sha gate the promotion; non-required checks are informational.

    Reconciled with scripts/evaluate_pr_precreation_gate.py (a failed required check refuses; a pending
    or missing one is not satisfied) and the INDEX exact-head rule (every required job ran and passed:
    skipped and neutral are not success). The policy and the runs come from one authenticated
    observation; caller-supplied check runs are recorded, never authorizing.
    """
    ctx = ctx or _context()
    sha = request.get("sha")
    supplied_ids = sorted(c.get("id") for c in (request.get("checks") or [])
                          if isinstance(c, Mapping) and c.get("head_sha") == sha and c.get("id") is not None)
    extra = {"exact_sha_check_run_ids": supplied_ids, "grants_authority": False}
    row, unknown = chain_evidence(ctx, "P4", (request.get("checks_observation") or {}).get("organization_receipt_sha256"),
                                  operation=OP_EXACT_HEAD_CHECKS, issuer_key="boundary",
                                  unverified_code=CHECKS_UNAUTHENTICATED,
                                  subject={"repository": request.get("repository"), "head_sha": sha})
    if unknown is not None:
        unknown.update(extra)
        return unknown
    observed = row["boundary_evidence"]
    required = observed.get("required_checks")
    runs = [r for r in (observed.get("check_runs") or []) if isinstance(r, Mapping) and r.get("head_sha") == sha]
    extra["exact_sha_check_run_ids"] = sorted({*supplied_ids, *(r.get("id") for r in runs if r.get("id") is not None)})
    if not isinstance(required, list) or not required or not all(isinstance(n, str) and n for n in required):
        return _unknown("P4", REQUIRED_CHECK_POLICY_UNOBSERVED, "the observation records no required-check policy",
                        **extra)
    failed, unsatisfied = [], []
    for name in sorted(set(required)):
        conclusions = [str(r.get("conclusion") or "").lower() for r in runs if r.get("name") == name]
        if any(c in CHECK_FAILED_CONCLUSIONS for c in conclusions):
            failed.append(name)
        elif not conclusions or any(c != "success" for c in conclusions):
            unsatisfied.append(f"{name}={'/'.join(conclusions) or 'missing'}")
    extra.update(required_checks=sorted(set(required)),
                 informational_checks=sorted({r.get("name") for r in runs if r.get("name") not in required}))
    if failed:
        return _result("P4", "FAIL", REQUIRED_CHECK_FAILED, "required checks failed at the exact sha: " + ", ".join(failed),
                       authenticity=UNKNOWN, **extra)
    if unsatisfied:
        return _result("P4", "FAIL", REQUIRED_CHECK_NOT_PASSED,
                       "required checks not run-and-passed at the exact sha: " + ", ".join(unsatisfied),
                       authenticity=UNKNOWN, **extra)
    unknown = _custody_unknown(ctx, "P4", row, CHECKS_UNAUTHENTICATED)
    if unknown is not None:
        unknown.update(extra)
        return unknown
    return _result("P4", "PASS", detail=f"{len(extra['required_checks'])} required checks success at the exact sha",
                   authenticity=AUTHENTICATED, evidence_receipt_sha256=row["receipt_sha256"], **extra)


def p5_intr(request: Mapping[str, Any], ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or _context()
    admission = request.get("intr_admission")
    if not isinstance(admission, Mapping) or admission.get("admitted_sha") != request.get("sha") \
            or admission.get("transition") != "SITE_PRODUCTION_PROMOTION":
        return _result("P5", "FAIL", INTR_MISSING, "no InTr admission reference for this sha")
    row, unknown = chain_evidence(ctx, "P5", admission.get("organization_receipt_sha256"), operation=OP_INTR_ADMITTED,
                                  issuer_key="boundary", unverified_code=INTR_UNAUTHENTICATED,
                                  subject={"admitted_sha": request.get("sha"), "transition": "SITE_PRODUCTION_PROMOTION"})
    if unknown is not None:
        return unknown
    if row["boundary_evidence"].get("manifest_sha256") != request.get("manifest_sha256"):
        return _result("P5", "FAIL", INTR_MISSING, "the InTr admission admits a different manifest", authenticity=UNKNOWN)
    unknown = _custody_unknown(ctx, "P5", row, INTR_UNAUTHENTICATED)
    if unknown is not None:
        return unknown
    return _result("P5", "PASS", detail="InTr admission " + row["receipt_sha256"], authenticity=AUTHENTICATED,
                   evidence_receipt_sha256=row["receipt_sha256"])


def p6_credential(request: Mapping[str, Any], ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or _context()
    credential = request.get("credential")
    if not isinstance(credential, Mapping):
        return _result("P6", "FAIL", CREDENTIAL_NOT_TVC, "no credential reference")
    if credential.get("authority") != CREDENTIAL_AUTHORITY or credential.get("github_token_runtime_authority") != "NONE":
        return _result("P6", "FAIL", CREDENTIAL_NOT_TVC, "credential authority is not TV/TVC with GitHub token authority NONE")
    tvc = ctx["issuers"].get("tvc")
    declared = credential.get("issuer")
    if declared is not None and tvc and declared != tvc:
        # A declared issuer other than TV/TVC (forged, or the requester itself) refuses.
        return _result("P6", "FAIL", ISSUER_NOT_TVC, f"credential declares issuer {declared!r}, not TV/TVC {tvc!r}",
                       authenticity=UNKNOWN)
    reference = credential.get("reference")
    row, unknown = chain_evidence(ctx, "P6", credential.get("issuance_receipt_sha256"), operation=OP_TVC_ISSUED,
                                  issuer_key="tvc", unverified_code=ISSUER_UNVERIFIED, wrong_issuer_code=ISSUER_NOT_TVC,
                                  subject={"credential_reference": reference, "dependency_surface": DEPENDENCY_SURFACE})
    if unknown is not None:
        return unknown
    issued = row["boundary_evidence"]
    if issued.get("credential_authority") != CREDENTIAL_AUTHORITY or issued.get("github_token_runtime_authority") != "NONE":
        return _result("P6", "FAIL", ISSUER_NOT_TVC, "the issuance does not record TV/TVC authority with GitHub token NONE",
                       authenticity=UNKNOWN)
    unknown = _custody_unknown(ctx, "P6", row, ISSUER_UNVERIFIED)
    if unknown is not None:
        return unknown
    return _result("P6", "PASS", detail=f"TV/TVC issuance {row['receipt_sha256']} for {reference}",
                   authenticity=AUTHENTICATED, evidence_receipt_sha256=row["receipt_sha256"], issuer=tvc)


def p7_provider_build(request: Mapping[str, Any], ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or _context()
    build, manifest = request.get("provider_build"), request.get("manifest")
    if not isinstance(manifest, Mapping):
        return _result("P7", "FAIL", IDENTITY_MISMATCH, "no manifest to match the provider build against")
    build = build if isinstance(build, Mapping) else {}
    for key, expected in (("service", manifest.get("service")), ("environment", manifest.get("environment")),
                          ("commit_sha", request.get("sha"))):
        if key in build and build.get(key) != expected:
            # Supplied identity that contradicts the manifest may refuse.
            return _result("P7", "FAIL", IDENTITY_MISMATCH, f"provider build {key} {build.get(key)!r} != {expected!r}",
                           authenticity=UNKNOWN)
    build_id = build.get("build_id") or manifest.get("provider_build_id")
    row, unknown = chain_evidence(ctx, "P7", build.get("observation_receipt_sha256"), operation=OP_PROVIDER_BUILD,
                                  issuer_key="boundary", unverified_code=BUILD_UNAUTHENTICATED,
                                  subject={"repository": request.get("repository"), "build_id": build_id})
    if unknown is not None:
        if unknown["detail"].startswith("no organization receipt referenced"):
            unknown["detail"] = ("build identity comes only from the request, the same caller input as the manifest "
                                 "(self-referential): " + unknown["detail"])
        return unknown
    observed = row["boundary_evidence"]
    for key, expected in (("service", manifest.get("service")), ("environment", manifest.get("environment")),
                          ("commit_sha", request.get("sha"))):
        if observed.get(key) != expected:
            return _result("P7", "FAIL", IDENTITY_MISMATCH, f"observed provider build {key} {observed.get(key)!r} != "
                                                            f"{expected!r}", authenticity=UNKNOWN)
    if manifest.get("provider_build_id") not in (None, observed.get("build_id")):
        return _result("P7", "FAIL", IDENTITY_MISMATCH, "observed provider build id differs from the manifest",
                       authenticity=UNKNOWN)
    unknown = _custody_unknown(ctx, "P7", row, BUILD_UNAUTHENTICATED)
    if unknown is not None:
        return unknown
    return _result("P7", "PASS", detail="observed provider build " + str(observed.get("build_id")),
                   authenticity=AUTHENTICATED, evidence_receipt_sha256=row["receipt_sha256"])


def evaluate(request: Mapping[str, Any], *, grants: list[dict[str, Any]] | None = None,
             floor_fence: int | None = None, chain_rows: list[dict[str, Any]] | None = None,
             issuers: Mapping[str, str | None] | None = None, basis_of=None) -> list[dict[str, Any]]:
    """P1-P7 over the supplied evidence; P8 is decided by the readback after an append. No clock, no network."""
    ctx = _context(chain_rows, issuers=issuers, basis_of=basis_of)
    return [p1_source_on_ref(request, ctx), p2_manifest_binds_sha(request),
            p3_claim_and_fence(request, grants, floor_fence, ctx), p4_checks(request, ctx), p5_intr(request, ctx),
            p6_credential(request, ctx), p7_provider_build(request, ctx)]


def validate_request(request: Any) -> None:
    if not isinstance(request, Mapping) or request.get("schema") != REQUEST_SCHEMA:
        raise ValueError("request schema must be " + REQUEST_SCHEMA)
    if request.get("mode") not in (PROMOTE, RETRO):
        raise ValueError("mode must be PROMOTE or RETRO_CLASSIFY")
    if request.get("repository") != SITE_REPOSITORY:
        raise ValueError("repository must be " + SITE_REPOSITORY)
    if not SHA40.match(str(request.get("sha"))):
        raise ValueError("sha must be the exact 40-hex commit")
    if not str(request.get("promotion_ref") or "").startswith("refs/heads/"):
        raise ValueError("promotion_ref must be a full refs/heads/ ref")


def unsatisfied_predicates(predicates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every predicate short of PASS at its required authenticity, plus any required predicate missing.

    Global invariant: UNKNOWN (or any state other than PASS, or PASS without the required authenticity)
    is never satisfied, so it can never contribute to AUTHORIZED.
    """
    present = {p.get("predicate") for p in predicates}
    out = [p for p in predicates if p.get("predicate") in REQUIRED_AUTHENTICITY
           and not (p.get("state") == "PASS" and p.get("authenticity") == REQUIRED_AUTHENTICITY[p["predicate"]])]
    out += [_unknown(pid, PREDICATE_SET_INCOMPLETE, "predicate not evaluated")
            for pid in REQUIRED_AUTHENTICITY if pid not in present]
    return out


def decide(request: Mapping[str, Any], predicates: list[dict[str, Any]], *,
           prior_authorization: Mapping[str, Any] | None) -> dict[str, Any]:
    failed = [p for p in predicates if p.get("state") == "FAIL"]
    unsatisfied = unsatisfied_predicates(predicates)
    first = (failed or unsatisfied or [None])[0]
    mode = request["mode"]
    if mode == RETRO:
        if first is not None:
            return {"transition_class": FAIL_CLOSED, "failure_code": first["failure_code"] or PREDICATE_SET_INCOMPLETE,
                    "failed_predicate": first["name"], "classification": WITHOUT_RECEIPT}
        if prior_authorization is None:
            return {"transition_class": FAIL_CLOSED, "failure_code": WITHOUT_RECEIPT,
                    "failed_predicate": "PRODUCTION_PROMOTION_AUTHORIZED_BY_MANIFEST_AND_SOVEREIGN_RECEIPT",
                    "classification": WITHOUT_RECEIPT}
        return {"transition_class": None, "classification": "AUTHORIZED_RECEIPT_PRESENT"}
    if failed:
        cls = REFUSED if first["failure_code"] in DENY_CODES else FAIL_CLOSED
        return {"transition_class": cls, "failure_code": first["failure_code"], "failed_predicate": first["name"]}
    if first is not None:
        # UNKNOWN never yields PASS: at most FAIL_CLOSED.
        return {"transition_class": FAIL_CLOSED, "failure_code": first["failure_code"] or PREDICATE_SET_INCOMPLETE,
                "failed_predicate": first["name"]}
    return {"transition_class": AUTHORIZED, "failure_code": None, "failed_predicate": None}


def prior_authorization_for(chain_rows: list[dict[str, Any]], request: Mapping[str, Any]) -> dict[str, Any] | None:
    build_id = (request.get("provider_build") or {}).get("build_id")
    for row in reversed(chain_rows):
        evidence = row.get("boundary_evidence") or {}
        if evidence.get("operation") == AUTHORIZED and evidence.get("sha") == request.get("sha") \
                and evidence.get("provider_build_id") == build_id:
            return row
    return None


def _six(decision: Mapping[str, Any], detail: str) -> dict[str, Any]:
    code = decision["failure_code"]
    return {"failure_code": code, "failed_predicate": decision["failed_predicate"], "detail": detail,
            "required_evidence_or_repair": REPAIR.get(code, "see detail"),
            "retry_entrypoint": RETRY_ENTRYPOINT, "next_attempt": "on the next promotion request after the repair is recorded"}


def authorize(request: Mapping[str, Any], *, source: Path = ROOT, repo_ledger_root: Path | None = None,
              org_ledger_root: Path | None = None, hb_epoch: int | str | None = None) -> dict[str, Any]:
    """Evaluate and, with ledger roots, record the transition and read it back."""
    validate_request(request)
    consumer = _load("sppa_org_claim_consumer", source / "scripts/consume_org_claim_allocator_request.py")
    kernel = _load("sppa_org_kernel", source / "org-kernel/kernel.py")
    custody = chain = None
    grants = floor_fence = None
    chain_rows: list[dict[str, Any]] = []
    chain_refusal = None
    if repo_ledger_root is not None:
        custody = consumer.ledger_custody(source, repo_ledger_root, org_ledger_root,
                                          hb_epoch=int(str(hb_epoch)) if hb_epoch is not None
                                          and kernel.supplied_epoch_failure(hb_epoch) is None else None)
        try:
            chain = consumer.verify_organization_chain(custody)
            chain_rows = list(chain["receipts"])
            grants = consumer.chain_grants(chain)
            floor_fence = consumer.provenance_floor(source)["fence"]
        except consumer.ClaimFailClosed as exc:
            chain_refusal = exc.predicate + ": " + exc.detail
    verified_rows = chain_rows if chain is not None and chain_refusal is None else None
    predicates = evaluate(request, grants=grants, floor_fence=floor_fence, chain_rows=verified_rows,
                          issuers=declared_issuers(source), basis_of=lambda row: evidence_custody_basis(custody, row))
    if chain_refusal is not None:
        predicates[2] = _result("P3", "FAIL", CLAIM_MISSING, "organization chain unverified: " + chain_refusal)
    decision = decide(request, predicates, prior_authorization=prior_authorization_for(verified_rows or [], request))
    manifest = request.get("manifest") if isinstance(request.get("manifest"), Mapping) else None
    build = request.get("provider_build") or {}
    failed = [p for p in predicates if p["state"] == "FAIL"]
    unsatisfied = unsatisfied_predicates(predicates)
    detail = "; ".join(f"{p['predicate']} {p['failure_code']}: {p['detail']}"
                       for p in failed + [p for p in unsatisfied if p not in failed])
    epoch_failure = kernel.supplied_epoch_failure(hb_epoch) if hb_epoch is not None else None
    if decision["transition_class"] == AUTHORIZED and (hb_epoch is None or epoch_failure is not None):
        # An authorizing receipt carries the carrier's epoch; none is derived from a clock.
        decision = {"transition_class": FAIL_CLOSED,
                    "failure_code": kernel.HB_EPOCH_NOT_SUPPLIED if hb_epoch is None else epoch_failure[0],
                    "failed_predicate": kernel.HB_EPOCH_PREDICATE}
        detail = "an AUTHORIZED receipt requires the carrier-supplied heartbeat epoch"
    cls = decision["transition_class"]
    evidence = {
        "disposition": DISPOSITION.get(cls, "ALLOW") if cls else "ALLOW",
        "mode": request["mode"],
        "repository": request["repository"],
        "sha": request["sha"],
        "promotion_ref": request["promotion_ref"],
        "promotion_ref_observed_sha": (request.get("source_reachability") or {}).get("base_sha"),
        "manifest_sha256": request.get("manifest_sha256") if manifest else None,
        "environment": manifest.get("environment") if manifest else build.get("environment"),
        "route": manifest.get("route") if manifest else UNKNOWN,
        "provider": build.get("provider"),
        "provider_service": build.get("service"),
        "provider_build_id": build.get("build_id"),
        "provider_route_serving": build.get("route_serving", UNKNOWN),
        "claim_receipt_sha256": (request.get("claim") or {}).get("organization_receipt_sha256"),
        "fencing_token": (request.get("claim") or {}).get("fencing_token"),
        "intr_admission_receipt_sha256": (request.get("intr_admission") or {}).get("organization_receipt_sha256"),
        "credential_authority": (request.get("credential") or {}).get("authority"),
        "exact_sha_check_run_ids": predicates[3].get("exact_sha_check_run_ids", []),
        "predicates": [{k: p.get(k) for k in ("predicate", "name", "state", "failure_code", "authenticity")}
                       for p in predicates],
        "failed_predicates": [p["name"] for p in failed],
        "unknown_predicates": [p["name"] for p in unsatisfied if p.get("state") != "FAIL"],
        "evidence_receipts": {p["predicate"]: p.get("evidence_receipt_sha256") for p in predicates
                              if p.get("evidence_receipt_sha256")},
        "classification": decision.get("classification"),
        "predecessor_receipt_sha256": (chain or {}).get("head_sha256"),
        "owning_existing_goal": request.get("owning_existing_goal") or OWNING_EXISTING_GOAL,
        "consequence_committed": cls == AUTHORIZED,
        "provider_settings_changed": False,
        "deployment_performed": False,
    }
    if cls in (REFUSED, FAIL_CLOSED):
        evidence.update(_six(decision, detail))
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA, "mode": request["mode"], "transition_class": cls,
        "disposition": evidence["disposition"], "classification": decision.get("classification"),
        "predicates": predicates, "evidence": evidence, "receipt_appended": False,
        "promotion_may_proceed": False, "authority_effect": "NONE",
    }
    if cls in (REFUSED, FAIL_CLOSED):
        result.update({k: evidence[k] for k in SIX_FIELDS})
    if cls is None:
        result["prior_authorization_receipt_sha256"] = \
            prior_authorization_for(verified_rows or [], request)["receipt_sha256"]
        return result
    if custody is None or chain_refusal is not None:
        result["organization_readback"] = "NOT_PERFORMED"
        return result
    if hb_epoch is None or epoch_failure is not None:
        # No supplied epoch in scope: the disposition is returned, not recorded,
        # and no clock is read to stamp a receipt (WU-B13 slice g). The six
        # fields are in the result; record_refusal says why nothing was written.
        result.update({"receipt_appended": False, "organization_readback": "NOT_PERFORMED"})
        result["record_refusal"] = kernel.no_epoch_caller_refusal(
            "scripts/authorize_site_production_promotion.py::authorize",
            retry_entrypoint=RETRY_ENTRYPOINT + " (hb_epoch=, or --hb-epoch)")
        return result
    transition_id = f"{cls}-{request['sha'][:12]}-" + stable_hash(
        {"mode": request["mode"], "sha": request["sha"], "build": build.get("build_id"),
         "manifest": evidence["manifest_sha256"], "failure_code": evidence.get("failure_code")})[:16]
    identity = ("sha", "provider_build_id", "manifest_sha256", "failure_code", "mode")
    successor = "sha256:" + stable_hash({"transition_id": transition_id, "evidence": evidence})
    predecessor = "sha256:" + stable_hash({"sha": request["sha"], "promotion_ref": request["promotion_ref"]})
    emitter, store = custody["emitter"], custody["repository_store"]
    prior = emitter.recorded(store, store.get(emitter.ledger_store.HEAD_KEY), transition_id, cls)
    if prior is not None:
        successor = prior["successor_state_sha256"]
    epoch = int(str(hb_epoch))
    repository_receipt = emitter.append(transition_id, cls, predecessor, successor, evidence, "NONE",
                                        hb_epoch=epoch, store=store, idempotent_on=identity)
    # Carried from the RECORDED repository evidence, so a retry consumes the same source with the same context.
    recorded = repository_receipt.get("evidence") or {}
    carried = {k: recorded.get(k) for k in (
        "disposition", "mode", "repository", "sha", "promotion_ref", "manifest_sha256", "environment", "route",
        "provider_service", "provider_build_id", "claim_receipt_sha256", "fencing_token",
        "predecessor_receipt_sha256", "classification", *SIX_FIELDS)}
    organization_receipt = custody["organization_ledger"].aggregate_transition(
        repository_receipt, org_transition_class="REPO_STATE_PROPAGATION",
        predecessor_org_state_sha256=repository_receipt["predecessor_state_sha256"],
        successor_org_state_sha256=repository_receipt["successor_state_sha256"],
        boundary_evidence={"operation": cls, **carried}, authority_effect="NONE",
        ledger=consumer.organization_target(custody), hb_epoch=epoch,
        _materialized_repository_ledger=custody["repository_store"])
    result.update({"receipt_appended": True, "transition_id": transition_id,
                   "repository_receipt_sha256": repository_receipt["receipt_sha256"],
                   "organization_receipt_sha256": organization_receipt["receipt_sha256"]})
    try:  # P8: the existing verifier, bound to the exact repository receipt and transition id.
        basis = consumer.organization_readback(custody, organization_receipt["receipt_sha256"],
                                               repository_receipt_sha256=repository_receipt["receipt_sha256"],
                                               transition_id=transition_id)
        result["organization_readback"] = "VERIFIED"
        result["organization_readback_custody_basis"] = basis
        predicates.append(_result("P8", "PASS", detail="organization receipt read back"))
    except consumer.OrganizationReadbackRefused as exc:
        result["organization_readback"] = "REFUSED:" + exc.refusal["failed_predicate"]
        predicates.append(_result("P8", "FAIL", READBACK_NOT_VERIFIED, exc.refusal["failed_predicate"]))
        if cls == AUTHORIZED:
            result.update({"disposition": "FAIL_CLOSED", "failure_code": READBACK_NOT_VERIFIED,
                           "failed_predicate": PREDICATE_NAME["P8"],
                           "required_evidence_or_repair": REPAIR[READBACK_NOT_VERIFIED],
                           "retry_entrypoint": RETRY_ENTRYPOINT, "owning_existing_goal": evidence["owning_existing_goal"],
                           "next_attempt": "after a fresh-fetch readback verifies the retained receipt"})
        return result
    result["promotion_may_proceed"] = cls == AUTHORIZED
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--repo-ledger-root", type=Path, default=None)
    parser.add_argument("--org-ledger-root", type=Path, default=None)
    parser.add_argument("--hb-epoch", type=str, default=None, help="carrier-supplied heartbeat epoch; never sampled")
    args = parser.parse_args()
    request = _load("sppa_cli_kernel", ROOT / "org-kernel/kernel.py").cli_input_json(
        args.request, "--request", retry_entrypoint="scripts/authorize_site_production_promotion.py")
    result = authorize(request, source=args.source_root.resolve(), repo_ledger_root=args.repo_ledger_root,
                       org_ledger_root=args.org_ledger_root, hb_epoch=args.hb_epoch)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "ALLOW" and result.get("transition_class") in (AUTHORIZED, None) else 1


if __name__ == "__main__":
    raise SystemExit(_load("sppa_cli_kernel", ROOT / "org-kernel/kernel.py").run_writer_cli(
        main, retry_entrypoint="scripts/authorize_site_production_promotion.py"))
