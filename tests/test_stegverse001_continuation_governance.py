from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "continue_stegverse001_evidence_chain.py"
WORKER_PATH = ROOT / "workers" / "stegverse001_evidence_chain_continuation_worker.py"
LEGACY_WATCHER = "watch_stegverse001_autonomy_receipt.py"
G23 = "sha256:81a078eeeacffb8fc86d287d7aaa8a9904c6f53973471dad7f6d7c3fa6818a35"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONT = load_module(SCRIPT_PATH, "sv001_continuation_governance")
WORKER = load_module(WORKER_PATH, "sv001_continuation_worker_governance")


class Sv001ContinuationGovernanceTests(unittest.TestCase):
    def write_json(self, path: Path, value: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def canonical_source(self) -> dict:
        return {
            "state": "COMPLETED",
            "transition_id": "SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED",
            "receipt_hash": G23,
            "authorized_execution": True,
        }

    def valid_admission(self) -> dict:
        return {
            "schema": "stegverse.master-records.sv001-custody-intr-admission/v1",
            "state": "INGRESS_ADMITTED",
            "governance_decision": "ALLOW",
            "transition_id": "SV001_MASTER_RECORDS_CUSTODY_AND_RECONSTRUCTION",
            "source_receipt_sha256": G23,
            "current_governance_decision_observed": True,
            "human_approval_checkpoint_inserted": False,
        }

    def test_observer_source_cannot_invoke_legacy_direct_custody_watcher(self):
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn(LEGACY_WATCHER, text)
        self.assertIn("custody_mutation_performed_by_observer", text)

    def test_missing_current_intr_admission_is_retryable_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = self.write_json(base / "source.json", self.canonical_source())
            result = CONT.continue_chain(
                ROOT,
                source_receipt=source,
                master_records_state=base / "mr",
                sv002_state=base / "sv002",
                intr_admission=base / "missing-admission.json",
            )
            self.assertEqual(result["state"], "CURRENT_INTR_ADMISSION_NOT_OBSERVED")
            self.assertTrue(result["retry_allowed"])
            self.assertFalse(result["custody_mutation_performed_by_observer"])
            self.assertFalse((base / "mr").exists())

    def test_denied_or_stale_admission_fails_closed(self):
        for mutation in (
            {"governance_decision": "DENY"},
            {"current_governance_decision_observed": False},
            {"source_receipt_sha256": "sha256:deadbeef"},
            {"human_approval_checkpoint_inserted": True},
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                source = self.write_json(base / "source.json", self.canonical_source())
                admission = self.valid_admission()
                admission.update(mutation)
                admission_path = self.write_json(base / "admission.json", admission)
                result = CONT.continue_chain(
                    ROOT,
                    source_receipt=source,
                    master_records_state=base / "mr",
                    sv002_state=base / "sv002",
                    intr_admission=admission_path,
                )
                self.assertEqual(result["state"], "CURRENT_INTR_ADMISSION_INVALID")
                self.assertFalse(result["retry_allowed"])
                self.assertFalse(result["custody_mutation_performed_by_observer"])

    def test_valid_allow_without_master_records_consequence_does_not_claim_success(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = self.write_json(base / "source.json", self.canonical_source())
            admission = self.write_json(base / "admission.json", self.valid_admission())
            result = CONT.continue_chain(
                ROOT,
                source_receipt=source,
                master_records_state=base / "mr",
                sv002_state=base / "sv002",
                intr_admission=admission,
            )
            self.assertEqual(result["state"], "MASTER_RECORDS_GOVERNED_CUSTODY_NOT_OBSERVED")
            self.assertTrue(result["retry_allowed"])
            self.assertFalse(result["custody_mutation_performed_by_observer"])

    def test_master_records_result_must_bind_exact_g23(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = self.write_json(base / "source.json", self.canonical_source())
            admission = self.write_json(base / "admission.json", self.valid_admission())
            mr_dir = base / "mr" / "receipts" / "stegverse001-bounded-autonomy"
            self.write_json(mr_dir / "resident-intake.latest.json", {"state": "PASS", "source_receipt_sha256": G23})
            self.write_json(mr_dir / "reconstruction.latest.json", {"state": "PASS", "source_receipt_sha256": "sha256:wrong"})
            result = CONT.continue_chain(
                ROOT,
                source_receipt=source,
                master_records_state=base / "mr",
                sv002_state=base / "sv002",
                intr_admission=admission,
            )
            self.assertEqual(result["state"], "MASTER_RECORDS_SOURCE_BINDING_MISMATCH")
            self.assertFalse(result["retry_allowed"])

    def test_worker_only_completes_on_observer_pass(self):
        pending = WORKER.worker_response({
            "continuation_state": "CURRENT_INTR_ADMISSION_NOT_OBSERVED",
            "local_receipt_ref": "receipts/latest.json",
            "continuation_result": {"retry_allowed": True},
        })
        self.assertEqual(pending["state"], "HANDOFF_READY")

        complete = WORKER.worker_response({
            "continuation_state": "PASS",
            "local_receipt_ref": "receipts/latest.json",
            "continuation_result": {"retry_allowed": False},
        })
        self.assertEqual(complete["state"], "COMPLETED")

    def test_worker_receipt_declares_no_custody_mutation(self):
        text = WORKER_PATH.read_text(encoding="utf-8")
        self.assertIn('"custody_mutation_performed_by_worker": False', text)
        self.assertIn('"prior_receipt_authorizes_next_transition": False', text)
        self.assertNotIn(LEGACY_WATCHER, text)


if __name__ == "__main__":
    unittest.main()
