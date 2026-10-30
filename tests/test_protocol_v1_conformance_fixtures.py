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
names one mutation of the positive packet and the disposition it declares;
a negative declares DENY or FAIL_CLOSED with the six fields, the positive ALLOW.

What is observed is narrower than what is declared. For a negative, the
evaluator yields only its refusal code: the test checks that the packet was
refused, that the code is the fixture's `failure_code`, and that the temporary
ledger root gained no entry (`refusal_code_and_temp_ledger_no_append`). The
declared disposition and the six fields are fixture expectations, checked for
shape only; they are never copied into the observed outcome, and no runtime
DENY-vs-FAIL_CLOSED classification or six-field refusal is claimed until the
evaluator returns a structured refusal of its own.

The bounded effect is the registered `stegverse-labs.boundary-diagnostic`
echo: the crossing runs for real, writes only to a temporary directory, and
appends to no ledger. `receive`, which does append, is not called for the
positive case or the seven refusals. The SDK's `derive_execution_request` is
not run either (the SDK is not a dependency here), so the request digest is
this fixture's own.

Replay (n2) is not a refusal. `receive` derives the transition id from the
request, so a redelivery under another packet id is the same transition: it
returns the recorded receipts and appends nothing more. n2 therefore drives
the real `receive` twice against temporary ledger roots -- real crossing,
binding check, closure reconstruction and ledger appends; only the absent SDK's
request derivation and result admission are supplied -- and asserts that
idempotent acceptance. The issue lists replay among the refusals; that refusal
is not implemented, and n2 records it as a six-field `spec_gap` owned by the
ingress lane rather than inventing it here.

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
REPLAY = "n2-replay"
NEGATIVES = ("n1-tamper", "n3-forged-identity", "n4-stale-head", "n5-wrong-route",
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


def evaluate(fixture, mutation):
    """Drive one packet through the existing ingress predicates, in binding order.

    Returns the closures the evaluator reconstructed. Raises `Refused` carrying
    the evaluator's own refusal code; nothing here grades a refusal.
    """
    manifest = copy.deepcopy(fixture["manifest"])
    standing = copy.deepcopy(fixture["standing"])
    kind = mutation["kind"]
    if kind == "PATCH_EGRESS":
        manifest["completion"]["egress"].update(mutation["patch"])
    if kind == "REPLACE_STANDING":
        standing = mutation["standing"]

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
        crossing = crossing_module.cross(manifest, registry=registry, packet_id=fixture["packet_id"],
                                         standing=standing)
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
    return {"crossing": crossing, "closures": closures, "transition_id": transition_id}


def run_case(case_id: str):
    return run_spec(case(case_id))


def run_spec(spec):
    """One case's observed outcome: refused or not, the evaluator's own refusal code, and the ledger root.

    Nothing in the outcome is read from `spec["expected"]`; only the mutation drives the run.
    """
    fixture = packet()
    with tempfile.TemporaryDirectory() as ledger_root, \
            mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ledger_root,
                                         "STEGVERSE_REPO_LEDGER_ROOT": ledger_root}):
        try:
            result = evaluate(fixture, spec["mutation"])
            outcome = {"refused": False, **result}
        except Refused as refusal:
            outcome = {"observed_failure_code": refusal.code, "refused": True}
        outcome["ledger_root_entries"] = sorted(os.listdir(ledger_root))
    return spec, outcome


def ingress_request(fixture):
    """The request the SDK would derive, as this fixture's own: the binding read live, the manifest's digest."""
    digest = crossing_module.sha(fixture["manifest"])
    request = {"manifest_declared_destination": binding(fixture["profile"]["profile_id"]),
               "wire_manifest_sha256": digest, "canonical_manifest_sha256": digest,
               "graph_id": fixture["manifest"]["manifest_id"],
               "canonical_task_id": fixture["manifest"]["manifest_id"],
               "processing_capability": fixture["bounded_effect"]["service_id"],
               "route_id": fixture["profile"]["profile_id"],
               "destination_resolution_source": "ORGANIZATION_BOUNDARY"}
    return {**request, "request_sha256": ingress.sha(request)}


def receipts(root: Path):
    directory = root / "receipts"
    return sorted(path.name for path in directory.glob("*.json")) if directory.is_dir() else []


# The carrier-supplied epoch the redelivery is received at: receive() appends nothing without one (#3290).
FIXTURE_HB_EPOCH = 4096


