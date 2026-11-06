"""Every non-ALLOW `receive()` returns and records all six fields (Labs#3441, Lane B ruling).

failure_code, failed_predicate, required_evidence_or_repair, retry_entrypoint,
owning_existing_goal and next_attempt: each a non-empty string on the returned result,
on the repository receipt's evidence and on the organization receipt's boundary evidence,
for the refusals the series raises (payload binding, authority effect, fence,
predecessor), for the ones that carried no six fields before (PR-1(ii): `REFUSAL_REPAIRS`),
and for the ones the crossing carries. Refusals already on a ledger are append-only and
are not read here: this holds for the refusals recorded from now on.

The checker `assert_six` is itself held to the rule: a result missing any one of the six,
blank, null or not a string, is rejected by it, so the test cannot pass on a refusal that
lost a field.
"""
from __future__ import annotations

import ast
import copy
import unittest
from pathlib import Path
from unittest import mock

from tests import test_protocol_v1_conformance_fixtures as fixtures
ingress = fixtures.ingress

ROOT = Path(__file__).resolve().parents[1]
SIX = ingress.SIX_FIELDS
SOURCE = ROOT / "resident-runtime/organization_manifest_ingress.py"


def assert_six(test: unittest.TestCase, carrier: dict, label: str) -> None:
    for field in SIX:
        test.assertIn(field, carrier, f"{label}: {field} missing")
        test.assertIsInstance(carrier[field], str, f"{label}: {field} is not a string")
        test.assertTrue(carrier[field].strip(), f"{label}: {field} is blank")


def assert_recorded_with_six(test: unittest.TestCase, result: dict, repository: list, organization: list,
                             label: str, *, declared: bool = True) -> None:
    """Returned, and the same six on both receipts' evidence."""
    assert_six(test, result, label + " returned")
    (repo_receipt,), (org_receipt,) = repository, organization
    assert_six(test, repo_receipt["evidence"], label + " repository evidence")
    assert_six(test, org_receipt["boundary_evidence"], label + " organization evidence")
    for field in SIX:
        test.assertEqual(repo_receipt["evidence"][field], result[field], f"{label}: {field}")
        test.assertEqual(org_receipt["boundary_evidence"][field], result[field], f"{label}: {field}")
    if declared:
        test.assertEqual(result["disposition"], ingress.refusal_disposition(
            result["failure_code"], result["failed_predicate"]), label)
    test.assertEqual(repo_receipt["evidence"]["disposition"], result["disposition"], label)


class CheckerIsHeldToTheRuleTest(unittest.TestCase):
    GOOD = {field: "x" for field in SIX}

    def test_the_checker_accepts_a_complete_set(self):
        assert_six(self, dict(self.GOOD), "good")

    def test_the_checker_rejects_each_field_missing_blank_null_or_not_a_string(self):
        for field in SIX:
            for name, mutate in (("missing", lambda c: c.pop(field)),
                                 ("blank", lambda c: c.__setitem__(field, "  ")),
                                 ("null", lambda c: c.__setitem__(field, None)),
                                 ("dict", lambda c: c.__setitem__(field, {"a": 1}))):
                with self.subTest(field=field, mutation=name):
                    carrier = dict(self.GOOD)
                    mutate(carrier)
                    with self.assertRaises(AssertionError):
                        assert_six(self, carrier, "mutated")


class RealReceiveRefusalsTest(unittest.TestCase):
    def test_every_protocol_negative_returns_and_records_all_six(self):
        for case_id in fixtures.NEGATIVES:
            with self.subTest(case=case_id):
                result, ledgers = fixtures.live(case_id)
                assert_recorded_with_six(self, result, ledgers["repository"]["receipts"],
                                         ledgers["organization"]["receipts"], case_id)

    def test_the_authority_effect_refusal_is_one_of_them_and_names_its_own_row(self):
        result, _ = fixtures.live("n6-authority-effect-not-warranted")
        self.assertEqual(result["failure_code"], ingress.AUTHORITY_NOT_WARRANTED)
        self.assertEqual(result["owning_existing_goal"], ingress.AUTHORITY_OWNING_GOAL)
        self.assertEqual(result["disposition"], "DENY")


