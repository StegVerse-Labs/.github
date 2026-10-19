"""SPPA: Site production-promotion authorization transition (Lane D, (B), lane file §18.3)."""
from __future__ import annotations

import copy
import importlib.util
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
)
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
SHA = "a" * 40
CARRIER_HB_EPOCH = 4096
CLAIM_TASK = "TASK-SITE-PRODUCTION-PROMOTION-TEST"
SCOPE = [{"dependency_surface": "site:production-deploy", "repository": {"full_name": "StegVerse-Labs/Site"}}]
WRANGLER = "6c85bee35be487ea18cd4b07b83a76dfa2e4829f1fecabd0b96c023ee681e200"


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class Ledger:
    """A copied source and supplied POSIX ledger roots, rooted by an allocator grant (never the real ledger)."""

    def __init__(self, base: Path, *, fence: int = 8):
        self.source = base / "source"
        for rel in SOURCE_FILES:
            (self.source / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.source / rel)
        self.repo, self.org = base / "repo-ledger", base / "org-ledger"
        (self.org / "receipts").mkdir(parents=True)
        self.consumer = load("sppa_test_consumer", "scripts/consume_org_claim_allocator_request.py")
        custody = self.consumer.ledger_custody(self.source, base / "seed-repo-ledger", self.org)
        evidence = {"disposition": "ALLOW", "task_id": CLAIM_TASK, "fencing_token": fence,
                    "claim_scope_sha256": sppa.stable_hash(SCOPE), "request_sha256": "0" * 64,
                    "failed_predicate": None, "organization_head_sha256": None,
                    "custody_authentication": self.consumer.CUSTODY_AUTHENTICATION, "consequence_committed": True}
        receipts = self.consumer.record_transition(
            custody, self.consumer.GRANTED, f"ORGANIZATION-WORKER-CLAIM-GRANTED-{CLAIM_TASK}-G{fence}",
            "sha256:" + "0" * 64, evidence, organization=True,
            identity=("task_id", "fencing_token", "claim_scope_sha256", "organization_head_sha256"))
        self.grant_sha = receipts["organization_receipt"]["receipt_sha256"]
        self.fence = fence

    def run(self, request: dict, **kwargs) -> dict:
        return sppa.authorize(request, source=self.source, repo_ledger_root=self.repo,
                              org_ledger_root=self.org, **kwargs)

    def org_receipt(self, digest: str) -> dict:
        custody = self.consumer.ledger_custody(self.source, self.repo, self.org)
        rows = self.consumer.verify_organization_chain(custody)["receipts"]
        return next(row for row in rows if row["receipt_sha256"] == digest)


