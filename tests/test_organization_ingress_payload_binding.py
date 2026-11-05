"""Ingress binds the crossing to the exact payload of the manifest it was delivered.

`receive` reconstructs every boundary receipt and chains them, but each receipt
is bound to the crossing's own `payload_hash`, and nothing recomputed that
digest from the manifest `receive` was handed. A crossing whose observed effect
(`application_result.echo.manifest`) was changed and whose `manifest_sha256`
was zeroed, with `payload_hash` left as it was, still reconstructed all five
closures and was admitted (review of StegVerse-Labs/.github#3375, issue #3369:
"exact-byte payload identity and binding").

These cases drive the real crossing -- `sdk_manifest_crossing.cross`, the real
`process_boundary.py` subprocess and the real `reconstruct_closures` -- against
this organization's own service registry, on the boundary-local diagnostic
service, whose application result echoes the payload it received. Only the
SDK's request derivation and result admission are stubbed, and the tamper is
applied to what the crossing returns. They assert that an untampered crossing
is admitted, and that each tamper is refused FAIL_CLOSED under
`CROSSING_PAYLOAD_RECOMPUTES_FROM_THE_DELIVERED_MANIFEST`, recorded as a
refusal, with nothing admitted on either ledger.

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
    "organization_ingress_payload_binding_subject",
    ROOT / "resident-runtime/organization_manifest_ingress.py")
ingress = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingress)
crossing_module = ingress.crossing_module

PREDICATE = "CROSSING_PAYLOAD_RECOMPUTES_FROM_THE_DELIVERED_MANIFEST"
FAILURE_CODE = "CROSSING_PAYLOAD_NOT_BOUND_TO_THE_DELIVERED_MANIFEST"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
ADMITTED_CLASS_PREFIX = "ORGANIZATION-SDK-MANIFEST-INGRESS-"
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))

#: A manifest bound to the boundary-local diagnostic surface over InTr. Its far
#: side echoes the payload it received, which is the observed effect tampered.
MANIFEST = {
    "processing": {"capability": "ecosystem_diagnostic",
                   "route_id": "stegverse.route.ecosystem-diagnostic.v1"},
    "completion": {"egress": {"final_stegverse_transition_surface": "boundary_diagnostic",
                              "transport": "INTERLOCK_INTR",
                              "far_side_transition_required": True}},
    "transition": {"authority_effect": "NONE"},
    "data": {"value": 1},
}
STANDING = {"mode": "ESTABLISH_GENESIS", "node_ref": "payload-binding-test",
            "generation": 1, "predecessor": None}


def request() -> dict:
    digest = ingress.sha(MANIFEST)
    return {"request_sha256": "b" * 64, "wire_manifest_sha256": digest,
            "canonical_manifest_sha256": digest, "graph_id": "graph-1",
            "canonical_task_id": "task-1", "processing_capability": "ecosystem_diagnostic",
            "route_id": "stegverse.route.ecosystem-diagnostic.v1",
            "destination_resolution_source": "ORGANIZATION_BOUNDARY"}


def reseal_chain(crossing: dict, payload_hash: str) -> dict:
    """The same crossing with its boundary receipts recomputed over another payload digest.

    Every receipt is derivable from public fields, so a crossing can carry a
    chain that reconstructs under any digest it names.
    """
    crossing = copy.deepcopy(crossing)
    base = {"packet_id": crossing["ingress_packet_id"],
            "service_id": crossing["resolved_service_id"], "payload_hash": payload_hash}
    previous = None
    for receipt in crossing["boundary_receipts"]:
        digest = ingress.sha({**base, "kind": receipt["kind"], "previous_receipt_id": previous})
        receipt.update({"previous_receipt_id": previous, "evidence_hash": digest,
                        "receipt_id": receipt["kind"].lower() + "-" + digest[:24]})
        previous = receipt["receipt_id"]
    crossing["payload_hash"] = payload_hash
    crossing["terminal_receipt_id"] = previous
    return crossing


class PayloadBindingCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        base = Path(self._temp.name)
        self.repo_root, self.org_root = base / "repo", base / "org"
        self.tamper = None
        real_cross = crossing_module.cross

        def cross(*args, **kwargs):
            crossing = real_cross(*args, **kwargs)
            self.crossed = copy.deepcopy(crossing)
            return self.tamper(copy.deepcopy(crossing)) if self.tamper else crossing

        patches = [
            mock.patch.dict(os.environ, {"GITHUB_SHA": REVISION,
                                         "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root),
                                         "STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root)}),
            mock.patch.object(ingress, "derive_execution_request", lambda m, b: request()),
            mock.patch.object(ingress, "bound_here", lambda r: {"operation": "receive"}),
            mock.patch.object(ingress, "admit_runtime_result", lambda *a: {"admitted": True}),
            mock.patch.object(crossing_module, "cross", cross),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def receive(self):
        return ingress.receive(copy.deepcopy(MANIFEST), registry=REGISTRY,
                               standing=dict(STANDING), packet_id="payload-binding-1")

    def receipts(self, root: Path) -> list[dict]:
        directory = root / "receipts"
        return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))] \
            if directory.is_dir() else []

    def admitted_receipts(self) -> list[dict]:
        return [r for r in self.receipts(self.repo_root)
                if r.get("transition_class") != ingress.REFUSED_CLASS]

    def assertRefusedUnbound(self, result: dict, detail_prefix: str) -> None:
        self.assertEqual(result["disposition"], "FAIL_CLOSED", result)
        self.assertEqual(result["failed_predicate"], PREDICATE, result)
        self.assertEqual(result["failure_code"], FAILURE_CODE, result)
        self.assertTrue(result["detail"].startswith(detail_prefix), result["detail"])
        self.assertIs(result["received"], False)
        self.assertIs(result["organization_receipt_observed"], False)
        self.assertIs(result["refusal_recorded"], True)
        self.assertEqual(result["authority_effect"], "NONE_REFUSAL_ONLY")
        for field in SIX_FIELDS:
            self.assertIn(field, result)
        # Nothing admitted at the repository level; the refusal is what was recorded.
        self.assertEqual(self.admitted_receipts(), [])
        refusals = [r for r in self.receipts(self.repo_root)
                    if r.get("transition_class") == ingress.REFUSED_CLASS]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["evidence"]["failed_predicate"], PREDICATE)


class UntamperedCrossingTests(PayloadBindingCase):
    def test_an_untampered_crossing_is_admitted(self):
        result = self.receive()
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertIs(result["organization_receipt_observed"], True)
        self.assertEqual(len(self.admitted_receipts()), 1)

    def test_the_far_side_echo_is_the_payload_the_crossing_hashed(self):
        """The boundary echoes what it hashed, so the echo binds to `payload_hash`."""
        self.receive()
        echoed = self.crossed["application_result"]["echo"]
        self.assertEqual(ingress.sha(echoed), self.crossed["payload_hash"])
        self.assertEqual(echoed["manifest"], MANIFEST)
        self.assertEqual(self.crossed["manifest_sha256"], "sha256:" + ingress.sha(MANIFEST))


class TamperedCrossingTests(PayloadBindingCase):
    def test_a_changed_echoed_effect_under_an_unchanged_payload_hash_is_refused(self):
        def changed_effect(crossing):
            crossing["application_result"]["echo"]["manifest"] = {**MANIFEST, "data": {"value": 2}}
            return crossing

        self.tamper = changed_effect
        result = self.receive()
        self.assertEqual(self.crossed["payload_hash"],
                         ingress.sha(self.crossed["application_result"]["echo"]))
        self.assertRefusedUnbound(result, "CROSSING_ECHOED_PAYLOAD_MISMATCH:")

    def test_a_zeroed_manifest_sha256_is_refused(self):
        def zeroed(crossing):
            crossing["manifest_sha256"] = "sha256:" + "0" * 64
            return crossing

        self.tamper = zeroed
        self.assertRefusedUnbound(self.receive(), "CROSSING_MANIFEST_SHA256_MISMATCH:")

    def test_the_reviewed_tamper_changed_effect_and_zeroed_digest_is_refused(self):
        """The #3375 review: effect changed, manifest_sha256 zeroed, payload_hash kept."""
        def reviewed(crossing):
            crossing["application_result"]["echo"]["manifest"] = {**MANIFEST, "data": {"value": 2}}
            crossing["manifest_sha256"] = "sha256:" + "0" * 64
            return crossing

        self.tamper = reviewed
        result = self.receive()
        # The chain still reconstructs: the closures alone do not see this tamper.
        self.assertEqual(len(ingress.reconstruct_closures(reviewed(copy.deepcopy(self.crossed)))), 5)
        self.assertRefusedUnbound(result, "CROSSING_MANIFEST_SHA256_MISMATCH:")

    def test_a_payload_hash_resealed_into_a_reconstructing_chain_is_refused(self):
        """A chain that reconstructs under a digest other than the delivered payload's."""
        other = ingress.sha({"another": "payload"})
        self.tamper = lambda crossing: reseal_chain(crossing, other)
        result = self.receive()
        self.assertEqual(len(ingress.reconstruct_closures(reseal_chain(self.crossed, other))), 5)
        self.assertRefusedUnbound(result, "CROSSING_PAYLOAD_HASH_MISMATCH:")

    def test_a_crossing_naming_no_digests_is_refused(self):
        def stripped(crossing):
            crossing.pop("manifest_sha256")
            return crossing

        self.tamper = stripped
        self.assertRefusedUnbound(self.receive(), "CROSSING_MANIFEST_SHA256_MISMATCH:")


if __name__ == "__main__":
    unittest.main()