class RefusalWithoutSixFieldsOfItsOwnTest(unittest.TestCase):
    """PR-1(ii): a refusal that carries none takes them from `REFUSAL_REPAIRS`, recorded at both levels."""

    def refuse(self, predicate: str, **extra):
        fixture = fixtures.packet()
        request = fixtures.ingress_request(fixture)
        with fixtures.LedgerRoots(request) as roots:
            result = ingress._refused(predicate, "DETAIL-FOR-" + predicate, manifest=fixture["manifest"],
                                      rule_ref=ingress.recomputation_rule_ref(), hb_epoch=4096, **extra)
            return result, fixtures.readback(roots.repo)["receipts"], fixtures.readback(roots.org)["receipts"]

    def test_each_predicate_this_operation_refuses_under_returns_and_records_all_six(self):
        predicates = sorted(ingress.REFUSAL_REPAIRS)
        self.assertGreaterEqual(len(predicates), 10)
        for predicate in predicates:
            with self.subTest(predicate=predicate):
                extra = {}
                if predicate == ingress.PARENT_MANIFEST_INVALID_PREDICATE:
                    extra["failure_code"] = sorted(ingress.PARENT_MANIFEST_OWNER_CODES)[0]
                result, repository, organization = self.refuse(predicate, **extra)
                self.assertNotEqual(result["failure_code"], ingress.REFUSAL_DISPOSITION_NOT_DECLARED)
                assert_recorded_with_six(self, result, repository, organization, predicate)

    def test_a_predicate_with_no_row_still_returns_and_records_all_six_under_the_undeclared_code(self):
        result, repository, organization = self.refuse("A_PREDICATE_NO_TABLE_ROW_DECLARES")
        self.assertEqual(result["failure_code"], ingress.REFUSAL_DISPOSITION_NOT_DECLARED)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        assert_recorded_with_six(self, result, repository, organization, "undeclared", declared=False)

    def test_a_refusal_the_caller_gave_six_fields_keeps_exactly_those(self):
        given = ingress.ingress_six_fields(
            ingress.PAYLOAD_NOT_BOUND, ingress.PAYLOAD_NOT_BOUND_PREDICATE, "THE-REPAIR",
            "THE-GOAL", "THE-RESUBMISSION")
        result, repository, organization = self.refuse(ingress.PAYLOAD_NOT_BOUND_PREDICATE, six_fields=given)
        assert_recorded_with_six(self, result, repository, organization, "given")
        for field in SIX:
            self.assertEqual(result[field], given[field], field)

    def test_six_fields_smuggled_in_extra_never_overwrite_the_refusals_own(self):
        result, _, _ = self.refuse("CROSSING_IS_DRIVABLE_FROM_THE_MANIFEST_AS_DECLARED",
                                   next_attempt="SMUGGLED", retry_entrypoint="SMUGGLED")
        self.assertNotEqual(result["next_attempt"], "SMUGGLED")
        self.assertNotEqual(result["retry_entrypoint"], "SMUGGLED")


class SourceCoverageTest(unittest.TestCase):
    """Reads `receive()` itself: no refusal call in it can leave the six fields to chance."""

    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        receive = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "receive")
        cls.calls = [node for node in ast.walk(receive) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == "refused"]

    def test_receive_refuses_in_several_places(self):
        self.assertGreaterEqual(len(self.calls), 12)

    def test_a_refusal_naming_its_predicate_as_a_string_has_a_repair_row(self):
        for call in self.calls:
            first = call.args[0] if call.args else None
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                with self.subTest(predicate=first.value):
                    self.assertIn(first.value, ingress.REFUSAL_REPAIRS)

    def test_every_other_refusal_in_receive_passes_its_own_six_fields(self):
        for call in self.calls:
            first = call.args[0] if call.args else None
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                continue
            keywords = {keyword.arg for keyword in call.keywords}
            with self.subTest(line=call.lineno):
                # `refused(*inadmissible)` is the SDK's role-conformance refusal: its predicates are rows.
                starred = any(isinstance(arg, ast.Starred) for arg in call.args)
                self.assertTrue(starred or "six_fields" in keywords or "failure_code" in keywords
                                or isinstance(first, ast.Name) and first.id == "PARENT_MANIFEST_INVALID_PREDICATE"
                                or isinstance(first, ast.Subscript) or isinstance(first, ast.IfExp),
                                f"receive() line {call.lineno} refuses with no six fields")

    def test_every_table_row_this_operation_refuses_under_has_a_repair_row(self):
        for (code, predicate) in ingress.REFUSAL_DISPOSITIONS:
            if code == ingress.REFUSED_CLASS:
                with self.subTest(predicate=predicate):
                    self.assertIn(predicate, ingress.REFUSAL_REPAIRS)
        for code in ingress.PARENT_MANIFEST_OWNER_CODES:
            self.assertIn((code, ingress.PARENT_MANIFEST_INVALID_PREDICATE), ingress.REFUSAL_DISPOSITIONS)
        self.assertIn(ingress.PARENT_MANIFEST_INVALID_PREDICATE, ingress.REFUSAL_REPAIRS)

    def test_the_series_refusals_have_disposition_rows(self):
        for pair in ((ingress.PAYLOAD_NOT_BOUND, ingress.PAYLOAD_NOT_BOUND_PREDICATE),
                     (ingress.AUTHORITY_NOT_WARRANTED, ingress.AUTHORITY_NOT_WARRANTED_PREDICATE),
                     (ingress.FENCE_NOT_VERIFIED, ingress.FENCE_PREDICATE),
                     (ingress.FENCE_STALE, ingress.FENCE_PREDICATE),
                     (ingress.PREDECESSOR_NOT_RECORDED, ingress.PREDECESSOR_PREDICATE),
                     (ingress.PREDECESSOR_SUPERSEDED, ingress.PREDECESSOR_PREDICATE)):
            with self.subTest(pair=pair):
                self.assertIn(ingress.refusal_disposition(*pair), {"DENY", "FAIL_CLOSED"})


if __name__ == "__main__":
    unittest.main()
