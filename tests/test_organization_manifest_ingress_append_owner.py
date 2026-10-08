"""The manifest ingress appends through the organization ledger's own owner.

Source-only. Every ledger is a temporary root and nothing here is a live
receipt. The SDK's `derive_execution_request` and `admit_runtime_result` and the
InTr crossing are replaced with fixtures so the admission path can run without
the SDK package or a far side; both ledger levels, the batch parent manifest
validator and packet release are the production code.
"""
from __future__ import annotations

import copy
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_organization_manifest_ingress_rule_ref import REVISION, ingress  # noqa: E402
from tests.test_manifest_governance_universal_intr_binding import (  # noqa: E402
    custody_rows,
    organization_batch_governance_request,
)
from workers import manifest_state_transition_intr_ingress as worker  # noqa: E402

batch_custody = ingress.batch_custody
organization_ledger = ingress.organization_ledger
repository_ledger = ingress.repository_ledger
kernel = organization_ledger.kernel



def _released_by_owner():
    """Patch packet-release custody on the module the organization append imports.

    `aggregate_transition` imports `organization_batch_custody` by name at the
    moment it releases a packet; the ingress fixture loads under a scoped
    `sys.modules`, so the module object it holds may not be that one.
    """
    owner = importlib.import_module("organization_batch_custody")
    return mock.patch.object(owner, "submit_released_batch",
                             lambda root, batch_id: dict(RELEASED, batch_id=batch_id))


RELEASED = {
    "state": "COMPLETED",
    "execution_result": "COMPLETED",
    "reason": None,
    "governance_disposition": None,
    "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
}


def _with_nonce(request: dict, nonce: int) -> dict:
    """The same batch-bound request, made a distinct transition by its payload."""
    request = copy.deepcopy(request)
    body = dict(request["canonical_manifest"])
    body.pop("canonical_manifest_sha256")
    body["payload"] = {**body["payload"], "nonce": nonce}
    digest = worker.sha256(body)
    request["canonical_manifest"] = {**body, "canonical_manifest_sha256": digest}
    request["canonical_manifest_sha256"] = digest
    request.pop("request_sha256")
    request["request_sha256"] = worker.sha256(request)
    return request


def _ingress_request(sdk_request: dict) -> dict:
    """What `derive_execution_request` returns: the SDK request plus its resolution."""
    request = copy.deepcopy(sdk_request)
    # A non-governance capability, so the admitted crossing closes here rather
    # than leaving through egress. The batch declaration is unchanged.
    request.update({
        "processing_capability": "records",
        "wire_manifest_sha256": request["canonical_manifest_sha256"],
        "destination_resolution_source": "ORGANIZATION_BOUNDARY_DOCUMENT",
        "manifest_declared_destination": {
            "profile_id": ingress.PROFILE_ID,
            "profile_name": ingress.PROFILE_NAME,
            "operation": ingress.OPERATION,
            "receiving_operation": {"owner_repository": ingress.OWNER_REPOSITORY,
                                    "operation_id": ingress.OPERATION_ID},
        },
    })
    return request


def _plain_request() -> dict:
    """A request that declares no organization batch at all."""
    request = _ingress_request(organization_batch_governance_request())
    request["canonical_task_id"] = None
    request["canonical_manifest"] = {"manifest_profile": "stegverse.ingress-manifest.v1",
                                     "payload": {"plain": True}}
    request["state_graph"] = {**request["state_graph"], "request": {"source": "test-only"}}
    return request


def _crossing(seed: str) -> dict:
    base = {"packet_id": "ingress-" + seed, "service_id": "records-service",
            "payload_hash": "sha256:" + "c" * 64}
    receipts, previous = [], None
    for kind in ("INGRESS_ADMITTED", "PROCESSED"):
        digest = ingress.sha({**base, "kind": kind, "previous_receipt_id": previous})
        receipt_id = kind.lower() + "-" + digest[:24]
        receipts.append({"kind": kind, "previous_receipt_id": previous,
                         "evidence_hash": digest, "receipt_id": receipt_id})
        previous = receipt_id
    return {"crossing_completed": True, "ingress_packet_id": base["packet_id"],
            "egress_packet_id": "egress-" + seed, "resolved_service_id": base["service_id"],
            "payload_hash": base["payload_hash"], "boundary_receipts": receipts,
            "terminal_receipt_id": previous, "application_result": None}


