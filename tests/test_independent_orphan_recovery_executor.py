from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_independent_orphan_recovery.py"
WORKER = ROOT / "workers" / "ecosystem_chat_orphan_recovery_worker.py"
spec = importlib.util.spec_from_file_location("independent_orphan_recovery_executor", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
worker_spec = importlib.util.spec_from_file_location("ecosystem_chat_orphan_recovery_worker", WORKER)
assert worker_spec and worker_spec.loader
worker_mod = importlib.util.module_from_spec(worker_spec)
worker_spec.loader.exec_module(worker_mod)


# Master Records boundary migration: the retained HB28 receipt carries this legacy field.
LEGACY_ORGANIZATION_RECORD_VALID_FIELD = "master_records_custody_valid"


class IndependentOrphanRecoveryExecutorTests(unittest.TestCase):
    def test_completed_registry_fragment_prevents_reacquisition(self) -> None:
        fragment = json.loads((ROOT / mod.FRAGMENT_PATH).read_text(encoding="utf-8"))
        task = next(row for row in fragment["tasks"] if row.get("task_id") == mod.RECOVERY_ID)
        self.assertEqual(task["state"], "COMPLETED")
        self.assertIsNone(task["claim_id"])
        self.assertEqual(task["admission"]["claim_state"], "TERMINAL_COMPLETED_NO_REACQUISITION")
        self.assertEqual(task["completion"]["recovery_fencing_token"], 22)
        self.assertFalse(task["completion"]["successor_authority_granted"])
        with self.assertRaisesRegex(RuntimeError, "not HANDOFF_READY"):
            mod.validate_registered_executor(ROOT)

    def test_current_terminal_receipt_binds_g22_without_parent_authority(self) -> None:
        receipt = json.loads((ROOT / "receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["recovery_fencing_token"], 22)
        self.assertGreater(receipt["recovery_fencing_token"], receipt["old_fencing_token"])
        self.assertTrue(receipt["checkpoint_valid"])
        # Retained receipt predates the Master Records boundary rename.
        self.assertTrue(receipt.get("master_records_organization_record_valid", receipt.get(LEGACY_ORGANIZATION_RECORD_VALID_FIELD)))
        self.assertTrue(receipt["old_authority_ended"])
        self.assertFalse(receipt["old_authority_reused"])
        self.assertFalse(receipt["successor_authority_granted"])
        self.assertEqual(receipt["next_transition"], "SEPARATE_HIGHER_FENCE_PARENT_SUCCESSOR_AUTHORIZATION")
        self.assertFalse(receipt["github_token_required"])
        self.assertFalse(receipt["third_party_execution_platform_required"])
        self.assertEqual(receipt["authority_effect"], "NONE")

    def test_recovery_package_contains_canonical_non_authorizing_g20_custody(self) -> None:
        path, custody = worker_mod.find_lifecycle_custody()
        self.assertIsNotNone(path)
        self.assertIsNotNone(custody)
        assert custody is not None
        self.assertEqual(custody["schema"], "stegverse.worker_lifecycle_custody.v2")
        self.assertEqual(custody["custody_id"], "SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001")
        self.assertTrue(custody["claim"]["released"])
        self.assertEqual(custody["claim"]["fencing_token"], 20)
        self.assertEqual(custody["custody"]["status"], "ACCEPTED_FOR_CUSTODY")
        self.assertEqual(custody["custody"]["reconstruction_status"], "PASS")
        self.assertEqual(custody["custody"]["authority_effect"], "NONE")
        self.assertFalse(custody["github_token_required"])
        self.assertEqual(worker_mod.canonical_master_records_ref(path), "master-records/orchestration:custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json")

    def _release_receipt(self, ledger: str, **evidence) -> dict:
        """Real producer: the G20 claim release appended to a tmp Organization ledger root."""
        from workers.canonical_state_transition_custody import build_state_receipt, submit_state_receipt

        with patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ledger}):
            result = submit_state_receipt(build_state_receipt(
                transition_id="WORKER_ORPHANED",
                transition_sequence=1,
                subject_or_correlation_id=worker_mod.PARENT_TASK,
                transition_outcome="OBSERVED",
                prior_state_ref_or_hash=None,
                resulting_state_ref_or_hash=None,
                governance_decision_ref_where_applicable=None,
                transition_evidence={"claim_id": worker_mod.OLD_CLAIM, "fencing_token": worker_mod.OLD_FENCE,
                                     "released": True, **evidence},
            ))
        return {"organization_receipt_sha256": result["organization_receipt"]["receipt_sha256"],
                "state_receipt_sha256": result["receipt_sha256"]}

    def test_historical_custody_without_organization_receipt_is_typed_fail_closed(self) -> None:
        _, custody = worker_mod.find_lifecycle_custody()
        self.assertNotIn("organization_receipt", custody)
        row, refusal = worker_mod.verify_released_claim_organization_receipt(custody)
        self.assertIsNone(row)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failed_predicate"], "RELEASED_CLAIM_ORGANIZATION_RECEIPT_ABSENT")
        self.assertEqual(refusal["retry_entrypoint"], worker_mod.VERIFY_ENTRYPOINT)
        self.assertEqual(refusal["satisfying_edge"], worker_mod.SATISFYING_EDGE)
        self.assertFalse(refusal["consequence_committed"])

    def test_released_claim_verifies_against_organization_receipt_not_master_records_pass(self) -> None:
        _, historical = worker_mod.find_lifecycle_custody()
        with tempfile.TemporaryDirectory() as ledger:
            record = dict(historical, organization_receipt=self._release_receipt(ledger))
            record["custody"] = {"authority_effect": "NONE"}  # no Master Records PASS at all
            row, refusal = worker_mod.verify_released_claim_organization_receipt(record, root=ledger)
            self.assertIsNone(refusal)
            self.assertEqual(row["receipt_sha256"], record["organization_receipt"]["organization_receipt_sha256"])

    def test_released_claim_refusals_are_typed(self) -> None:
        _, historical = worker_mod.find_lifecycle_custody()
        with tempfile.TemporaryDirectory() as ledger:
            wrong = dict(historical, organization_receipt=self._release_receipt(ledger, fencing_token=21))
            row, refusal = worker_mod.verify_released_claim_organization_receipt(wrong, root=ledger)
            self.assertIsNone(row)
            self.assertEqual((refusal["disposition"], refusal["failed_predicate"]),
                             ("DENY", "RELEASED_CLAIM_ORGANIZATION_RECEIPT_CLAIM_MISMATCH"))
            self.assertIsNone(refusal["retry_entrypoint"])
            good = self._release_receipt(ledger)
            crossed = dict(historical, organization_receipt=dict(
                good, state_receipt_sha256=wrong["organization_receipt"]["state_receipt_sha256"]))
            row, refusal = worker_mod.verify_released_claim_organization_receipt(crossed, root=ledger)
            self.assertEqual((refusal["disposition"], refusal["failed_predicate"]),
                             ("DENY", "ORGANIZATION_RECEIPT_NOT_BOUND_TO_STATE_RECEIPT"))
            # With no cache supplied, the receipt is read back from the locus the
            # Organization manifest declares (OL-1b), never from a host path.
            bound = dict(historical, organization_receipt=good)
            with patch.dict(os.environ, {}):
                os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT", None)
                row, refusal = worker_mod.verify_released_claim_organization_receipt(bound)
            self.assertIsNone(refusal)
            self.assertEqual(row["receipt_sha256"], good["organization_receipt_sha256"])

    def test_missing_carrier_snapshot_is_not_an_execution_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            epoch, observed = mod.current_reference_epoch(Path(tmp))
        self.assertEqual(epoch, 0)
        self.assertFalse(observed)


if __name__ == "__main__":
    unittest.main()
