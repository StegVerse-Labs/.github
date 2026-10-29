"""Protocol v1.0 packet conformance, as fixtures on the existing SDK:ManifestIngress path.

StegVerse-Labs/.github#3369 asks for one positive packet and eight negatives --
tamper, replay, forged identity, stale head, wrong route, missing authority,
missing receipts, reconstruction failure -- run through the existing evaluator,
not a new one. The path is the one `org-runtime/interlock-intr.json` already
binds for `sdk-manifest-ingress` (SDK#566), entered at its real receiving
operation:

    resident-runtime/organization_manifest_ingress.py::receive
      bound_here -> sdk_manifest_crossing.py::cross -> process_boundary.py
      -> node_standing.py::require -> reconstruct_closures -> both ledger levels

The fixtures live under
`org-kernel/organization-ledger/fixtures/protocol-v1-conformance/`. Each case
names one mutation of the positive packet, what it actually exercises
(`covers`), and the #3369 item it is filed under with an honest status.

Every negative is driven through the real `receive()` against temporary ledger
roots. Only the absent SDK's `derive_execution_request` and
`admit_runtime_result` are supplied; the crossing, the boundary subprocess,
standing, the binding check, closure reconstruction and both ledger appends
are the real code. `receive()` does not refuse silently: each refusal is
recorded at both ledger levels as `ORGANIZATION_SDK_MANIFEST_INGRESS_REFUSED`
and returned as FAIL_CLOSED with `received: False`, `refusal_recorded: True`
and `authority_effect: NONE_REFUSAL_ONLY`. The test asserts that no-effect
shape, reads the refusal receipts back from the temporary roots, checks their
digests and that they carry the case's failure code, and checks that no
ingress transition receipt was written.

A case's `expected` block is not hand-written. It is the six fields
`receive()` returned for that case (`disposition`, `failed_predicate`,
`failure_code` -- the returned `detail` --, `received`, `refusal_recorded`,
`authority_effect`) and the disposition and class of the refusal record it
appended, written by `python3 -m tests.test_protocol_v1_conformance_fixtures
--regenerate` (run from the repository root, so `tests/__init__.py` declares
the POSIX ledger locus as `tests/conftest.py` does under pytest) and asserted
equal to a live run here. The protocol's other
refusal fields (`required_evidence_or_repair`, `retry_entrypoint`,
`owning_existing_goal`, `next_attempt`) are not emitted by `receive()` on these
paths, so no case claims them as observed.

Items the real path cannot express -- a stale head or fence, a submitter
whose KV/SKAP verification is bound to the manifest, missing authority, a
redelivery answered before its endpoint runs, a payload whose `payload_hash`
is left unchanged -- are recorded as six-field `spec_gap` entries, each
checked to name a code that exists nowhere in the ingress source, rather than
being invented here. Replay itself is not one of them: idempotent redelivery
is the specified behaviour (I-10), and n2 covers "no duplicate effect" at both
ledger levels. Each registered task a gap names as its owner is checked to
exist in `data/canonical-task-records/`.

Fixture evidence only. Nothing here is runtime ALLOW, no live receipt is
minted, and admission, claim/fence and protected runs stay with the Registry
owner.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "org-kernel/organization-ledger/fixtures/protocol-v1-conformance"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
#: The six fields `receive()` returns for a refusal, as the case's `expected` records them.
OBSERVED_FIELDS = ("disposition", "failed_predicate", "failure_code", "received",
                   "refusal_recorded", "authority_effect")
REPLAY = "n2-replay"
NON_GATING = "n9-non-gating-propagation-failure"
NEGATIVES = ("n1-tamper", "n3-wrong-receiving-operation", "n4-generation-not-successor",
             "n5-wrong-route", "n6-ingress-resolution-absent", "n7-missing-receipts",
             "n8-reconstruction-failure")
ALL_CASES = ("positive", REPLAY, NON_GATING) + NEGATIVES
#: Every #3369 item, and the one case it is filed under.
ISSUE_ITEMS = {"POSITIVE": "positive", "TAMPER": "n1-tamper", "REPLAY": REPLAY,
               "FORGED_IDENTITY": "n3-wrong-receiving-operation",
               "STALE_HEAD_OR_FENCE": "n4-generation-not-successor",
               "WRONG_ROUTE": "n5-wrong-route",
               "MISSING_AUTHORITY": "n6-ingress-resolution-absent",
               "MISSING_RECEIPTS": "n7-missing-receipts",
               "RECONSTRUCTION_FAILURE_GATING": "n8-reconstruction-failure",
               "RECONSTRUCTION_FAILURE_NON_GATING": NON_GATING}
GAP_SOURCES = ("resident-runtime/organization_manifest_ingress.py",
               "resident-runtime/sdk_manifest_crossing.py",
               "org-boundary/runtime/node_standing.py")
TASK_RECORDS = ROOT / "data/canonical-task-records"
#: A registered task id named inside an owner field, e.g. ORGANIZATION-BATCH-CUSTODY-REPLAY-001.
TASK_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}\b")
MASTER_RECORDS_PROPAGATION = ROOT / "resident-runtime/submit_org_transition_to_master_records.py"
ORG_CONTRACT = ROOT / ".stegverse/transition-ledger/org-contract.json"

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


def case_path(case_id: str) -> Path:
    return FIXTURES / "cases" / f"{case_id}.json"


def case(case_id: str):
    return load(case_path(case_id))


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


def ingress_request(fixture, manifest=None):
    """The request the SDK would derive, as this fixture's own: the binding read live, the manifest's digest."""
    manifest = fixture["manifest"] if manifest is None else manifest
    digest = crossing_module.sha(manifest)
    request = {"manifest_declared_destination": binding(fixture["profile"]["profile_id"]),
               "wire_manifest_sha256": digest, "canonical_manifest_sha256": digest,
               "graph_id": manifest["manifest_id"],
               "canonical_task_id": manifest["manifest_id"],
               "processing_capability": fixture["bounded_effect"]["service_id"],
               "route_id": fixture["profile"]["profile_id"],
               "destination_resolution_source": "ORGANIZATION_BOUNDARY"}
    return {**request, "request_sha256": ingress.sha(request)}


def cross_positive():
    """The positive packet's crossing alone, for the bounded-effect echo bytes. Appends nothing by construction."""
    fixture = packet()
    ingress.bound_here({"manifest_declared_destination": binding(fixture["profile"]["profile_id"])})
    crossing = crossing_module.cross(copy.deepcopy(fixture["manifest"]), registry=load(ROOT / fixture["registry_source"]),
                                     packet_id=fixture["packet_id"], standing=copy.deepcopy(fixture["standing"]))
    return crossing, ingress.reconstruct_closures(crossing)


