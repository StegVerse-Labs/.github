"""Ingress observes a declared WorkerCoordinator claim against the committed registry.

StegVerse-Labs/.github#3369 gap 2 (stale head / fence), option 2C of
`design/INGRESS_GAP_OPTIONS_3369.md`: when a manifest declares
`extensions.stegverse_workercoordinator_claim: {"claim_id": "<id>-G<fence>",
"fencing_token": <fence>}` (under `extensions`, the namespace the SDK's
`validate_ingress_manifest` admits),
`receive()` checks -- before the crossing -- that an unreleased BOUND task in
`control/worker-registry.json` holds exactly that claim and fence. A malformed
declaration, an unreadable registry or an unheld claim is FAIL_CLOSED
`FENCE_DECLARED_NOT_VERIFIED`; a held claim that is released, terminal or at
another generation is DENY `FENCE_STALE_OR_RELEASED`. Ingress mints nothing. An
absent declaration is admitted and reported `worker_claim_state: UNVERIFIED`.
A redelivery of an admission the ledger already records is answered as that
admission even when the fence has moved since (I-10): no contradicting refusal.

These cases drive the real `receive()`, the real crossing and the real
`process_boundary.py` subprocess on the boundary-local diagnostic service,
against temporary ledger roots and a temporary worker registry. Only the SDK's
request derivation, the binding resolution and result admission are stubbed.
`cross` is wrapped to count its calls, so "before the crossing" is observed.

Source validation only. No claim, fence or authority effect is minted.
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
    "organization_ingress_worker_claim_subject",
    ROOT / "resident-runtime/organization_manifest_ingress.py")
ingress = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingress)
crossing_module = ingress.crossing_module

PREDICATE = "DECLARED_FENCE_IS_THE_CURRENT_WORKERCOORDINATOR_FENCE"
NOT_VERIFIED = "FENCE_DECLARED_NOT_VERIFIED"
STALE = "FENCE_STALE_OR_RELEASED"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
COMMITTED_WORKER_REGISTRY = json.loads(
    (ROOT / ingress.WORKER_REGISTRY_REF).read_text(encoding="utf-8"))

MANIFEST = {
    "processing": {"capability": "ecosystem_diagnostic",
                   "route_id": "stegverse.route.ecosystem-diagnostic.v1"},
    "completion": {"egress": {"final_stegverse_transition_surface": "boundary_diagnostic",
                              "transport": "INTERLOCK_INTR",
                              "far_side_transition_required": True}},
    "transition": {"authority_effect": "NONE"},
    "data": {"value": 1},
}
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "worker-claim-test",
            "generation": 1, "predecessor": None}

HELD_CLAIM = "TEST-WORKER-CLAIM-TASK-001-G7"


def worker_registry(**task_overrides) -> dict:
    task = {"task_id": "TEST-WORKER-CLAIM-TASK-001", "claim_id": HELD_CLAIM,
            "executor_binding": "BOUND", "state": "ACTIVE", "archive_eligible": False,
            "heartbeat_timing": {"fencing_token": 7}}
    task.update(task_overrides)
    return {"schema": ingress.WORKER_REGISTRY_SCHEMA, "tasks": [task], "workers": []}


def request(manifest) -> dict:
    digest = ingress.sha(manifest)
    return {"request_sha256": ingress.sha({"manifest": digest}), "wire_manifest_sha256": digest,
            "canonical_manifest_sha256": digest, "graph_id": "graph-1",
            "canonical_task_id": "task-1", "processing_capability": "ecosystem_diagnostic",
            "route_id": "stegverse.route.ecosystem-diagnostic.v1",
            "destination_resolution_source": "ORGANIZATION_BOUNDARY"}


def with_claim(claim) -> dict:
    manifest = copy.deepcopy(MANIFEST)
    manifest.setdefault("extensions", {})[ingress.WORKER_CLAIM_EXTENSION] = claim
    return manifest


class WorkerClaimCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo", base / "org"
        self.checkout = base / "checkout"
        (self.checkout / "control").mkdir(parents=True)
        self.crossings = []
        real_cross = crossing_module.cross

        def cross(*args, **kwargs):
            self.crossings.append(args[0])
            return real_cross(*args, **kwargs)

        patches = [
            mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                         "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)}),
            mock.patch.object(ingress, "derive_execution_request", lambda m, b: request(m)),
            mock.patch.object(ingress, "bound_here", lambda r: {"operation": "receive"}),
            mock.patch.object(ingress, "admit_runtime_result", lambda *a: {"admitted": True}),
            mock.patch.object(crossing_module, "cross", cross),
            # The committed registry is read from the checkout this module runs
            # in; point it at a temporary checkout so the cases control it.
            mock.patch.object(ingress, "ROOT", self.checkout),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.install(worker_registry())

    def install(self, registry) -> None:
        path = self.checkout / ingress.WORKER_REGISTRY_REF
        if registry is None:
            if path.exists():
                path.unlink()
            return
        path.write_text(registry if isinstance(registry, str) else json.dumps(registry),
                        encoding="utf-8")

    def receive(self, manifest):
        return ingress.receive(manifest, registry=REGISTRY, standing=dict(STANDING),
                               packet_id="worker-claim-1")

    def fresh(self) -> None:
        """A clean case inside a subTest: tear the previous one down first."""
        self.doCleanups()
        self.setUp()

    def receipts(self, root: Path) -> list[dict]:
        directory = root / "receipts"
        return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))] \
            if directory.is_dir() else []

    def assertRefusedBeforeCrossing(self, result, manifest, code, disposition) -> None:
        self.assertEqual(result["disposition"], disposition, result)
        self.assertEqual(result["failed_predicate"], PREDICATE, result)
        self.assertEqual(result["failure_code"], code, result)
        self.assertTrue(result["detail"].startswith(code + ":"), result["detail"])
        for field in SIX_FIELDS:
            self.assertTrue(result.get(field), field)
        self.assertEqual(result["owning_existing_goal"], ingress.FENCE_OWNING_GOAL)
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
        self.assertEqual(repository["authority_effect"], "NONE")
        self.assertEqual(organization["receipt_sha256"], result["refusal_organization_receipt_sha256"])
        self.assertEqual(organization["repo_receipt_sha256"], repository["receipt_sha256"])
        self.assertEqual(organization["authority_effect"], "NONE")

    def assertAdmitted(self, manifest, state):
        result = self.receive(manifest)
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertEqual(result["worker_claim_state"], state)
        self.assertIs(result["workercoordinator_claim_fence_required_by_route"], False)
        self.assertEqual(len(self.crossings), 1)
        repository, = self.receipts(self.repo_root)
        organization, = self.receipts(self.org_root)
        self.assertEqual(repository["transition_class"], ingress.OPERATION_ID)
        # The state is reported on the result only; receipt bytes carry nothing of it.
        for receipt in (repository, organization):
            self.assertNotIn("worker_claim_state", json.dumps(receipt))
            self.assertNotIn("workercoordinator_claim_fence_required_by_route", json.dumps(receipt))
        return result


class AbsentDeclarationTests(WorkerClaimCase):
    def test_a_manifest_without_a_declaration_crosses_as_unverified(self):
        self.assertAdmitted(copy.deepcopy(MANIFEST), ingress.WORKER_CLAIM_UNVERIFIED)

    def test_an_absent_declaration_does_not_read_the_registry(self):
        self.install(None)
        self.assertAdmitted(copy.deepcopy(MANIFEST), ingress.WORKER_CLAIM_UNVERIFIED)


class VerifiedDeclarationTests(WorkerClaimCase):
    def test_a_held_claim_at_its_current_fence_crosses_as_verified(self):
        self.assertAdmitted(with_claim({"claim_id": HELD_CLAIM, "fencing_token": 7}),
                            ingress.WORKER_CLAIM_VERIFIED)

    def test_a_fence_held_on_the_lease_verifies_like_one_on_the_timing(self):
        self.install(worker_registry(heartbeat_timing={}, lease={"fencing_token": 7}))
        self.assertAdmitted(with_claim({"claim_id": HELD_CLAIM, "fencing_token": 7}),
                            ingress.WORKER_CLAIM_VERIFIED)


class NotVerifiedTests(WorkerClaimCase):
    """Fail closed: nothing in the declaration or the registry establishes the claim."""

    def refuse(self, claim):
        manifest = with_claim(claim)
        result = self.receive(manifest)
        self.assertRefusedBeforeCrossing(result, manifest, NOT_VERIFIED, "FAIL_CLOSED")
        self.assertEqual(result["next_attempt"]["resubmit"],
                         "THE_MANIFEST_WITH_A_VERIFIABLE_OR_ABSENT_WORKER_CLAIM")
        return result

    def test_each_malformed_declaration_is_refused(self):
        for claim in (None, "TEST-G7", [], {}, {"claim_id": HELD_CLAIM},
                      {"claim_id": HELD_CLAIM, "fencing_token": "7"},
                      {"claim_id": HELD_CLAIM, "fencing_token": True},
                      {"claim_id": HELD_CLAIM, "fencing_token": 0},
                      {"claim_id": "", "fencing_token": 7},
                      {"claim_id": "TEST-WORKER-CLAIM-TASK-001", "fencing_token": 7},
                      {"claim_id": HELD_CLAIM, "fencing_token": 8}):
            with self.subTest(claim=claim):
                self.fresh()
                self.refuse(claim)

    def test_a_claim_no_task_holds_is_refused(self):
        result = self.refuse({"claim_id": "NOBODY-HOLDS-THIS-G7", "fencing_token": 7})
        self.assertIn("no WorkerCoordinator task holds claim", result["detail"])

    def test_a_missing_registry_is_refused_not_trusted(self):
        self.install(None)
        result = self.refuse({"claim_id": HELD_CLAIM, "fencing_token": 7})
        self.assertIn("is not readable", result["detail"])

    def test_an_unparseable_registry_is_refused(self):
        self.install("{not json")
        self.refuse({"claim_id": HELD_CLAIM, "fencing_token": 7})

    def test_another_registry_schema_is_refused(self):
        self.install({**worker_registry(), "schema": "stegverse.worker-registry-fragment/v0.1"})
        result = self.refuse({"claim_id": HELD_CLAIM, "fencing_token": 7})
        self.assertIn("schema", result["detail"])

    def test_a_claim_held_twice_is_refused(self):
        registry = worker_registry()
        registry["tasks"].append(dict(registry["tasks"][0], task_id="TEST-WORKER-CLAIM-TASK-002"))
        self.install(registry)
        result = self.refuse({"claim_id": HELD_CLAIM, "fencing_token": 7})
        self.assertIn("held by 2", result["detail"])


class StaleOrReleasedTests(WorkerClaimCase):
    """Deny: a task holds the claim id, but not as a live claim at that fence."""

    def deny(self, claim, **task_overrides):
        self.install(worker_registry(**task_overrides))
        manifest = with_claim(claim)
        result = self.receive(manifest)
        self.assertRefusedBeforeCrossing(result, manifest, STALE, "DENY")
        self.assertEqual(result["next_attempt"]["resubmit"],
                         "THE_MANIFEST_UNDER_THE_CURRENT_WORKERCOORDINATOR_FENCE")
        return result

    def test_a_superseded_fence_is_denied(self):
        # The registry moved to G8 under claim ...-G8; the submitter still names G7.
        result = self.deny({"claim_id": HELD_CLAIM, "fencing_token": 7},
                           heartbeat_timing={"fencing_token": 8})
        self.assertIn("holds fence 8", result["detail"])

    def test_a_released_binding_is_denied(self):
        self.deny({"claim_id": HELD_CLAIM, "fencing_token": 7}, executor_binding="RELEASED")

    def test_a_terminal_task_is_denied(self):
        for state in sorted(ingress.WORKER_CLAIM_TERMINAL_STATES):
            with self.subTest(state=state):
                self.fresh()
                self.deny({"claim_id": HELD_CLAIM, "fencing_token": 7}, state=state)

    def test_an_archived_task_is_denied(self):
        self.deny({"claim_id": HELD_CLAIM, "fencing_token": 7}, archive_eligible=True)

    def test_a_task_with_no_fence_is_denied(self):
        self.deny({"claim_id": HELD_CLAIM, "fencing_token": 7}, heartbeat_timing={})


class ReplayTests(WorkerClaimCase):
    """A recorded admission is the same transition on redelivery, whatever the fence did since."""

    def test_a_redelivered_verified_manifest_is_the_recorded_transition(self):
        manifest = with_claim({"claim_id": HELD_CLAIM, "fencing_token": 7})
        first = self.assertAdmitted(manifest, ingress.WORKER_CLAIM_VERIFIED)
        second = self.receive(copy.deepcopy(manifest))
        self.assertEqual(second["disposition"], "ALLOW")
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(second["organization_receipt_sha256"], first["organization_receipt_sha256"])
        self.assertEqual(second["worker_claim_state"], ingress.WORKER_CLAIM_VERIFIED)
        self.assertEqual(len(self.receipts(self.repo_root)), 1)

    def test_a_redelivery_after_the_fence_moved_is_still_the_recorded_admission(self):
        manifest = with_claim({"claim_id": HELD_CLAIM, "fencing_token": 7})
        first = self.assertAdmitted(manifest, ingress.WORKER_CLAIM_VERIFIED)
        # The registry moves on to G8 after the admission was recorded.
        self.install(worker_registry(claim_id="TEST-WORKER-CLAIM-TASK-001-G8",
                                     heartbeat_timing={"fencing_token": 8}))
        second = self.receive(copy.deepcopy(manifest))
        self.assertEqual(second["disposition"], "ALLOW", second.get("detail"))
        self.assertIs(second["transition_replayed"], True)
        self.assertEqual(second["organization_receipt_sha256"], first["organization_receipt_sha256"])
        self.assertEqual(second["worker_claim_state"], ingress.WORKER_CLAIM_REPLAYED)
        # No refusal was minted beside the recorded admission.
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(len(self.receipts(self.org_root)), 1)

    def test_a_never_admitted_stale_fence_is_still_refused(self):
        # Something else was recorded; this request was not.
        self.assertAdmitted(copy.deepcopy(MANIFEST), ingress.WORKER_CLAIM_UNVERIFIED)
        self.crossings.clear()
        self.install(worker_registry(heartbeat_timing={"fencing_token": 8}))
        manifest = with_claim({"claim_id": HELD_CLAIM, "fencing_token": 7})
        result = self.receive(manifest)
        self.assertEqual(result["failure_code"], STALE)
        self.assertEqual(result["disposition"], "DENY")
        self.assertEqual(self.crossings, [])


class SdkValidatorTests(unittest.TestCase):
    """The declaration lives where the pinned SDK's validator admits it."""

    def setUp(self):
        import stegverse
        from stegverse.manifest_contract import validate_ingress_manifest
        self.validate = validate_ingress_manifest
        # The pin's materialized tree carries only the importable package, so the
        # SDK's example manifest is read from the repo's byte-copy of it (the same
        # fixture test_build_optical_component_010_org_request.py uses).
        example = (Path(__file__).resolve().parent / "fixtures"
                   / "sdk-external-framework-generic-manifest.json")
        self.example = json.loads(example.read_text(encoding="utf-8"))
        self.validate(self.example)

    def test_a_top_level_declaration_would_never_reach_receive(self):
        with self.assertRaises(ValueError) as refused:
            self.validate({**self.example, "worker_claim": {"claim_id": "X-G1", "fencing_token": 1}})
        self.assertIn("unknown top-level manifest fields: worker_claim", str(refused.exception))

    def test_the_extension_placement_passes_the_pinned_validator(self):
        manifest = copy.deepcopy(self.example)
        manifest["extensions"][ingress.WORKER_CLAIM_EXTENSION] = {"claim_id": "X-G1", "fencing_token": 1}
        self.validate(manifest)
        self.assertTrue(ingress.declares_worker_claim(manifest))
        self.assertEqual(ingress.WORKER_CLAIM_FIELD, "extensions." + ingress.WORKER_CLAIM_EXTENSION)


