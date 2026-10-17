"""D7 and the refusal disposition table at the Labs ingress (twin of StegVerse-org/.github#185).

When a manifest's published route binds
`stegverse.manifest_state_transition_runtime.execute_manifest` and no service's
`admits_processing` names the declared {capability, route_id}, the ingress
refuses it before the crossing could fall back to the `completion.egress`
surface: FAIL_CLOSED PROCESSING_SERVICE_NOT_DECLARED_FOR_CONSUMER_ROUTE, stored
and returned alike. Routes bound to another runtime and manifests that only
target the completion return keep the fallback.

Every refusal's disposition is the (failure_code, failed_predicate) row of
REFUSAL_DISPOSITIONS, the same value stored and returned; a pair with no row is
FAIL_CLOSED REFUSAL_DISPOSITION_NOT_DECLARED.

Ledger roots are temporary per test, under the POSIX locus the test package
declares (tests/__init__.py, tests/conftest.py).
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from stegverse import route_resolution

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
MANIFEST = ROOT / "tests/fixtures/d6-labs-purpose-bound-worker-manifest.json"
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "d7-labs", "predecessor": None}
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
D7_CODE = "PROCESSING_SERVICE_NOT_DECLARED_FOR_CONSUMER_ROUTE"
D7_PREDICATE = "CONSUMER_ROUTE_RESOLVES_TO_A_DECLARED_PROCESSING_SERVICE"


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ingress = _load("organization_manifest_ingress_d7_labs", "resident-runtime/organization_manifest_ingress.py")
d6 = _load("d6_far_side_registry_d7_labs", "tests/fixtures/d6_far_side_registry.py")


def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def revision():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=False).stdout.strip() or "0" * 40


class D7IngressTests(unittest.TestCase):
    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        work = Path(self._work.name)
        self.repo_root = work / "repo-ledger"
        environment = {"GITHUB_SHA": os.environ.get("GITHUB_SHA") or revision(),
                       "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
                       "STEGVERSE_ORG_LEDGER_ROOT": str(work / "org-ledger")}
        patch = mock.patch.dict(os.environ, environment)
        patch.start()
        self.addCleanup(patch.stop)

    def receive(self, value, registry=REGISTRY, packet_id="d7-labs"):
        return ingress.receive(value, registry=registry, standing=GENESIS,
                               packet_id=packet_id, hb_epoch=43)

    def refusals(self):
        directory = self.repo_root / "receipts"
        found = [json.loads(p.read_text()) for p in directory.rglob("*.json")] if self.repo_root.exists() else []
        return [r for r in found if r.get("transition_class") == ingress.REFUSED_CLASS]

    def assert_six_fields(self, carrier):
        for field in SIX_FIELDS:
            self.assertTrue(isinstance(carrier.get(field), str) and carrier[field].strip(), field)

    def test_d7_is_fail_closed_stored_and_returned_alike(self):
        out = self.receive(manifest())
        self.assertEqual(out["disposition"], "FAIL_CLOSED", out.get("detail"))
        self.assertEqual(out["refusal_stored_disposition"], "FAIL_CLOSED")
        self.assertEqual(out["failure_code"], D7_CODE)
        self.assertEqual(out["failed_predicate"], D7_PREDICATE)
        self.assertEqual(out["owning_existing_goal"], "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001")
        self.assertIn("stegverse-labs.sdk-manifest-ingress", out["retry_entrypoint"])
        self.assert_six_fields(out)
        self.assertIs(out["refusal_recorded"], True)
        record, = [r["evidence"] for r in self.refusals()]
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        for field in SIX_FIELDS:
            self.assertEqual(record[field], out[field], field)
        self.assertTrue(out["refusal_organization_receipt_sha256"])

    def test_d7_never_reaches_the_crossing(self):
        with mock.patch.object(ingress.crossing_module, "cross",
                               side_effect=AssertionError("the crossing was driven")):
            out = self.receive(manifest())
        self.assertEqual(out["failure_code"], D7_CODE)
        self.assertNotIn("crossing", out)

    def test_an_admitted_pair_far_side_refusal_passes_the_crossing_six_fields_through(self):
        for case, expected in d6.fixture()["cases"].items():
            with self.subTest(case=case):
                out = self.receive(manifest(), registry=d6.registry_for(case), packet_id="d7-labs-" + case)
                self.assertEqual(out["failure_code"], expected["expected_failure_code"])
                self.assertEqual(out["failed_predicate"], expected["expected_failed_predicate"])
                self.assertEqual(out["retry_entrypoint"], "resident-runtime/sdk_manifest_crossing.py::cross")
                self.assertEqual(out["disposition"], "FAIL_CLOSED")
                self.assertEqual(out["refusal_stored_disposition"], "FAIL_CLOSED")

    def test_a_declared_row_clears_d7_and_other_routes_keep_the_fallback(self):
        self.assertIsNotNone(ingress.processing_service_precheck(manifest(), REGISTRY))
        self.assertIsNone(ingress.processing_service_precheck(manifest(), d6.registry_for("receiver-unavailable")))
        completion_only = {key: value for key, value in manifest().items() if key != "processing"}
        self.assertIsNone(ingress.processing_service_precheck(completion_only, REGISTRY))
        for route_id in ("stegverse.route.native-source-math.v1", "stegverse.route.customer-local-governance.v1"):
            if route_id not in route_resolution.PUBLISHED_ROUTES:
                continue
            with self.subTest(route=route_id):
                published = route_resolution.PUBLISHED_ROUTES[route_id]
                value = copy.deepcopy(manifest())
                value["extensions"][route_resolution.ROUTE_DECLARATION_EXTENSION] = {
                    field: published[field] for field in route_resolution._ROUTE_FIELDS}
                value["processing"] = {"capability": published["processor_capability"], "route_id": route_id}
                self.assertIsNone(ingress.processing_service_precheck(value, REGISTRY))

    def test_the_disposition_table_is_keyed_on_the_code_and_predicate_pair(self):
        generic = ingress.REFUSED_CLASS
        table = ingress.REFUSAL_DISPOSITIONS
        self.assertEqual(table[(D7_CODE, D7_PREDICATE)], "FAIL_CLOSED")
        self.assertEqual(table[(ingress.APPEND_NOT_COMMITTED, ingress.APPEND_NOT_COMMITTED_PREDICATE)], "FAIL_CLOSED")
        self.assertEqual(table[("HB_EPOCH_NOT_SUPPLIED", "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")], "FAIL_CLOSED")
        self.assertEqual(table[("HB_EPOCH_INVALID", "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")], "FAIL_CLOSED")
        self.assertEqual(table[(generic, "ORGANIZATION_RESOLVES_ITS_OWN_INGRESS_DESTINATION")], "FAIL_CLOSED")
        self.assertEqual(table[(generic, "ONE_TRANSITION_ID_BINDS_ONE_MANIFEST")], "DENY")
        self.assertEqual(table[(generic, ingress.PARENT_MANIFEST_INVALID_PREDICATE)], "DENY")
        self.assertEqual({v for (code, _), v in table.items() if code == generic}, {"DENY", "FAIL_CLOSED"})
        refusals = ingress.crossing_module.REFUSALS
        for code, (predicate, *_rest) in refusals.items():
            self.assertIn((code, predicate), table, code)
        self.assertIsNone(ingress.refusal_disposition("MANIFEST_DECLARES_NO_EGRESS", "ANOTHER_PREDICATE"))

    def test_an_undeclared_pair_is_refused_fail_closed_under_its_own_code(self):
        fields = {"failure_code": "MANIFEST_DECLARES_NO_EGRESS", "failed_predicate": "SOME_OTHER_PREDICATE",
                  "required_evidence_or_repair": "repair", "retry_entrypoint": "entry",
                  "owning_existing_goal": "goal", "next_attempt": "next"}
        disposition, out = ingress.declared_refusal(fields)
        self.assertEqual(disposition, "FAIL_CLOSED")
        self.assertEqual(out["failure_code"], "REFUSAL_DISPOSITION_NOT_DECLARED")
        self.assertEqual(out["undeclared_refusal_failure_code"], "MANIFEST_DECLARES_NO_EGRESS")
        self.assertEqual(out["undeclared_refusal_failed_predicate"], "SOME_OTHER_PREDICATE")

    def test_an_unresolvable_route_skips_the_precheck_and_the_derivation_refusal_fires(self):
        """Negative D7: no resolvable consumer route, so D7 is not claimed; the derivation refusal stands."""
        value = manifest()
        del value["extensions"][route_resolution.ROUTE_DECLARATION_EXTENSION]
        self.assertIsNone(ingress.processing_service_precheck(value, REGISTRY))
        out = self.receive(value)
        self.assertEqual(out["failed_predicate"], "ORGANIZATION_RESOLVES_ITS_OWN_INGRESS_DESTINATION")
        self.assertNotEqual(out.get("failure_code"), D7_CODE)
        self.assertEqual(out["disposition"], "FAIL_CLOSED")
        self.assertEqual(out["refusal_stored_disposition"], "FAIL_CLOSED")
        self.assertIs(out["refusal_recorded"], True)
        record, = [r["evidence"] for r in self.refusals()]
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        self.assertEqual(record["failed_predicate"], "ORGANIZATION_RESOLVES_ITS_OWN_INGRESS_DESTINATION")


if __name__ == "__main__":
    unittest.main()
