"""Source integration only: synthetic decision fixture never proves live InTr."""
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from workers import org_federation_intr_profile as ingress


def load_ledger():
    spec = importlib.util.spec_from_file_location("existing_org_ledger", ROOT / "resident-runtime/aggregate_repo_transition.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FederationIngressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = load_ledger()
        self.env = patch.dict(os.environ, {
            "STEGVERSE_TVC_RELAY_AUTHORIZATION_ID": "test-authorized-relay",
            "STEGVERSE_ORG_LEDGER_ROOT": str(self.root / "org-ledger"),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.packet = ingress.K.build_packet(
            origin_org="External-Org", origin_service="external.service",
            destination_org="StegVerse-Labs", destination_service="stegverse-labs.org-control",
            payload={"message_class": "ecosystem.communication", "body": {"test": True}},
            transition_reference="federation.test.v1", authority_effect="NONE",
            packet_id="source-test-packet-001")
        self.frame = ingress.K.carrier_frame(self.packet, now_ns=1_800_000_000_000_000_000)
        self.request = self.make_request()
        self.calls = []

    def make_request(self, predecessor="GENESIS", canonical="GENESIS"):
        return {
            "schema": ingress.REQUEST_SCHEMA, "frame": self.frame,
            "packet_sha256": self.frame["packet_sha256"],
            "frame_sha256": self.frame["frame_sha256"],
            "payload_sha256": ingress.K.sha(self.packet["payload"]),
            "intr_decision_receipt_sha256": "d" * 64,
            "predecessor_organization_receipt_sha256": predecessor,
            "predecessor_canonical_receipt_sha256": canonical,
        }

    def headers(self, raw, relay="test-authorized-relay"):
        return {
            "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
            "X-StegVerse-Authorization-Id": relay,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
            "Content-Type": "application/json",
        }

    def decision(self, sha="d" * 64, disposition="ALLOW", frame=None):
        frame = self.frame if frame is None else frame
        return {
            "state": "PASS", "receipt_sha256": sha,
            "reconstructed_receipt_sha256": sha, "required_evidence_validation_status": "PASS",
            "master_records_grants_transition_authority": False,
            "receipt": {
                "schema": "stegverse.canonical-state-transition-receipt/v1",
                "transition_outcome": "ALLOW", "governance_decision_ref_where_applicable": "intr-authenticated-ref",
                "transition_evidence": {
                    "authority": "Interlock/InTr", "disposition": disposition,
                    "locally_generated_allow": False,
                    "packet_sha256": frame["packet_sha256"], "frame_sha256": frame["frame_sha256"],
                    "payload_sha256": ingress.K.sha(self.packet["payload"]),
                    "origin_organization": "External-Org", "destination_organization": "StegVerse-Labs",
                    "transition_id": "federation.test.v1",
                },
            },
        }

    def raw(self):
        return json.dumps(self.request, sort_keys=True, separators=(",", ":")).encode()

    def custody(self, receipt):
        self.calls.append(receipt)
        expectation = receipt["transition_evidence"]["expected_organization_previous_receipt_sha256"]
        org = self.ledger.aggregate_transition(
            receipt, expected_previous_receipt_sha256=expectation, enforce_expected_previous=True)
        digest = ingress.K.sha(receipt).split(":", 1)[1]
        return {
            "state": "RECORDED", "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS", "receipt_sha256": digest,
            "reconstructed_receipt_sha256": digest, "organization_receipt": org,
        }

    def admit(self, *, decision=None, custody=None):
        raw = self.raw()
        return ingress.admit(
            runtime_root=self.root, body=raw, headers=self.headers(raw),
            decision_reconstructor=(lambda _: self.decision() if decision is None else decision),
            custody_submit=self.custody if custody is None else custody)

    def test_positive_source_simulation_writes_exact_canonical_org_genesis(self):
        result = self.admit()
        self.assertEqual(result["state"], "INGRESS_RECORDED")
        self.assertFalse(result["receiver_execution_observed"])
        self.assertFalse(result["external_intr_allow_authenticated_by_runtime"])
        self.assertIsNone(result["predecessor_organization_receipt_sha256"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["transition_outcome"], "OBSERVED")
        self.assertEqual(result["organization_receipt_sha256"],
                         json.loads((self.root / "org-ledger/HEAD.json").read_text())["receipt_sha256"])
        self.assertEqual(self.admit(), result)
        self.assertEqual(len(self.calls), 1)

    def test_missing_or_wrong_relay_binding_rejected(self):
        raw = self.raw()
        with self.assertRaisesRegex(ValueError, "federation_tvc_relay_binding"):
            ingress.validate(body=raw, headers=self.headers(raw, "wrong"),
                             decision_reconstructor=lambda _: self.decision())
        with patch.dict(os.environ, {"STEGVERSE_TVC_RELAY_AUTHORIZATION_ID": ""}):
            with self.assertRaisesRegex(ValueError, "federation_tvc_relay_binding"):
                ingress.validate(body=raw, headers=self.headers(raw),
                                 decision_reconstructor=lambda _: self.decision())

    def test_external_allow_is_not_accepted_without_exact_reconstruction(self):
        raw = self.raw()
        with self.assertRaisesRegex(ValueError, "federation_external_decision_reconstruction_failed"):
            ingress.validate(body=raw, headers=self.headers(raw),
                             decision_reconstructor=lambda _: {"state": "BOUNDARY"})
        with self.assertRaisesRegex(ValueError, "federation_external_intr_decision_binding_mismatch"):
            ingress.validate(body=raw, headers=self.headers(raw),
                             decision_reconstructor=lambda _: self.decision(disposition="DENY"))

    def test_tampered_carrier_rejected(self):
        self.request["frame"]["packet_sha256"] = "sha256:" + "0" * 64
        raw = self.raw()
        with self.assertRaisesRegex(ValueError, "carrier_frame_hash_mismatch"):
            ingress.validate(body=raw, headers=self.headers(raw),
                             decision_reconstructor=lambda _: self.decision())

    def test_stale_organization_predecessor_rejected_before_custody(self):
        self.admit()
        self.frame = ingress.K.carrier_frame(
            ingress.K.build_packet(
                origin_org="External-Org", origin_service="external.service",
                destination_org="StegVerse-Labs", destination_service="stegverse-labs.org-control",
                payload={"message_class": "ecosystem.communication", "body": {"test": True}},
                transition_reference="federation.test.v1", authority_effect="NONE",
                packet_id="source-test-packet-002"), now_ns=1_800_000_000_000_000_000)
        self.packet = ingress.K.recover_packet(self.frame)
        self.request = self.make_request()
        with self.assertRaisesRegex(ValueError, "federation_org_immediate_predecessor_mismatch"):
            self.admit(decision=self.decision(frame=self.frame))
        self.assertEqual(len(self.calls), 1)

    def test_predecessor_head_tamper_rejected_by_ledger(self):
        first = self.admit()
        path = self.root / "org-ledger/HEAD.json"
        path.write_text(json.dumps({"receipt_sha256": "sha256:" + "0" * 64}))
        with self.assertRaisesRegex(ValueError, "organization_immediate_predecessor_unavailable"):
            self.ledger.aggregate_transition(self.calls[0])


if __name__ == "__main__":
    unittest.main()
