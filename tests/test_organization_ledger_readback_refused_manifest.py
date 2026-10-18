"""The organization-ledger readback binds a refused manifest in ingress's encoding.

Source-only. Ledgers are written to temporary roots and nothing here is a live
receipt. Ingress hashes a refused manifest with the default ensure_ascii=True;
receipts are hashed with ensure_ascii=False. The readback must bind a refusal
the way ingress recorded it, or a manifest carrying non-ASCII text cannot be
bound to its refusal receipt (StegVerse-org/.github#183, H27).
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_organization_manifest_ingress_rule_ref import REVISION, ingress  # noqa: E402

SIX_FIELDS = ("disposition", "failure_code", "failed_predicate",
              "required_evidence_or_repair", "retry_entrypoint", "consequence_committed")


def _load_readback():
    spec = importlib.util.spec_from_file_location(
        "organization_ledger_readback_under_test",
        ROOT / "resident-runtime/organization_ledger_readback.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


readback = _load_readback()

ASCII_MANIFEST = {"processing": {"capability": "x"}, "source_output_id": "refused-cafe"}
NON_ASCII_MANIFEST = {"processing": {"capability": "x"}, "source_output_id": "refused-café-✓"}


class RefusedManifestBindingTest(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        base = Path(self._temp.name)
        self.org_root = base / "org"
        self.repo_root = base / "repo"
        self._env = mock.patch.dict(os.environ, {
            "GITHUB_SHA": REVISION,
            "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
            "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
        })
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._temp.cleanup()

    def refuse(self, manifest):
        result = ingress.receive(manifest, registry={})
        self.assertIs(result["refusal_recorded"], True)
        return result

    def recorded_digest(self, result):
        digest = result["refusal_organization_receipt_sha256"].split(":", 1)[1]
        receipt = json.loads((self.org_root / "receipts" / f"{digest}.json").read_text())
        return receipt["predecessor_org_state_sha256"]

    def test_the_readback_encoding_is_the_ingress_refusal_encoding(self):
        for manifest in (ASCII_MANIFEST, NON_ASCII_MANIFEST):
            with self.subTest(manifest=manifest):
                self.assertEqual(readback.submitted_manifest_sha(manifest),
                                 ingress.refusal_record("P", "d", manifest)["submitted_manifest_sha256"])

    def test_a_refused_ascii_manifest_is_bound_at_readback(self):
        result = self.refuse(ASCII_MANIFEST)
        self.assertEqual(readback.submitted_manifest_sha(ASCII_MANIFEST), self.recorded_digest(result))
        bound = readback.readback(str(self.org_root), result, ASCII_MANIFEST)
        self.assertIs(bound["ingress_refused"], True)
        self.assertIs(bound["ingress_receipt_bound_to_manifest"], True)
        self.assertEqual(bound["ingress_organization_receipt_sha256"],
                         result["refusal_organization_receipt_sha256"])

    def test_a_refused_manifest_carrying_non_ascii_text_is_bound_at_readback(self):
        self.assertNotEqual(json.dumps(NON_ASCII_MANIFEST, ensure_ascii=False),
                            json.dumps(NON_ASCII_MANIFEST))
        result = self.refuse(NON_ASCII_MANIFEST)
        recorded = self.recorded_digest(result)
        self.assertEqual(readback.submitted_manifest_sha(NON_ASCII_MANIFEST), recorded)
        # The receipt-body encoding is a different digest for this manifest.
        self.assertNotEqual(readback.sha(NON_ASCII_MANIFEST), recorded)
        bound = readback.readback(str(self.org_root), result, NON_ASCII_MANIFEST)
        self.assertIs(bound["ingress_refused"], True)
        self.assertIs(bound["ingress_receipt_bound_to_manifest"], True)

    def test_a_refused_manifest_that_does_not_match_its_recorded_digest_fails_closed(self):
        result = self.refuse(NON_ASCII_MANIFEST)
        for other in ({**NON_ASCII_MANIFEST, "source_output_id": "refused-cafe-✓"},
                      {**NON_ASCII_MANIFEST, "label": "✓"}, None):
            with self.subTest(other=other):
                with self.assertRaises(readback.ReadbackRefused) as refused:
                    readback.readback(str(self.org_root), result, other)
                self.assertEqual(refused.exception.failed_predicate,
                                 "RECEIPT_IS_BOUND_TO_THE_SUBMITTED_MANIFEST")

    def test_the_cli_refuses_a_mismatched_manifest_with_the_six_fields(self):
        result = self.refuse(NON_ASCII_MANIFEST)
        base = Path(self._temp.name)
        (base / "ingress.json").write_text(json.dumps(result), encoding="utf-8")
        (base / "manifest.json").write_text(
            json.dumps({**NON_ASCII_MANIFEST, "label": "✓"}, ensure_ascii=False), encoding="utf-8")
        (base / "same.json").write_text(json.dumps(NON_ASCII_MANIFEST, ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, str(ROOT / "resident-runtime/organization_ledger_readback.py"),
                   "--location", str(self.org_root), "--ingress-result", str(base / "ingress.json")]
        refused = subprocess.run(command + ["--manifest", str(base / "manifest.json")],
                                 capture_output=True, text=True)
        self.assertEqual(refused.returncode, 1, refused.stderr)
        out = json.loads(refused.stdout)
        for field in SIX_FIELDS:
            self.assertIn(field, out)
        self.assertEqual(out["disposition"], "FAIL_CLOSED")
        self.assertEqual(out["failed_predicate"], "RECEIPT_IS_BOUND_TO_THE_SUBMITTED_MANIFEST")
        self.assertIs(out["consequence_committed"], False)
        bound = subprocess.run(command + ["--manifest", str(base / "same.json")],
                               capture_output=True, text=True)
        self.assertEqual(bound.returncode, 0, bound.stdout + bound.stderr)
        self.assertIs(json.loads(bound.stdout)["ingress_receipt_bound_to_manifest"], True)

    def test_an_ingress_result_that_is_not_an_object_is_refused(self):
        self.refuse(ASCII_MANIFEST)
        for other in ([], "x", 1):
            with self.subTest(other=other):
                with self.assertRaises(readback.ReadbackRefused) as refused:
                    readback.readback(str(self.org_root), other, ASCII_MANIFEST)
                self.assertEqual(refused.exception.failed_predicate, "INGRESS_RESULT_IS_AN_OBJECT")

    def test_the_cli_refuses_flags_it_would_otherwise_ignore_with_the_six_fields(self):
        result = self.refuse(ASCII_MANIFEST)
        base = Path(self._temp.name)
        (base / "ingress.json").write_text(json.dumps(result), encoding="utf-8")
        (base / "list.json").write_text("[]", encoding="utf-8")
        (base / "manifest.json").write_text(json.dumps(ASCII_MANIFEST), encoding="utf-8")
        (base / "closure.json").write_text("{}", encoding="utf-8")
        command = [sys.executable, str(ROOT / "resident-runtime/organization_ledger_readback.py"),
                   "--location", str(self.org_root)]
        cases = (
            (["--closure-result", str(base / "closure.json"), "--ingress-result", str(base / "ingress.json")],
             "CLOSURE_RESULT_IS_READ_WITHOUT_AN_INGRESS_BINDING"),
            (["--closure-result", str(base / "closure.json"), "--manifest", str(base / "manifest.json")],
             "CLOSURE_RESULT_IS_READ_WITHOUT_AN_INGRESS_BINDING"),
            (["--manifest", str(base / "manifest.json")], "MANIFEST_IS_BOUND_THROUGH_AN_INGRESS_RESULT"),
            (["--ingress-result", str(base / "list.json")], "INGRESS_RESULT_IS_AN_OBJECT"),
        )
        for flags, predicate in cases:
            with self.subTest(flags=flags):
                run = subprocess.run(command + flags, capture_output=True, text=True)
                self.assertEqual(run.returncode, 1, run.stderr)
                out = json.loads(run.stdout)
                for field in SIX_FIELDS:
                    self.assertIn(field, out)
                self.assertEqual(out["disposition"], "FAIL_CLOSED")
                self.assertEqual(out["failed_predicate"], predicate)
                self.assertIs(out["consequence_committed"], False)


if __name__ == "__main__":
    unittest.main()