def promote_request(ledger: Ledger) -> dict:
    manifest = {
        "schema": sppa.MANIFEST_SCHEMA, "repository": "StegVerse-Labs/Site", "sha": SHA,
        "promotion_ref": "refs/heads/main", "environment": "production", "route": "stegverse.org/*",
        "service": "site", "worker_main": "src/worker.js", "assets_directory": ".", "d1_bindings": ["HIL_REGISTRY"],
        "wrangler_config_sha256": WRANGLER, "dependency_surface": "site:production-deploy",
        "claim_task_id": CLAIM_TASK, "claim_scope": SCOPE, "provider_build_id": "build-ok",
        "owning_existing_goal": sppa.OWNING_EXISTING_GOAL,
    }
    return {
        "schema": sppa.REQUEST_SCHEMA, "mode": sppa.PROMOTE, "repository": "StegVerse-Labs/Site", "sha": SHA,
        "promotion_ref": "refs/heads/main",
        "source_reachability": {"base_ref": "refs/heads/main", "base_sha": SHA, "head_sha": SHA,
                                "compare_status": "identical", "ahead_by": 0, "behind_by": 0},
        "manifest": manifest, "manifest_sha256": sppa.stable_hash(manifest), "wrangler_config_sha256": WRANGLER,
        "claim": {"organization_receipt_sha256": ledger.grant_sha, "fencing_token": ledger.fence,
                  "claim_authority": sppa.CLAIM_AUTHORITY},
        "intr_admission": {"admission_receipt_sha256": "b" * 64, "admitted_sha": SHA,
                           "transition": "SITE_PRODUCTION_PROMOTION"},
        "credential": {"authority": "TV/TVC", "github_token_runtime_authority": "NONE", "reference": "tvc:site-deploy"},
        "provider_build": {"provider": "cloudflare-workers-builds", "service": "site", "build_id": "build-ok",
                           "environment": "production", "commit_sha": SHA},
        "checks": [{"id": 1, "name": "validate", "head_sha": SHA, "conclusion": "success"}],
        "owning_existing_goal": sppa.OWNING_EXISTING_GOAL,
    }


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
        # Six successful checks on the exact sha are evidence only.
        p4 = result["predicates"][3]
        self.assertEqual((p4["state"], p4["all_success"], p4["grants_authority"]), ("EVIDENCE_ONLY", True, False))

    def test_site_1607_retro_receipt_is_appended_and_reads_back(self):
        ledger = Ledger(self.base)
        # Without a supplied epoch the refusal is returned and nothing is written.
        unstamped = ledger.run(fixture())
        self.assertEqual(unstamped["failure_code"], "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF")
        self.assertFalse(unstamped["receipt_appended"])
        result = ledger.run(fixture(), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["failure_code"], "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF")
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
        # A retry of the same classification returns the same receipt.
        again = ledger.run(fixture(), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(again["organization_receipt_sha256"], result["organization_receipt_sha256"])

    # PROMOTE ------------------------------------------------------------------
    def test_all_predicates_with_carrier_epoch_authorize_and_read_back(self):
        ledger = Ledger(self.base)
        result = ledger.run(promote_request(ledger), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["transition_class"], sppa.AUTHORIZED, result)
        self.assertEqual(result["disposition"], "ALLOW")
        self.assertEqual(result["organization_readback"], "VERIFIED")
        self.assertTrue(result["promotion_may_proceed"])
        self.assertEqual([p["state"] for p in result["predicates"]],
                         ["PASS", "PASS", "PASS", "EVIDENCE_ONLY", "PASS", "PASS", "PASS", "PASS"])
        row = ledger.org_receipt(result["organization_receipt_sha256"])
        self.assertEqual(row["boundary_evidence"]["operation"], sppa.AUTHORIZED)
        self.assertEqual(row["boundary_evidence"]["fencing_token"], 8)
        self.assertEqual(row["hb_reference"]["epoch"], CARRIER_HB_EPOCH)
        self.assertIs(row["hb_reference"]["derived_from_clock"], False)
        self.assertFalse(result["evidence"]["deployment_performed"])
        self.assertFalse(result["evidence"]["provider_settings_changed"])

    def test_authorization_without_carrier_epoch_fails_closed(self):
        ledger = Ledger(self.base)
        for epoch in (None, "+33", "31"):
            result = ledger.run(promote_request(ledger), hb_epoch=epoch)
            self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED, epoch)
            self.assertIn(result["failure_code"], ("HB_EPOCH_NOT_SUPPLIED", "HB_EPOCH_INVALID"))
            self.assertFalse(result["promotion_may_proceed"])

    def test_each_refusal_code_and_disposition(self):
        ledger = Ledger(self.base)
        cases = []

        def case(name, mutate, code, cls):
            request = promote_request(ledger)
            mutate(request)
            cases.append((name, request, code, cls))

        case("diverged", lambda r: r["source_reachability"].update(compare_status="diverged"),
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
        case("preview build", lambda r: r["provider_build"].update(environment="preview"),
             sppa.IDENTITY_MISMATCH, sppa.REFUSED)
        case("other commit", lambda r: r["provider_build"].update(commit_sha="e" * 40),
             sppa.IDENTITY_MISMATCH, sppa.REFUSED)
        for name, request, code, cls in cases:
            result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
            self.assertEqual((result["failure_code"], result["transition_class"]), (code, cls), name)
            for field in SIX:
                self.assertTrue(result[field], (name, field))
            self.assertFalse(result["promotion_may_proceed"], name)
            self.assertEqual(result["organization_readback"], "VERIFIED", name)

    def test_fence_at_or_below_the_issued_floor_is_behind(self):
        ledger = Ledger(self.base, fence=7)
        result = ledger.run(promote_request(ledger), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["failure_code"], sppa.FENCE_BEHIND)
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)

    def test_checks_are_evidence_only(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
        request["checks"] = [{"id": 2, "name": "validate", "head_sha": SHA, "conclusion": "failure"}]
        result = ledger.run(request, hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertEqual(result["transition_class"], sppa.AUTHORIZED)
        self.assertEqual(result["evidence"]["exact_sha_check_run_ids"], [2])
        self.assertFalse(result["predicates"][3]["grants_authority"])

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

        with mock.patch.object(sppa, "_load", patched):
            result = ledger.run(promote_request(ledger), hb_epoch=str(CARRIER_HB_EPOCH))
        self.assertTrue(result["receipt_appended"])
        self.assertEqual(result["failure_code"], sppa.READBACK_NOT_VERIFIED)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertFalse(result["promotion_may_proceed"])

    # Retro after an authorization --------------------------------------------
    def test_retro_finds_the_authorization_for_the_same_build_only(self):
        ledger = Ledger(self.base)
        request = promote_request(ledger)
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
        self.assertEqual((result["transition_class"], result["failure_code"]),
                         (sppa.FAIL_CLOSED, sppa.WITHOUT_RECEIPT))

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
        self.assertEqual(set(sppa.REFUSAL_CODES), {
            "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF", "PROMOTION_MANIFEST_MISSING", "PROMOTION_MANIFEST_SHA_MISMATCH",
            "PROMOTION_CLAIM_OR_FENCE_MISSING", "FENCE_GENERATION_BEHIND_ISSUED_FENCES",
            "PROMOTION_INTR_ADMISSION_MISSING", "PROMOTION_CREDENTIAL_AUTHORITY_NOT_TVC",
            "PROVIDER_DEPLOY_IDENTITY_MISMATCH", "PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT",
            "PROMOTION_READBACK_NOT_VERIFIED"})

    def test_manifest_schema_matches_the_transition(self):
        schema = json.loads((ROOT / "schemas/site-production-promotion-manifest.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema"]["const"], sppa.MANIFEST_SCHEMA)
        self.assertEqual(set(schema["required"]), set(sppa.MANIFEST_REQUIRED))
        manifest = promote_request(Ledger(self.base))["manifest"]
        try:
            import jsonschema
        except ImportError:
            self.assertTrue(set(sppa.MANIFEST_REQUIRED) <= set(manifest))
            return
        jsonschema.validate(manifest, schema)


if __name__ == "__main__":
    unittest.main()