def readback(level_root: Path):
    """Every receipt file under one temporary ledger level, parsed, with the level's HEAD."""
    directory = level_root / "receipts"
    rows = [load(path) for path in sorted(directory.glob("*.json"))] if directory.is_dir() else []
    head = level_root / "HEAD.json"
    return {"receipts": rows, "head": load(head) if head.is_file() else None}


def ledger_bytes(directory: Path):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in sorted(directory.rglob("*")) if path.is_file()}


class LedgerRoots:
    """Temporary repository and organization ledger roots, with only the absent SDK supplied."""

    def __init__(self, request):
        self.request = request

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo, self.org = self.root / "repo", self.root / "org"
        self._patches = [
            mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(self.org),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo)}),
            mock.patch.object(ingress, "derive_execution_request",
                              lambda manifest, boundary: copy.deepcopy(self.request)),
            mock.patch.object(ingress, "admit_runtime_result",
                              lambda manifest, request, result: {"admitted": True}),
        ]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc):
        for patch in reversed(self._patches):
            patch.stop()
        self._tmp.cleanup()
        return False


def drive(spec):
    """One case through the real `receive()`: its returned result and both ledger levels read back.

    Only the mutation drives the run; nothing is read from `spec["expected"]`.
    """
    fixture = packet()
    mutation = spec["mutation"]
    kind = mutation["kind"]
    manifest = copy.deepcopy(fixture["manifest"])
    standing = copy.deepcopy(fixture["standing"])
    if kind == "PATCH_EGRESS":
        manifest["completion"]["egress"].update(mutation["patch"])
    if kind == "REPLACE_STANDING":
        standing = copy.deepcopy(mutation["standing"])
    request = ingress_request(fixture, manifest)
    if kind == "PATCH_RECEIVING_OPERATION":
        request["manifest_declared_destination"]["receiving_operation"].update(mutation["patch"])
    if kind == "DROP_RESOLUTION":
        request.pop("manifest_declared_destination")

    real_cross = ingress.crossing_module.cross

    def cross(*args, **kwargs):
        crossing = real_cross(*args, **kwargs)
        if kind == "TAMPER_PAYLOAD_AFTER_CROSSING":
            # The payload is altered after the boundary bound its receipts, and
            # its digest is honestly recomputed from the altered bytes.
            echo = crossing["application_result"]["echo"]
            altered = {**echo, "manifest": {**echo["manifest"], **mutation["manifest_patch"]}}
            crossing = {**crossing, "application_result": {"echo": altered},
                        "payload_hash": crossing_module.sha(altered)}
        if kind == "DROP_BOUNDARY_RECEIPTS":
            crossing = {**crossing, "boundary_receipts": []}
        if kind == "DROP_TERMINAL_RECEIPT":
            crossing = {**crossing, "boundary_receipts": crossing["boundary_receipts"][:-1]}
        return crossing

    with LedgerRoots(request) as roots, mock.patch.object(ingress.crossing_module, "cross", cross):
        result = ingress.receive(manifest, registry=load(ROOT / fixture["registry_source"]),
                                 standing=standing, packet_id=fixture["packet_id"])
        return result, {"repository": readback(roots.repo), "organization": readback(roots.org)}


