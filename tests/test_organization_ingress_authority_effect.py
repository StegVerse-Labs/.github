"""Ingress refuses a declared authority effect other than NONE before the crossing.

`sdk_manifest_crossing.crossing_packet` copies `transition.authority_effect`
onto the InTr envelope verbatim, and `process_boundary.py` passes it through to
its result, while the boundary document says an effect is
`DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS` and both ledger appends record
"NONE". Nothing on the `receive()` path checked it (StegVerse-Labs/.github#3369,
"missing authority"). Until a landed warrant receipt can be verified at
ingress, `receive()` refuses any declared effect that is not NONE -- an absent
`transition` or `authority_effect` is NONE, as the crossing reads it -- under
`DECLARED_AUTHORITY_EFFECT_IS_NONE_UNTIL_A_WARRANT_RECEIPT_BINDS`, before
`cross()` is called, and records the refusal at both ledger levels.

These cases drive the real `receive()`, the real crossing and the real
`process_boundary.py` subprocess on the boundary-local diagnostic service,
against temporary ledger roots. Only the SDK's request derivation, the binding
resolution and result admission are stubbed. `cross` is wrapped to count its
calls, so "before the crossing" is observed, not inferred.

Source validation only. No authority effect is claimed.
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
REVISION = "0123456789abcdef0123456789abcdef01234567"

_spec = importlib.util.spec_from_file_location(
    "organization_ingress_authority_effect_subject",
    ROOT / "resident-runtime/organization_manifest_ingress.py")
ingress = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingress)
crossing_module = ingress.crossing_module

PREDICATE = "DECLARED_AUTHORITY_EFFECT_IS_NONE_UNTIL_A_WARRANT_RECEIPT_BINDS"
FAILURE_CODE = "AUTHORITY_EFFECT_NOT_WARRANTED_AT_INGRESS"
OWNING_GOAL = "SDK-MANIFEST-ECOSYSTEM-TRANSITION-DISPOSITION-001"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))

MANIFEST = {
    "processing": {"capability": "ecosystem_diagnostic",
                   "route_id": "stegverse.route.ecosystem-diagnostic.v1"},
    "completion": {"egress": {"final_stegverse_transition_surface": "boundary_diagnostic",
                              "transport": "INTERLOCK_INTR",
                              "far_side_transition_required": True}},
    "transition": {"authority_effect": "NONE"},
    "data": {"value": 1},
}
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "authority-effect-test",
            "generation": 1, "predecessor": None}

#: Declared effects the operation must refuse. Each is something a submitter
#: could put on the envelope; none is the string NONE.
REFUSED_EFFECTS = ("GRANTS_EXECUTION_AUTHORITY", "NONE_REQUEST_ONLY", "none", "", None, 0,
                   ["NONE"], {"effect": "NONE"})


def request(manifest) -> dict:
    digest = ingress.sha(manifest)
    return {"request_sha256": ingress.sha({"manifest": digest}), "wire_manifest_sha256": digest,
            "canonical_manifest_sha256": digest, "graph_id": "graph-1",
            "canonical_task_id": "task-1", "processing_capability": "ecosystem_diagnostic",
            "route_id": "stegverse.route.ecosystem-diagnostic.v1",
            "destination_resolution_source": "ORGANIZATION_BOUNDARY"}


def with_transition(transition):
    manifest = copy.deepcopy(MANIFEST)
    manifest["transition"] = transition
    return manifest


def without_transition():
    manifest = copy.deepcopy(MANIFEST)
    manifest.pop("transition")
    return manifest


class AuthorityEffectCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo", base / "org"
        self.crossings = []
        self.binding = lambda r: {"operation": "receive"}
        real_cross = crossing_module.cross

        def cross(*args, **kwargs):
            self.crossings.append(args[0])
            return real_cross(*args, **kwargs)

        patches = [
            mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                         "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)}),
            mock.patch.object(ingress, "derive_execution_request", lambda m, b: request(m)),
            mock.patch.object(ingress, "bound_here", lambda r: self.binding(r)),
            mock.patch.object(ingress, "admit_runtime_result", lambda *a: {"admitted": True}),
            mock.patch.object(crossing_module, "cross", cross),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def receive(self, manifest):
        return ingress.receive(manifest, registry=REGISTRY, standing=dict(STANDING),
                               packet_id="authority-effect-1")

    def receipts(self, root: Path) -> list[dict]:
        directory = root / "receipts"
        return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))] \
            if directory.is_dir() else []

    def assertRefusedBeforeCrossing(self, result: dict, manifest) -> None:
        self.assertEqual(result["disposition"], "FAIL_CLOSED", result)
        self.assertEqual(result["failed_predicate"], PREDICATE, result)
        self.assertEqual(result["failure_code"], FAILURE_CODE, result)
        self.assertTrue(result["detail"].startswith(FAILURE_CODE + ":"), result["detail"])
        for field in SIX_FIELDS:
            self.assertTrue(result.get(field), field)
        self.assertEqual(result["owning_existing_goal"], OWNING_GOAL)
        self.assertEqual(result["retry_entrypoint"], ingress.RETRY_ENTRYPOINT)
        self.assertIs(result["next_attempt"]["awaits_an_external_machine"], False)
        self.assertIs(result["received"], False)
        self.assertIs(result["refusal_recorded"], True)
        self.assertIs(result["organization_receipt_observed"], False)
        self.assertEqual(result["authority_effect"], "NONE_REFUSAL_ONLY")
        self.assertEqual(result["request_sha256"], request(manifest)["request_sha256"])
        # The crossing -- and so the boundary and its endpoint -- never ran.
        self.assertEqual(self.crossings, [])
        # Recorded at both levels as a refusal, and nothing else.
        repository, = self.receipts(self.repo_root)
        organization, = self.receipts(self.org_root)
        self.assertEqual(repository["transition_class"], ingress.REFUSED_CLASS)
        self.assertEqual(repository["receipt_sha256"], result["refusal_repository_receipt_sha256"])
        self.assertEqual(repository["evidence"]["failed_predicate"], PREDICATE)
        self.assertEqual(repository["evidence"]["detail"], result["detail"])
        self.assertEqual(repository["evidence"]["disposition"], "DENY")
        self.assertEqual(repository["authority_effect"], "NONE")
        self.assertEqual(organization["receipt_sha256"], result["refusal_organization_receipt_sha256"])
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])
        self.assertEqual(organization["boundary_evidence"]["failed_predicate"], PREDICATE)
        self.assertEqual(organization["authority_effect"], "NONE")


class RefusedEffectTests(AuthorityEffectCase):
    def test_each_non_none_declared_effect_is_refused_before_the_crossing(self):
        for effect in REFUSED_EFFECTS:
            with self.subTest(effect=effect):
                self.setUp()
                manifest = with_transition({"authority_effect": effect})
                result = self.receive(manifest)
                self.assertRefusedBeforeCrossing(result, manifest)
                self.assertEqual(result["detail"], FAILURE_CODE + ":declared transition.authority_effect "
                                 + json.dumps(effect, sort_keys=True))

    def test_a_transition_that_is_not_an_object_is_refused(self):
        manifest = with_transition("GRANTS_EXECUTION_AUTHORITY")
        result = self.receive(manifest)
        self.assertRefusedBeforeCrossing(result, manifest)
        self.assertEqual(result["detail"], FAILURE_CODE + ":transition is not an object")

    def test_a_redelivered_refusal_is_recorded_once(self):
        manifest = with_transition({"authority_effect": "GRANTS_EXECUTION_AUTHORITY"})
        first = self.receive(manifest)
        second = self.receive(copy.deepcopy(manifest))
        self.assertEqual(first["refusal_repository_receipt_sha256"],
                         second["refusal_repository_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(len(self.receipts(self.org_root)), 1)
        self.assertEqual(self.crossings, [])

    def test_the_binding_check_still_runs_first(self):
        """A request bound elsewhere is refused for its binding, whatever effect it declares."""
        def elsewhere(request):
            raise ValueError("ORGANIZATION_INGRESS_RESOLUTION_ABSENT_FROM_REQUEST")

        self.binding = elsewhere
        result = self.receive(with_transition({"authority_effect": "GRANTS_EXECUTION_AUTHORITY"}))
        self.assertEqual(result["failed_predicate"], "CAPABILITY_IS_BOUND_TO_THIS_RECEIVING_OPERATION")
        self.assertEqual(result["detail"], "ORGANIZATION_INGRESS_RESOLUTION_ABSENT_FROM_REQUEST")
        self.assertEqual(self.crossings, [])


class AdmittedEffectTests(AuthorityEffectCase):
    """What legitimate submissions send -- NONE, or nothing -- still crosses."""

    def assertAdmitted(self, manifest):
        result = self.receive(manifest)
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertEqual(len(self.crossings), 1)
        repository, = self.receipts(self.repo_root)
        self.assertEqual(repository["transition_class"], ingress.OPERATION_ID)
        return result

    def test_declared_none_crosses(self):
        self.assertAdmitted(copy.deepcopy(MANIFEST))

    def test_an_absent_transition_crosses(self):
        self.assertAdmitted(without_transition())

    def test_a_transition_without_an_authority_effect_crosses(self):
        self.assertAdmitted(with_transition({}))

    def test_a_null_transition_crosses_as_the_crossing_reads_it(self):
        self.assertAdmitted(with_transition(None))


class PredicateTests(unittest.TestCase):
    def test_the_predicate_reads_the_effect_exactly_as_the_crossing_does(self):
        """Whatever the crossing would put on the envelope is what is checked."""
        for transition in (None, {}, {"authority_effect": "NONE"}, [], ""):
            manifest = with_transition(transition)
            envelope_effect = str((manifest.get("transition") or {}).get("authority_effect", "NONE"))
            self.assertEqual(envelope_effect, "NONE")
            self.assertIsNone(ingress.declared_authority_effect_failure(manifest), transition)
        for effect in REFUSED_EFFECTS:
            self.assertIsNotNone(ingress.declared_authority_effect_failure(
                with_transition({"authority_effect": effect})), effect)

    def test_the_failure_code_predicate_and_registered_owner_are_the_modules(self):
        self.assertEqual(ingress.AUTHORITY_NOT_WARRANTED, FAILURE_CODE)
        self.assertEqual(ingress.AUTHORITY_NOT_WARRANTED_PREDICATE, PREDICATE)
        self.assertEqual(ingress.AUTHORITY_OWNING_GOAL, OWNING_GOAL)
        self.assertTrue((ROOT / "data/canonical-task-records" / f"{OWNING_GOAL}.json").is_file())


if __name__ == "__main__":
    unittest.main()
