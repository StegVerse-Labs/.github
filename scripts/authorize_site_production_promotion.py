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
REFUSAL_CODES = (SOURCE_NOT_ON_REF, MANIFEST_MISSING, MANIFEST_SHA_MISMATCH, CLAIM_MISSING, FENCE_BEHIND,
                 INTR_MISSING, CREDENTIAL_NOT_TVC, IDENTITY_MISMATCH, WITHOUT_RECEIPT, READBACK_NOT_VERIFIED)
# Evidence that is present and contradicts the promotion is a DENY in PROMOTE
# mode; absent or unverifiable evidence is FAIL_CLOSED. A deploy that already
# happened (RETRO_CLASSIFY) is always FAIL_CLOSED: nothing can be refused after the fact.
DENY_CODES = frozenset({SOURCE_NOT_ON_REF, MANIFEST_SHA_MISMATCH, CREDENTIAL_NOT_TVC, IDENTITY_MISMATCH})

PREDICATES = (
    ("P1", "PROMOTION_SOURCE_ON_PROMOTION_REF"),
    ("P2", "PROMOTION_MANIFEST_BINDS_SHA"),
    ("P3", "PROMOTION_CLAIM_AND_FENCE_ISSUED"),
    ("P4", "EXACT_SHA_CHECKS_SUCCESS"),
    ("P5", "INTR_ADMISSION_PRESENT"),
    ("P6", "CREDENTIAL_AUTHORITY_TVC"),
    ("P7", "PROVIDER_BUILD_MATCHES_MANIFEST"),
    ("P8", "FRESH_FETCH_READBACK_VERIFIED"),
)
PREDICATE_NAME = dict(PREDICATES)
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


def p1_source_on_ref(request: Mapping[str, Any]) -> dict[str, Any]:
    sha, ref = request.get("sha"), request.get("promotion_ref")
    observed = request.get("source_reachability")
    if not isinstance(observed, Mapping) or observed.get("head_sha") != sha or observed.get("base_ref") != ref:
        return _result("P1", "FAIL", SOURCE_NOT_ON_REF, "no reachability observation for this sha on the promotion ref")
    status = observed.get("compare_status")
    if status not in REACHABLE_COMPARE_STATUSES:
        return _result("P1", "FAIL", SOURCE_NOT_ON_REF,
                       f"{sha} is not reachable from {ref} at {observed.get('base_sha')} (compare status {status}, "
                       f"ahead_by {observed.get('ahead_by')}, behind_by {observed.get('behind_by')})")
    return _result("P1", "PASS", detail=f"{sha} reachable from {ref} ({status})")


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
    return _result("P2", "PASS", detail="manifest " + declared + " binds the sha")


def p3_claim_and_fence(request: Mapping[str, Any], grants: list[dict[str, Any]] | None,
                       floor_fence: int | None) -> dict[str, Any]:
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
    return _result("P3", "PASS", detail=f"allocator grant {digest} fence {fence} > floor {floor_fence}",
                   fencing_token=fence)


def p4_checks(request: Mapping[str, Any]) -> dict[str, Any]:
    """Evidence only (§18.3): recorded, never authorizing; CI grants no runtime authority."""
    sha = request.get("sha")
    checks = request.get("checks") or []
    on_sha = [c for c in checks if c.get("head_sha") == sha]
    success = bool(on_sha) and all(c.get("conclusion") == "success" for c in on_sha)
    return _result("P4", "EVIDENCE_ONLY", detail=f"{len(on_sha)} check runs on the exact sha, all success: {success}",
                   exact_sha_check_run_ids=sorted(c.get("id") for c in on_sha), all_success=success,
                   grants_authority=False)


def p5_intr(request: Mapping[str, Any]) -> dict[str, Any]:
    admission = request.get("intr_admission")
    if not isinstance(admission, Mapping) or admission.get("admitted_sha") != request.get("sha") \
            or admission.get("transition") != "SITE_PRODUCTION_PROMOTION" \
            or not SHA256.match(str(admission.get("admission_receipt_sha256"))):
        return _result("P5", "FAIL", INTR_MISSING, "no InTr admission reference for this sha")
    return _result("P5", "PASS", detail="InTr admission " + admission["admission_receipt_sha256"],
                   authenticity=UNKNOWN)


def p6_credential(request: Mapping[str, Any]) -> dict[str, Any]:
    credential = request.get("credential")
    if not isinstance(credential, Mapping):
        return _result("P6", "FAIL", CREDENTIAL_NOT_TVC, "no credential reference")
    if credential.get("authority") != CREDENTIAL_AUTHORITY or credential.get("github_token_runtime_authority") != "NONE":
        return _result("P6", "FAIL", CREDENTIAL_NOT_TVC, "credential authority is not TV/TVC with GitHub token authority NONE")
    return _result("P6", "PASS", detail="TV/TVC reference " + str(credential.get("reference")))