def observed(result, ledgers):
    """What a case's `expected` block records, taken from a live run."""
    fields = {"disposition": result.get("disposition"), "failed_predicate": result.get("failed_predicate"),
              "failure_code": result.get("detail"), "received": result.get("received"),
              "refusal_recorded": result.get("refusal_recorded"),
              "authority_effect": result.get("authority_effect")}
    repository = ledgers["repository"]["receipts"]
    record = {"disposition": repository[0]["evidence"].get("disposition"),
              "transition_class": repository[0]["transition_class"]} if repository else None
    return fields, record


def run_redelivery(spec):
    """The positive packet received, then redelivered under the case's packet id, by the real `receive`."""
    fixture = packet()
    registry = load(ROOT / fixture["registry_source"])
    with LedgerRoots(ingress_request(fixture)) as roots:
        deliveries = []
        for packet_id in (fixture["packet_id"], spec["mutation"]["packet_id"]):
            deliveries.append(ingress.receive(copy.deepcopy(fixture["manifest"]), registry=registry,
                                              standing=copy.deepcopy(fixture["standing"]), packet_id=packet_id))
            deliveries[-1]["ledgers_after"] = {
                "repository": readback(roots.repo), "organization": readback(roots.org)}
    return deliveries


def run_non_gating_propagation(spec):
    """Receive the positive packet, fail its Master Records propagation for real, then redeliver.

    The propagation is the real `submit_org_transition_to_master_records.py`,
    run on the organization receipt just appended, with no mesh location
    supplied by a materializer -- the case's mutation. Both ledger levels are
    read as bytes before and after.
    """
    fixture = packet()
    registry = load(ROOT / fixture["registry_source"])
    with LedgerRoots(ingress_request(fixture)) as roots:
        first = ingress.receive(copy.deepcopy(fixture["manifest"]), registry=registry,
                                standing=copy.deepcopy(fixture["standing"]), packet_id=fixture["packet_id"])
        before = ledger_bytes(roots.root)
        org_receipt = roots.org / "receipts" / (first["organization_receipt_sha256"].split(":", 1)[1] + ".json")
        receipt = load(org_receipt)
        standing_file = roots.root / "standing.json"
        standing_file.write_text(json.dumps(fixture["standing"]), encoding="utf-8")
        before["standing.json"] = standing_file.read_bytes()
        command = [sys.executable, str(MASTER_RECORDS_PROPAGATION), "--org-receipt", str(org_receipt),
                   "--predecessor-ecosystem-state-sha256", receipt["predecessor_org_state_sha256"],
                   "--successor-ecosystem-state-sha256", receipt["successor_org_state_sha256"],
                   "--standing", str(standing_file)]
        if mutation_mesh_root := spec["mutation"].get("mesh_root"):
            command += ["--mesh-root", mutation_mesh_root]
        completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, check=False)
        after = ledger_bytes(roots.root)
        second = ingress.receive(copy.deepcopy(fixture["manifest"]), registry=registry,
                                 standing=copy.deepcopy(fixture["standing"]), packet_id=fixture["packet_id"])
        final = ledger_bytes(roots.root)
    propagation = json.loads(completed.stdout.strip().splitlines()[-1])
    return {"first": first, "second": second, "propagation": propagation,
            "propagation_returncode": completed.returncode,
            "ledger_unchanged_by_failed_propagation": before == after,
            "ledger_unchanged_by_redelivery": after == final}


