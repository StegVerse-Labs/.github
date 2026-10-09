"""Origin is attested by TV/TVC, not asserted by the sender.

Every inter-organization record carried `origin_attestation_state: NOT_PROVEN`
with `origin_is_asserted_by_the_sender: true`, and measured against RE's
disorder classes that single dimension was the entire score:
`unresolved_actor_identity` at 1.0, all nine others at zero.

`docs/NODE_INGRESS_SETTLED_SPECIFICATION.md` section 4 settled how to close it
and said it needs no new capability: TV/TVC already holds
`TV_EXPORT_HMAC_SIGN` and `TV_EXPORT_HMAC_VERIFY`, keyed from a systemd
credential on a TV/TVC resident host with no development fallback. The caller
cannot forge an attestation because it holds no key. Neither can this boundary.
It asks.

These assert the properties that make the attestation worth the field it fills:
the statement binds the whole crossing so a signature cannot be moved to
another origin, packet, payload or destination; the receiver reconstructs the
statement from the packet rather than being handed a copy it could edit; an
unreachable authority is a hold and never a pass; an offered attestation that
fails is distinct from one never offered; no verification algorithm lives here;
and what attestation does *not* establish is carried with every record.

The conformance against TV/TVC's own functions is a separate module, because
`StegVerse-Labs/tvc` cannot be checked out by this repository's CI without a
credential and `github_token_runtime_authority` is NONE.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = "docs/CANONICAL_NODE_INGRESS_CONTRACT_001.json"
MODULE = "org-boundary/runtime/origin_attestation.py"

PEER = "StegVerse-Labs"
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "attestation", "predecessor": None}


def _module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


attestation = _module("origin_attestation", MODULE)
egress = _module("organization_egress_boundary",
                 "resident-runtime/organization_egress_boundary.py")
kernel = egress.kernel

BOUNDARY = json.loads((ROOT / "org-runtime/interlock-intr.json").read_text())


def declared(**overrides):
    body = {"origin_organization": "StegVerse-org",
            "destination_organization": PEER,
            "destination_service": "stegverse-labs.sdk-manifest-ingress",
            "packet_id": "attestation-test-1",
            "payload_sha256": kernel.sha({"probe": True}),
            "transport_profile": "stegverse.intr.org-boundary.v1"}
    body.update(overrides)
    return attestation.statement(**body)


class StandInAuthority:
    """A credential authority that holds the key and answers as TV/TVC does.

    It reproduces the authority's *receipt contract*, not its algorithm: this
    class is the authority's side of the boundary, which is exactly the side
    this repository does not implement. `tests/test_origin_attestation_tvc_
    conformance.py` runs the same exchange against TV/TVC's real functions.
    """

    def __init__(self, key=b"stand-in-key"):
        self.key = key
        self.signed = []

    def _hmac(self, payload):
        import hashlib
        import hmac
        digest = hashlib.sha256(payload).hexdigest()
        return digest, hmac.new(self.key, digest.encode("ascii"), hashlib.sha256).hexdigest()

    def sign(self, *, payload):
        digest, value = self._hmac(payload)
        self.signed.append(digest)
        return {"algo": "hmac-sha256", "value": value, "sha256": digest}

    def verify(self, *, payload, signature_bytes):
        carried = json.loads(signature_bytes.decode("utf-8"))
        digest, value = self._hmac(payload)
        if carried.get("sha256") != digest:
            raise ValueError("TV signature export digest mismatch")
        return {"schema_version": "stegverse.tvc.tv-verification-receipt.v1",
                "credential_authority": "TV/TVC",
                "operation": "TV_EXPORT_HMAC_VERIFY",
                "export_sha256": digest,
                "signature_sha256": "sha-of-artifact",
                "signature_algorithm": "hmac-sha256",
                "signature_valid": carried.get("value") == value}

    def mapping(self):
        return {"sign": self.sign, "verify": self.verify}


class StatementTests(unittest.TestCase):
    def test_every_bound_field_is_required(self):
        for field in attestation.STATEMENT_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(attestation.AttestationRefused) as refused:
                    declared(**{field: ""})
                self.assertEqual(refused.exception.failed_predicate,
                                 "STATEMENT_DECLARES_EVERY_BOUND_FIELD")

    def test_the_receiver_reconstructs_the_statement_from_the_packet_alone(self):
        """A statement that travelled beside its signature is one the sender can edit."""
        payload = {"message_class": "ecosystem.communication", "body": {}}
        packet = kernel.build_packet(
            origin_org="StegVerse-org", origin_service="stegverse-org.org-control",
            destination_org=PEER, destination_service="stegverse-labs.org-control",
            payload=payload, standing=GENESIS,
            transition_reference="intr:transition:reconstruct",
            authority_effect="NONE", packet_id="reconstruct-1")
        recovered = kernel.recover_packet(kernel.carrier_frame(packet))
        self.assertEqual(
            attestation.statement_from_packet(packet, kernel.sha(payload)),
            attestation.statement_from_packet(recovered, kernel.sha(recovered["payload"])))

    def test_the_whole_statement_is_bound_into_the_signed_bytes(self):
        base = attestation.payload_bytes(declared())
        for field, value in (("origin_organization", PEER),
                             ("destination_organization", "StegGhost"),
                             ("destination_service", "stegghost.org-control"),
                             ("packet_id", "another-packet"),
                             ("payload_sha256", kernel.sha({"evil": True})),
                             ("transport_profile", "something.else.v1")):
            with self.subTest(field=field):
                self.assertNotEqual(attestation.payload_bytes(declared(**{field: value})), base)


class DelegationTests(unittest.TestCase):
    """This boundary asks. It does not verify, and it holds no key."""

    def test_no_credential_algorithm_is_implemented_here(self):
        source = (ROOT / MODULE).read_text(encoding="utf-8")
        for token in ("import hmac", "hmac.new", "hashlib.sha256", "compare_digest"):
            self.assertNotIn(token, source, token)

    def test_an_unreachable_authority_is_a_hold_not_a_pass(self):
        for authority in (None, {}, {"sign": None}, {"verify": lambda **k: None}):
            with self.subTest(authority=authority):
                with self.assertRaises(attestation.AttestationRefused) as refused:
                    attestation.attest(declared(), authority)
                self.assertEqual(refused.exception.failed_predicate,
                                 "CREDENTIAL_AUTHORITY_IS_REACHABLE")

    def test_the_authority_is_asked_to_sign_and_then_asked_to_verify(self):
        """Recording PROVEN on the strength of having asked would be asserting again."""
        authority = StandInAuthority()
        signature, receipt = attestation.attest(declared(), authority.mapping())
        self.assertEqual(len(authority.signed), 1)
        self.assertIs(receipt["signature_valid"], True)
        self.assertEqual(signature["algo"], "hmac-sha256")

    def test_a_receipt_from_another_authority_is_refused(self):
        with self.assertRaises(attestation.AttestationRefused) as refused:
            attestation.verify(declared(), StandInAuthority().sign(
                payload=attestation.payload_bytes(declared())),
                lambda **k: {"credential_authority": "SOMEONE_ELSE",
                             "operation": "TV_EXPORT_HMAC_VERIFY", "signature_valid": True})
        self.assertEqual(refused.exception.failed_predicate,
                         "RECEIPT_COMES_FROM_THE_DECLARED_CREDENTIAL_AUTHORITY")

    def test_a_signing_receipt_is_not_a_verification(self):
        with self.assertRaises(attestation.AttestationRefused) as refused:
            attestation.verify(declared(), StandInAuthority().sign(
                payload=attestation.payload_bytes(declared())),
                lambda **k: {"credential_authority": "TV/TVC",
                             "operation": "TV_EXPORT_HMAC_SIGN", "signature_valid": True})
        self.assertEqual(refused.exception.failed_predicate,
                         "RECEIPT_IS_A_VERIFICATION_NOT_ANOTHER_OPERATION")

    def test_an_authority_reporting_invalid_is_refused(self):
        authority = StandInAuthority()
        signature = authority.sign(payload=attestation.payload_bytes(declared()))
        forger = StandInAuthority(key=b"a-forgers-key")
        with self.assertRaises(attestation.AttestationRefused) as refused:
            attestation.verify(declared(), signature, forger.verify)
        self.assertEqual(refused.exception.failed_predicate,
                         "CREDENTIAL_AUTHORITY_REPORTS_THE_SIGNATURE_VALID")

    def test_a_signature_of_another_shape_or_algorithm_is_refused(self):
        authority = StandInAuthority()
        for carried, predicate in (
                ({"algo": "hmac-sha256", "value": "x"},
                 "SIGNATURE_IS_AN_OBJECT_OF_THE_AUTHORITYS_SHAPE"),
                ("a string", "SIGNATURE_IS_AN_OBJECT_OF_THE_AUTHORITYS_SHAPE"),
                ({"algo": "ed25519", "value": "x", "sha256": "y"},
                 "SIGNATURE_DECLARES_THE_AUTHORITYS_ALGORITHM")):
            with self.subTest(predicate=predicate):
                with self.assertRaises(attestation.AttestationRefused) as refused:
                    attestation.verify(declared(), carried, authority.verify)
                self.assertEqual(refused.exception.failed_predicate, predicate)

    def test_a_signature_cannot_be_moved_to_another_statement(self):
        authority = StandInAuthority()
        signature = authority.sign(payload=attestation.payload_bytes(declared()))
        for field, value in (("origin_organization", PEER),
                             ("packet_id", "another-packet"),
                             ("destination_organization", "StegGhost"),
                             ("payload_sha256", kernel.sha({"evil": True}))):
            with self.subTest(field=field):
                with self.assertRaises(attestation.AttestationRefused) as refused:
                    attestation.verify(declared(**{field: value}), signature, authority.verify)
                self.assertEqual(refused.exception.failed_predicate,
                                 "STATEMENT_MATCHES_WHAT_THE_AUTHORITY_SIGNED")


class RecordTests(unittest.TestCase):
    def test_an_offered_attestation_that_failed_is_not_an_absent_one(self):
        refused = attestation.refusal_record("SOME_PREDICATE", "because", declared())
        absent = attestation.unattested_record()
        self.assertEqual(refused["origin_attestation_state"], attestation.REFUSED)
        self.assertEqual(absent["origin_attestation_state"], attestation.NOT_PROVEN)
        self.assertNotEqual(refused["origin_attestation_state"],
                            absent["origin_attestation_state"])
        self.assertIs(refused["an_offered_attestation_that_failed_is_not_an_absent_one"], True)

    def test_the_record_carries_what_attestation_does_not_establish(self):
        authority = StandInAuthority()
        statement = declared()
        signature, receipt = attestation.attest(statement, authority.mapping())
        record = attestation.record(statement, signature, receipt)
        self.assertEqual(record["origin_attestation_state"], attestation.PROVEN)
        self.assertIs(record["proves_the_authority_signed_this_statement"], True)
        self.assertIs(record["proves_the_authority_authenticated_the_asker"], False)
        self.assertIs(record["asker_binding_is_the_credential_authoritys_to_establish"], True)
        self.assertIs(record["initiator_identification_also_requires_the_bilateral_match"], True)
        self.assertIs(record["attested_origin_is_an_identified_sender_not_an_authorized_one"], True)
        self.assertEqual(record["authority_effect"], "NONE_ATTESTATION_RECORD_ONLY")

    def test_the_unattested_record_is_what_every_crossing_carried_before(self):
        absent = attestation.unattested_record()
        self.assertIs(absent["origin_is_asserted_by_the_sender"], True)
        self.assertIs(absent["origin_is_verified_by_this_boundary"], False)
        self.assertIs(absent["no_attestation_was_offered"], True)


# Ported from StegVerse-org/.github@f791799 with paths and imports adapted.
# `CrossingTests` (emission and closure through
# resident-runtime/organization_egress_boundary.py, measured by
# resident-runtime/receipt_disorder_measurement.py) is not ported: this
# organization holds no receipt_disorder_measurement.py, and its egress emit()
# calls resident-runtime/aggregate_repo_transition.py::append, which this
# organization's ledger does not define. That gap is the egress boundary's, not
# the A4 contract's; the contract itself is held below and in
# tests/test_origin_attestation_tvc_conformance.py.


class BoundaryDeclarationTests(unittest.TestCase):
    def test_the_boundary_declares_the_binding_and_its_limit(self):
        block = BOUNDARY["egress"]["origin_attestation"]
        self.assertEqual(block["credential_authority"], "TV/TVC")
        self.assertEqual(block["verify_operation"], attestation.VERIFY_OPERATION)
        self.assertEqual(block["statement_fields"], list(attestation.STATEMENT_FIELDS))
        self.assertIs(block["proves_the_authority_signed_the_statement"], True)
        self.assertIs(block["proves_the_authority_authenticated_the_asker"], False)
        self.assertIs(block["verification_algorithm_implemented_here"], False)
        self.assertIs(block["boundary_holds_key_material"], False)

    def test_the_unattested_disposition_is_declared_not_implicit(self):
        block = BOUNDARY["egress"]["origin_attestation"]
        self.assertEqual(block["unattested_crossing_disposition"],
                         "ADMITTED_AND_RECORDED_AS_UNATTESTED")
        self.assertIs(
            block["requiring_attestation_is_an_owner_policy_decision_not_made_here"], True)


if __name__ == "__main__":
    unittest.main()
