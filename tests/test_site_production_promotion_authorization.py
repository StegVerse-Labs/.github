"""SPPA: Site production-promotion authorization transition (Lane D, (B), lane file §18.3).

Includes the fail-open correction (StegVerse-org/.github#167 c6249647656 against #3244):
caller-supplied evidence may refuse, never authorize; UNKNOWN never yields PASS.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import itertools
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/site-production-promotion/site-1607-build-1790bb75-retro.request.json"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sppa = load("sppa_under_test", "scripts/authorize_site_production_promotion.py")
SOURCE_FILES = (
    ".stegverse/transition-ledger/emit.py",
    ".stegverse/transition-ledger/contract.json",
    ".stegverse/transition-ledger/org-contract.json",
    "org-kernel/kernel.py",
    "org-kernel/node_store.py",
    "resident-runtime/ledger_store.py",
    "resident-runtime/aggregate_repo_transition.py",
    "resident-runtime/organization_batch_custody.py",
    "scripts/consume_org_claim_allocator_request.py",
    "tasks/TASK-2026-0012.json",
    sppa.INTR_BOUNDARY_DECLARATION,
    sppa.TVC_ISSUER_DECLARATION,
)
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
SHA = "a" * 40
CARRIER_HB_EPOCH = 4096
CLAIM_TASK = "TASK-SITE-PRODUCTION-PROMOTION-TEST"
SCOPE = [{"dependency_surface": "site:production-deploy", "repository": {"full_name": "StegVerse-Labs/Site"}}]
WRANGLER = "6c85bee35be487ea18cd4b07b83a76dfa2e4829f1fecabd0b96c023ee681e200"
BOUNDARY = "StegVerse-Labs/.github"   # org-runtime/interlock-intr.json owner_repository
TVC = "StegVerse-Labs/TVC"            # control/formalism-tvc-repository-transport.json tvc_broker.repository
FIXTURE_BASIS = "TEST_FIXTURE_AUTHENTICATED_CUSTODY_BASIS"
REQUIRED = ["validate", "test-suite-ratchet"]


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@contextlib.contextmanager
def authenticated_custody():
    """Stand in for an authenticating custody basis, which no existing verifier reports today (Q74-01)."""
    with mock.patch.object(sppa, "AUTHENTICATING_CUSTODY_BASES", frozenset({FIXTURE_BASIS})), \
            mock.patch.object(sppa, "evidence_custody_basis", lambda custody, row: FIXTURE_BASIS):
        yield


class Ledger:
    """A copied source and supplied POSIX ledger roots, rooted by an allocator grant (never the real ledger)."""

    def __init__(self, base: Path, *, fence: int = 8):
        self.base = base
        self.source = base / "source"
        for rel in SOURCE_FILES:
            (self.source / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.source / rel)
        self.repo, self.org = base / "repo-ledger", base / "org-ledger"
        (self.org / "receipts").mkdir(parents=True)
        self.consumer = load("sppa_test_consumer", "scripts/consume_org_claim_allocator_request.py")
        self.custody = self.consumer.ledger_custody(self.source, base / "seed-repo-ledger", self.org)
        evidence = {"disposition": "ALLOW", "task_id": CLAIM_TASK, "fencing_token": fence,
                    "claim_scope_sha256": sppa.stable_hash(SCOPE), "request_sha256": "0" * 64,
                    "failed_predicate": None, "organization_head_sha256": None,
                    "custody_authentication": self.consumer.CUSTODY_AUTHENTICATION, "consequence_committed": True}
        receipts = self.consumer.record_transition(
            self.custody, self.consumer.GRANTED, f"ORGANIZATION-WORKER-CLAIM-GRANTED-{CLAIM_TASK}-G{fence}",
            "sha256:" + "0" * 64, evidence, organization=True,
            identity=("task_id", "fencing_token", "claim_scope_sha256", "organization_head_sha256"))
        self.grant_sha = receipts["organization_receipt"]["receipt_sha256"]
        self.fence = fence
        self._seq = 0

    def observe(self, repository: str, operation: str, evidence: dict) -> str:
        """Append an organization receipt sourced from `repository` (its own repository receipt)."""
        org = self.custody["organization_ledger"]
        self._seq += 1
        body = {"schema": "stegverse.repo-transition-receipt/v1", "repository": repository,
                "transition_id": f"{operation}-{self._seq}", "transition_class": operation,
                "predecessor_state_sha256": "sha256:" + "1" * 64,
                "successor_state_sha256": org.sha({"op": operation, "n": self._seq, "e": evidence}),
                "evidence": evidence, "authority_effect": "NONE", "observed_at": "fixture",
                "previous_receipt_sha256": None}
        receipt = dict(body, receipt_sha256=org.sha(body))
        row = org.aggregate_transition(
            receipt, org_transition_class="REPO_STATE_PROPAGATION",
            predecessor_org_state_sha256=receipt["predecessor_state_sha256"],
            successor_org_state_sha256=receipt["successor_state_sha256"],
            boundary_evidence={"operation": operation, **evidence}, authority_effect="NONE",
            ledger=self.consumer.organization_target(self.custody))
        return row["receipt_sha256"]

    def run(self, request: dict, **kwargs) -> dict:
        return sppa.authorize(request, source=self.source, repo_ledger_root=self.repo,
                              org_ledger_root=self.org, **kwargs)

    def chain_rows(self) -> list:
        custody = self.consumer.ledger_custody(self.source, self.repo, self.org)
        return self.consumer.verify_organization_chain(custody)["receipts"]

    def org_receipt(self, digest: str) -> dict:
        return next(row for row in self.chain_rows() if row["receipt_sha256"] == digest)


def manifest_for() -> dict:
    return {
        "schema": sppa.MANIFEST_SCHEMA, "repository": "StegVerse-Labs/Site", "sha": SHA,
        "promotion_ref": "refs/heads/main", "environment": "production", "route": "stegverse.org/*",
        "service": "site", "worker_main": "src/worker.js", "assets_directory": ".", "d1_bindings": ["HIL_REGISTRY"],
        "wrangler_config_sha256": WRANGLER, "dependency_surface": "site:production-deploy",
        "claim_task_id": CLAIM_TASK, "claim_scope": SCOPE, "provider_build_id": "build-ok",
        "owning_existing_goal": sppa.OWNING_EXISTING_GOAL,
    }


def caller_only_request(ledger: Ledger | None = None) -> dict:
    """Everything a caller can assert by itself, with no organization evidence receipts."""
    manifest = manifest_for()
    return {
        "schema": sppa.REQUEST_SCHEMA, "mode": sppa.PROMOTE, "repository": "StegVerse-Labs/Site", "sha": SHA,
        "promotion_ref": "refs/heads/main",
        "source_reachability": {"base_ref": "refs/heads/main", "base_sha": SHA, "head_sha": SHA,
                                "compare_status": "identical", "ahead_by": 0, "behind_by": 0},
        "manifest": manifest, "manifest_sha256": sppa.stable_hash(manifest), "wrangler_config_sha256": WRANGLER,
        "claim": {"organization_receipt_sha256": ledger.grant_sha if ledger else "sha256:" + "d" * 64,
                  "fencing_token": ledger.fence if ledger else 8, "claim_authority": sppa.CLAIM_AUTHORITY},
        "intr_admission": {"admitted_sha": SHA, "transition": "SITE_PRODUCTION_PROMOTION"},
        "credential": {"authority": "TV/TVC", "github_token_runtime_authority": "NONE", "reference": "tvc:site-deploy"},
        "provider_build": {"provider": "cloudflare-workers-builds", "service": "site", "build_id": "build-ok",
                           "environment": "production", "commit_sha": SHA},
        "checks": [{"id": 1, "name": "validate", "head_sha": SHA, "conclusion": "success"},
                   {"id": 2, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": "success"}],
        "owning_existing_goal": sppa.OWNING_EXISTING_GOAL,
    }


def observations(ledger: Ledger, *, issuer: str = TVC, check_runs: list | None = None,
                 required: list | None = None) -> dict:
    manifest_sha = sppa.stable_hash(manifest_for())
    runs = check_runs if check_runs is not None else [
        {"id": 11, "name": "validate", "head_sha": SHA, "conclusion": "success"},
        {"id": 12, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": "success"},
        {"id": 13, "name": "informational-lint", "head_sha": SHA, "conclusion": "failure"}]
    return {
        "source": ledger.observe(BOUNDARY, sppa.OP_SOURCE_REACHABILITY, {
            "repository": "StegVerse-Labs/Site", "head_sha": SHA, "base_ref": "refs/heads/main", "base_sha": SHA,
            "compare_status": "identical"}),
        "checks": ledger.observe(BOUNDARY, sppa.OP_EXACT_HEAD_CHECKS, {
            "repository": "StegVerse-Labs/Site", "head_sha": SHA,
            "required_checks": REQUIRED if required is None else required, "check_runs": runs}),
        "intr": ledger.observe(BOUNDARY, sppa.OP_INTR_ADMITTED, {
            "admitted_sha": SHA, "transition": "SITE_PRODUCTION_PROMOTION", "manifest_sha256": manifest_sha}),
        "tvc": ledger.observe(issuer, sppa.OP_TVC_ISSUED, {
            "credential_reference": "tvc:site-deploy", "dependency_surface": "site:production-deploy",
            "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE"}),
        "build": ledger.observe(BOUNDARY, sppa.OP_PROVIDER_BUILD, {
            "repository": "StegVerse-Labs/Site", "build_id": "build-ok", "service": "site",
            "environment": "production", "commit_sha": SHA, "provider": "cloudflare-workers-builds"}),
    }


def attach(request: dict, obs: dict) -> dict:
    request["source_observation"] = {"organization_receipt_sha256": obs["source"]}
    request["checks_observation"] = {"organization_receipt_sha256": obs["checks"]}
    request["intr_admission"]["organization_receipt_sha256"] = obs["intr"]
    request["credential"]["issuance_receipt_sha256"] = obs["tvc"]
    request["provider_build"]["observation_receipt_sha256"] = obs["build"]
    return request


def promote_request(ledger: Ledger, **kwargs) -> dict:
    """Fully evidenced: every authorizing predicate names an organization receipt on the chain."""
    return attach(caller_only_request(ledger), observations(ledger, **kwargs))


def reseal(request: dict) -> dict:
    request["manifest_sha256"] = sppa.stable_hash(request["manifest"])
    return request


class SiteProductionPromotionAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.base = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    # Retro-classification of Site#1607 build 1790bb75 @ 924d92ed ---------------
    def test_site_1607_retro_classification_without_ledger(self):
        result = sppa.authorize(fixture())
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF")
        self.assertEqual(result["failed_predicate"], "PROMOTION_SOURCE_ON_PROMOTION_REF")
        self.assertEqual(result["classification"], "PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT")
        self.assertEqual([(p["predicate"], p["failure_code"]) for p in result["predicates"] if p["state"] == "FAIL"],
                         [("P1", "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF"), ("P2", "PROMOTION_MANIFEST_MISSING"),
                          ("P3", "PROMOTION_CLAIM_OR_FENCE_MISSING"), ("P5", "PROMOTION_INTR_ADMISSION_MISSING"),
                          ("P6", "PROMOTION_CREDENTIAL_AUTHORITY_NOT_TVC"), ("P7", "PROVIDER_DEPLOY_IDENTITY_MISMATCH")])
        for field in SIX:
            self.assertTrue(result[field], field)
        self.assertFalse(result["receipt_appended"])
        self.assertFalse(result["promotion_may_proceed"])
        self.assertEqual(result["evidence"]["provider_route_serving"], sppa.UNKNOWN)
        self.assertEqual(result["evidence"]["provider_build_id"], "1790bb75-3340-4bd3-929d-f188b9f23405")
        # Six caller-observed successful checks are not an authenticated observation: UNKNOWN, never PASS.
        p4 = result["predicates"][3]
        self.assertEqual((p4["state"], p4["failure_code"]), ("UNKNOWN", sppa.CHECKS_UNAUTHENTICATED))
        self.assertEqual(len(p4["exact_sha_check_run_ids"]), 6)
        self.assertFalse(p4["grants_authority"])

    def test_site_1607_retro_receipt_is_appended_and_reads_back(self):
        ledger = Ledger(self.base)
        result = ledger.run(fixture())
        self.assertEqual(result["failure_code"], "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF")
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)
        self.assertTrue(result["receipt_appended"])
        self.assertEqual(result["organization_readback"], "VERIFIED")
        row = ledger.org_receipt(result["organization_receipt_sha256"])
        self.assertEqual(row["schema"], "stegverse.organization-transition-receipt/v1")
        evidence = row["boundary_evidence"]
        self.assertEqual(evidence["operation"], sppa.FAIL_CLOSED)
        self.assertEqual(evidence["sha"], "924d92edf0f379af54bdf7702895e2966bc7fed1")
        self.assertEqual(evidence["provider_build_id"], "1790bb75-3340-4bd3-929d-f188b9f23405")
        self.assertEqual(evidence["classification"], "PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT")
        for field in SIX:
            self.assertTrue(evidence.get(field), field)
        self.assertEqual(row["authority_effect"], "NONE")
        again = ledger.run(fixture())
        self.assertEqual(again["organization_receipt_sha256"], result["organization_receipt_sha256"])

    def test_site_1607_retro_stays_fail_closed_with_authenticated_custody(self):
        ledger = Ledger(self.base)
        with authenticated_custody():
            result = ledger.run(fixture())
        self.assertEqual((result["transition_class"], result["failure_code"]),
                         (sppa.FAIL_CLOSED, "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF"))

    # PROMOTE: the one authorizing path ------------------------------------------
    def test_fully_authenticated_evidence_with_carrier_epoch_authorizes_and_reads_back(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        with authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["transition_class"], sppa.AUTHORIZED, result)
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["organization_readback"], "VERIFIED")
        self.assertTrue(result["promotion_may_proceed"])
        self.assertEqual([p["state"] for p in result["predicates"]], ["PASS"] * 8)
        self.assertEqual([p.get("authenticity") for p in result["predicates"][:7]],
                         ["AUTHENTICATED", "DECLARATION_BOUND"] + ["AUTHENTICATED"] * 5)
        p4 = result["predicates"][3]
        self.assertEqual(p4["required_checks"], sorted(REQUIRED))
        self.assertEqual(p4["informational_checks"], ["informational-lint"])  # a failing extra check is informational
        row = ledger.org_receipt(result["organization_receipt_sha256"])
        self.assertEqual(row["boundary_evidence"]["operation"], sppa.AUTHORIZED)
        self.assertEqual(row["boundary_evidence"]["fencing_token"], 8)
        self.assertEqual(row["hb_reference"]["epoch"], CARRIER_HB_EPOCH)
        self.assertIs(row["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(set(result["evidence"]["evidence_receipts"]), {"P1", "P3", "P4", "P5", "P6", "P7"})
        self.assertFalse(result["evidence"]["deployment_performed"])
        self.assertFalse(result["evidence"]["provider_settings_changed"])

    def test_fully_evidenced_request_fails_closed_under_the_real_custody_verifier(self):
        """No custody basis the existing verifier reports authenticates: AUTHORIZED is unreachable on main."""
        self.assertEqual(sppa.AUTHENTICATING_CUSTODY_BASES, frozenset())
        ledger = Ledger(self.base)
        verifier = ledger.custody["organization_receipt_custody"]
        for basis in (verifier.READBACK_CUSTODY_BASIS_ABSENT, verifier.READBACK_CUSTODY_BASIS_HANDOVER,
                      ledger.custody["organization_ledger"].CUSTODY_AUTHORITY_BASIS_GENERATION_0):
            self.assertNotIn(basis, sppa.AUTHENTICATING_CUSTODY_BASES)
        result = ledger.run(promote_request(ledger), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)
        self.assertNotEqual(result["disposition"], "ALLOW")
        self.assertFalse(result["promotion_may_proceed"])
        self.assertEqual({p["state"] for p in result["predicates"][:7] if p["predicate"] != "P2"}, {"UNKNOWN"})
        self.assertIn("custody basis", result["evidence"]["detail"])

    def test_authorization_without_carrier_epoch_fails_closed(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        with authenticated_custody():
            for epoch in (None, "+33", "31"):
                result = ledger.run(copy.deepcopy(request), hb_epoch=epoch)
                self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED, epoch)
                self.assertIn(result["failure_code"], ("HB_EPOCH_NOT_SUPPLIED", "HB_EPOCH_INVALID"))
                self.assertFalse(result["promotion_may_proceed"])

    # UNKNOWN never yields PASS ----------------------------------------------------
    def test_global_invariant_unknown_or_unauthenticated_pass_is_never_authorized(self):
        request = caller_only_request()
        good = [sppa._result(pid, "PASS", authenticity=sppa.REQUIRED_AUTHENTICITY[pid]) for pid in sppa.REQUIRED_AUTHENTICITY]
        self.assertEqual(sppa.decide(request, good, prior_authorization=None)["transition_class"], sppa.AUTHORIZED)
        for index, pid in enumerate(sppa.REQUIRED_AUTHENTICITY):
            for variant in ({"state": "UNKNOWN"}, {"state": "EVIDENCE_ONLY"}, {"authenticity": sppa.UNKNOWN},
                            {"authenticity": None}, {"state": "PASS", "authenticity": "SUPPLIED"}):
                predicates = copy.deepcopy(good)
                predicates[index].update(variant)
                decision = sppa.decide(request, predicates, prior_authorization=None)
                self.assertEqual(decision["transition_class"], sppa.FAIL_CLOSED, (pid, variant))
            missing = [p for p in good if p["predicate"] != pid]
            self.assertEqual(sppa.decide(request, missing, prior_authorization=None)["failure_code"],
                             sppa.PREDICATE_SET_INCOMPLETE, pid)
            retro = dict(request, mode=sppa.RETRO)
            predicates = copy.deepcopy(good)
            predicates[index]["state"] = "UNKNOWN"
            self.assertEqual(sppa.decide(retro, predicates, prior_authorization={"receipt_sha256": "x"})
                             ["transition_class"], sppa.FAIL_CLOSED, pid)

    def test_each_predicate_unknown_fails_closed_never_pass(self):
        ledger = Ledger(self.base)
        cases = {
            "P1": (lambda r: r.pop("source_observation"), sppa.SOURCE_UNAUTHENTICATED),
            "P3": (None, sppa.EVIDENCE_CUSTODY_UNAUTHENTICATED),
            "P4": (lambda r: r.pop("checks_observation"), sppa.CHECKS_UNAUTHENTICATED),
            "P5": (lambda r: r["intr_admission"].pop("organization_receipt_sha256"), sppa.INTR_UNAUTHENTICATED),
            "P6": (lambda r: r["credential"].pop("issuance_receipt_sha256"), sppa.ISSUER_UNVERIFIED),
            "P7": (lambda r: r["provider_build"].pop("observation_receipt_sha256"), sppa.BUILD_UNAUTHENTICATED),
        }
        base = promote_request(ledger)
        rows = ledger.chain_rows()
        issuers = sppa.declared_issuers(ledger.source)
        grants = ledger.consumer.chain_grants({"receipts": rows})
        for pid, (mutate, code) in cases.items():
            request = copy.deepcopy(base)
            if mutate is None:
                # P3 alone unauthenticated: every other receipt authenticates.
                basis = lambda row: None if row["receipt_sha256"] == ledger.grant_sha else FIXTURE_BASIS
            else:
                mutate(request)
                basis = lambda row: FIXTURE_BASIS
            with mock.patch.object(sppa, "AUTHENTICATING_CUSTODY_BASES", frozenset({FIXTURE_BASIS})):
                predicates = sppa.evaluate(request, grants=grants, floor_fence=7, chain_rows=rows, issuers=issuers,
                                           basis_of=basis)
                decision = sppa.decide(request, predicates, prior_authorization=None)
            target = next(p for p in predicates if p["predicate"] == pid)
            self.assertEqual((target["state"], target["failure_code"]), ("UNKNOWN", code), pid)
            self.assertEqual([p["state"] for p in predicates if p["predicate"] != pid], ["PASS"] * 6, pid)
            self.assertEqual((decision["transition_class"], decision["failure_code"]), (sppa.FAIL_CLOSED, code), pid)

    def test_no_combination_of_caller_only_evidence_reaches_authorized(self):
        ledger = Ledger(self.base)
        rows = ledger.chain_rows()
        grants = ledger.consumer.chain_grants({"receipts": rows})
        issuers = sppa.declared_issuers(ledger.source)
        off_chain = "sha256:" + "e" * 64
        slots = {
            "source_observation": lambda r, v: r.update(source_observation=v and {"organization_receipt_sha256": v}),
            "checks_observation": lambda r, v: r.update(checks_observation=v and {"organization_receipt_sha256": v}),
            "intr": lambda r, v: r["intr_admission"].update(organization_receipt_sha256=v),
            "tvc": lambda r, v: r["credential"].update(issuance_receipt_sha256=v, issuer=TVC),
            "build": lambda r, v: r["provider_build"].update(observation_receipt_sha256=v),
            "grant": lambda r, v: r["claim"].update(organization_receipt_sha256=v or ledger.grant_sha),
        }
        count = 0
        with mock.patch.object(sppa, "AUTHENTICATING_CUSTODY_BASES", frozenset({FIXTURE_BASIS})):
            for values in itertools.product((None, off_chain), repeat=len(slots)):
                request = caller_only_request(ledger)
                for (name, apply), value in zip(slots.items(), values):
                    apply(request, value)
                for chain in (rows, None):
                    predicates = sppa.evaluate(request, grants=grants if chain else None, floor_fence=7,
                                               chain_rows=chain, issuers=issuers, basis_of=lambda row: FIXTURE_BASIS)
                    decision = sppa.decide(request, predicates, prior_authorization=None)
                    self.assertNotEqual(decision["transition_class"], sppa.AUTHORIZED, values)
                    count += 1
        self.assertEqual(count, 2 ** 6 * 2)
        # And through authorize(), with the caller-only request and the real ledger + epoch.
        with authenticated_custody():
            result = ledger.run(caller_only_request(ledger), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)
        self.assertFalse(result["promotion_may_proceed"])

    def test_sppa_own_receipt_is_not_a_provider_observation(self):
        """Self-referential: a prior SPPA receipt (built from caller input) cannot stand in for the provider."""
        ledger = Ledger(self.base)
        prior = ledger.run(fixture())["organization_receipt_sha256"]
        request = promote_request(ledger)
        request["provider_build"]["observation_receipt_sha256"] = prior
        with authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual((result["transition_class"], result["failure_code"]),
                         (sppa.FAIL_CLOSED, sppa.BUILD_UNAUTHENTICATED))

    # P6 issuer binding -----------------------------------------------------------
    def test_issuer_bound_negative_cases(self):
        ledger = Ledger(self.base)
        cases = [
            ("forged issuer (another org repo)", dict(issuer="StegVerse-Labs/Forged-Issuer"), None,
             sppa.ISSUER_NOT_TVC, sppa.REFUSED),
            ("self-signed by the Site", dict(issuer="StegVerse-Labs/Site"), None, sppa.ISSUER_NOT_TVC, sppa.REFUSED),
            ("self-signed at the org boundary", dict(issuer=BOUNDARY), None, sppa.ISSUER_NOT_TVC, sppa.REFUSED),
            ("declared forged issuer", {}, lambda r: r["credential"].update(issuer="StegVerse-Labs/Site"),
             sppa.ISSUER_NOT_TVC, sppa.REFUSED),
            ("missing issuance", {}, lambda r: r["credential"].pop("issuance_receipt_sha256"),
             sppa.ISSUER_UNVERIFIED, sppa.FAIL_CLOSED),
            ("issuance off chain", {}, lambda r: r["credential"].update(issuance_receipt_sha256="sha256:" + "f" * 64),
             sppa.ISSUER_UNVERIFIED, sppa.FAIL_CLOSED),
            ("issuance for another reference", {}, lambda r: r["credential"].update(reference="tvc:other"),
             sppa.ISSUER_UNVERIFIED, sppa.FAIL_CLOSED),
        ]
        with authenticated_custody():
            for name, kwargs, mutate, code, cls in cases:
                request = promote_request(ledger, **kwargs)
                if mutate:
                    mutate(request)
                result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
                self.assertEqual((result["failure_code"], result["transition_class"]), (code, cls), name)
                self.assertFalse(result["promotion_may_proceed"], name)
                for field in SIX:
                    self.assertTrue(result[field], (name, field))

    def test_unreadable_tvc_issuer_declaration_is_unverifiable(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        (ledger.source / sppa.TVC_ISSUER_DECLARATION).unlink()
        with authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual((result["failure_code"], result["transition_class"]), (sppa.ISSUER_UNVERIFIED, sppa.FAIL_CLOSED))
        self.assertEqual(sppa.declared_issuers(ROOT), {"boundary": BOUNDARY, "tvc": TVC})

    # P4 required-check policy ------------------------------------------------------
    def test_required_check_policy(self):
        ledger = Ledger(self.base)
        ok = {"id": 11, "name": "validate", "head_sha": SHA, "conclusion": "success"}
        cases = [
            ("required failed", [ok, {"id": 12, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": "failure"}],
             None, sppa.REQUIRED_CHECK_FAILED, sppa.REFUSED),
            ("required cancelled", [ok, {"id": 12, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": "cancelled"}],
             None, sppa.REQUIRED_CHECK_FAILED, sppa.REFUSED),
            ("one of duplicate runs failed", [ok, dict(ok, id=14, conclusion="failure"),
                                              {"id": 12, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": "success"}],
             None, sppa.REQUIRED_CHECK_FAILED, sppa.REFUSED),
            ("required skipped", [ok, {"id": 12, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": "skipped"}],
             None, sppa.REQUIRED_CHECK_NOT_PASSED, sppa.FAIL_CLOSED),
            ("required pending", [ok, {"id": 12, "name": "test-suite-ratchet", "head_sha": SHA, "conclusion": None}],
             None, sppa.REQUIRED_CHECK_NOT_PASSED, sppa.FAIL_CLOSED),
            ("required missing", [ok], None, sppa.REQUIRED_CHECK_NOT_PASSED, sppa.FAIL_CLOSED),
            ("required passed on another sha", [ok, {"id": 12, "name": "test-suite-ratchet", "head_sha": "b" * 40,
                                                     "conclusion": "success"}],
             None, sppa.REQUIRED_CHECK_NOT_PASSED, sppa.FAIL_CLOSED),
            ("no policy observed", [ok], [], sppa.REQUIRED_CHECK_POLICY_UNOBSERVED, sppa.FAIL_CLOSED),
        ]
        with authenticated_custody():
            for name, runs, required, code, cls in cases:
                request = promote_request(ledger, check_runs=runs, required=required)
                result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
                self.assertEqual((result["failure_code"], result["transition_class"]), (code, cls), name)
                self.assertFalse(result["promotion_may_proceed"], name)
            # Caller-supplied failing checks without an observation: still not authorizing, never PASS.
            request = promote_request(ledger)
            request.pop("checks_observation")
            request["checks"] = [{"id": 2, "name": "validate", "head_sha": SHA, "conclusion": "success"}]
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
            self.assertEqual((result["failure_code"], result["transition_class"]),
                             (sppa.CHECKS_UNAUTHENTICATED, sppa.FAIL_CLOSED))

    # Refusals and dispositions ---------------------------------------------------------
    def test_each_refusal_code_and_disposition(self):
        ledger = Ledger(self.base)
        cases = []

        def case(name, mutate, code, cls, **kwargs):
            request = promote_request(ledger, **kwargs)
            mutate(request)
            cases.append((name, request, code, cls))

        case("supplied diverged", lambda r: r["source_reachability"].update(compare_status="diverged"),
             sppa.SOURCE_NOT_ON_REF, sppa.REFUSED)
        case("no manifest", lambda r: r.update(manifest=None), sppa.MANIFEST_MISSING, sppa.FAIL_CLOSED)
        case("tampered manifest", lambda r: r["manifest"].update(route="other/*"),
             sppa.MANIFEST_SHA_MISMATCH, sppa.REFUSED)
        case("wrangler differs", lambda r: reseal(r) if r["manifest"].update(wrangler_config_sha256="c" * 64) is None else r,
             sppa.MANIFEST_SHA_MISMATCH, sppa.REFUSED)
        case("session claim", lambda r: r["claim"].update(claim_authority="CHAT_SESSION"),
             sppa.CLAIM_MISSING, sppa.FAIL_CLOSED)
        case("claim off chain", lambda r: r["claim"].update(organization_receipt_sha256="d" * 64),
             sppa.CLAIM_MISSING, sppa.FAIL_CLOSED)
        case("no claim", lambda r: r.update(claim=None), sppa.CLAIM_MISSING, sppa.FAIL_CLOSED)
        case("no intr", lambda r: r.update(intr_admission=None), sppa.INTR_MISSING, sppa.FAIL_CLOSED)
        case("github credential", lambda r: r["credential"].update(authority="GITHUB_TOKEN"),
             sppa.CREDENTIAL_NOT_TVC, sppa.REFUSED)
        case("supplied preview build", lambda r: r["provider_build"].update(environment="preview"),
             sppa.IDENTITY_MISMATCH, sppa.REFUSED)
        case("supplied other commit", lambda r: r["provider_build"].update(commit_sha="e" * 40),
             sppa.IDENTITY_MISMATCH, sppa.REFUSED)
        with authenticated_custody():
            for name, request, code, cls in cases:
                result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
                self.assertEqual((result["failure_code"], result["transition_class"]), (code, cls), name)
                for field in SIX:
                    self.assertTrue(result[field], (name, field))
                self.assertFalse(result["promotion_may_proceed"], name)
                self.assertEqual(result["organization_readback"], "VERIFIED", name)

    def test_observed_contradictions_refuse(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        request["source_observation"]["organization_receipt_sha256"] = ledger.observe(
            BOUNDARY, sppa.OP_SOURCE_REACHABILITY, {"repository": "StegVerse-Labs/Site", "head_sha": SHA,
                                                    "base_ref": "refs/heads/main", "compare_status": "diverged"})
        with authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual((result["failure_code"], result["transition_class"]), (sppa.SOURCE_NOT_ON_REF, sppa.REFUSED))
        request = promote_request(ledger)
        request["provider_build"]["observation_receipt_sha256"] = ledger.observe(
            BOUNDARY, sppa.OP_PROVIDER_BUILD, {"repository": "StegVerse-Labs/Site", "build_id": "build-ok",
                                               "service": "site", "environment": "preview", "commit_sha": SHA})
        with authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual((result["failure_code"], result["transition_class"]), (sppa.IDENTITY_MISMATCH, sppa.REFUSED))

    def test_observation_from_an_undeclared_repository_is_unknown(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        request["provider_build"]["observation_receipt_sha256"] = ledger.observe(
            "StegVerse-Labs/Site", sppa.OP_PROVIDER_BUILD, {"repository": "StegVerse-Labs/Site", "build_id": "build-ok",
                                                            "service": "site", "environment": "production",
                                                            "commit_sha": SHA})
        with authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual((result["failure_code"], result["transition_class"]),
                         (sppa.BUILD_UNAUTHENTICATED, sppa.FAIL_CLOSED))

    def test_fence_at_or_below_the_issued_floor_is_behind(self):
        ledger = Ledger(self.base, fence=7)
        with authenticated_custody():
            result = ledger.run(promote_request(ledger), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["failure_code"], sppa.FENCE_BEHIND)
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)

    def test_readback_refusal_withholds_promotion(self):
        ledger = Ledger(self.base)
        real_load = sppa._load

        def patched(name, path):
            module = real_load(name, path)
            if name == "sppa_org_claim_consumer":
                def refuse(*args, **kwargs):
                    raise module.OrganizationReadbackRefused({"disposition": "FAIL_CLOSED",
                                                              "failed_predicate": "ORGANIZATION_RECEIPT_READBACK_MISSING"})
                module.organization_readback = refuse
            return module

        request = promote_request(ledger)
        with mock.patch.object(sppa, "_load", patched), authenticated_custody():
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertTrue(result["receipt_appended"])
        self.assertEqual(result["failure_code"], sppa.READBACK_NOT_VERIFIED)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertFalse(result["promotion_may_proceed"])

    # Retro after an authorization --------------------------------------------
    def test_retro_finds_the_authorization_for_the_same_build_only(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        with authenticated_custody():
            self.assertEqual(ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))["transition_class"], sppa.AUTHORIZED)
            retro = copy.deepcopy(request)
            retro["mode"] = sppa.RETRO
            found = ledger.run(retro)
            self.assertEqual(found["classification"], "AUTHORIZED_RECEIPT_PRESENT")
            self.assertFalse(found["receipt_appended"])
            other = copy.deepcopy(retro)
            other["provider_build"]["build_id"] = "build-unauthorized"
            other["manifest"].pop("provider_build_id")
            reseal(other)
            result = ledger.run(other)
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)
        self.assertIn(result["failure_code"], (sppa.WITHOUT_RECEIPT, sppa.BUILD_UNAUTHENTICATED, sppa.INTR_MISSING))
        # Without authenticated custody the same retro is FAIL_CLOSED, never AUTHORIZED_RECEIPT_PRESENT.
        self.assertEqual(ledger.run(copy.deepcopy(retro))["transition_class"], sppa.FAIL_CLOSED)

    # Boundaries ----------------------------------------------------------------
    def test_invalid_requests_are_refused_before_anything_is_read(self):
        for mutate in (lambda r: r.update(schema="x"), lambda r: r.update(mode="DEPLOY"),
                       lambda r: r.update(repository="StegVerse-Labs/Other"), lambda r: r.update(sha="924d92ed"),
                       lambda r: r.update(promotion_ref="main")):
            request = fixture()
            mutate(request)
            with self.assertRaises(ValueError):
                sppa.authorize(request)

    def test_transition_touches_no_provider_clock_or_network(self):
        text = (ROOT / "scripts/authorize_site_production_promotion.py").read_text(encoding="utf-8")
        for forbidden in ("import subprocess", "urllib", "import requests", "http.client", "datetime.now",
                          "time.time", "time_ns", "wrangler deploy", "api.cloudflare.com", "os.environ"):
            self.assertNotIn(forbidden, text)
        self.assertTrue({"PROMOTION_SOURCE_NOT_ON_PROMOTION_REF", "PROMOTION_MANIFEST_MISSING",
                         "PROMOTION_MANIFEST_SHA_MISMATCH", "PROMOTION_CLAIM_OR_FENCE_MISSING",
                         "FENCE_GENERATION_BEHIND_ISSUED_FENCES", "PROMOTION_INTR_ADMISSION_MISSING",
                         "PROMOTION_CREDENTIAL_AUTHORITY_NOT_TVC", "PROVIDER_DEPLOY_IDENTITY_MISMATCH",
                         "PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT", "PROMOTION_READBACK_NOT_VERIFIED"}
                        <= set(sppa.REFUSAL_CODES))
        self.assertEqual(len(sppa.REFUSAL_CODES), len(set(sppa.REFUSAL_CODES)))
        for code in sppa.REFUSAL_CODES:
            self.assertIn(code, sppa.REPAIR, code)

    def test_manifest_schema_matches_the_transition(self):
        schema = json.loads((ROOT / "schemas/site-production-promotion-manifest.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema"]["const"], sppa.MANIFEST_SCHEMA)
        self.assertEqual(set(schema["required"]), set(sppa.MANIFEST_REQUIRED))
        manifest = manifest_for()
        try:
            import jsonschema
        except ImportError:
            self.assertTrue(set(sppa.MANIFEST_REQUIRED) <= set(manifest))
            return
        jsonschema.validate(manifest, schema)


class ForgedIssuerEvidenceRegressionTests(unittest.TestCase):
    """Caller-controlled evidence must not authorize a sovereign promotion.

    Carried from the interim stopgap pushed to this branch (dd317bd/8e08e46/88a2067), adapted to the
    correction: caller-only P1/P5/P6/P7 are never PASS (FAIL or UNKNOWN), and replay is deterministic.
    """

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self._td.name))

    def tearDown(self):
        self._td.cleanup()

    def test_forged_well_formed_inputs_never_authorize(self):
        request = caller_only_request(self.ledger)
        request["credential"]["issuer"] = TVC  # a well-formed but unproven issuer declaration
        results = sppa.evaluate(request, grants=[], floor_fence=0)
        for name in ("P1", "P5", "P6", "P7"):
            predicate = next(row for row in results if row["predicate"] == name)
            self.assertIn(predicate["state"], ("FAIL", "UNKNOWN"), name)
        decision = sppa.decide(request, results, prior_authorization=None)
        self.assertNotEqual(decision["transition_class"], sppa.AUTHORIZED)

    def test_replay_of_forged_evidence_never_authorizes(self):
        request = caller_only_request(self.ledger)
        first = sppa.evaluate(request, grants=[], floor_fence=0)
        second = sppa.evaluate(copy.deepcopy(request), grants=[], floor_fence=0)
        self.assertEqual(first, second)
        for predicates in (first, second):
            self.assertNotEqual(
                sppa.decide(request, predicates, prior_authorization=None)["transition_class"],
                sppa.AUTHORIZED)


if __name__ == "__main__":
    unittest.main()