def non_gating_observed(run):
    return {"propagation_disposition": run["propagation"].get("disposition"),
            "propagation_failed_predicate": run["propagation"].get("failed_predicate"),
            "propagation_status": run["propagation"].get("status"),
            "propagation_consequence_committed": run["propagation"].get("consequence_committed"),
            "ledger_unchanged_by_failed_propagation": run["ledger_unchanged_by_failed_propagation"],
            "transition_replayed_after_failed_propagation": run["second"].get("transition_replayed"),
            "same_organization_receipt_after_failed_propagation":
                run["second"].get("organization_receipt_sha256") == run["first"].get("organization_receipt_sha256"),
            "master_records_organization_record_observed":
                run["first"].get("master_records_organization_record_observed")}


def assert_matches_expected(test, spec, fields, record):
    test.assertEqual(fields, spec["expected"], spec["case_id"])
    test.assertEqual(record, spec["expected_refusal_record"], spec["case_id"])


def mutated_copy(case_id: str, directory: str, **expected_patch):
    """A temporary copy of a committed case with its recorded expectations patched, read back from disk."""
    spec = case(case_id)
    spec["expected"].update(expected_patch)
    path = Path(directory) / f"{case_id}.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return load(path)


def regenerate():
    """Write each case's `expected` block from a live run of the real `receive()`."""
    for case_id in NEGATIVES:
        spec = case(case_id)
        result, ledgers = drive(spec)
        spec["expected"], spec["expected_refusal_record"] = observed(result, ledgers)
        case_path(case_id).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    spec = case(NON_GATING)
    spec["expected"] = non_gating_observed(run_non_gating_propagation(spec))
    case_path(NON_GATING).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")


_LIVE = {}


def live(case_id: str):
    """One live run per case per process; the run reads only the committed mutation."""
    if case_id not in _LIVE:
        _LIVE[case_id] = drive(case(case_id))
    return _LIVE[case_id]


