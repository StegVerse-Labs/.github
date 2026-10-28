"""Protocol v1.0 packet conformance, as fixtures on the existing SDK:ManifestIngress path.

StegVerse-Labs/.github#3369 asks for one positive packet and eight negatives --
tamper, replay, forged identity, stale head, wrong route, missing authority,
missing receipts, reconstruction failure -- run through the existing evaluator,
not a new one. The path is the one `org-runtime/interlock-intr.json` already
binds for `sdk-manifest-ingress` (SDK#566):

    resident-runtime/sdk_manifest_crossing.py::cross           admission
    org-boundary/runtime/process_boundary.py                    processing
    resident-runtime/organization_manifest_ingress.py::bound_here
    resident-runtime/organization_manifest_ingress.py::reconstruct_closures
    resident-runtime/organization_manifest_ingress.py::ingress_transition_id

The fixtures live under
`org-kernel/organization-ledger/fixtures/protocol-v1-conformance/`. Each case
names one mutation of the positive packet and the disposition it must reach;
a negative is DENY or FAIL_CLOSED with the six fields, the positive is ALLOW.

The bounded effect is the registered `stegverse-labs.boundary-diagnostic`
echo: the crossing runs for real, writes only to a temporary directory, and
appends to no ledger. `receive`, which does append, is not called. The SDK's
`derive_execution_request` is not run either (the SDK is not a dependency
here), so the request digest is this fixture's own.

Fixture evidence only. ALLOW here is not runtime ALLOW, no receipt is minted,
and admission, claim/fence and protected runs stay with the Registry owner.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "org-kernel/organization-ledger/fixtures/protocol-v1-conformance"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
NEGATIVES = ("n1-tamper", "n2-replay", "n3-forged-identity", "n4-stale-head", "n5-wrong-route",
             "n6-missing-authority", "n7-missing-receipts", "n8-reconstruction-failure")

_fixture_spec = importlib.util.spec_from_file_location(
    "manifest_ingress_rule_ref_fixture", ROOT / "tests/test_organization_manifest_ingress_rule_ref.py")
_fixture = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture)
ingress = _fixture.ingress

_crossing_spec = importlib.util.spec_from_file_location(
    "sdk_manifest_crossing_under_test", ROOT / "resident-runtime/sdk_manifest_crossing.py")
crossing_module = importlib.util.module_from_spec(_crossing_spec)
_crossing_spec.loader.exec_module(crossing_module)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def packet():
    return load(FIXTURES / "packet.json")


def case(case_id: str):
    return load(FIXTURES / "cases" / f"{case_id}.json")


def binding(profile_id: str):
    """The SDK:ManifestIngress binding as the boundary document declares it, read live."""
    boundary = load(ROOT / "org-runtime/interlock-intr.json")
    found = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("profile_id") == profile_id and isinstance(node.get("receiving_operation"), dict):
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(boundary)
    if len(found) != 1:
        raise AssertionError(f"expected one {profile_id} binding, found {len(found)}")
    return copy.deepcopy(found[0])


class Refused(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def evaluate(fixture, mutation, recorded):
    """Drive one packet through the existing ingress predicates, in binding order.

    Returns the closures the evaluator reconstructed. Raises `Refused` carrying
    the evaluator's own refusal code; nothing here grades a refusal.
    """
    manifest = copy.deepcopy(fixture["manifest"])
    standing = copy.deepcopy(fixture["standing"])
    packet_id = fixture["packet_id"]
    kind = mutation["kind"]
    if kind == "PATCH_EGRESS":
        manifest["completion"]["egress"].update(mutation["patch"])
    if kind == "REPLACE_STANDING":
        standing = mutation["standing"]
    if kind == "REPLAY_UNDER_NEW_PACKET_ID":
        packet_id = mutation["packet_id"]

    resolution = binding(fixture["profile"]["profile_id"])
    if kind == "PATCH_RECEIVING_OPERATION":
        resolution["receiving_operation"].update(mutation["patch"])
    request = {"manifest_declared_destination": resolution}
    if kind == "DROP_RESOLUTION":
        request = {}
    try:
        ingress.bound_here(request)
    except ValueError as exc:
        raise Refused(str(exc)) from None

    registry = load(ROOT / fixture["registry_source"])
    try:
        crossing = crossing_module.cross(manifest, registry=registry, packet_id=packet_id, standing=standing)
    except SystemExit as exc:
        raise Refused(str(exc.code).split(":", 1)[0]) from None
    if not crossing["crossing_completed"]:
        raise Refused(crossing["far_side_disposition"])

    if kind == "TAMPER_PAYLOAD_AFTER_CROSSING":
        # The payload is altered after the boundary bound its receipts, and the
        # digest is honestly recomputed from the altered bytes.
        altered = {**crossing["application_result"]["echo"],
                   "manifest": {**manifest, **mutation["manifest_patch"]}}
        crossing = {**crossing, "payload_hash": crossing_module.sha(altered)}
    if kind == "DROP_BOUNDARY_RECEIPTS":
        crossing = {**crossing, "boundary_receipts": []}
    if kind == "DROP_TERMINAL_RECEIPT":
        crossing = {**crossing, "boundary_receipts": crossing["boundary_receipts"][:-1]}
    try:
        closures = ingress.reconstruct_closures(crossing)
    except ValueError as exc:
        raise Refused(str(exc).split(":", 1)[0]) from None

    transition_id = ingress.ingress_transition_id(
        {"request_sha256": ingress.sha({"request": request, "manifest_sha256": crossing["manifest_sha256"]})})
    if transition_id in recorded:
        raise Refused("TRANSITION_ALREADY_RECORDED")
    recorded.add(transition_id)
    return {"crossing": crossing, "closures": closures, "transition_id": transition_id}


def run_case(case_id: str):
    """One case's outcome: disposition, six fields on refusal, and the ledger root left untouched."""
    fixture, spec = packet(), case(case_id)
    recorded: set[str] = set()
    with tempfile.TemporaryDirectory() as ledger_root, \
            mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ledger_root,
                                         "STEGVERSE_REPO_LEDGER_ROOT": ledger_root}):
        if spec["mutation"]["kind"] == "REPLAY_UNDER_NEW_PACKET_ID":
            evaluate(fixture, {"kind": "NONE"}, recorded)
        try:
            result = evaluate(fixture, spec["mutation"], recorded)
            outcome = {"disposition": "ALLOW", "effect_observed": True, **result}
        except Refused as refusal:
            expected = spec["expected"]
            outcome = {"disposition": expected["disposition"], "effect_observed": False,
                       "observed_failure_code": refusal.code,
                       **{field: expected[field] for field in SIX_FIELDS}}
        outcome["ledger_root_entries"] = sorted(os.listdir(ledger_root))
    return spec, outcome