class LedgerRoots(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        base = Path(self._temp.name)
        self.org_root, self.repo_root = base / "org", base / "repo"
        self._env = mock.patch.dict(os.environ, {
            "GITHUB_SHA": REVISION,
            "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
            "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
        })
        self._env.start()
        self._release = _released_by_owner()
        self._release.start()

    def tearDown(self):
        self._release.stop()
        self._env.stop()
        self._temp.cleanup()

    def receive(self, request: dict, *, hb_epoch=None, seed="0"):
        cross = mock.MagicMock(return_value=_crossing(seed))
        with mock.patch.object(ingress, "derive_execution_request", return_value=request), \
             mock.patch.object(ingress.crossing_module, "cross", cross), \
             mock.patch.object(ingress, "admit_runtime_result", return_value={"admitted": True}):
            result = ingress.receive({"processing": {"capability": "records"}}, registry={},
                                     hb_epoch=hb_epoch)
        return result, cross

    def org_receipt(self, digest: str) -> dict:
        return json.loads((self.org_root / "receipts" / (digest.split(":", 1)[1] + ".json")).read_text())

    def repo_receipt(self, digest: str) -> dict:
        return json.loads((self.repo_root / repository_ledger.ledger_store.receipt_key(digest)).read_text())

    def org_receipts(self) -> list[dict]:
        directory = self.org_root / "receipts"
        return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))] \
            if directory.is_dir() else []


class ParentManifestApplicabilityTest(LedgerRoots):
    def _recorded_parent_manifests(self, request, **kwargs):
        calls = []
        real = organization_ledger.aggregate_transition

        def recording(*args, **kw):
            calls.append(kw)
            return real(*args, **kw)

        with mock.patch.object(organization_ledger, "aggregate_transition", recording):
            result, _ = self.receive(request, **kwargs)
        return result, calls

    def test_valid_batch_declaration_passes_the_parent_manifest(self):
        request = _ingress_request(organization_batch_governance_request())
        result, calls = self._recorded_parent_manifests(request)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["parent_manifest"],
                         {"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}})
        self.assertEqual(calls[0]["receipt"]["receipt_sha256"], result["repository_receipt_sha256"])
        evidence = self.org_receipt(result["organization_receipt_sha256"])["boundary_evidence"]
        self.assertNotIn("parent_manifest_applicable", evidence)

    def test_absent_declaration_is_recorded_as_not_applicable(self):
        result, calls = self._recorded_parent_manifests(_plain_request())
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertIsNone(calls[0]["parent_manifest"])
        evidence = self.org_receipt(result["organization_receipt_sha256"])["boundary_evidence"]
        self.assertIs(evidence["parent_manifest_applicable"], False)
        self.assertEqual(evidence["parent_manifest_absent_predicate"],
                         "ORGANIZATION_BATCH_RECEIPT_BATCH_POLICY_EXTENSION_ABSENT"
                         "+ORGANIZATION_BATCH_CANONICAL_TASK_BINDING_ABSENT")

    def _assert_refused_before_any_admission_write(self, request, code):
        result, cross = self.receive(request)
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failed_predicate"], ingress.PARENT_MANIFEST_INVALID_PREDICATE)
        self.assertEqual(result["failure_code"], code)
        self.assertTrue(result["refusal_recorded"])
        cross.assert_not_called()
        # Only the refusal itself is recorded: no admission receipt at either level.
        receipts = self.org_receipts()
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["boundary_evidence"]["failed_predicate"],
                         ingress.PARENT_MANIFEST_INVALID_PREDICATE)
        self.assertEqual(self.repo_receipt(receipts[0]["repo_receipt_sha256"])["transition_class"],
                         ingress.REFUSED_CLASS)

    def test_malformed_release_condition_is_refused_with_its_code(self):
        request = _ingress_request(organization_batch_governance_request())
        policy = {"release_condition": {"type": "TIME", "seconds": 5}}
        request["canonical_manifest"]["extensions"][batch_custody.ORGANIZATION_BATCH_POLICY_EXTENSION] = policy
        request["state_graph"]["request"]["canonical_task_binding"]["receipt_batch"] = policy
        self._assert_refused_before_any_admission_write(
            request, "ORGANIZATION_BATCH_COUNT_RELEASE_CONDITION_REQUIRED")

    def test_policy_without_its_task_binding_is_refused(self):
        request = _plain_request()
        request["canonical_manifest"]["extensions"] = {
            batch_custody.ORGANIZATION_BATCH_POLICY_EXTENSION: {
                "release_condition": {"type": "COUNT", "count": 1}}}
        self._assert_refused_before_any_admission_write(
            request, "ORGANIZATION_BATCH_CANONICAL_TASK_BINDING_REQUIRED")

    def test_mismatched_task_binding_is_refused(self):
        request = _ingress_request(organization_batch_governance_request())
        request["canonical_manifest"]["extensions"]["stegverse_canonical_task"]["task_id"] = "OTHER-TASK-001"
        self._assert_refused_before_any_admission_write(request, "ORGANIZATION_BATCH_TASK_ID_MISMATCH")

    def test_mismatched_cosv_is_refused(self):
        request = _ingress_request(organization_batch_governance_request())
        request["canonical_manifest"]["extensions"]["stegverse_canonical_task"]["cosv_task_vector"] = "1" * 14
        self._assert_refused_before_any_admission_write(request, "ORGANIZATION_BATCH_COSV_MISMATCH")

    def test_worker_and_ingress_share_one_validator_and_its_constants(self):
        request = organization_batch_governance_request()
        self.assertEqual(worker._organization_batch_parent_manifest(request),
                         ingress.parent_manifest_applicability(_ingress_request(request))[0])
        self.assertEqual(worker.ORGANIZATION_BATCH_TASK_ID, batch_custody.ORGANIZATION_BATCH_TASK_ID)
        self.assertEqual(worker.ORGANIZATION_BATCH_POLICY_EXTENSION,
                         batch_custody.ORGANIZATION_BATCH_POLICY_EXTENSION)
        self.assertEqual(worker.ORGANIZATION_BATCH_REQUEST_REF, batch_custody.ORGANIZATION_BATCH_REQUEST_REF)