class FixtureShapeTest(unittest.TestCase):
    def test_positive_replay_non_gating_and_seven_refusals_are_committed(self):
        names = sorted(path.stem for path in (FIXTURES / "cases").glob("*.json"))
        self.assertEqual(names, sorted(ALL_CASES))

    def test_manifest_digest_is_exact_byte_identity(self):
        fixture = packet()
        self.assertEqual(fixture["manifest_sha256"], "sha256:" + crossing_module.sha(fixture["manifest"]))

    def test_every_case_is_fixture_evidence_only(self):
        self.assertEqual(packet()["evidence_class"], "FIXTURE_ONLY_NOT_RUNTIME_RECEIPT")
        self.assertEqual(packet()["authority_effect"], "NONE")
        for case_id in ALL_CASES:
            self.assertEqual(case(case_id)["evidence_class"], "FIXTURE_ONLY_NOT_RUNTIME_RECEIPT")

    def test_positive_declares_allow(self):
        self.assertEqual(case("positive")["expected"]["disposition"], "ALLOW")

    def test_every_issue_item_is_filed_once_with_an_honest_status(self):
        filed = {}
        for case_id in ALL_CASES:
            spec = case(case_id)
            self.assertEqual(spec["case_id"], case_id)
            self.assertIsInstance(spec["covers"], str)
            self.assertTrue(spec["covers"].strip(), case_id)
            filed.setdefault(spec["issue_3369_item"], []).append(case_id)
            status = spec["issue_3369_item_status"]
            self.assertIn(status, {"COVERED", "COVERED_WITH_SPEC_GAP", "SPEC_GAP"}, case_id)
            self.assertEqual("spec_gap" in spec, status != "COVERED", case_id)
        self.assertEqual(filed, {item: [case_id] for item, case_id in ISSUE_ITEMS.items()})

    def test_every_negative_expectation_is_the_generated_observed_shape(self):
        for case_id in NEGATIVES:
            spec = case(case_id)
            self.assertEqual(tuple(sorted(spec["expected"])), tuple(sorted(OBSERVED_FIELDS)), case_id)
            self.assertEqual(spec["expected_source"], "GENERATED_FROM_REAL_RECEIVE", case_id)

    def test_every_spec_gap_is_six_fields_and_names_no_implemented_code(self):
        sources = "".join((ROOT / path).read_text(encoding="utf-8") for path in GAP_SOURCES)
        gaps = 0
        for case_id in ALL_CASES:
            gap = case(case_id).get("spec_gap")
            if gap is None:
                continue
            gaps += 1
            self.assertEqual(gap["disposition"], "GAP_NOT_IMPLEMENTED", case_id)
            self.assertIsInstance(gap.get("issue_3369_item"), str, case_id)
            for field in SIX_FIELDS:
                self.assertIsInstance(gap.get(field), str, f"{case_id}:{field}")
                self.assertTrue(gap[field].strip(), f"{case_id}:{field}")
            # A gap is not implemented, so nothing may claim it was observed.
            self.assertNotIn(gap["failure_code"], sources, case_id)
        self.assertEqual(gaps, 5)

    def test_replay_declares_idempotent_redelivery(self):
        spec = case(REPLAY)
        self.assertEqual(spec["expected"]["disposition"], "IDEMPOTENT_REDELIVERY")
        # Redelivery is idempotent by specification (I-10); the gap is the order
        # in which receive() processes a redelivery, not a missing refusal.
        self.assertEqual(spec["issue_3369_item_status"], "COVERED_WITH_SPEC_GAP")
        self.assertEqual(spec["spec_gap"]["failure_code"], "REDELIVERY_REPROCESSED_BEFORE_DEDUPLICATION")

    def test_every_registered_owner_a_spec_gap_names_exists(self):
        named = 0
        for case_id in ALL_CASES:
            gap = case(case_id).get("spec_gap")
            if gap is None:
                continue
            for task_id in TASK_ID.findall(gap["owning_existing_goal"]):
                named += 1
                self.assertTrue((TASK_RECORDS / f"{task_id}.json").is_file(), f"{case_id}:{task_id}")
        self.assertGreater(named, 0)

    def test_no_spec_gap_waits_on_a_device_or_node_attestation_gate(self):
        # Device attestation is prohibited as a gate by the global invariants;
        # submitter verification belongs to the KV/SKAP Vault.
        invariants = load(ROOT / "data/task-registry-global-invariants.json")
        self.assertIn("NO_DEVICE_ATTESTATION_OR_PHYSICAL_DEVICE_IDENTITY_GATE", json.dumps(invariants))
        for case_id in ALL_CASES:
            gap = case(case_id).get("spec_gap") or {}
            self.assertNotIn("attestation owner", gap.get("next_attempt", ""), case_id)
        self.assertEqual(case("n3-wrong-receiving-operation")["spec_gap"]["failure_code"],
                         "SUBMITTER_KV_SKAP_VERIFICATION_NOT_BOUND_AT_INGRESS")

    def test_payload_binding_gap_is_recorded_on_tamper(self):
        self.assertEqual(case("n1-tamper")["spec_gap"]["failure_code"],
                         "PAYLOAD_HASH_NOT_RECOMPUTED_FROM_MANIFEST_AT_INGRESS")


class PositiveCaseTest(unittest.TestCase):
    def test_positive_crossing_echoes_the_bounded_effect_and_reconstructs(self):
        crossing, closures = cross_positive()
        fixture = packet()
        # Digest recomputed here from the manifest bytes, not read from the fixture's declared digest.
        self.assertEqual(crossing["manifest_sha256"], "sha256:" + crossing_module.sha(fixture["manifest"]))
        self.assertEqual(crossing["resolved_service_id"], fixture["bounded_effect"]["service_id"])
        self.assertEqual(crossing["application_result"]["echo"]["manifest"], fixture["manifest"])
        self.assertEqual(crossing["authority_effect"], "NONE")
        self.assertEqual([closure["transition_id"] for closure in closures],
                         ["INGRESS_ACCEPTED", "DISPATCHED", "CONSUMED", "RESULT_BOUND", "EGRESS_EMITTED"])

    def test_positive_expectation_is_what_real_receive_returns_against_temporary_roots(self):
        fixture = packet()
        with LedgerRoots(ingress_request(fixture)):
            result = ingress.receive(copy.deepcopy(fixture["manifest"]), registry=load(ROOT / fixture["registry_source"]),
                                     standing=copy.deepcopy(fixture["standing"]), packet_id=fixture["packet_id"])
        self.assertEqual(result["disposition"], case("positive")["expected"]["disposition"], result.get("detail"))
        self.assertEqual(result["authority_effect"], "NONE_RECEIVING_OPERATION_ONLY")
        self.assertIs(result["master_records_organization_record_observed"], False)


