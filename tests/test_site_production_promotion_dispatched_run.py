"""Manifest-dispatched real-ledger SPPA run (Lane D, stacked on Labs#3244).

A committed request at the fixed path is materialized into the resident
runtime and visited by the resident dispatcher; the consumer evaluates it
through SPPA against the supplied ledger. Temporary ledgers only.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


consumer = load("sppa_dispatched_consumer", "scripts/consume_site_production_promotion_request.py")
dispatcher = load("sppa_dispatched_dispatcher", "scripts/dispatch_resident_execution_requests.py")
sppa_tests = load("sppa_dispatched_sppa_tests", "tests/test_site_production_promotion_authorization.py")
sppa = sppa_tests.sppa
REL = consumer.REQUEST_RELS[0]
RESIDENT = {"PATH": "/usr/bin:/bin"}
SIX = sppa_tests.SIX


def resident_request(promotion: dict, request_id: str = "site-production-promotion-001") -> dict:
    return {
        "schema": consumer.SCHEMA, "state": "REQUESTED", "task_id": consumer.TASK_ID, "mode": consumer.MODE,
        "entrypoint": consumer.ENTRYPOINT, "transition": consumer.TRANSITION, "request_id": request_id,
        "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY", "github_token_required": False,
        "network_source_fetch_allowed": False, "second_machine_required": False,
        "heartbeat_grants_execution_authority": False, "request_grants_promotion_authority": False,
        "provider_settings_change_allowed": False, "deployment_performed_by_consumer": False,
        "sppa_remains_promotion_authority_record": True,
        "promotion_request": promotion, "promotion_request_sha256": consumer.stable_hash(promotion),
    }


def materialized_ledger(base: Path):
    """The SPPA test ledger, with the transition materialized into its source as the resident copy would be."""
    ledger = sppa_tests.Ledger(base)
    target = ledger.source / consumer.TRANSITION
    target.write_bytes((ROOT / consumer.TRANSITION).read_bytes())
    return ledger


class DispatchedSppaRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.base = Path(self._td.name)
        self.runtime = self.base / "runtime"

    def tearDown(self) -> None:
        self._td.cleanup()

    def commit(self, request: dict) -> None:
        path = self.runtime / REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(request), encoding="utf-8")

    def run_consumer(self, ledger=None, **kwargs):
        kwargs.setdefault("env", RESIDENT)
        source = ledger.source if ledger else ROOT
        if ledger is not None:
            kwargs.setdefault("repo_ledger_root", ledger.repo)
            kwargs.setdefault("org_ledger_root", ledger.org)
        return consumer.consume(source, self.runtime, **kwargs)

    def test_no_committed_request_is_no_run(self):
        self.assertEqual(self.run_consumer()["state"], "NO_REQUEST")
        # The repository commits no SPPA request: nothing here triggers a real run.
        for rel in consumer.REQUEST_RELS:
            self.assertFalse((ROOT / rel).exists(), rel)

    def test_without_ledger_roots_fails_closed_before_evaluation(self):
        self.commit(resident_request(sppa_tests.fixture()))
        result = self.run_consumer()
        self.assertEqual((result["state"], result["failure_code"]), ("FAIL_CLOSED", consumer.LEDGER_REQUIRED))
        for field in SIX:
            self.assertTrue(result[field], field)
        self.assertFalse(result["transition_attempted"])

    def test_hosted_environment_is_refused(self):
        self.commit(resident_request(sppa_tests.fixture()))
        result = self.run_consumer(env={"PATH": "/bin", "GITHUB_ACTIONS": "true"})
        self.assertEqual(result["failure_code"], consumer.HOSTED_REFUSED)
        self.assertFalse(result["receipt_appended"])

    def test_invalid_requests_are_refused_and_append_nothing(self):
        ledger = materialized_ledger(self.base)
        good = resident_request(sppa_tests.fixture())
        mutations = [dict(mode="DEPLOY"), dict(authority_effect="PROMOTION_AUTHORITY"),
                     dict(promotion_request_sha256="0" * 64)]
        mutations += [{key: True} for key in consumer.REQUIRED_FALSE]
        mutations += [dict(sppa_remains_promotion_authority_record=False)]
        for mutation in mutations:
            request = {**copy.deepcopy(good), **mutation}
            self.commit(request)
            result = self.run_consumer(ledger)
            self.assertEqual(result["failure_code"], consumer.REQUEST_INVALID, mutation)
            self.assertFalse(result["receipt_appended"], mutation)
        self.assertFalse((ledger.repo / "receipts").exists() and any((ledger.repo / "receipts").iterdir()))

    def test_site_1607_retro_request_records_and_reads_back(self):
        ledger = materialized_ledger(self.base)
        self.commit(resident_request(sppa_tests.fixture()))
        # A refusal is recorded only at a supplied epoch; without one nothing is written.
        result = self.run_consumer(ledger, hb_epoch="4096")
        self.assertEqual(result["state"], "ATTEMPT_RECORDED")
        self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED)
        self.assertEqual(result["failure_code"], "PROMOTION_SOURCE_NOT_ON_PROMOTION_REF")
        self.assertEqual(result["classification"], "PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT")
        self.assertEqual(result["organization_readback"], "VERIFIED")
        self.assertFalse(result["promotion_may_proceed"])
        for field in SIX:
            self.assertTrue(result[field], field)
        latest = json.loads((self.runtime / consumer.RECEIPT_REL).read_text(encoding="utf-8"))
        self.assertEqual(latest["organization_receipt_sha256"], result["organization_receipt_sha256"])
        self.assertEqual(self.run_consumer(ledger, hb_epoch="4096"), result)

    # TVC issuer evidence is another repository's receipt (lead ruling 21:00Z).
    @sppa_tests.refused_until_cross_repo_route
    def test_first_real_promotion_run_is_fail_closed_on_unauthenticated_evidence(self):
        """Under the real custody verifier no evidence receipt authenticates (SPPA correction, Q74-01)."""
        ledger = materialized_ledger(self.base)
        self.commit(resident_request(sppa_tests.promote_request(ledger)))
        for epoch in (None, str(sppa_tests.CARRIER_HB_EPOCH)):
            result = self.run_consumer(ledger, hb_epoch=epoch)
            self.assertEqual(result["transition_class"], sppa.FAIL_CLOSED, epoch)
            self.assertEqual(result["failure_code"], sppa.SOURCE_UNAUTHENTICATED, epoch)
            self.assertFalse(result["promotion_may_proceed"], epoch)
            for field in SIX:
                self.assertTrue(result[field], field)

    # TVC issuer evidence is another repository's receipt (lead ruling 21:00Z).
    @sppa_tests.refused_until_cross_repo_route
    def test_authenticated_promotion_run_is_fail_closed_until_a_carrier_epoch_arrives(self):
        ledger = materialized_ledger(self.base)
        self.commit(resident_request(sppa_tests.promote_request(ledger)))
        real_load = consumer._load

        def authenticated(name, path):
            module = real_load(name, path)
            if name == "sppa_consumer_transition":
                # Test-only stand-in for an authenticating custody basis (none exists on main).
                module.AUTHENTICATING_CUSTODY_BASES = frozenset({sppa_tests.FIXTURE_BASIS})
                module.evidence_custody_basis = lambda custody, row: sppa_tests.FIXTURE_BASIS
            return module

        with mock.patch.object(consumer, "_load", authenticated):
            first = self.run_consumer(ledger)
            self.assertEqual((first["transition_class"], first["failure_code"]),
                             (sppa.FAIL_CLOSED, "HB_EPOCH_NOT_SUPPLIED"))
            self.assertFalse(first["carrier_hb_epoch_supplied"])
            self.assertFalse(first["promotion_may_proceed"])
            # Once a carrier frame supplies the epoch (Q-D-6), the same request authorizes and reads back.
            later = self.run_consumer(ledger, hb_epoch=str(sppa_tests.CARRIER_HB_EPOCH))
        self.assertEqual(later["transition_class"], sppa.AUTHORIZED)
        self.assertEqual(later["organization_readback"], "VERIFIED")
        self.assertTrue(later["promotion_may_proceed"])
        self.assertFalse(later["deployment_performed"])

    def test_dispatcher_visits_the_selector_with_the_supplied_ledger_roots(self):
        consumer_path = self.runtime / dict(dispatcher.CONSUMERS)["site_production_promotion"]
        consumer_path.parent.mkdir(parents=True, exist_ok=True)
        consumer_path.write_text("# consumer\n", encoding="utf-8")
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0, stdout='{"state":"NO_REQUEST"}\n', stderr="")

        receipt = dispatcher.dispatch(ROOT, self.runtime, runner=runner,
                                      env={"PATH": "/bin", "STEGVERSE_REPO_LEDGER_ROOT": "/ledgers/repo",
                                           "STEGVERSE_ORG_LEDGER_ROOT": "/ledgers/org"},
                                      only_consumers=("site_production_promotion",))
        self.assertEqual(receipt["selected_consumers"], ["site_production_promotion"])
        command = calls[0]
        self.assertEqual(command[command.index("--repo-ledger-root") + 1], "/ledgers/repo")
        self.assertEqual(command[command.index("--org-ledger-root") + 1], "/ledgers/org")

    def test_registration_and_materialization_without_a_request(self):
        dispatch_text = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
        self.assertIn('("site_production_promotion", "scripts/consume_site_production_promotion_request.py")',
                      dispatch_text)
        for rel in ("scripts/install_sovereign_heartbeat_service.py", "scripts/bootstrap_sovereign_runtime.py",
                    "scripts/refresh_sovereign_worker_runtime_source.py"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("scripts/consume_site_production_promotion_request.py", text, rel)
            self.assertIn("scripts/authorize_site_production_promotion.py", text, rel)
            self.assertNotIn(REL.as_posix(), text, rel)
        for workflow in (ROOT / ".github/workflows").glob("*.yml"):
            text = workflow.read_text(encoding="utf-8")
            self.assertNotIn("consume_site_production_promotion_request", text, workflow.name)
            self.assertNotIn("authorize_site_production_promotion", text, workflow.name)
        source = (ROOT / "scripts/consume_site_production_promotion_request.py").read_text(encoding="utf-8")
        for forbidden in ("import subprocess", "urllib", "import requests", "datetime.now", "time.time", "time_ns"):
            self.assertNotIn(forbidden, source)

    def test_request_schema_matches_the_consumer(self):
        schema = json.loads((ROOT / "schemas/site-production-promotion-resident-request.schema.json")
                            .read_text(encoding="utf-8"))
        for key, expected in consumer.REQUIRED.items():
            self.assertEqual(schema["properties"][key]["const"], expected, key)
        for key in consumer.REQUIRED_FALSE:
            self.assertIs(schema["properties"][key]["const"], False, key)
        request = resident_request(sppa_tests.fixture())
        try:
            import jsonschema
        except ImportError:
            self.assertTrue(set(schema["required"]) <= set(request))
            return
        jsonschema.validate(request, schema)


if __name__ == "__main__":
    unittest.main()