def run_redelivery(spec):
    """The positive packet received, then redelivered under the case's packet id, by the real `receive`."""
    fixture = packet()
    request = ingress_request(fixture)
    registry = load(ROOT / fixture["registry_source"])
    with tempfile.TemporaryDirectory() as directory, \
            mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(Path(directory) / "org"),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(Path(directory) / "repo")}), \
            mock.patch.object(ingress, "derive_execution_request", lambda manifest, boundary: copy.deepcopy(request)), \
            mock.patch.object(ingress, "admit_runtime_result", lambda manifest, request, result: {"admitted": True}):
        deliveries = []
        for packet_id in (fixture["packet_id"], spec["mutation"]["packet_id"]):
            deliveries.append(ingress.receive(copy.deepcopy(fixture["manifest"]), registry=registry,
                                              standing=copy.deepcopy(fixture["standing"]), packet_id=packet_id,
                                              hb_epoch=FIXTURE_HB_EPOCH))
            deliveries[-1]["receipts_after"] = {
                "repository": receipts(Path(directory) / "repo"), "organization": receipts(Path(directory) / "org")}
    return deliveries


def assert_refusal_code_and_temp_ledger_no_append(test, spec, outcome):
    test.assertIs(outcome["refused"], True)
    test.assertEqual(outcome["observed_failure_code"], spec["expected"]["failure_code"])
    test.assertNotIn("closures", outcome)
    test.assertEqual(outcome["ledger_root_entries"], [])


def mutated_copy(case_id: str, directory: str, **expected_patch):
    """A temporary copy of a committed case with its declared expectations patched, read back from disk."""
    spec = case(case_id)
    spec["expected"].update(expected_patch)
    path = Path(directory) / f"{case_id}.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return load(path)


class FixtureShapeTest(unittest.TestCase):
    def test_positive_replay_and_seven_refusals_are_committed(self):
        names = sorted(path.stem for path in (FIXTURES / "cases").glob("*.json"))
        self.assertEqual(names, sorted(("positive", REPLAY) + NEGATIVES))

    def test_manifest_digest_is_exact_byte_identity(self):
        fixture = packet()
        self.assertEqual(fixture["manifest_sha256"], "sha256:" + crossing_module.sha(fixture["manifest"]))

    def test_every_case_is_fixture_evidence_only(self):
        self.assertEqual(packet()["evidence_class"], "FIXTURE_ONLY_NOT_RUNTIME_RECEIPT")
        self.assertEqual(packet()["authority_effect"], "NONE")
        for case_id in ("positive", REPLAY) + NEGATIVES:
            self.assertEqual(case(case_id)["evidence_class"], "FIXTURE_ONLY_NOT_RUNTIME_RECEIPT")

    def test_positive_declares_allow(self):
        self.assertEqual(case("positive")["expected"]["disposition"], "ALLOW")

    def test_every_negative_declares_six_fields_and_a_non_allow_disposition(self):
        for case_id in NEGATIVES:
            expected = case(case_id)["expected"]
            self.assertIn(expected["disposition"], {"DENY", "FAIL_CLOSED"}, case_id)
            for field in SIX_FIELDS:
                self.assertIsInstance(expected.get(field), str, f"{case_id}:{field}")
                self.assertTrue(expected[field].strip(), f"{case_id}:{field}")

    def test_replay_declares_idempotent_redelivery_and_a_six_field_spec_gap(self):
        spec = case(REPLAY)
        self.assertEqual(spec["expected"]["disposition"], "IDEMPOTENT_REDELIVERY")
        gap = spec["spec_gap"]
        self.assertEqual(gap["disposition"], "GAP_NOT_IMPLEMENTED")
        for field in SIX_FIELDS:
            self.assertIsInstance(gap.get(field), str, field)
            self.assertTrue(gap[field].strip(), field)
        # The refusal the issue lists is not in the ingress source, so nothing may claim it was observed.
        source = (ROOT / "resident-runtime/organization_manifest_ingress.py").read_text(encoding="utf-8")
        self.assertNotIn(gap["failure_code"], source)