class NegativeCaseTest(unittest.TestCase):
    def test_each_negative_matches_the_expectation_generated_from_real_receive(self):
        for case_id in NEGATIVES:
            with self.subTest(case=case_id):
                assert_matches_expected(self, case(case_id), *observed(*live(case_id)))

    def test_each_negative_has_the_real_no_effect_shape(self):
        for case_id in NEGATIVES:
            with self.subTest(case=case_id):
                result, _ = live(case_id)
                self.assertEqual(result["disposition"], "FAIL_CLOSED")
                self.assertIs(result["received"], False)
                self.assertIs(result["refusal_recorded"], True)
                self.assertEqual(result["authority_effect"], "NONE_REFUSAL_ONLY")
                self.assertIs(result["organization_receipt_observed"], False)
                self.assertEqual(result["refusal_transition_class"], ingress.REFUSED_CLASS)
                for absent in ("organization_transition_id", "organization_receipt_sha256",
                               "repository_receipt_sha256", "transition_closures", "sdk_admitted_result"):
                    self.assertNotIn(absent, result)

    def test_each_negative_refusal_is_read_back_from_both_temporary_ledger_roots(self):
        for case_id in NEGATIVES:
            with self.subTest(case=case_id):
                spec = case(case_id)
                result, ledgers = live(case_id)
                repository = ledgers["repository"]["receipts"]
                organization = ledgers["organization"]["receipts"]
                self.assertEqual(len(repository), 1)
                self.assertEqual(len(organization), 1)
                (repo_receipt,), (org_receipt,) = repository, organization
                # No ingress transition or commit receipt: the only record is the refusal.
                self.assertEqual(repo_receipt["transition_class"], ingress.REFUSED_CLASS)
                self.assertNotEqual(repo_receipt["transition_class"], ingress.OPERATION_ID)
                self.assertEqual(repo_receipt["transition_id"], result["refusal_transition_id"])
                self.assertEqual(repo_receipt["receipt_sha256"], result["refusal_repository_receipt_sha256"])
                self.assertEqual(ledgers["repository"]["head"]["receipt_sha256"], repo_receipt["receipt_sha256"])
                body = {key: value for key, value in repo_receipt.items() if key != "receipt_sha256"}
                self.assertEqual(ingress.repository_ledger.sha(body), repo_receipt["receipt_sha256"])
                evidence = repo_receipt["evidence"]
                self.assertEqual(evidence["detail"], spec["expected"]["failure_code"])
                self.assertEqual(evidence["failed_predicate"], spec["expected"]["failed_predicate"])
                self.assertEqual(evidence["disposition"], "DENY")
                self.assertIs(evidence["received"], False)
                self.assertEqual(evidence["submitted_manifest_sha256"], repo_receipt["predecessor_state_sha256"])

                self.assertEqual(org_receipt["receipt_sha256"], result["refusal_organization_receipt_sha256"])
                self.assertEqual(ledgers["organization"]["head"]["receipt_sha256"], org_receipt["receipt_sha256"])
                body = {key: value for key, value in org_receipt.items() if key != "receipt_sha256"}
                self.assertEqual(ingress.organization_ledger.sha(body), org_receipt["receipt_sha256"])
                self.assertEqual(org_receipt["repo_receipt_sha256"], repo_receipt["receipt_sha256"])
                self.assertEqual(org_receipt["repo_transition_id"], result["refusal_transition_id"])
                self.assertEqual(org_receipt["boundary_evidence"]["disposition"], "DENY")
                self.assertEqual(org_receipt["boundary_evidence"]["failed_predicate"],
                                 spec["expected"]["failed_predicate"])

    def test_generation_successor_refusal_code_is_the_standing_contracts_own(self):
        result, _ = live("n4-generation-not-successor")
        self.assertEqual(result["detail"],
                         "node-standing-fail_closed:non-genesis-predecessor-invalid:generation-not-successor")


