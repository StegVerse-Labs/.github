"""Ingress checks a declared VERIFY_EXISTING predecessor against its own ledger before the crossing.

StegVerse-Labs/.github#3369 gap 2 (stale head / fence), the head half, option
2A of `design/INGRESS_GAP_OPTIONS_3369.md`. A declared standing in
VERIFY_EXISTING mode names a predecessor (the lineage contract's field set:
generation, manifest_sha256, result_sha256, heartbeat_epoch). `receive()` now
requires, before `cross()`, that this repository's ledger records an admission
for the same node_ref at `predecessor.generation` whose canonical manifest
digest is `predecessor.manifest_sha256` (FAIL_CLOSED
`DECLARED_PREDECESSOR_NOT_RECORDED` otherwise), and that no other recorded
successor of that node has already bound that predecessor (DENY
`DECLARED_PREDECESSOR_SUPERSEDED`). Shape and successor arithmetic stay with
the standing contract at the boundary; a redelivery of a recorded admission is
the recorded transition. `result_sha256` is not compared: no receipt records a
result digest, and the result says so.

These cases drive the real `receive()`, the real crossing and the real
`process_boundary.py` subprocess against temporary ledger roots. Only the SDK's
request derivation, the binding resolution and result admission are stubbed.

Source validation only. Nothing is minted; the ledger is only read.
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
    "organization_ingress_declared_predecessor_subject",
    ROOT / "resident-runtime/organization_manifest_ingress.py")
ingress = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingress)
crossing_module = ingress.crossing_module

PREDICATE = "DECLARED_PREDECESSOR_IS_RECORDED_AND_UNSUPERSEDED_IN_THIS_LEDGER"
NOT_RECORDED = "DECLARED_PREDECESSOR_NOT_RECORDED"
SUPERSEDED = "DECLARED_PREDECESSOR_SUPERSEDED"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))
NODE = "predecessor-test-node"
RESULT_DIGEST = "1" * 64


def manifest(value) -> dict:
    return {
        "processing": {"capability": "ecosystem_diagnostic",
                       "route_id": "stegverse.route.ecosystem-diagnostic.v1"},
        "completion": {"egress": {"final_stegverse_transition_surface": "boundary_diagnostic",
                                  "transport": "INTERLOCK_INTR",
                                  "far_side_transition_required": True}},
        "transition": {"authority_effect": "NONE"},
        "data": {"value": value},
    }


def genesis() -> dict:
    return {"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "generation": 1, "predecessor": None}


def successor(predecessor_manifest, *, generation=2, predecessor_generation=1) -> dict:
    return {"mode": "VERIFY_EXISTING", "node_ref": NODE, "generation": generation,
            "predecessor": {"generation": predecessor_generation,
                            "manifest_sha256": ingress.sha(predecessor_manifest),
                            "result_sha256": RESULT_DIGEST, "heartbeat_epoch": 1}}


def request(manifest) -> dict:
    # As the SDK derives it: the wire manifest and its validated projection are
    # bound separately, and a predecessor binding is the digest of the wire body.
    digest = ingress.sha(manifest)
    return {"request_sha256": ingress.sha({"manifest": digest}), "wire_manifest_sha256": digest,
            "canonical_manifest_sha256": ingress.sha({"projection": manifest}), "graph_id": "graph-1",
            "canonical_task_id": "task-1", "processing_capability": "ecosystem_diagnostic",
            "route_id": "stegverse.route.ecosystem-diagnostic.v1",
            "destination_resolution_source": "ORGANIZATION_BOUNDARY"}


class DeclaredPredecessorCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo", base / "org"
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
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def receive(self, manifest, standing, packet="predecessor-1"):
        return ingress.receive(manifest, registry=REGISTRY, standing=dict(standing), packet_id=packet)

    def receipts(self, root: Path) -> list[dict]:
        directory = root / "receipts"
        return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))] \
            if directory.is_dir() else []

    def admit(self, manifest, standing):
        before = len(self.crossings)
        result = self.receive(manifest, standing)
        self.assertEqual(result["disposition"], "ALLOW", result.get("detail"))
        self.assertEqual(len(self.crossings), before + 1)
        return result

    def assertRefusedBeforeCrossing(self, result, manifest, code, disposition) -> None:
        self.assertEqual(result["disposition"], disposition, result)
        self.assertEqual(result["failed_predicate"], PREDICATE, result)
        self.assertEqual(result["failure_code"], code, result)
        self.assertTrue(result["detail"].startswith(code + ":"), result["detail"])
        for field in SIX_FIELDS:
            self.assertTrue(result.get(field), field)
        self.assertEqual(result["owning_existing_goal"], ingress.PREDECESSOR_OWNING_GOAL)
        self.assertIs(result["next_attempt"]["awaits_an_external_machine"], False)
        self.assertIs(result["received"], False)
        self.assertIs(result["refusal_recorded"], True)
        self.assertEqual(result["authority_effect"], "NONE_REFUSAL_ONLY")
        self.assertEqual(result["request_sha256"], request(manifest)["request_sha256"])
        repository = [r for r in self.receipts(self.repo_root) if r["transition_class"] == ingress.REFUSED_CLASS]
        self.assertEqual(len(repository), 1)
        self.assertEqual(repository[0]["receipt_sha256"], result["refusal_repository_receipt_sha256"])
        self.assertEqual(repository[0]["evidence"]["failed_predicate"], PREDICATE)
        self.assertEqual(repository[0]["authority_effect"], "NONE")


class LineageTests(DeclaredPredecessorCase):
    def test_a_recorded_predecessor_admits_its_successor(self):
        first = manifest(1)
        genesis_result = self.admit(first, genesis())
        self.assertIsNone(genesis_result["declared_predecessor_result_binding"])
        second = self.admit(manifest(2), successor(first))
        self.assertEqual(second["declared_predecessor_result_binding"], ingress.PREDECESSOR_RESULT_BINDING)
        self.assertEqual(second["declared_predecessor_record"], ingress.PREDECESSOR_RECORD_FULL)
        self.assertIsNone(genesis_result["declared_predecessor_record"])
        self.assertEqual(len([r for r in self.receipts(self.repo_root)
                              if r["transition_class"] == ingress.OPERATION_ID]), 2)

    def test_the_recorded_admission_carries_the_standing_the_check_reads(self):
        first = manifest(1)
        self.admit(first, genesis())
        receipt, = self.receipts(self.repo_root)
        self.assertEqual(receipt["evidence"]["crossing"]["standing"], genesis())
        self.assertEqual(receipt["evidence"]["wire_manifest_sha256"], ingress.sha(first))
        self.assertNotEqual(receipt["evidence"]["canonical_manifest_sha256"], ingress.sha(first))

    def test_a_chain_of_three_generations_admits_in_order(self):
        first, second, third = manifest(1), manifest(2), manifest(3)
        self.admit(first, genesis())
        self.admit(second, successor(first))
        self.admit(third, successor(second, generation=3, predecessor_generation=2))

    def test_receipt_bytes_carry_nothing_of_the_check(self):
        first = manifest(1)
        self.admit(first, genesis())
        self.admit(manifest(2), successor(first))
        for receipt in self.receipts(self.repo_root) + self.receipts(self.org_root):
            self.assertNotIn("declared_predecessor_result_binding", json.dumps(receipt))


class RecordShapeTests(DeclaredPredecessorCase):
    """What counts as a recorded admission, and what the check tolerates."""

    def test_a_genesis_recorded_without_a_generation_key_is_generation_one(self):
        first = manifest(1)
        self.admit(first, {"mode": "ESTABLISH_GENESIS", "node_ref": NODE, "predecessor": None})
        second = self.admit(manifest(2), successor(first))
        self.assertEqual(second["declared_predecessor_record"], ingress.PREDECESSOR_RECORD_FULL)

    def test_an_admission_recorded_before_standings_were_recorded_matches_on_its_digest(self):
        first = manifest(1)
        self.admit(first, genesis())
        real = ingress.admitted_ingress_receipts

        def legacy():
            stripped = []
            for receipt in real():
                receipt = json.loads(json.dumps(receipt))
                receipt["evidence"]["crossing"].pop("standing", None)
                stripped.append(receipt)
            return stripped

        with mock.patch.object(ingress, "admitted_ingress_receipts", legacy):
            second = self.admit(manifest(2), successor(first))
        self.assertEqual(second["declared_predecessor_record"], ingress.PREDECESSOR_RECORD_LEGACY)

    def test_a_repository_receipt_without_its_organization_receipt_is_not_an_admission(self):
        first = manifest(1)
        self.admit(first, genesis())
        attempt = manifest(2)
        with mock.patch.object(ingress, "_organization_receipt_read_back", lambda sha: (False, None)):
            result = self.receive(attempt, successor(first))
        self.assertRefusedBeforeCrossing(result, attempt, NOT_RECORDED, "FAIL_CLOSED")
        self.assertIn("with its organization receipt", result["detail"])

    def test_an_unreadable_ledger_fails_closed(self):
        first = manifest(1)
        self.admit(first, genesis())
        attempt = manifest(2)
        with mock.patch.object(ingress, "admitted_ingress_receipts", lambda: None):
            result = self.receive(attempt, successor(first))
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], NOT_RECORDED)
        self.assertIn("could not be read", result["detail"])

    def test_the_chain_is_walked_once_per_ingress(self):
        first = manifest(1)
        self.admit(first, genesis())
        real = ingress.admitted_ingress_receipts
        calls = []

        def counted():
            calls.append(1)
            return real()

        with mock.patch.object(ingress, "admitted_ingress_receipts", counted):
            self.admit(manifest(2), successor(first))
        self.assertEqual(len(calls), 1)

    def test_a_malformed_predecessor_digest_is_left_to_the_boundary(self):
        standing = successor(manifest(1))
        standing["predecessor"]["manifest_sha256"] = "sha256:" + "a" * 64
        self.assertIsNone(ingress.declared_predecessor_failure(standing, request(manifest(2)), []))


class NotRecordedTests(DeclaredPredecessorCase):
    def test_a_predecessor_this_ledger_never_admitted_is_refused(self):
        never = manifest(0)
        attempt = manifest(2)
        result = self.receive(attempt, successor(never))
        self.assertRefusedBeforeCrossing(result, attempt, NOT_RECORDED, "FAIL_CLOSED")
        self.assertEqual(self.crossings, [])
        self.assertEqual(result["next_attempt"]["resubmit"],
                         "THE_MANIFEST_WITH_A_PREDECESSOR_THIS_LEDGER_RECORDS")

    def test_a_predecessor_recorded_under_another_node_is_not_this_nodes(self):
        first = manifest(1)
        self.admit(first, genesis())
        standing = successor(first)
        standing["node_ref"] = "some-other-node"
        attempt = manifest(2)
        result = self.receive(attempt, standing)
        self.assertRefusedBeforeCrossing(result, attempt, NOT_RECORDED, "FAIL_CLOSED")

    def test_a_predecessor_recorded_at_another_generation_is_refused(self):
        first = manifest(1)
        self.admit(first, genesis())
        attempt = manifest(3)
        result = self.receive(attempt, successor(first, generation=3, predecessor_generation=2))
        self.assertRefusedBeforeCrossing(result, attempt, NOT_RECORDED, "FAIL_CLOSED")

    def test_an_empty_ledger_records_no_predecessor(self):
        attempt = manifest(2)
        result = self.receive(attempt, successor(manifest(1)))
        self.assertRefusedBeforeCrossing(result, attempt, NOT_RECORDED, "FAIL_CLOSED")
        self.assertIn("no admission for node", result["detail"])


class SupersededTests(DeclaredPredecessorCase):
    def test_a_second_successor_of_the_same_predecessor_is_denied(self):
        first = manifest(1)
        self.admit(first, genesis())
        self.admit(manifest(2), successor(first))
        fork = manifest(22)
        result = self.receive(fork, successor(first))
        self.assertRefusedBeforeCrossing(result, fork, SUPERSEDED, "DENY")
        self.assertEqual(len(self.crossings), 2)
        self.assertIn("already bound by the recorded successor", result["detail"])
        self.assertEqual(result["next_attempt"]["resubmit"],
                         "THE_SUCCESSOR_OF_THE_RECORDED_HEAD_FOR_THIS_NODE")

    def test_the_recorded_successor_redelivered_is_the_recorded_transition(self):
        first, second = manifest(1), manifest(2)
        self.admit(first, genesis())
        admitted = self.admit(second, successor(first))
        replay = self.receive(copy.deepcopy(second), successor(first), packet="predecessor-redelivery")
        self.assertEqual(replay["disposition"], "ALLOW", replay.get("detail"))
        self.assertIs(replay["transition_replayed"], True)
        self.assertEqual(replay["organization_receipt_sha256"], admitted["organization_receipt_sha256"])
        self.assertEqual(len([r for r in self.receipts(self.repo_root)
                              if r["transition_class"] == ingress.OPERATION_ID]), 2)


class BoundaryKeepsItsOwnRefusalsTests(DeclaredPredecessorCase):
    """Shape and successor arithmetic are the standing contract's at the boundary."""

    def test_a_non_successor_generation_reaches_the_boundary_and_is_refused_there(self):
        first = manifest(1)
        self.admit(first, genesis())
        result = self.receive(manifest(3), successor(first, generation=3, predecessor_generation=1))
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertNotEqual(result["failed_predicate"], PREDICATE)
        self.assertIn("generation-not-successor", result["detail"])
        self.assertEqual(len(self.crossings), 2)

    def test_genesis_is_never_checked_against_the_ledger(self):
        self.admit(manifest(1), genesis())
        again = self.admit(manifest(5), {**genesis(), "node_ref": "another-node"})
        self.assertIsNone(again["declared_predecessor_result_binding"])

    def test_a_malformed_predecessor_is_left_to_the_boundary(self):
        standing = {"mode": "VERIFY_EXISTING", "node_ref": NODE, "generation": 2,
                    "predecessor": "not-an-object"}
        self.assertIsNone(ingress.declared_predecessor_failure(standing, request(manifest(2))))


class PredicateTests(unittest.TestCase):
    def test_the_owning_goal_is_registered(self):
        self.assertTrue((ROOT / "data/canonical-task-records"
                         / f"{ingress.PREDECESSOR_OWNING_GOAL}.json").is_file())

    def test_result_binding_is_declared_not_checked(self):
        self.assertIn("NOT_CHECKED", ingress.PREDECESSOR_RESULT_BINDING)


if __name__ == "__main__":
    unittest.main()