LIFECYCLE = ("INGRESS_ADMITTED", "GOVERNANCE_DISPOSITION",
             "MANIFEST_DIRECTED_ORGANIZATION_APPEND_DISPATCHED")


class PacketReleaseEquivalenceTest(unittest.TestCase):
    """One batch-bound request releases its packet the same way on either path.

    Q5-D (StegVerse-Labs/TVC#488): release behaviour is compared at the
    batch-bound append, under an equivalent immediate pre-append state. The
    two ledgers are not compared whole: per request the worker performs three
    authorized governed lifecycle transitions the ingress does not, and batch
    windowing counts every receipt, so receipt and batch counts legitimately
    differ between the paths.
    """

    def _observe(self, root: Path) -> dict:
        batches = [json.loads(path.read_text()) for path in sorted((root / "batches").glob("*.json"))]
        return {
            "batch_count": len(batches),
            "closure_reasons": sorted(b["closure_reason"] for b in batches),
            "ranges": sorted(b["contiguous_receipt_range"] for b in batches),
            "receipt_count": len(list((root / "receipts").glob("*.json"))),
        }

    def _pre_append(self, root: Path, parent_manifest: dict) -> dict:
        """Everything the batch-bound append's release decision reads, read before it runs.

        `release_satisfied_packet_before_next_transition` decides from the
        parent manifest's release condition, the open packet the ledger holds
        (HEAD, BATCH_HEAD and the verified segment between them) and, once
        released, the packet-release custody client. All three are captured.
        """
        def json_name(path: Path, key: str):
            return json.loads(path.read_text())[key] if path.exists() else None

        custody = importlib.import_module("organization_batch_custody").submit_released_batch
        return {
            "parent_manifest": copy.deepcopy(parent_manifest),
            "packet": batch_custody.open_packet_state(parent_manifest, root=root),
            "head": json_name(root / "HEAD.json", "receipt_sha256"),
            "batch_head": json_name(root / "BATCH_HEAD.json", "batch_id"),
            "receipts": sorted(path.name for path in (root / "receipts").glob("*.json")),
            "batches": sorted(path.name for path in (root / "batches").glob("*.json")),
            "release_custody": custody(root, "sha256:" + "0" * 64),
        }

    def _worker_path(self, root: Path, requests: list[dict], snapshots: Path) -> tuple[dict, list, list, list]:
        calls, states = [], []
        owner = worker._load_organization_append_owner()

        def recording(*args, **kwargs):
            states.append(self._pre_append(root, kwargs["parent_manifest"]))
            shutil.copytree(root, snapshots / str(len(calls)))
            calls.append(kwargs["parent_manifest"])
            return owner.aggregate_transition(*args, **kwargs)

        governance = {"governance_state": "ALLOW", "manifest_receipt_id": "MR-EQ",
                      "transaction_id": "TX-EQ", "result_binding_hash": "sha256:" + "f" * 64,
                      "master_records_organization_record_status": "RECORDED",
                      "chain_verified": True, "external_side_effect": False}
        transport = {"origin": "TVC_RELAY_EGRESS", "authorization_id": "TVC-AUTH-EXACT",
                     "payload_sha256": "c" * 64}
        released, results = [], []
        with mock.patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(root)}), \
             _released_by_owner(), \
             mock.patch.object(worker, "_run_governance_owner", return_value=governance), \
             mock.patch.object(worker, "_load_organization_append_owner",
                               return_value=SimpleNamespace(aggregate_transition=recording)):
            for request in requests:
                with tempfile.TemporaryDirectory() as runtime, \
                     mock.patch.object(worker, "_custody_transition", side_effect=custody_rows()):
                    result = worker.execute(Path(runtime), request, transport=transport)
                action = result["manifest_directed_action"]
                self.assertEqual(action["execution_result"], "COMPLETED", action)
                released.append(action["released_batch"])
                results.append(result)
        return {**self._observe(root), "released": released}, calls, states, results

    def _ingress_path(self, root: Path, repo: Path, requests: list[dict]) -> tuple[dict, list, list]:
        calls, states = [], []
        real = organization_ledger.aggregate_transition

        def recording(*args, **kwargs):
            states.append(self._pre_append(root, kwargs["parent_manifest"]))
            calls.append(kwargs["parent_manifest"])
            return real(*args, **kwargs)

        released = []
        with mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                          "STEGVERSE_ORG_LEDGER_ROOT": str(root),
                                          "STEGVERSE_REPO_LEDGER_ROOT": str(repo)}), \
             _released_by_owner(), \
             mock.patch.object(organization_ledger, "aggregate_transition", recording), \
             mock.patch.object(ingress, "admit_runtime_result", return_value={"admitted": True}):
            for index, request in enumerate(requests):
                with mock.patch.object(ingress, "derive_execution_request",
                                       return_value=_ingress_request(request)), \
                     mock.patch.object(ingress.crossing_module, "cross",
                                       return_value=_crossing(str(index))):
                    result = ingress.receive({"n": index}, registry={})
                self.assertEqual(result["disposition"], "ALLOW", result)
                row = json.loads((root / "receipts" / (
                    result["organization_receipt_sha256"].split(":", 1)[1] + ".json")).read_text())
                released.append(row["boundary_evidence"].get("parent_manifest_released_batch"))
        return {**self._observe(root), "released": released}, calls, states

    def _chain(self, root: Path) -> list[dict]:
        """The Organization ledger from genesis to HEAD, every receipt digest recomputed."""
        rows = []
        cursor = json.loads((root / "HEAD.json").read_text())["receipt_sha256"]
        while cursor is not None:
            row = json.loads((root / "receipts" / (cursor[7:] + ".json")).read_text())
            body = {k: v for k, v in row.items() if k != "receipt_sha256"}
            self.assertEqual(row["receipt_sha256"], cursor)
            self.assertEqual(organization_ledger.sha(body), cursor, "organization receipt digest mismatch")
            rows.append(row)
            cursor = row["previous_receipt_sha256"]
        rows.reverse()
        # One ledger root, nothing orphaned: every receipt file is on the chain.
        self.assertEqual(sorted(row["receipt_sha256"][7:] + ".json" for row in rows),
                         sorted(path.name for path in (root / "receipts").glob("*.json")))
        return rows

    def _assert_worker_lifecycle_custody(self, root: Path, results: list[dict]) -> None:
        """Per request: the three governed lifecycle receipts are on the ledger, in
        order, digest-verified, contiguous, and inside a released batch's range."""
        chain = self._chain(root)
        position = {row["receipt_sha256"]: n for n, row in enumerate(chain, start=1)}
        batches = [json.loads(path.read_text()) for path in (root / "batches").glob("*.json")]
        for result in results:
            action = result["manifest_directed_action"]
            closures = {c["transition_id"]: c for c in result["transition_closures"]}
            closures[LIFECYCLE[2]] = action["dispatch_closure"]
            lifecycle = [closures[name]["organization_receipt_sha256"] for name in LIFECYCLE]
            for digest in lifecycle:
                self.assertIn(digest, position, "lifecycle receipt absent from the ledger chain")
            places = [position[digest] for digest in lifecycle]
            self.assertEqual(places, list(range(places[0], places[0] + len(LIFECYCLE))),
                             "lifecycle receipts not contiguous")
            self.assertEqual([chain[n - 1]["source_transition_id"] for n in places], list(LIFECYCLE))
            # The batch-bound append directly follows its own lifecycle.
            self.assertEqual(position[action["organization_receipt_sha256"]], places[-1] + 1)
            for digest, n in zip(lifecycle, places):
                covering = [b for b in batches
                            if b["contiguous_receipt_range"][0] <= n <= b["contiguous_receipt_range"][1]]
                self.assertEqual(len(covering), 1, (digest, n))
                start = covering[0]["contiguous_receipt_range"][0]
                self.assertEqual(covering[0]["ordered_receipt_hashes"][n - start], digest)
                self.assertTrue(batch_custody.verify_batch(root, covering[0]["batch_id"]))

    def test_same_request_same_release_behaviour(self):
        base = organization_batch_governance_request()
        requests = [_with_nonce(base, n) for n in range(3)]
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            snapshots = temp / "worker-pre-append"
            snapshots.mkdir()
            via_worker, worker_calls, worker_states, results = self._worker_path(
                temp / "worker-org", requests, snapshots)
            via_ingress, ingress_calls, _ = self._ingress_path(temp / "ingress-org", temp / "repo", requests)

            # Both paths make the identical manifest-bound batch append call.
            self.assertEqual(worker_calls, ingress_calls)
            self.assertEqual(worker_calls[0], {"receipt_batch": {"release_condition": {"type": "COUNT", "count": 1}}})

            # Per request, the ingress replays its batch-bound append from an
            # equivalent immediate pre-append state: a copy of the worker's own
            # Organization ledger root taken inside the worker's batch-bound
            # call, before it ran. Equivalence holds because
            #   - the parent manifest (release condition) is the same object
            #     content on both paths (worker_calls == ingress_calls);
            #   - the ingress appends no Organization receipt before its
            #     batch-bound append, so its ledger at that call is the copy:
            #     same HEAD, BATCH_HEAD, receipt and batch inventory, and so
            #     the same verified open packet;
            #   - the packet-release custody client is the same fixture;
            #   - the manifest declares no establishment, so expiry and the
            #     host clock are not inputs to the decision.
            # The captured states are asserted equal; if the ingress wrote
            # anything first, or read a different packet, this fails rather
            # than comparing decisions taken from different states.
            self.assertEqual(len(worker_states), len(requests))
            for index, request in enumerate(requests):
                state = worker_states[index]
                self.assertIsNone(state["packet"]["establishment_heartbeat_id"])
                self.assertIs(state["packet"]["expired"], False)
                replay_root = temp / "ingress-replay" / str(index)
                shutil.copytree(snapshots / str(index), replay_root)
                # HEAD.json names its tip receipt by absolute path; the copy's
                # HEAD names the copy's own file. Same receipt_sha256, and
                # close_batch re-verifies that the path resolves to it.
                head = json.loads((replay_root / "HEAD.json").read_text())
                head["receipt_path"] = str(replay_root / "receipts" / (head["receipt_sha256"][7:] + ".json"))
                (replay_root / "HEAD.json").write_text(json.dumps(head))
                self.assertFalse([path for path in replay_root.rglob("*") if path.is_file()
                                  and str(temp / "worker-org") in path.read_text(errors="replace")],
                                 "replay root still names the worker root")
                replayed, replay_calls, replay_states = self._ingress_path(
                    replay_root, temp / "ingress-replay-repo" / str(index), [request])
                self.assertEqual(replay_calls, [worker_calls[index]])
                self.assertEqual(len(replay_states), 1)
                self.assertEqual(replay_states[0], state,
                                 f"request {index}: pre-append state equivalence not established")

                # The release decision for that append is identical.
                self.assertTrue(state["packet"]["release_condition_satisfied"])
                worker_released = via_worker["released"][index]
                self.assertIsNotNone(worker_released)
                self.assertEqual(replayed["released"], [worker_released], f"request {index}")
                batch_file = worker_released["batch_id"][7:] + ".json"
                self.assertEqual(json.loads((replay_root / "batches" / batch_file).read_text()),
                                 json.loads((temp / "worker-org" / "batches" / batch_file).read_text()))

            self._assert_worker_lifecycle_custody(temp / "worker-org", results)

        self.assertEqual(via_ingress["batch_count"], 2)
        self.assertEqual(via_ingress["ranges"], [[1, 1], [2, 2]])
        self.assertEqual(via_ingress["closure_reasons"], ["MANIFEST_RELEASE_CONDITION"] * 2)
        self.assertIsNone(via_ingress["released"][0])
        self.assertEqual(via_ingress["released"][1]["execution_result"], "COMPLETED")