class ReplayCaseTest(unittest.TestCase):
    def test_redelivery_under_another_packet_id_is_the_same_transition_with_no_second_append(self):
        spec = case(REPLAY)
        expected = spec["expected"]
        first, second = run_redelivery(spec)
        self.assertEqual(first["disposition"], "ALLOW", first.get("detail"))
        self.assertNotIn(second["disposition"], {"DENY", "FAIL_CLOSED"}, second.get("detail"))
        self.assertIs(first["transition_replayed"], False)
        self.assertIs(second["transition_replayed"], expected["transition_replayed"])
        self.assertEqual(first["organization_transition_id"] == second["organization_transition_id"],
                         expected["same_transition_id"])
        self.assertEqual(second["repository_receipt_sha256"], first["repository_receipt_sha256"])
        self.assertEqual(second["organization_receipt_sha256"], first["organization_receipt_sha256"])

        repository = first["ledgers_after"]["repository"]["receipts"]
        organization = first["ledgers_after"]["organization"]["receipts"]
        self.assertEqual(len(repository), expected["repository_receipts"])
        self.assertEqual(len(organization), expected["organization_receipts"])
        (repo_receipt,), (org_receipt,) = repository, organization
        self.assertEqual(repo_receipt["receipt_sha256"], first["repository_receipt_sha256"])
        self.assertEqual(repo_receipt["transition_id"], first["organization_transition_id"])
        self.assertEqual(repo_receipt["transition_class"], ingress.OPERATION_ID)
        self.assertEqual(repo_receipt["evidence"]["request_sha256"], first["request_sha256"])
        self.assertEqual(org_receipt["receipt_sha256"], first["organization_receipt_sha256"])
        self.assertEqual(org_receipt["repo_receipt_sha256"], repo_receipt["receipt_sha256"])
        self.assertEqual(org_receipt["boundary_evidence"]["ingress_packet_id"], packet()["packet_id"])
        self.assertEqual(second["ledgers_after"], first["ledgers_after"])
        self.assertEqual(second["delivery_attempt"]["ingress_packet_id"], spec["mutation"]["packet_id"])
        self.assertIs(second["delivery_attempt"]["is_the_recorded_delivery"], False)


class NonGatingPropagationCaseTest(unittest.TestCase):
    def test_failed_master_records_propagation_leaves_the_transition_in_place(self):
        spec = case(NON_GATING)
        self.assertIs(load(ORG_CONTRACT)["propagation_gates_organization_runtime_reality"], False)
        run = run_non_gating_propagation(spec)
        self.assertEqual(non_gating_observed(run), spec["expected"])
        self.assertEqual(run["propagation_returncode"], 1)
        self.assertEqual(run["first"]["disposition"], "ALLOW", run["first"].get("detail"))
        self.assertIs(run["second"]["transition_replayed"], True)
        self.assertIs(run["ledger_unchanged_by_redelivery"], True)


class ExpectationMutationRegressionTest(unittest.TestCase):
    """Recorded expectations cannot reach the observed outcome; a wrong recorded value is caught."""

    def test_changing_a_recorded_field_fails_the_live_equality(self):
        patches = {"disposition": "ALLOW", "failed_predicate": "MUTATED_PREDICATE",
                   "failure_code": "MUTATED_FAILURE_CODE", "received": True,
                   "refusal_recorded": False, "authority_effect": "NONE"}
        for case_id in NEGATIVES:
            fields, record = observed(*live(case_id))
            for name, value in patches.items():
                with self.subTest(case=case_id, mutated=name), tempfile.TemporaryDirectory() as directory:
                    spec = mutated_copy(case_id, directory, **{name: value})
                    self.assertEqual(spec["expected"][name], value)
                    with self.assertRaises(AssertionError):
                        assert_matches_expected(self, spec, fields, record)

    def test_a_recorded_expectation_does_not_reach_the_run(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = mutated_copy("n3-wrong-receiving-operation", directory, disposition="ALLOW",
                                failed_predicate="MUTATED_PREDICATE")
            fields, record = observed(*drive(spec))
        self.assertEqual((fields, record), observed(*live("n3-wrong-receiving-operation")))


if __name__ == "__main__":
    if sys.argv[1:] == ["--regenerate"]:
        regenerate()
    else:
        unittest.main()