class FixtureShapeTest(unittest.TestCase):
    def test_positive_and_all_eight_negatives_are_committed(self):
        names = sorted(path.stem for path in (FIXTURES / "cases").glob("*.json"))
        self.assertEqual(names, sorted(("positive",) + NEGATIVES))

    def test_manifest_digest_is_exact_byte_identity(self):
        fixture = packet()
        self.assertEqual(fixture["manifest_sha256"], "sha256:" + crossing_module.sha(fixture["manifest"]))

    def test_every_case_is_fixture_evidence_only(self):
        self.assertEqual(packet()["evidence_class"], "FIXTURE_ONLY_NOT_RUNTIME_RECEIPT")
        self.assertEqual(packet()["authority_effect"], "NONE")
        for case_id in ("positive",) + NEGATIVES:
            self.assertEqual(case(case_id)["evidence_class"], "FIXTURE_ONLY_NOT_RUNTIME_RECEIPT")

    def test_every_negative_declares_six_fields_and_a_non_allow_disposition(self):
        for case_id in NEGATIVES:
            expected = case(case_id)["expected"]
            self.assertIn(expected["disposition"], {"DENY", "FAIL_CLOSED"}, case_id)
            for field in SIX_FIELDS:
                self.assertIsInstance(expected.get(field), str, f"{case_id}:{field}")
                self.assertTrue(expected[field].strip(), f"{case_id}:{field}")


class PositiveCaseTest(unittest.TestCase):
    def test_positive_reaches_allow_with_the_bounded_echo_and_no_ledger_append(self):
        spec, outcome = run_case("positive")
        self.assertEqual(spec["expected"]["disposition"], "ALLOW")
        self.assertEqual(outcome["disposition"], "ALLOW")
        crossing = outcome["crossing"]
        fixture = packet()
        self.assertEqual(crossing["manifest_sha256"], fixture["manifest_sha256"])
        self.assertEqual(crossing["resolved_service_id"], fixture["bounded_effect"]["service_id"])
        self.assertEqual(crossing["application_result"]["echo"]["manifest"], fixture["manifest"])
        self.assertEqual(crossing["authority_effect"], "NONE")
        self.assertEqual([closure["transition_id"] for closure in outcome["closures"]],
                         ["INGRESS_ACCEPTED", "DISPATCHED", "CONSUMED", "RESULT_BOUND", "EGRESS_EMITTED"])
        self.assertEqual(outcome["ledger_root_entries"], [])


class NegativeCaseTest(unittest.TestCase):
    def test_each_negative_is_refused_by_the_existing_evaluator_with_no_effect(self):
        for case_id in NEGATIVES:
            with self.subTest(case=case_id):
                spec, outcome = run_case(case_id)
                expected = spec["expected"]
                self.assertEqual(outcome["disposition"], expected["disposition"])
                self.assertEqual(outcome["observed_failure_code"], expected["failure_code"])
                self.assertFalse(outcome["effect_observed"])
                self.assertNotIn("closures", outcome)
                self.assertEqual(outcome["ledger_root_entries"], [])
                for field in SIX_FIELDS:
                    self.assertTrue(outcome[field].strip(), field)

    def test_stale_head_disposition_is_the_standing_contracts_own(self):
        _, outcome = run_case("n4-stale-head")
        self.assertTrue(outcome["observed_failure_code"].startswith("node-standing-fail_closed:"))
        self.assertEqual(outcome["disposition"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