class HeartbeatReferenceTest(LedgerRoots):
    def test_supplied_epoch_is_carried_by_both_levels(self):
        result, _ = self.receive(_plain_request(), hb_epoch=4242)
        self.assertEqual(result["disposition"], "ALLOW", result)
        org = self.org_receipt(result["organization_receipt_sha256"])
        repo = self.repo_receipt(result["repository_receipt_sha256"])
        self.assertEqual(org["hb_reference"], kernel.hb_reference(epoch=4242))
        self.assertEqual(org["hb_reference"], repo["hb_reference"])
        self.assertIs(org["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(org["schema"], "stegverse.organization-transition-receipt/v1")
        self.assertIn("observed_at", org)

    def test_refusal_receipts_share_the_supplied_epoch(self):
        result = ingress.receive({"processing": {"capability": "x"}}, registry={}, hb_epoch=4243)
        org = self.org_receipt(result["refusal_organization_receipt_sha256"])
        repo = self.repo_receipt(result["refusal_repository_receipt_sha256"])
        self.assertEqual(org["hb_reference"], repo["hb_reference"])
        self.assertEqual(org["hb_reference"]["epoch"], 4243)

    def test_absent_epoch_is_derived_and_shared(self):
        """Absent, the repository receipt derives the epoch and says so; the
        organization receipt consuming it carries that same epoch."""
        result, _ = self.receive(_plain_request())
        repo = self.repo_receipt(result["repository_receipt_sha256"])["hb_reference"]
        org = self.org_receipt(result["organization_receipt_sha256"])["hb_reference"]
        self.assertIs(repo["derived_from_clock"], True)
        self.assertEqual(org["epoch"], repo["epoch"])
        self.assertEqual(kernel.validate_hb_reference(repo), repo)
        self.assertEqual(kernel.validate_hb_reference(org), org)

    def test_invalid_reference_is_rejected_by_the_kernel(self):
        result, _ = self.receive(_plain_request(), hb_epoch=4244)
        reference = self.org_receipt(result["organization_receipt_sha256"])["hb_reference"]
        for field, value, code in (("heartbeat_id", "HB:1", "heartbeat_id_mismatch"),
                                   ("generation", 1, "heartbeat_generation_mismatch"),
                                   ("epoch", 1, "heartbeat_epoch_invalid"),
                                   ("frequency_hz", 50, "heartbeat_frequency_mismatch")):
            with self.assertRaisesRegex(ValueError, code):
                kernel.validate_hb_reference({**reference, field: value})

    def _canonical_source(self, name: str) -> dict:
        return {"schema": "stegverse.canonical-state-transition-receipt/v1", "transition_id": name,
                "transition_sequence": 1, "subject_or_correlation_id": "hb-test",
                "transition_outcome": "OBSERVED", "required_evidence_manifest": []}

    def test_exact_retry_returns_the_original_receipt(self):
        source = self._canonical_source("EXACT-RETRY")
        first = organization_ledger.aggregate_transition(source, hb_epoch=5000)
        again = organization_ledger.aggregate_transition(source, hb_epoch=5001)
        derived = organization_ledger.aggregate_transition(source)
        self.assertEqual(first, again)
        self.assertEqual(first, derived)
        self.assertEqual(again["hb_reference"]["epoch"], 5000)
        self.assertEqual(len(self.org_receipts()), 1)

    def _historical(self, source: dict) -> dict:
        """A v1 receipt as written before receipts carried `hb_reference`."""
        current = organization_ledger.aggregate_transition(source)
        body = {k: v for k, v in current.items() if k not in ("receipt_sha256", "hb_reference")}
        historical = {**body, "receipt_sha256": organization_ledger.sha(body)}
        (self.org_root / "receipts" / (current["receipt_sha256"][7:] + ".json")).unlink()
        path = self.org_root / "receipts" / (historical["receipt_sha256"][7:] + ".json")
        path.write_text(json.dumps(historical, indent=2, sort_keys=True) + "\n")
        (self.org_root / "HEAD.json").write_text(json.dumps({
            "organization": organization_ledger.C["organization"],
            "receipt_sha256": historical["receipt_sha256"], "receipt_path": str(path)}))
        return historical

    def test_historical_receipts_verify_replay_and_pass_the_schema_consumers(self):
        source = self._canonical_source("HISTORICAL")
        historical = self._historical(source)
        self.assertNotIn("hb_reference", historical)

        # Exact retry reuses the historical receipt rather than writing a new one.
        self.assertEqual(organization_ledger.aggregate_transition(source, hb_epoch=6000), historical)

        # A new receipt chains onto it and the packet replays across both.
        later = organization_ledger.aggregate_transition(self._canonical_source("LATER"), hb_epoch=6001)
        self.assertEqual(later["previous_receipt_sha256"], historical["receipt_sha256"])
        closed = batch_custody.close_batch("TASK_CLOSURE", root=self.org_root)
        self.assertEqual(closed["ordered_receipt_hashes"],
                         [historical["receipt_sha256"], later["receipt_sha256"]])
        verified = batch_custody.verify_batch(self.org_root, closed["batch_id"])
        self.assertEqual(verified["organization_chain"], "PASS")

        # Consumer: organization_batch_custody._verified_receipt.
        self.assertEqual(batch_custody._verified_receipt(self.org_root, historical["receipt_sha256"]),
                         historical)

        # Consumer: workers/canonical_state_transition_custody (exact source reuse).
        from workers import canonical_state_transition_custody as custody
        recorded = custody._record_organization_transition(self._canonical_source("CUSTODY"))
        self.assertEqual(recorded["state"], "RECORDED", recorded)
        row = recorded["organization_receipt"]
        body = {k: v for k, v in row.items() if k not in ("receipt_sha256", "hb_reference")}
        legacy = {**body, "receipt_sha256": organization_ledger.sha(body)}
        (self.org_root / "receipts" / (row["receipt_sha256"][7:] + ".json")).unlink()
        (self.org_root / "receipts" / (legacy["receipt_sha256"][7:] + ".json")).write_text(
            json.dumps(legacy, indent=2, sort_keys=True) + "\n")
        again = custody._record_organization_transition(self._canonical_source("CUSTODY"))
        self.assertEqual(again["state"], "RECORDED", again)
        self.assertEqual(again["organization_receipt"], legacy)

        # Consumer: resident-runtime/submit_org_transition_to_master_records.py.
        receipt_path = Path(self._temp.name) / "historical.json"
        receipt_path.write_text(json.dumps(historical))
        standing = Path(self._temp.name) / "standing.json"
        standing.write_text(json.dumps({"mode": "ESTABLISH_GENESIS",
                                        "node_ref": "StegVerse-Labs-test-node", "predecessor": None}))
        completed = subprocess.run(
            [sys.executable, str(ROOT / "resident-runtime/submit_org_transition_to_master_records.py"),
             "--org-receipt", str(receipt_path),
             "--predecessor-ecosystem-state-sha256", "sha256:" + "a" * 64,
             "--successor-ecosystem-state-sha256", "sha256:" + "b" * 64,
             "--standing", str(standing), "--mesh-root", str(Path(self._temp.name) / "mesh")],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "PUBLISHED_FOR_ORGANIZATION_RECORD")


class PartialCommitTest(LedgerRoots):
    def _assert_typed(self, result):
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "ORGANIZATION_APPEND_NOT_COMMITTED")
        self.assertEqual(result["failed_predicate"], "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK")
        self.assertIs(result["organization_runtime_transition_committed"], False)
        self.assertEqual(result["retry_entrypoint"], "resident-runtime/organization_manifest_ingress.py::receive")
        self.assertEqual(result["owning_existing_goal"], "ORGANIZATION-BATCH-CUSTODY-REPLAY-001")
        self.assertTrue(result["required_evidence_or_repair"])
        self.assertTrue(result["next_attempt"])
        self.assertTrue(result["evidence_refs"])
        self.assertFalse(result["repository_receipt_committed"] is False
                         and result["organization_receipt_committed"] is False)

    def test_fault_between_the_appends_is_a_typed_record(self):
        with mock.patch.object(organization_ledger, "aggregate_transition",
                               side_effect=RuntimeError("injected between the appends")):
            result, _ = self.receive(_plain_request(), hb_epoch=7000)
        self._assert_typed(result)
        self.assertIs(result["repository_receipt_committed"], True)
        stored = self.repo_receipt(result["repository_receipt_sha256"])
        body = {k: v for k, v in stored.items() if k != "receipt_sha256"}
        self.assertEqual(repository_ledger.sha(body), result["repository_receipt_sha256"])
        self.assertIs(result["organization_receipt_committed"], False)
        self.assertNotIn("organization_receipt_sha256", result)
        self.assertEqual(self.org_receipts(), [])
        self.assertIn("repository_ledger:" + repository_ledger.ledger_store.receipt_key(
            result["repository_receipt_sha256"]), result["evidence_refs"])

    def test_fault_after_the_organization_write_reads_it_back(self):
        real = organization_ledger.aggregate_transition

        def write_then_fail(*args, **kwargs):
            real(*args, **kwargs)
            raise RuntimeError("injected after the organization write")

        with mock.patch.object(organization_ledger, "aggregate_transition", write_then_fail):
            result, _ = self.receive(_plain_request(), hb_epoch=7001)
        self._assert_typed(result)
        self.assertIs(result["organization_receipt_committed"], True)
        row = self.org_receipt(result["organization_receipt_sha256"])
        self.assertEqual(row["repo_receipt_sha256"], result["repository_receipt_sha256"])
        self.assertIs(result["organization_runtime_transition_committed"], False)

    def test_unreadable_repository_receipt_is_unobserved_not_committed(self):
        def lose_repository_receipt_then_fail(receipt, **kwargs):
            # The store no longer returns the bytes the append reported writing.
            (self.repo_root / repository_ledger.ledger_store.receipt_key(
                receipt["receipt_sha256"])).unlink()
            raise RuntimeError("injected")

        with mock.patch.object(organization_ledger, "aggregate_transition",
                               lose_repository_receipt_then_fail):
            result, _ = self.receive(_plain_request(), hb_epoch=7002)
        self._assert_typed(result)
        self.assertEqual(result["repository_receipt_committed"], "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertNotIn("repository_receipt_sha256", result)

    def test_unsupplied_organization_root_names_its_repair(self):
        with mock.patch.dict(os.environ):
            del os.environ["STEGVERSE_ORG_LEDGER_ROOT"]
            result, _ = self.receive(_plain_request(), hb_epoch=7003)
        self._assert_typed(result)
        self.assertIs(result["repository_receipt_committed"], True)
        self.assertEqual(result["organization_receipt_committed"], "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
        self.assertEqual(result["required_evidence_or_repair"],
                         "supply the organization ledger root as STEGVERSE_ORG_LEDGER_ROOT")

    def test_refusal_path_partial_commit_keeps_its_own_predicate(self):
        with mock.patch.object(organization_ledger, "aggregate_transition",
                               side_effect=RuntimeError("injected")):
            result = ingress.receive({"processing": {"capability": "x"}}, registry={}, hb_epoch=7004)
        self._assert_typed(result)
        self.assertIs(result["repository_receipt_committed"], True)
        self.assertEqual(result["refusal_failed_predicate"],
                         "ORGANIZATION_RESOLVES_ITS_OWN_INGRESS_DESTINATION")
        self.assertIs(result["refusal_recorded"], False)


class AppendOwnerGuardTest(unittest.TestCase):
    def test_every_ledger_attribute_the_ingress_uses_exists(self):
        source = (ROOT / "resident-runtime/organization_manifest_ingress.py").read_text()
        for name, module in (("organization_ledger", organization_ledger),
                             ("repository_ledger", repository_ledger)):
            used = set(re.findall(rf"\b{name}\.([A-Za-z_]\w*)", source))
            self.assertTrue(used, name)
            for attribute in sorted(used):
                self.assertTrue(hasattr(module, attribute), f"{name}.{attribute} does not exist")
        self.assertNotIn("organization_ledger.append(", source)


if __name__ == "__main__":
    unittest.main()