class OrderingTests(WorkerClaimCase):
    def test_the_authority_effect_check_still_runs_first(self):
        manifest = with_claim({"claim_id": "NOBODY-HOLDS-THIS-G7", "fencing_token": 7})
        manifest["transition"] = {"authority_effect": "GRANTS_EXECUTION_AUTHORITY"}
        result = self.receive(manifest)
        self.assertEqual(result["failure_code"], ingress.AUTHORITY_NOT_WARRANTED)
        self.assertEqual(self.crossings, [])

    def test_a_redelivered_refusal_is_recorded_once(self):
        manifest = with_claim({"claim_id": "NOBODY-HOLDS-THIS-G7", "fencing_token": 7})
        first = self.receive(manifest)
        second = self.receive(copy.deepcopy(manifest))
        self.assertEqual(first["refusal_repository_receipt_sha256"],
                         second["refusal_repository_receipt_sha256"])
        self.assertEqual(len(self.receipts(self.repo_root)), 1)
        self.assertEqual(self.crossings, [])


class CommittedRegistryTests(unittest.TestCase):
    """The verifier reads the committed WorkerCoordinator truth, and mints nothing."""

    def test_the_committed_registry_is_the_schema_the_verifier_expects(self):
        self.assertEqual(COMMITTED_WORKER_REGISTRY["schema"], ingress.WORKER_REGISTRY_SCHEMA)
        self.assertEqual(ingress.load_worker_registry()["schema"], ingress.WORKER_REGISTRY_SCHEMA)

    def test_every_committed_bound_claim_verifies_at_its_own_fence_and_at_no_other(self):
        bound = [task for task in COMMITTED_WORKER_REGISTRY["tasks"]
                 if task.get("executor_binding") == "BOUND" and task.get("claim_id")
                 and task.get("archive_eligible") is not True
                 and task.get("state") not in ingress.WORKER_CLAIM_TERMINAL_STATES]
        self.assertTrue(bound, "the committed registry holds no BOUND claim to check against")
        for task in bound:
            fence = ingress._registry_fence(task)
            self.assertIsNotNone(fence, task["claim_id"])
            self.assertTrue(task["claim_id"].endswith(f"-G{fence}"), task["claim_id"])
            self.assertIsNone(ingress.declared_worker_claim_failure(
                with_claim({"claim_id": task["claim_id"], "fencing_token": fence})))
            stale = ingress.declared_worker_claim_failure(
                with_claim({"claim_id": task["claim_id"].replace(f"-G{fence}", f"-G{fence + 1}"),
                            "fencing_token": fence + 1}))
            self.assertEqual(stale[0], NOT_VERIFIED, stale)

    def test_the_verifier_is_read_only(self):
        before = (ROOT / ingress.WORKER_REGISTRY_REF).read_bytes()
        ingress.declared_worker_claim_failure(with_claim({"claim_id": "X-G1", "fencing_token": 1}))
        self.assertEqual((ROOT / ingress.WORKER_REGISTRY_REF).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
