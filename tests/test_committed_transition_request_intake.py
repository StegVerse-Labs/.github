"""Intake validation of committed transition requests (WU-B21, intake slice).

A request committed under .stegverse/transition-requests/ (schema
stegverse.organization-transition-request/v1) is validated before any append
(owning_existing_goal and standing required; exactly one of build_manifest or
manifest; a supplied hb_epoch under the kernel's supplied_epoch_failure), built
by the pinned SDK and received on this organization's own ingress. Every
non-ALLOW outcome is one line of JSON with the six fields. Stdlib only (no
YAML dependency).

The push-to-main trigger in organization-ledger-transition.yml, and the tests
that assert it, land after #3241 and #3207 (the rest of WU-B21).
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "resident-runtime/committed_transition_request.py"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")

spec = importlib.util.spec_from_file_location("committed_transition_request_test", HELPER)
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)
KERNEL = intake._kernel()
PATH = ".stegverse/transition-requests/LABS-INTAKE-001.json"


def request(**changes):
    value = {"schema": intake.SCHEMA, "request_id": "LABS-INTAKE-001",
             "owning_existing_goal": "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001",
             "standing": {"mode": "ESTABLISH_GENESIS", "node_ref": "StegVerse-Labs/.github", "predecessor": None},
             "build_manifest": {"process": "organization-records", "data": {}}, "hb_epoch": "40"}
    value.update(changes)
    return {k: v for k, v in value.items() if v is not intake}


def check(value, egress_bound=frozenset({"governance"})):
    return intake.validate(PATH, value, egress_bound=set(egress_bound), epoch_failure=KERNEL.supplied_epoch_failure)


class RequestValidation(unittest.TestCase):
    def assert_six(self, record, code):
        self.assertEqual(record["failure_code"], code, record)
        self.assertIn(record["disposition"], ("FAIL_CLOSED", "DENY"))
        for field in SIX_FIELDS:
            self.assertIsInstance(record.get(field), str, (field, record))
            self.assertTrue(record[field].strip(), (field, record))
        self.assertEqual(record["retry_entrypoint"], ".github/workflows/organization-ledger-transition.yml")
        self.assertNotIn("\n", json.dumps(record))

    def test_a_complete_request_is_receivable(self):
        self.assertIsNone(check(request()))
        self.assertIsNone(check(request(hb_epoch=32)))

    def test_goal_and_standing_are_required(self):
        self.assert_six(check(request(owning_existing_goal=intake)), "TRANSITION_REQUEST_GOAL_ABSENT")
        self.assert_six(check(request(owning_existing_goal=" ")), "TRANSITION_REQUEST_GOAL_ABSENT")
        self.assert_six(check(request(standing=intake)), "TRANSITION_REQUEST_STANDING_ABSENT")
        self.assert_six(check(request(standing={})), "TRANSITION_REQUEST_STANDING_ABSENT")

    def test_exactly_one_manifest_form(self):
        self.assert_six(check(request(manifest={})), "TRANSITION_REQUEST_MANIFEST_FORM_INVALID")
        self.assert_six(check(request(build_manifest=intake)), "TRANSITION_REQUEST_MANIFEST_FORM_INVALID")
        self.assertIsNone(check(request(build_manifest=intake, manifest={"processing": {"capability": "x"}},
                                        expected_canonical_manifest_sha256="0" * 64)))

    def test_the_epoch_is_supplied_and_never_read_from_a_clock(self):
        record = check(request(hb_epoch=intake))
        self.assert_six(record, "HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(record["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        for bad in ("31", " 40", "+40", "4_0", 40.0, True):
            self.assert_six(check(request(hb_epoch=bad)), "HB_EPOCH_INVALID")

    def test_the_kernel_epoch_rule_is_reused_not_vendored(self):
        source = HELPER.read_text(encoding="utf-8")
        self.assertNotIn("def supplied_epoch_failure", source)
        self.assertIn("supplied_epoch_failure", source)

    def test_validation_reads_no_clock(self):
        def clock(*args, **kwargs):
            raise AssertionError("a clock was read")
        with mock.patch("time.time", clock), mock.patch("time.time_ns", clock), \
                mock.patch("time.monotonic", clock), mock.patch("time.gmtime", clock), \
                mock.patch("time.localtime", clock):
            self.assertIsNone(check(request()))
            self.assert_six(check(request(hb_epoch=intake)), "HB_EPOCH_NOT_SUPPLIED")
            self.assert_six(check(request(hb_epoch="31")), "HB_EPOCH_INVALID")
        source = HELPER.read_text(encoding="utf-8")
        for name in ("import time", "datetime", "time.time", "monotonic"):
            self.assertNotIn(name, source)

    def test_schema_path_and_id(self):
        self.assert_six(check(request(schema="other/v1")), "TRANSITION_REQUEST_SCHEMA_INVALID")
        self.assert_six(check(request(request_id="a b")), "TRANSITION_REQUEST_ID_INVALID")
        self.assert_six(check(None), "TRANSITION_REQUEST_UNREADABLE")
        self.assert_six(intake.validate("docs/x.json", request(), egress_bound=set(),
                                        epoch_failure=KERNEL.supplied_epoch_failure),
                        "TRANSITION_REQUEST_PATH_INVALID")

    def test_mesh_and_egress_bound_requests_are_deferred_not_spent(self):
        record = check(request(mesh_root="git+https://github.com/StegVerse-Labs/.github#refs/stegverse/federation-mesh"))
        self.assert_six(record, "TRANSITION_REQUEST_DEFERRED_MESH_NOT_BOUND")
        self.assertTrue(record["deferred"])
        record = check(request(build_manifest={"process": "governance"}))
        self.assert_six(record, "TRANSITION_REQUEST_DEFERRED_EGRESS_WITHOUT_MESH")
        self.assertTrue(record["deferred"])

    def test_the_boundary_names_its_egress_bound_processes(self):
        boundary = json.loads((ROOT / "org-runtime/interlock-intr.json").read_text(encoding="utf-8"))
        self.assertIn("governance", intake.egress_bound_processes(boundary))


class ManifestAndOutcome(unittest.TestCase):
    def test_build_and_exact_forms(self):
        canonical = lambda manifest: "a" * 64  # noqa: E731
        built = intake.committed_manifest(request(), build=lambda **kw: {"built": kw}, canonical_of=canonical)
        self.assertEqual((built["disposition"], built["source"]), ("ALLOW", "BUILT_BY_PINNED_SDK"))

        def unbuildable(**kw):
            raise ValueError("bad")
        record = intake.committed_manifest(request(), build=unbuildable, canonical_of=canonical)
        RequestValidation.assert_six(self, record, "TRANSITION_REQUEST_NOT_BUILDABLE")
        exact = request(build_manifest=intake, manifest={"m": 1}, expected_canonical_manifest_sha256="a" * 64)
        self.assertEqual(intake.committed_manifest(exact, build=None, canonical_of=canonical)["source"],
                         "EXACT_COMMITTED_MANIFEST")
        record = intake.committed_manifest({**exact, "expected_canonical_manifest_sha256": "b" * 64},
                                           build=None, canonical_of=canonical)
        RequestValidation.assert_six(self, record, "EXACT_MANIFEST_DIGEST_MISMATCH")
        record = intake.committed_manifest({**exact, "expected_canonical_manifest_sha256": "x"},
                                           build=None, canonical_of=canonical)
        RequestValidation.assert_six(self, record, "EXACT_MANIFEST_UNBOUND")

    def test_ingress_outcomes(self):
        line, proceed = intake.ingress_outcome("r", {"disposition": "ALLOW", "organization_receipt_sha256": "sha256:" + "c" * 64})
        self.assertTrue(proceed)
        self.assertEqual(line["disposition"], "ALLOW")
        line, proceed = intake.ingress_outcome("r", {"disposition": "DENY", "failed_predicate": "P",
                                                     "refusal_organization_receipt_sha256": "d" * 64})
        self.assertTrue(proceed)  # a recorded DENY is a disposition, and is published
        RequestValidation.assert_six(self, line, "INGRESS_DENY")
        line, proceed = intake.ingress_outcome("r", {"disposition": "FAIL_CLOSED", "failed_predicate": "Q"})
        self.assertFalse(proceed)
        RequestValidation.assert_six(self, line, "INGRESS_FAIL_CLOSED")
        line, proceed = intake.ingress_outcome("r", None)
        self.assertFalse(proceed)
        RequestValidation.assert_six(self, line, "INGRESS_RESULT_ABSENT")

    def test_confirm_requires_every_recorded_receipt_on_the_fresh_fetch(self):
        readback = {"disposition": "ALLOW", "chain": [{"receipt_sha256": "e" * 64}]}
        self.assertEqual(intake.confirm(readback, [("r", {"organization_receipt_sha256": "sha256:" + "e" * 64})]), [])
        missing = intake.confirm(readback, [("r", {"organization_receipt_sha256": "f" * 64})])
        RequestValidation.assert_six(self, missing[0], "INTAKE_RECEIPT_NOT_ON_PUBLISHED_REF")
        RequestValidation.assert_six(self, intake.confirm({"disposition": "FAIL_CLOSED"}, [])[0],
                                     "INTAKE_READBACK_NOT_ALLOW")


class ValidateCommand(unittest.TestCase):
    def run_validate(self, requests):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp, ".stegverse/transition-requests")
            folder.mkdir(parents=True)
            names = []
            for name, value in requests.items():
                Path(folder, name).write_text(json.dumps(value), encoding="utf-8")
                names.append(".stegverse/transition-requests/" + name)
            Path(tmp, "requests.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
            run = subprocess.run([sys.executable, str(HELPER), "validate", "--requests", "requests.txt",
                                  "--receivable-out", "receivable.txt"], cwd=tmp, capture_output=True, text=True,
                                 env=dict(os.environ))
            receivable = Path(tmp, "receivable.txt").read_text(encoding="utf-8").split()
        return run, receivable

    def test_one_invalid_request_refuses_the_push_before_any_append(self):
        run, receivable = self.run_validate({"a.json": request(), "b.json": request(hb_epoch=intake)})
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(receivable, [])
        lines = run.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1)
        RequestValidation.assert_six(self, json.loads(lines[0]), "HB_EPOCH_NOT_SUPPLIED")

    def test_deferred_requests_are_reported_and_the_rest_received(self):
        run, receivable = self.run_validate({"a.json": request(),
                                             "b.json": request(build_manifest={"process": "governance"})})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(receivable, [".stegverse/transition-requests/a.json"])
        deferred = json.loads(run.stdout.strip().splitlines()[0])
        RequestValidation.assert_six(self, deferred, "TRANSITION_REQUEST_DEFERRED_EGRESS_WITHOUT_MESH")


if __name__ == "__main__":
    unittest.main()
