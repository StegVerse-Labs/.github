import json
import tempfile
import unittest
from pathlib import Path

from workers import sv_dn1_sdk_browser_evidence_adapter as adapter


class SvDn1SdkBrowserEvidenceAdapterTests(unittest.TestCase):
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
            "node_registration": {"node_id": "n1", "device_continuity_id": "d1"},
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
                "transport_profile": "stegverse.universal-intr.adjacent-hop/v1",
                "previous_receipt_hash": tx,
                "source_transform_hash": tx,
                "destination_validation": "PASS",
                "lineage_verified": True,
                "claims": {
                    "universal_intr_policy_id": "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001",
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
            "journal_replay": {"state": "PASS", "entries": len(rows), "tail_sha256": rows[-1]["entry_sha256"]},
        }

    def test_valid_bundle_materializes_legacy_upstream_view(self):
        bundle = self._bundle()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "bundle.json"
            source.write_text(json.dumps(bundle), encoding="utf-8")
            resident, intr = adapter.materialize(source, root / "bound")
            self.assertEqual(json.loads((resident / "receipts/latest.json").read_text())["state"], "COMPLETE")
            self.assertEqual(json.loads((intr / "receipts/latest.json").read_text())["destination_validation"], "PASS")
            receipt = json.loads((root / "bound/upstream-adapter/adapter-receipt.json").read_text())
            self.assertTrue(receipt["existing_node_reused"])
            self.assertFalse(receipt["new_node_identity_minted"])

    def test_mutated_journal_fails_closed(self):
        bundle = self._bundle()
        bundle["continued_receipts"][0]["receipt"]["claim_id"] = "tampered"
        with self.assertRaisesRegex(RuntimeError, "receipt hash mismatch"):
            adapter.validate(bundle)

    def test_intr_lineage_drift_fails_closed(self):
        bundle = self._bundle()
        bundle["intr_receipt"]["previous_receipt_hash"] = "sha256:" + "d" * 64
        with self.assertRaisesRegex(RuntimeError, "previous-receipt lineage mismatch"):
            adapter.validate(bundle)

    def test_pre_sdk_bundle_may_not_claim_admission(self):
        bundle = self._bundle()
        bundle["intr_receipt"]["claims"]["sdk_admitted"] = True
        with self.assertRaisesRegex(RuntimeError, "overclaims activation/admission"):
            adapter.validate(bundle)


if __name__ == "__main__":
    unittest.main()