def p7_provider_build(request: Mapping[str, Any]) -> dict[str, Any]:
    build, manifest = request.get("provider_build"), request.get("manifest")
    if not isinstance(build, Mapping) or not build.get("build_id"):
        return _result("P7", "FAIL", IDENTITY_MISMATCH, "no provider build identity")
    if not isinstance(manifest, Mapping):
        return _result("P7", "FAIL", IDENTITY_MISMATCH, "no manifest to match the provider build against")
    for key, expected in (("service", manifest.get("service")), ("environment", manifest.get("environment")),
                          ("commit_sha", request.get("sha"))):
        if build.get(key) != expected:
            return _result("P7", "FAIL", IDENTITY_MISMATCH, f"provider build {key} {build.get(key)!r} != {expected!r}")
    if manifest.get("provider_build_id") not in (None, build.get("build_id")):
        return _result("P7", "FAIL", IDENTITY_MISMATCH, "provider build id differs from the manifest")
    return _result("P7", "PASS", detail="provider build " + str(build.get("build_id")))


def evaluate(request: Mapping[str, Any], *, grants: list[dict[str, Any]] | None = None,
             floor_fence: int | None = None) -> list[dict[str, Any]]:
    """P1-P7 over the supplied evidence; P8 is decided by the readback after an append. No clock, no network."""
    return [p1_source_on_ref(request), p2_manifest_binds_sha(request),
            p3_claim_and_fence(request, grants, floor_fence), p4_checks(request), p5_intr(request),
            p6_credential(request), p7_provider_build(request)]


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


def decide(request: Mapping[str, Any], predicates: list[dict[str, Any]], *,
           prior_authorization: Mapping[str, Any] | None) -> dict[str, Any]:
    failed = [p for p in predicates if p["state"] == "FAIL"]
    mode = request["mode"]
    if mode == RETRO:
        if failed:
            first = failed[0]
            return {"transition_class": FAIL_CLOSED, "failure_code": first["failure_code"],
                    "failed_predicate": first["name"], "classification": WITHOUT_RECEIPT}
        if prior_authorization is None:
            return {"transition_class": FAIL_CLOSED, "failure_code": WITHOUT_RECEIPT,
                    "failed_predicate": "PRODUCTION_PROMOTION_AUTHORIZED_BY_MANIFEST_AND_SOVEREIGN_RECEIPT",
                    "classification": WITHOUT_RECEIPT}
        return {"transition_class": None, "classification": "AUTHORIZED_RECEIPT_PRESENT"}
    if failed:
        first = failed[0]
        cls = REFUSED if first["failure_code"] in DENY_CODES else FAIL_CLOSED
        return {"transition_class": cls, "failure_code": first["failure_code"], "failed_predicate": first["name"]}
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
        custody = consumer.ledger_custody(source, repo_ledger_root, org_ledger_root)
        try:
            chain = consumer.verify_organization_chain(custody)
            chain_rows = list(chain["receipts"])
            grants = consumer.chain_grants(chain)
            floor_fence = consumer.provenance_floor(source)["fence"]
        except consumer.ClaimFailClosed as exc:
            chain_refusal = exc.predicate + ": " + exc.detail
    predicates = evaluate(request, grants=grants, floor_fence=floor_fence)
    if chain_refusal is not None:
        predicates[2] = _result("P3", "FAIL", CLAIM_MISSING, "organization chain unverified: " + chain_refusal)
    decision = decide(request, predicates, prior_authorization=prior_authorization_for(chain_rows, request))
    manifest = request.get("manifest") if isinstance(request.get("manifest"), Mapping) else None
    build = request.get("provider_build") or {}
    failed = [p for p in predicates if p["state"] == "FAIL"]
    detail = "; ".join(f"{p['predicate']} {p['failure_code']}: {p['detail']}" for p in failed)
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
        "intr_admission_receipt_sha256": (request.get("intr_admission") or {}).get("admission_receipt_sha256"),
        "credential_authority": (request.get("credential") or {}).get("authority"),
        "exact_sha_check_run_ids": predicates[3]["exact_sha_check_run_ids"],
        "predicates": [{k: p[k] for k in ("predicate", "name", "state", "failure_code")} for p in predicates],
        "failed_predicates": [p["name"] for p in failed],
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
            prior_authorization_for(chain_rows, request)["receipt_sha256"]
        return result
    if custody is None or chain_refusal is not None:
        result["organization_readback"] = "NOT_PERFORMED"
        return result
    if hb_epoch is None or epoch_failure is not None:
        # A refusal without a supplied epoch writes nothing: a receipt is never
        # stamped from a clock here. The six fields are in the result.
        result.update({"receipt_appended": False, "organization_readback": "NOT_PERFORMED"})
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
        ledger=consumer.organization_target(custody), hb_epoch=epoch)
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
    request = json.loads(args.request.read_text(encoding="utf-8"))
    result = authorize(request, source=args.source_root.resolve(), repo_ledger_root=args.repo_ledger_root,
                       org_ledger_root=args.org_ledger_root, hb_epoch=args.hb_epoch)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "ALLOW" and result.get("transition_class") in (AUTHORIZED, None) else 1


if __name__ == "__main__":
    raise SystemExit(main())