class PositiveCaseTest(unittest.TestCase):
    def test_positive_is_not_refused_and_echoes_the_bounded_effect_with_no_ledger_append(self):
        _, outcome = run_case("positive")
        self.assertIs(outcome["refused"], False)
        self.assertNotIn("observed_failure_code", outcome)
        crossing = outcome["crossing"]
        fixture = packet()
        # Digest recomputed here from the manifest bytes, not read from the fixture's declared digest.
        self.assertEqual(crossing["manifest_sha256"], "sha256:" + crossing_module.sha(fixture["manifest"]))
        self.assertEqual(crossing["resolved_service_id"], fixture["bounded_effect"]["service_id"])
        self.assertEqual(crossing["application_result"]["echo"]["manifest"], fixture["manifest"])
        self.assertEqual(crossing["authority_effect"], "NONE")
        self.assertEqual([closure["transition_id"] for closure in outcome["closures"]],
                         ["INGRESS_ACCEPTED", "DISPATCHED", "CONSUMED", "RESULT_BOUND", "EGRESS_EMITTED"])
        self.assertEqual(outcome["ledger_root_entries"], [])


class NegativeCaseTest(unittest.TestCase):
    def test_each_negative_refusal_code_and_temp_ledger_no_append(self):
        for case_id in NEGATIVES:
            with self.subTest(case=case_id):
                spec, outcome = run_case(case_id)
                assert_refusal_code_and_temp_ledger_no_append(self, spec, outcome)
                self.assertEqual(set(outcome), {"refused", "observed_failure_code", "ledger_root_entries"})

    def test_stale_head_refusal_code_is_the_standing_contracts_own(self):
        _, outcome = run_case("n4-stale-head")
        self.assertTrue(outcome["observed_failure_code"].startswith("node-standing-fail_closed:"))


class ReplayCaseTest(unittest.TestCase):
    def test_redelivery_under_another_packet_id_is_the_same_transition_with_no_second_append(self):
        spec = case(REPLAY)
        expected = spec["expected"]
        first, second = run_redelivery(spec)
        for delivery in (first, second):
            self.assertNotIn(delivery["disposition"], {"DENY", "FAIL_CLOSED"}, delivery.get("detail"))
        self.assertIs(first["transition_replayed"], False)
        self.assertIs(second["transition_replayed"], expected["transition_replayed"])
        self.assertEqual(first["organization_transition_id"] == second["organization_transition_id"],
                         expected["same_transition_id"])
        self.assertEqual(second["repository_receipt_sha256"], first["repository_receipt_sha256"])
        self.assertEqual(second["organization_receipt_sha256"], first["organization_receipt_sha256"])
        self.assertEqual(len(first["receipts_after"]["repository"]), expected["repository_receipts"])
        self.assertEqual(len(first["receipts_after"]["organization"]), expected["organization_receipts"])
        self.assertEqual(second["receipts_after"], first["receipts_after"])
        self.assertEqual(second["delivery_attempt"]["ingress_packet_id"], spec["mutation"]["packet_id"])
        self.assertIs(second["delivery_attempt"]["is_the_recorded_delivery"], False)


class ExpectationMutationRegressionTest(unittest.TestCase):
    """Declared expectations cannot reach the observed outcome; a wrong declared code is caught."""

    def test_changing_declared_disposition_or_a_six_field_value_leaves_the_observed_outcome_unchanged(self):
        patches = {"disposition": {"disposition": "ALLOW"},
                   "failed_predicate": {"failed_predicate": "MUTATED_PREDICATE"},
                   "next_attempt": {"next_attempt": "mutated next attempt"}}
        for case_id in NEGATIVES:
            _, baseline = run_case(case_id)
            for name, patch in patches.items():
                with self.subTest(case=case_id, mutated=name), tempfile.TemporaryDirectory() as directory:
                    spec = mutated_copy(case_id, directory, **patch)
                    self.assertEqual(spec["expected"][name], patch[name])
                    _, outcome = run_spec(spec)
                    self.assertEqual(outcome, baseline)
                    assert_refusal_code_and_temp_ledger_no_append(self, spec, outcome)

    def test_changing_declared_failure_code_fails_the_refusal_code_assertion(self):
        for case_id in NEGATIVES:
            with self.subTest(case=case_id), tempfile.TemporaryDirectory() as directory:
                spec = mutated_copy(case_id, directory, failure_code="MUTATED_FAILURE_CODE")
                _, outcome = run_spec(spec)
                with self.assertRaises(AssertionError):
                    assert_refusal_code_and_temp_ledger_no_append(self, spec, outcome)


if __name__ == "__main__":
    unittest.main()
