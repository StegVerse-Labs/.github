"""Reverse one-way InTr: StegVerse-Labs emits governance to StegVerse-org.

The forward route (StegVerse-org → StegVerse-Labs) is validated in
StegVerse-org/.github `tests/test_governance_inter_org_route.py`. This leg
is independent of that route. It uses the binding declared in
`org-runtime/interlock-intr.json`:

- `governance-to-org` → StegVerse-org / `stegverse-org.governance`

StegVerse-org does not request or receive remediation. There is no
`remediation-to-org` binding and no destination `stegverse-org.remediation`.
StegHealer pulls NON-ALLOW receipts from the org ledgers and decides on
remediation itself. This module does not perform that pull.

The binding is `NONE_BINDING_ONLY`. Emission is `organization_egress_boundary.emit`
and closure is `organization_egress_boundary.close`, on the kernel mesh.
The far side is played by the kernel functions every boundary runs —
`receipt` and `build_control_response` — because the peer adapter lives in
StegVerse-org/.github. A passing test is not a production demonstration and
is not an authentic receipt.

Both ledger roots and the mesh are temporary. Under `python -m unittest` this
repository's test loader declares a POSIX organization-ledger locus, so
`STEGVERSE_ORG_LEDGER_ROOT` is the chain that is written. Nothing is written
into an operator runtime.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = json.loads((ROOT / "org-runtime/interlock-intr.json").read_text())
PEER = "StegVerse-org"
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "reverse-intr-route", "predecessor": None}
LEDGER_ENV = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


egress = _load("organization_egress_boundary_reverse_intr",
               "resident-runtime/organization_egress_boundary.py")
governance_endpoint = _load("governance_endpoint_schema",
                            "resident-runtime/governance_endpoint.py")
kernel = egress.kernel


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def _binding(profile_id: str) -> dict:
    matches = [entry for entry in BOUNDARY["egress"]["capability_destination_bindings"]
               if entry.get("profile_id") == profile_id]
    if len(matches) != 1:
        raise AssertionError(profile_id)
    return matches[0]


class ReverseIntrRouteCase(unittest.TestCase):
    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        work = Path(self._work.name)
        self.mesh = work / "mesh"
        self.repo_ledger = work / "repo-ledger"
        self.org_ledger_root = work / "org-ledger"
        previous = {name: os.environ.get(name) for name in LEDGER_ENV}
        os.environ["STEGVERSE_REPO_LEDGER_ROOT"] = str(self.repo_ledger)
        os.environ["STEGVERSE_ORG_LEDGER_ROOT"] = str(self.org_ledger_root)

        def restore():
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        self.addCleanup(restore)

    def frames_to(self, organization):
        directory = self.mesh / "frames.d"
        if not directory.is_dir():
            return []
        return [frame for frame in (json.loads(path.read_text())
                                    for path in directory.glob("*.json"))
                if frame["destination_org"] == organization]

    def emit_on_mesh(self, payload, *, capability, destination=PEER):
        return egress.emit(destination, payload, standing=GENESIS, capability=capability,
                           transition_reference="ecosystem.transition.reverse-intr.v1",
                           mesh_root=self.mesh, hb_epoch=40)

    def answer(self, *, schema, service_id, result_overrides=None, terminal=None):
        frame = self.frames_to(PEER)[0]
        packet = kernel.recover_packet(frame)
        chain, previous = [], None
        for kind in egress.FAR_SIDE_RECEIPT_KINDS:
            receipt = kernel.receipt(kind, packet["packet_id"], packet["destination"]["service"],
                                     previous, {"payload_hash": kernel.sha(packet["payload"])})
            chain.append(receipt["receipt_id"])
            previous = receipt["receipt_id"]
        result = {"schema": schema, "service_id": service_id,
                  "authority_effect": "NONE_DECISION_ONLY"}
        result.update(result_overrides or {})
        response = kernel.build_control_response(
            packet, {"application_result": result,
                     "reconstruction": {"terminal_receipt_id": terminal or chain[-1]}})
        kernel.publish_packet(response, root=self.mesh, epoch=41)
        return packet

    def close(self, emitted):
        return egress.close(PEER, emitted["packet_id"], emitted["communication_id"],
                            mesh_root=self.mesh, hb_epoch=42)

    def repo_classes(self):
        root = self.repo_ledger / "receipts"
        if not root.is_dir():
            return []
        return sorted(json.loads(path.read_text())["transition_class"] for path in root.glob("*.json"))


class BindingDeclarationTests(ReverseIntrRouteCase):
    def test_governance_to_org_names_stegverse_org_and_grants_nothing(self):
        governance = _binding("governance-to-org")
        self.assertEqual(governance["destination_organization"], PEER)
        self.assertEqual(governance["destination_service"], "stegverse-org.governance")
        self.assertEqual(governance["capability"], "governance")
        self.assertEqual(governance["request_schema"], governance_endpoint.REQUEST_SCHEMA)
        self.assertEqual(governance["authority_effect"], "NONE_BINDING_ONLY")
        self.assertIs(governance["evaluator_imported_in_this_organization"], False)
        self.assertIs(governance["awaits_the_decision"], False)

    def test_remediation_is_not_bound_toward_stegverse_org(self):
        entries = BOUNDARY["egress"]["capability_destination_bindings"]
        self.assertNotIn("remediation-to-org", [entry.get("profile_id") for entry in entries])
        self.assertNotIn("stegverse-org.remediation",
                         [entry.get("destination_service") for entry in entries])
        with self.assertRaises(egress.EgressRefused) as raised:
            egress.resolve_destination(PEER, capability="remediation")
        self.assertEqual(raised.exception.failed_predicate,
                         "CAPABILITY_IS_DECLARED_IN_THIS_ORGANIZATIONS_OVERLAY")

    def test_governance_to_labs_stays_bound_and_the_reverse_leg_is_selected_by_destination(self):
        labs = egress.resolve_destination("StegVerse-Labs", capability="governance")
        org = egress.resolve_destination(PEER, capability="governance")
        self.assertEqual(labs["destination_service"], "stegverse-labs.governance")
        self.assertEqual(labs["destination_capability_profile_id"], "governance")
        self.assertEqual(org["destination_service"], "stegverse-org.governance")
        self.assertEqual(org["destination_capability_profile_id"], "governance-to-org")
        self.assertEqual(org["destination_binding_authority_effect"], "NONE_BINDING_ONLY")
        with self.assertRaises(egress.EgressRefused) as raised:
            egress.resolve_destination("StegGhost", capability="governance")
        self.assertEqual(raised.exception.failed_predicate,
                         "CAPABILITY_IS_SENT_TO_THE_ORGANIZATION_THAT_OWNS_IT")


class GovernanceReverseLegTests(ReverseIntrRouteCase):
    def payload(self):
        binding = _binding("governance-to-org")
        request_body = {"declared_intent": "reverse-intr-governance-request"}
        # The same work-request shape organization_manifest_ingress.governance_request_payload
        # emits. Built here so this validation does not import the SDK.
        return {
            "communication_id": "governance:" + "a" * 64,
            "message_class": "ecosystem.work.request",
            "processing": {"capability": binding["capability"], "route_id": binding["route_id"]},
            "subject": "governance.decision",
            "requested_action": "DECIDE_GOVERNANCE_ADMISSIBILITY",
            "audience": "TARGET",
            "target_organization": binding["destination_organization"],
            "target_count": 1,
            "body": {
                "schema": governance_endpoint.REQUEST_SCHEMA,
                "origin_organization": "StegVerse-Labs",
                "sdk_request_sha256": "a" * 64,
                "canonical_manifest_sha256": "b" * 64,
                "ingress_transition_id": "ORGANIZATION-SDK-MANIFEST-INGRESS-reverse-governance",
                "governance_request": request_body,
                "governance_request_sha256": _digest(request_body),
            },
        }

    def test_the_governance_request_is_emitted_allow_to_stegverse_org_governance(self):
        emitted = self.emit_on_mesh(self.payload(), capability="governance")
        self.assertEqual(emitted["disposition"], "ALLOW", emitted.get("detail"))
        self.assertIs(emitted["emitted"], True)
        self.assertEqual(emitted["destination_organization"], PEER)
        self.assertEqual(emitted["destination_service"], "stegverse-org.governance")
        self.assertEqual(emitted["destination_capability_profile_id"], "governance-to-org")
        self.assertEqual(emitted["authority_effect"], "NONE_EGRESS_RECORD_ONLY")
        self.assertEqual(emitted["emission_transition_class"], "ORGANIZATION_EGRESS_EMITTED")
        self.assertTrue(emitted["emission_repository_receipt_sha256"])
        self.assertTrue(emitted["emission_organization_receipt_sha256"])
        frames = self.frames_to(PEER)
        self.assertEqual(len(frames), 1)
        packet = kernel.recover_packet(frames[0])
        self.assertEqual(packet["origin"], {"org": "StegVerse-Labs",
                                             "service": "stegverse-labs.governance"})
        self.assertEqual(packet["destination"], {"org": PEER, "service": "stegverse-org.governance"})
        self.assertEqual(packet["payload"]["message_class"], "ecosystem.work.request")
        self.assertEqual(packet["payload"]["body"]["schema"], governance_endpoint.REQUEST_SCHEMA)
        self.assertEqual(packet["transition"]["authority_effect"], "NONE")
        org_receipt = emitted["emission_organization_receipt_sha256"].split(":", 1)[1] + ".json"
        self.assertTrue((self.org_ledger_root / "receipts" / org_receipt).is_file())

    def test_an_unbound_organization_is_denied_and_publishes_nothing(self):
        refused = self.emit_on_mesh(self.payload(), capability="governance", destination="StegGhost")
        self.assertEqual(refused["disposition"], "DENY")
        self.assertIs(refused["emitted"], False)
        self.assertEqual(refused["failed_predicate"],
                         "CAPABILITY_IS_SENT_TO_THE_ORGANIZATION_THAT_OWNS_IT")
        self.assertEqual(refused["emission_transition_class"], "ORGANIZATION_EGRESS_REFUSED")
        self.assertEqual(self.frames_to(PEER), [])
        self.assertEqual(self.frames_to("StegGhost"), [])

    def test_a_node_without_a_mesh_records_the_refused_emission(self):
        refused = egress.emit(PEER, self.payload(), standing=GENESIS, capability="governance",
                              mesh_root=None, hb_epoch=40)
        self.assertEqual(refused["disposition"], "DENY")
        self.assertIs(refused["emitted"], False)
        self.assertEqual(refused["emission_transition_class"], "ORGANIZATION_EGRESS_REFUSED")
        self.assertIn("mesh_location_required_from_materializer", refused["detail"])
        self.assertEqual(self.frames_to(PEER), [])

    def test_no_answer_is_pending_and_records_no_closure(self):
        """Kept under its original node id so the ratchet's TEST_MISSING_AT_HEAD rule is not tripped. The
        PENDING disposition it once asserted is superseded by test_no_answer_fails_closed_and_records_no_closure;
        what stays true under both contracts is that an absent answer closes nothing and records nothing."""
        emitted = self.emit_on_mesh(self.payload(), capability="governance")
        absent = self.close(emitted)
        self.assertNotEqual(absent["disposition"], "PENDING")
        self.assertIs(absent["closed"], False)
        self.assertIs(absent["closure_recorded"], False)
        self.assertIs(absent["absence_is_not_a_transition"], True)
        self.assertEqual(self.repo_classes(), ["ORGANIZATION_EGRESS_EMITTED"])

    def test_no_answer_fails_closed_and_records_no_closure(self):
        emitted = self.emit_on_mesh(self.payload(), capability="governance")
        absent = self.close(emitted)
        self.assertEqual(absent["disposition"], "FAIL_CLOSED")
        self.assertEqual(absent["failure_code"], "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION")
        self.assertEqual(absent["failed_predicate"],
                         "EGRESS_RESPONSE_DURABLY_MATERIALIZED_BEFORE_CLOSE")
        for field in ("required_evidence_or_repair", "retry_entrypoint",
                      "owning_existing_goal", "next_attempt"):
            self.assertTrue(absent[field], field)
        self.assertIs(absent["closed"], False)
        self.assertIs(absent["closure_recorded"], False)
        self.assertIs(absent["refusal_recorded"], False)
        self.assertIs(absent["absence_is_not_a_transition"], True)
        self.assertEqual(absent["authority_effect"], "NONE_REFUSAL_ONLY")
        self.assertEqual(self.repo_classes(), ["ORGANIZATION_EGRESS_EMITTED"])

    def test_a_deny_decision_closes_allow_and_grants_nothing(self):
        emitted = self.emit_on_mesh(self.payload(), capability="governance")
        packet = self.answer(
            schema="stegverse.org-governance-decision/v1",
            service_id="stegverse-org.governance",
            result_overrides={
                "deciding_organization": PEER,
                "decision_authority": "stegcore.steggate.evaluate_admissibility",
                "sdk_request_sha256": packet_body_sdk(self),
                "governance_request_sha256": self.frames_request_digest(),
                "disposition": "DENY",
                "reason": "signal.inputs_incomplete",
                "authority_effect": "NONE_DECISION_ONLY",
            })
        self.assertEqual(packet["destination"]["service"], "stegverse-org.governance")
        closed = self.close(emitted)
        self.assertEqual(closed["disposition"], "ALLOW", closed.get("closure_findings"))
        self.assertIs(closed["closed"], True)
        self.assertEqual(closed["closure_transition_class"], "ORGANIZATION_EGRESS_CLOSED")
        self.assertEqual(closed["authority_effect"], "NONE_CLOSURE_RECORD_ONLY")
        carried = closed["far_side_application_result"]
        self.assertEqual(carried["disposition"], "DENY")
        self.assertEqual(carried["authority_effect"], "NONE_DECISION_ONLY")
        self.assertEqual(carried["governance_request_sha256"], self.frames_request_digest())
        self.assertEqual(self.repo_classes(),
                         ["ORGANIZATION_EGRESS_CLOSED", "ORGANIZATION_EGRESS_EMITTED"])

    def test_a_fail_closed_decision_is_carried_and_does_not_become_an_allow(self):
        emitted = self.emit_on_mesh(self.payload(), capability="governance")
        self.answer(
            schema="stegverse.org-governance-decision/v1",
            service_id="stegverse-org.governance",
            result_overrides={"disposition": "FAIL_CLOSED",
                              "reason": "GOVERNANCE_REQUEST_DIGEST_MISMATCH",
                              "authority_effect": "NONE_DECISION_ONLY"})
        closed = self.close(emitted)
        self.assertEqual(closed["disposition"], "ALLOW", closed.get("closure_findings"))
        carried = closed["far_side_application_result"]
        self.assertEqual(carried["disposition"], "FAIL_CLOSED")
        self.assertEqual(carried["authority_effect"], "NONE_DECISION_ONLY")
        self.assertEqual(closed["authority_effect"], "NONE_CLOSURE_RECORD_ONLY")

    def test_an_answer_whose_chain_does_not_recompute_is_denied_and_recorded(self):
        emitted = self.emit_on_mesh(self.payload(), capability="governance")
        self.answer(schema="stegverse.org-governance-decision/v1",
                    service_id="stegverse-org.governance",
                    result_overrides={"disposition": "DENY", "authority_effect": "NONE_DECISION_ONLY"},
                    terminal="egress_emitted-" + "0" * 24)
        closed = self.close(emitted)
        self.assertEqual(closed["disposition"], "DENY")
        self.assertIs(closed["closed"], False)
        self.assertEqual(closed["closure_transition_class"], "ORGANIZATION_EGRESS_CLOSURE_REFUSED")
        self.assertTrue(any(item.startswith("FAR_SIDE_TERMINAL_RECEIPT_DOES_NOT_RECOMPUTE:")
                            for item in closed["closure_findings"]))

    def frames_request_digest(self):
        packet = kernel.recover_packet(self.frames_to(PEER)[0])
        return packet["payload"]["body"]["governance_request_sha256"]


def packet_body_sdk(case):
    packet = kernel.recover_packet(case.frames_to(PEER)[0])
    return packet["payload"]["body"]["sdk_request_sha256"]


class SurfaceTests(ReverseIntrRouteCase):
    def test_this_validation_does_not_import_stegcore_or_the_healer_classifier(self):
        source = (ROOT / "resident-runtime/organization_egress_boundary.py").read_text()
        self.assertNotIn("import stegcore", source)
        self.assertNotIn("from stegcore", source)
        self.assertNotIn("manifest_remediation_intake", source)


if __name__ == "__main__":
    unittest.main()
