import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workers import sv_dn1_browser_evidence_intr_ingress as ingress
from workers import sv_dn1_sdk_browser_evidence_adapter as adapter


class SvDn1BrowserEvidenceInTrIngressTests(unittest.TestCase):
    def _entry(self, rows, receipt):
        entry = {
            "schema": "stegos.web_bootstrap_journal_entry.v1",
            "sequence": len(rows) + 1,
            "previous_entry_sha256": rows[-1]["entry_sha256"] if rows else None,
            "receipt": receipt,
        }
        entry["receipt_sha256"] = adapter.sha256(receipt)
        entry["entry_sha256"] = adapter.sha256(entry)
        rows.append(entry)
        return entry

    def _bundle(self):
        rows = []
        claim = self._entry(rows, {
            "schema": "stegos.web_task_claim_receipt.v1",
            "task_id": "SV-DN1-RESIDENT-OBSERVER-001",
            "claim_id": "claim-1",
            "fencing_token": 1,
        })
        terminal = self._entry(rows, {
            "schema": "stegos.web_task_terminal_receipt.v1",
            "task_id": "SV-DN1-RESIDENT-OBSERVER-001",
            "claim_id": "claim-1",
            "fencing_token": 1,
            "state": "COMPLETED",
            "claim_entry_sha256": claim["entry_sha256"],
        })
        reconstruction = self._entry(rows, {
            "schema": "stegos.web_task_reconstruction_receipt.v1",
            "task_id": "SV-DN1-RESIDENT-OBSERVER-001",
            "claim_id": "claim-1",
            "fencing_token": 1,
            "state": "PASS",
            "terminal_entry_sha256": terminal["entry_sha256"],
            "same_execution": True,
        })
        tx = "sha256:" + "a" * 64
        exchange_id = "sha256:" + "b" * 64
        raw = "sha256:" + "c" * 64
        return {
            "schema": "stegverse.sv-dn1.browser-resident-observation-bundle/v3",
            "observation_class": "AUTHENTIC_ESTABLISHED_STEGVERSE_WEB_NODE",
            "state": "OBSERVED",
            "node_registration": {
                "node_id": "stegnode-web-" + "1" * 32,
                "device_continuity_id": "stegdevice-" + "2" * 40,
                "state": "ESTABLISHED",
                "credential_authority": "TV/TVC",
            },
            "resident_receipt": {
                "state": "COMPLETE",
                "transition_id": "SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE",
                "raw_response_sha256": raw,
                "semantic_exchange_id": exchange_id,
            },
            "source_capture": {"raw_sha256": raw},
            "semantic_exchange": {
                "exchange_id": exchange_id,
                "far_side_receipt": {"transformation_hash": tx},
            },
            "intr_receipt": {
                "state": "COMPLETE",
                "route_id": "SV-DN-1-HF-PUBLIC",
                "exchange_id": exchange_id,
                "transport_profile": ingress.TRANSPORT_PROFILE,
                "previous_receipt_hash": tx,
                "source_transform_hash": tx,
                "destination_validation": "PASS",
                "lineage_verified": True,
                "claims": {
                    "universal_intr_policy_id": ingress.POLICY_ID,
                    "boundary_from": "EXTERNAL_SYSTEM",
                    "boundary_to": "STEGOS_ECOSYSTEM",
                    "sdk_admitted": False,
                    "runtime_activation_claimed": False,
                    "production_interlock_runtime_activated": False,
                },
            },
            "claim_entry": claim,
            "terminal_entry": terminal,
            "reconstruction_entry": reconstruction,
            "continued_receipts": rows,
            "journal_replay": {
                "state": "PASS",
                "entries": len(rows),
                "tail_sha256": rows[-1]["entry_sha256"],
            },
        }

    def _transport(self):
        bundle = self._bundle()
        bundle_sha = ingress.sha_uri(bundle)
        materialization_id = "INTR-MAT-" + bundle_sha[7:31]
        reg = bundle["node_registration"]
        tail = bundle["journal_replay"]["tail_sha256"]
        interlock = {
            "schema": ingress.INTERLOCK_SCHEMA,
            "role": "SOURCE_EGRESS_INTERLOCK",
            "materialization_id": materialization_id,
            "profile_id": "SV-DN-1",
            "node_id": reg["node_id"],
            "device_continuity_id": reg["device_continuity_id"],
            "bundle_sha256": bundle_sha,
            "journal_tail_sha256": "sha256:" + tail,
            "prior_receipt_hash": "sha256:" + tail,
            "boundary_from": ingress.BOUNDARY_FROM,
            "boundary_to": ingress.BOUNDARY_TO,
            "transport_profile": ingress.TRANSPORT_PROFILE,
            "universal_intr_policy_id": ingress.POLICY_ID,
            "credential_authority": "TV/TVC",
            "credential_used": False,
            "authority_effect": "NONE",
        }
        interlock["receipt_hash"] = ingress.sha_uri(interlock)
        return {
            "schema": ingress.TRANSPORT_SCHEMA,
            "profile": ingress.PROFILE,
            "profile_id": "SV-DN-1",
            "materialization_id": materialization_id,
            "bundle_sha256": bundle_sha,
            "node_id": reg["node_id"],
            "device_continuity_id": reg["device_continuity_id"],
            "universal_intr_policy_id": ingress.POLICY_ID,
            "transport_profile": ingress.TRANSPORT_PROFILE,
            "boundary_from": ingress.BOUNDARY_FROM,
            "boundary_to": ingress.BOUNDARY_TO,
            "source_interlock_receipt": interlock,
            "previous_receipt_hash": interlock["receipt_hash"],
            "bundle": bundle,
            "request_grants_execution_authority": False,
            "claim_or_fence_minted": False,
            "credential_authority": "TV/TVC",
            "credential_used": False,
            "github_token_runtime_authority": "NONE",
            "sdk_admitted": False,
            "governance_decision_made": False,
            "repository_writeback_performed": False,
            "deployment_performed": False,
            "publication_decision_made": False,
            "certification_claimed": False,
            "authority_effect": "NONE_TRANSPORT_ONLY",
        }

    def test_valid_transport_materializes_bundle_and_locator(self):
        payload = self._transport()
        with tempfile.TemporaryDirectory() as td, patch.object(ingress, "dispatch_consumer", return_value={
            "consumer_dispatch_attempted": False,
            "consumer_execution_authority": False,
            "claim_or_fence_minted_by_ingress": False,
            "authority_effect": "NONE",
        }):
            root = Path(td)
            receipt = ingress.admit(runtime_root=root, payload=payload, transport_payload_sha256="f" * 64)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertTrue(receipt["exact_bundle_validated"])
            self.assertTrue(receipt["journal_replay_validated"])
            self.assertTrue(receipt["source_interlock_validated"])
            self.assertEqual(receipt["destination_validation"], "PASS")
            self.assertTrue(receipt["lineage_verified"])
            self.assertFalse(receipt["sdk_admitted"])
            locator = json.loads((root / ingress.LOCATOR_REL).read_text())
            self.assertEqual(locator["state"], "AVAILABLE_LOCAL_ONLY")
            self.assertTrue(Path(locator["bundle_path"]).is_file())
            persisted = json.loads(Path(locator["bundle_path"]).read_text())
            self.assertEqual(persisted, payload["bundle"])

    def test_tampered_bundle_fails_closed(self):
        payload = self._transport()
        payload["bundle"]["continued_receipts"][0]["receipt"]["claim_id"] = "tampered"
        with self.assertRaisesRegex(RuntimeError, "receipt hash mismatch"):
            ingress.validate_transport(payload)

    def test_source_interlock_hash_drift_fails_closed(self):
        payload = self._transport()
        payload["source_interlock_receipt"]["receipt_hash"] = "sha256:" + "0" * 64
        payload["previous_receipt_hash"] = payload["source_interlock_receipt"]["receipt_hash"]
        with self.assertRaisesRegex(ValueError, "source_interlock_receipt_hash_mismatch"):
            ingress.validate_transport(payload)

    def test_transport_may_not_claim_sdk_admission(self):
        payload = self._transport()
        payload["sdk_admitted"] = True
        with self.assertRaisesRegex(ValueError, "sdk_admitted_must_be_false"):
            ingress.validate_transport(payload)

    def test_materialization_id_is_content_addressed(self):
        payload = self._transport()
        payload["materialization_id"] = "INTR-MAT-" + "0" * 24
        with self.assertRaisesRegex(ValueError, "materialization_id_mismatch"):
            ingress.validate_transport(payload)


if __name__ == "__main__":
    unittest.main()
